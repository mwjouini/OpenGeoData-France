# -*- coding: utf-8 -*-
"""
Gestionnaire d'importation universel et résilient pour OpenGeoData France.
Prend en charge tous les formats géographiques et tabulaires :
- Flux WMS (GéoPlateforme IGN, Géorisques, BRGM, GPU, CRIGEs)
- Flux WFS (Admin Express, IRIS, BD TOPO, ZNIEFF, Natura 2000, GPU)
- Fonds XYZ (OpenStreetMap, etc.)
- Documents d'urbanisme CNIG (PLU, PLUi, POS, CC, SUP)
- Formats vectoriels standards (GeoPackage, Shapefile, GeoJSON, KML, GML, FlatGeoBuf, TAB, DXF, GPX)
- Formats raster (GeoTIFF, ECW, JP2, ASC, DEM, MNT)
- Données de transport (GTFS : stops + shapes, NeTEx XML / Transmodel)
- Tables et fichiers délimités (CSV, TSV, Parquet, JSON tabulaire COG INSEE, SIRENE)
- Détection par Magic Bytes, désarchivage récursif et découpage spatial territorial par commune / EPCI.
"""

import os
import json
import gzip
import shutil
import zipfile
import tempfile
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import ssl
import csv
import re
import time
import concurrent.futures
from ..models import DataItem, UrbanDocItem

try:
    from qgis.core import (
        QgsProject,
        QgsVectorLayer,
        QgsRasterLayer,
        QgsCoordinateReferenceSystem,
        QgsCoordinateTransform,
        QgsGeometry,
        QgsFeature,
        QgsJsonUtils,
        QgsFeatureRequest,
        QgsWkbTypes,
        QgsInvertedPolygonRenderer,
        QgsSingleSymbolRenderer,
        QgsFillSymbol,
        QgsSymbol,
        QgsRendererCategory,
        QgsCategorizedSymbolRenderer,
        QgsMessageLog,
        Qgis
    )
except ImportError:
    class _MockQgis:
        class MessageLevel:
            Info = 0
            Warning = 1
            Critical = 2
    Qgis = _MockQgis
    class _MockQgsMessageLog:
        @staticmethod
        def logMessage(msg, tag="", level=0):
            pass
    QgsMessageLog = _MockQgsMessageLog
    QgsProject = None
    QgsVectorLayer = None
    QgsRasterLayer = None
    QgsCoordinateReferenceSystem = None
    QgsCoordinateTransform = None
    QgsGeometry = None
    QgsFeature = None
    QgsJsonUtils = None
    QgsFeatureRequest = None
    QgsWkbTypes = None
    QgsInvertedPolygonRenderer = None
    QgsSingleSymbolRenderer = None
    QgsFillSymbol = None
    QgsSymbol = None
    QgsRendererCategory = None
    QgsCategorizedSymbolRenderer = None

from ..utils.ssl_helper import get_secure_ssl_context, fetch_url_bytes


class ImportManager:
    """Gestionnaire universel d'importation de couches géographiques et tabulaires dans QGIS."""

    DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 OpenGeoDataFR/1.1.0"

    def __init__(self, cache_dir=None):
        if cache_dir is None:
            base_dir = r"E:\OpenGeoData France"
            if os.path.exists(base_dir):
                self.cache_dir = os.path.join(base_dir, "cache")
            else:
                self.cache_dir = os.path.join(tempfile.gettempdir(), "opengeodata_cache")
        else:
            self.cache_dir = cache_dir

        os.makedirs(self.cache_dir, exist_ok=True)
        self.ssl_ctx = get_secure_ssl_context()
        self._geom_cache = {}
        self.created_layers = []

    def _is_main_thread(self):
        """Vérifie si le code s'exécute actuellement sur le thread graphique principal de QGIS / Qt."""
        try:
            from qgis.PyQt.QtWidgets import QApplication
            from qgis.PyQt.QtCore import QThread
            app = QApplication.instance()
            if app and QThread.currentThread() == app.thread():
                return True
        except (ImportError, AttributeError):
            return True
        return False

    def _add_layer_safely(self, layer, add_to_legend=True):
        """
        Enregistre la couche dans created_layers.
        Si l'appel s'exécute sur le thread principal GUI, l'ajoute immédiatement à QgsProject.
        Si l'appel s'exécute dans un QThread de travail, l'ajout à QgsProject est différé
        au thread principal via signal pour éviter tout crash C++ QSortFilterProxyModel.
        """
        if not layer or not layer.isValid():
            return
        if self._is_main_thread():
            try:
                if QgsProject and QgsProject.instance() and layer.id() not in QgsProject.instance().mapLayers():
                    QgsProject.instance().addMapLayer(layer, add_to_legend)
            except Exception as e:
                QgsMessageLog.logMessage(f"Erreur ajout direct couche QgsProject: {e}", "OpenGeoDataFR", Qgis.MessageLevel.Warning)
        if layer not in self.created_layers:
            self.created_layers.append(layer)

    def _fetch_url(self, req_or_url, timeout=30, max_retries=3):
        """Télécharge avec headers navigateur standards et mécanisme de réessai en cas d'interruption."""
        if isinstance(req_or_url, str):
            req = urllib.request.Request(req_or_url, headers={
                'User-Agent': self.DEFAULT_USER_AGENT,
                'Accept': '*/*',
                'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
                'Connection': 'keep-alive'
            })
        else:
            req = req_or_url
            if not req.has_header('User-agent'):
                req.add_header('User-Agent', self.DEFAULT_USER_AGENT)
            if not req.has_header('Accept'):
                req.add_header('Accept', '*/*')

        url_str = req.full_url if hasattr(req, 'full_url') else str(req)
        parsed = urllib.parse.urlparse(url_str)
        if parsed.scheme not in ('http', 'https'):
            raise ValueError(f"Protocole d'URL non autorisé : {parsed.scheme}")

        last_err = None
        for attempt in range(max_retries):
            try:
                return urllib.request.urlopen(req, timeout=timeout, context=self.ssl_ctx)  # nosec B310
            except Exception as ex:
                last_err = ex
                time.sleep(0.5 * (attempt + 1))

        raise last_err

    def _get_territory_geometry(self, territory_filter):
        """
        Récupère la géométrie polygonale officielle du territoire (Commune(s) / Département / EPCI / Région)
        avec mise en cache disque persistante et requêtes parallèles haute vitesse.
        Gère les listes de codes multiples (ex: 60010,60012,60054...), les EPCI (epci:200067098),
        les départements (dep:60) et les régions (reg:32).
        """
        if not territory_filter or str(territory_filter).lower() in ("france", "toutes les échelles", "all"):
            return None, None

        tf = str(territory_filter).strip()
        cache_key = f"geom_{tf}"
        if cache_key in self._geom_cache:
            return self._geom_cache[cache_key]

        geom_crs = "EPSG:4326"
        geom_cache_dir = os.path.join(self.cache_dir, "geoms")
        os.makedirs(geom_cache_dir, exist_ok=True)

        def _fetch_or_load_json(url, cache_filename):
            cache_file = os.path.join(geom_cache_dir, cache_filename)
            if os.path.exists(cache_file) and os.path.getsize(cache_file) > 10:
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception:
                    pass
            try:
                with self._fetch_url(url, timeout=12) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode('utf-8'))
                        try:
                            with open(cache_file, 'w', encoding='utf-8') as f:
                                json.dump(data, f)
                        except Exception:
                            pass
                        return data
            except Exception as e:
                QgsMessageLog.logMessage(f"Erreur téléchargement contour ({url}): {e}", "OpenGeoDataFR", Qgis.MessageLevel.Warning)
            return None

        def _geom_from_dict(geom_dict):
            if not geom_dict:
                return None
            if QgsJsonUtils is not None and hasattr(QgsJsonUtils, 'geometryFromGeoJson'):
                try:
                    return QgsJsonUtils.geometryFromGeoJson(json.dumps(geom_dict))
                except Exception:
                    return None
            return geom_dict

        collected_geoms = []

        # Cas 1 : EPCI (ex: epci:200067098 ou 9 chiffres)
        if tf.startswith("epci:") or (tf.isdigit() and len(tf) == 9):
            epci_code = tf.replace("epci:", "").strip()
            url = f"https://geo.api.gouv.fr/communes?codeEpci={epci_code}&geometry=contour&format=geojson"
            data = _fetch_or_load_json(url, f"epci_{epci_code}.geojson")
            if data and isinstance(data, dict) and 'features' in data:
                for feat in data['features']:
                    geom_dict = feat.get('geometry')
                    if geom_dict:
                        g = _geom_from_dict(geom_dict)
                        if g is not None:
                            collected_geoms.append(g)

        # Cas 2 : Département (ex: dep:60 ou 2/3 chiffres)
        elif tf.startswith("dep:") or (len(tf) in (2, 3) and (tf.isdigit() or tf.upper() in ('2A', '2B'))):
            dep_code = tf.replace("dep:", "").strip().upper()
            url = f"https://geo.api.gouv.fr/departements/{dep_code}?geometry=contour&format=geojson"
            data = _fetch_or_load_json(url, f"dep_{dep_code}.geojson")
            if data:
                geom_dict = data.get('geometry') if isinstance(data, dict) and 'geometry' in data else (data['features'][0].get('geometry') if isinstance(data, dict) and data.get('features') else None)
                if geom_dict:
                    g = _geom_from_dict(geom_dict)
                    if g is not None:
                        collected_geoms.append(g)

        # Cas 3 : Région (ex: reg:32)
        elif tf.startswith("reg:"):
            reg_code = tf.replace("reg:", "").strip()
            url = f"https://geo.api.gouv.fr/regions/{reg_code}?geometry=contour&format=geojson"
            data = _fetch_or_load_json(url, f"reg_{reg_code}.geojson")
            if data:
                geom_dict = data.get('geometry') if isinstance(data, dict) and 'geometry' in data else (data['features'][0].get('geometry') if isinstance(data, dict) and data.get('features') else None)
                if geom_dict:
                    g = _geom_from_dict(geom_dict)
                    if g is not None:
                        collected_geoms.append(g)

        # Cas 4 : Communes uniques ou multiples (ex: 60010,60012,60054...)
        else:
            codes = [c.strip() for c in tf.split(',') if c.strip()]
            
            def _fetch_commune_worker(c):
                c_clean = c.replace("epci:", "").replace("dep:", "").replace("reg:", "").replace("com:", "").strip()
                if c_clean.isdigit() and len(c_clean) == 5:
                    u = f"https://geo.api.gouv.fr/communes/{c_clean}?fields=nom,code&geometry=contour&format=geojson"
                    cf = f"com_{c_clean}.geojson"
                else:
                    u = f"https://geo.api.gouv.fr/communes?nom={urllib.parse.quote(c_clean)}&fields=nom,code&geometry=contour&format=geojson&limit=1"
                    cf = f"com_nom_{urllib.parse.quote(c_clean)}.geojson"
                return _fetch_or_load_json(u, cf)

            # Exécution parallèle multithreadée
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(12, len(codes) or 1)) as executor:
                futures = [executor.submit(_fetch_commune_worker, c) for c in codes]
                for f in concurrent.futures.as_completed(futures):
                    data = f.result()
                    if data:
                        geom_dict = None
                        if isinstance(data, dict):
                            if 'geometry' in data and data['geometry']:
                                geom_dict = data['geometry']
                            elif 'features' in data and data['features']:
                                geom_dict = data['features'][0].get('geometry')
                        elif isinstance(data, list) and data:
                            geom_dict = data[0].get('geometry') if isinstance(data[0], dict) else None

                        if geom_dict:
                            g = _geom_from_dict(geom_dict)
                            if g is not None:
                                collected_geoms.append(g)

        if not collected_geoms:
            self._geom_cache[cache_key] = (None, geom_crs)
            return None, geom_crs

        if QgsGeometry is None:
            self._geom_cache[cache_key] = (collected_geoms[0], geom_crs)
            return collected_geoms[0], geom_crs

        if len(collected_geoms) == 1:
            fused_geom = collected_geoms[0]
        else:
            try:
                fused_geom = QgsGeometry.unaryUnion(collected_geoms)
            except Exception:
                fused_geom = collected_geoms[0]
                for other in collected_geoms[1:]:
                    fused_geom = fused_geom.combine(other)

        # Réparation automatique si la géométrie résultante présente des auto-intersections
        if hasattr(fused_geom, 'makeValid') and not fused_geom.isGeosValid():
            try:
                fused_geom = fused_geom.makeValid()
            except Exception:
                pass

        self._geom_cache[cache_key] = (fused_geom, geom_crs)
        return fused_geom, geom_crs

    def import_item(self, item, as_wms=False, target_crs=None, territory_filter=None, progress_callback=None):
        """
        Importe un DataItem ou UrbanDocItem dans le projet QGIS actif avec gestion du CRS, filtre territorial et symbologie.
        Retourne (success, msg, created_layers).
        """
        if not item:
            return False, "Élément d'import non valide.", []

        self.created_layers = []

        try:
            if hasattr(item, 'doc_type') and item.data_type == "urban_doc":
                success, msg = self._import_urban_doc(item, as_wms=as_wms, target_crs=target_crs, territory_filter=territory_filter, progress_callback=progress_callback)
                return success, msg, self.created_layers

            if item.data_type == 'wms' or item.service_type == 'WMS' or as_wms:
                success, msg = self._import_wms_layer(item, target_crs=target_crs, territory_filter=territory_filter)
                return success, msg, self.created_layers

            if item.data_type == 'wfs' or item.service_type == 'WFS':
                success, msg = self._import_wfs_layer(item, target_crs=target_crs, territory_filter=territory_filter, progress_callback=progress_callback)
                return success, msg, self.created_layers

            if item.url:
                success, msg = self._import_file_resource(item, target_crs=target_crs, territory_filter=territory_filter, progress_callback=progress_callback)
                return success, msg, self.created_layers

            return False, "Aucune URL ni service valide trouvé pour cet élément.", []
        except Exception as e:
            QgsMessageLog.logMessage(f"Erreur d'importation: {e}", "OpenGeoDataFR", Qgis.MessageLevel.Critical)
            return False, f"Erreur lors de l'importation : {str(e)}", self.created_layers

    def _detect_file_type_from_bytes(self, filepath):
        """
        Détecte le type réel du fichier en inspectant ses premiers octets (Magic Bytes).
        Retourne : 'zip', 'gzip', 'sqlite', 'tiff', 'json', 'xml', 'csv', ou 'unknown'.
        """
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            return 'unknown'

        try:
            with open(filepath, 'rb') as f:
                header = f.read(512)

            if header.startswith(b'PK\x03\x04') or header.startswith(b'PK\x05\x06'):
                return 'zip'
            if header.startswith(b'\x1f\x8b'):
                return 'gzip'
            if header.startswith(b'SQLite format 3'):
                return 'sqlite'
            if header.startswith(b'II*\x00') or header.startswith(b'MM\x00*'):
                return 'tiff'
            
            clean_head = header.strip()
            if clean_head.startswith(b'{') or clean_head.startswith(b'['):
                return 'json'
            if clean_head.startswith(b'<?xml') or (clean_head.startswith(b'<') and b'>' in clean_head):
                return 'xml'
            
            # Détection texte / CSV
            try:
                text_sample = header.decode('utf-8-sig', errors='ignore')
                if any(delim in text_sample for delim in (',', ';', '\t', '|')) and '\n' in text_sample:
                    return 'csv'
            except Exception:
                pass

        except Exception as e:
            QgsMessageLog.logMessage(f"Erreur inspection magic bytes {filepath}: {e}", "OpenGeoDataFR", Qgis.MessageLevel.Warning)

        return 'unknown'

    @staticmethod
    def _safe_rename(src, dst):
        """
        Renomme ou copie de manière sécurisée un fichier sous Windows sans blocage WinError 32.
        """
        if not src or not os.path.exists(src) or src == dst:
            return dst if dst and os.path.exists(dst) else src
        try:
            if os.path.exists(dst):
                try:
                    os.remove(dst)
                except Exception:
                    pass
            os.replace(src, dst)
            return dst
        except Exception:
            try:
                shutil.copy2(src, dst)
                try:
                    os.remove(src)
                except Exception:
                    pass
                return dst
            except Exception:
                return src

    def download_file(self, url, filename_hint="downloaded_file", format_hint=None, progress_callback=None):
        """
        Télécharge une ressource de manière sécurisée et robuste avec streaming, inspection binaire et gestion d'archives.
        """
        try:
            url_clean = url.split('?')[0] if url else "file.dat"
            ext = os.path.splitext(url_clean)[1].lower()
            url_lower = (url or '').lower()
            fmt = (format_hint or '').lower().strip()

            if 'api-adresse.data.gouv.fr' in url_lower or 'ban' in url_lower or 'geocod' in url_lower:
                ext = '.geojson'
            elif 'geo.api.gouv.fr' in url_lower or 'outputformat=json' in url_lower or 'outputformat=application/json' in url_lower or 'format=geojson' in url_lower:
                ext = '.geojson'
            elif 'format=json' in url_lower:
                ext = '.json'
            elif not ext or len(ext) > 6 or ext in ('.php', '.asp', '.aspx', '.jsp', '.cgi', '.dat', '.bin', '.tmp', '.action', '/'):
                if 'geojson' in fmt or 'geojson' in url_lower:
                    ext = '.geojson'
                elif 'json' in fmt or 'json' in url_lower:
                    ext = '.json'
                elif 'csv' in fmt or 'csv' in url_lower:
                    ext = '.csv'
                elif 'xlsx' in fmt or 'excel' in fmt or 'xlsx' in url_lower:
                    ext = '.xlsx'
                elif 'xls' in fmt or 'xls' in url_lower:
                    ext = '.xls'
                elif 'ods' in fmt or 'ods' in url_lower:
                    ext = '.ods'
                elif 'parquet' in fmt:
                    ext = '.parquet'
                elif 'shp' in fmt or 'shape' in fmt or 'zip' in fmt:
                    ext = '.zip'
                elif 'gpkg' in fmt or 'geopackage' in fmt:
                    ext = '.gpkg'
                elif 'kml' in fmt:
                    ext = '.kml'
                elif 'gml' in fmt:
                    ext = '.gml'
                elif 'tif' in fmt or 'tiff' in fmt:
                    ext = '.tif'
                elif 'table' in fmt:
                    ext = '.csv'
                else:
                    ext = '.geojson' if ('search' in url_lower or 'api' in url_lower) else '.dat'

            safe_name = "".join([c for c in filename_hint if c.isalnum() or c in ('_', '-')])
            if not safe_name:
                safe_name = f"data_{int(time.time())}"

            dest_file = os.path.join(self.cache_dir, f"{safe_name}{ext}")

            if progress_callback:
                progress_callback("Connexion au serveur distant...")

            response = None
            try:
                response = self._fetch_url(url, timeout=35)
            except Exception as net_err:
                fallback_url = self._resolve_fallback_url(url)
                if fallback_url:
                    if progress_callback:
                        progress_callback("Lien mis à jour détecté, nouvelle tentative...")
                    response = self._fetch_url(fallback_url, timeout=35)
                    dest_file = os.path.join(self.cache_dir, f"{safe_name}_fallback{ext}")
                else:
                    raise net_err

            total_size = response.headers.get('content-length')
            total_size = int(total_size) if total_size and total_size.isdigit() else 0
            downloaded = 0
            chunk_size = 65536

            with open(dest_file, 'wb') as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0 and progress_callback:
                        pct = int((downloaded / total_size) * 100)
                        progress_callback(f"Téléchargement en cours : {pct}% ({downloaded // 1024} KB)")

            # Vérification de sécurité : si le serveur a renvoyé une page HTML (404/erreur camouflée)
            if dest_file.endswith(('.json', '.geojson', '.csv', '.zip', '.gpkg', '.tif', '.dat', '.xlsx', '.xls', '.ods')):
                try:
                    with open(dest_file, 'rb') as check_f:
                        start_bytes = check_f.read(256).strip()
                    if start_bytes.startswith(b'<!DOCTYPE') or start_bytes.startswith(b'<!doctype') or start_bytes.startswith(b'<html') or start_bytes.startswith(b'<HTML'):
                        os.remove(dest_file)
                        raise RuntimeError(f"Le serveur distant a renvoyé une page HTML au lieu du fichier géographique attendu ({url}).")
                except RuntimeError:
                    raise
                except Exception:
                    pass

        except Exception as e:
            QgsMessageLog.logMessage(f"Erreur téléchargement {url}: {e}", "OpenGeoDataFR", Qgis.MessageLevel.Critical)
            raise e

        # Détection automatique du type réel par Magic Bytes
        magic_type = self._detect_file_type_from_bytes(dest_file)

        # 1. Traitement GZIP (.gz ou magic bytes)
        if dest_file.endswith('.gz') or magic_type == 'gzip':
            if progress_callback:
                progress_callback("Décompression du fichier GZ en cours...")
            uncompressed_path = dest_file[:-3] if dest_file.endswith('.gz') else f"{dest_file}.unpacked"
            try:
                with gzip.open(dest_file, 'rb') as f_in, open(uncompressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
                return uncompressed_path
            except Exception as gz_err:
                QgsMessageLog.logMessage(f"Erreur décompression GZ: {gz_err}", "OpenGeoDataFR", Qgis.MessageLevel.Warning)
                return dest_file

        # Traitement spécial Spreadsheets (XLSX, XLS, ODS, Parquet)
        is_spreadsheet = dest_file.lower().endswith(('.xlsx', '.xls', '.ods', '.parquet')) or any(k in fmt for k in ('xlsx', 'xls', 'ods', 'excel', 'spreadsheet', 'parquet'))
        if is_spreadsheet:
            if not dest_file.lower().endswith(('.xlsx', '.xls', '.ods', '.parquet')):
                sheet_ext = '.xlsx' if ('xlsx' in fmt or 'excel' in fmt) else ('.xls' if 'xls' in fmt else ('.parquet' if 'parquet' in fmt else '.ods'))
                return self._safe_rename(dest_file, f"{dest_file}{sheet_ext}")
            return dest_file

        # 2. Traitement ZIP (.zip ou magic bytes)
        is_zip = not is_spreadsheet and (dest_file.endswith('.zip') or magic_type == 'zip' or zipfile.is_zipfile(dest_file))
        if is_zip:
            if progress_callback:
                progress_callback("Décompression de l'archive ZIP en cours...")
            extract_dir = os.path.join(self.cache_dir, safe_name)
            self._extract_archive_recursively(dest_file, extract_dir, progress_callback=progress_callback)
            return extract_dir

        # 3. Traitement JSON / GeoJSON par magic bytes
        if magic_type == 'json' and not dest_file.endswith(('.json', '.geojson')):
            return self._safe_rename(dest_file, f"{dest_file}.json")

        # 4. Traitement SQLite / GPKG par magic bytes
        if magic_type == 'sqlite' and not dest_file.endswith(('.gpkg', '.sqlite', '.db')):
            return self._safe_rename(dest_file, f"{dest_file}.gpkg")

        # 5. Traitement XML par magic bytes
        if magic_type == 'xml' and not dest_file.endswith(('.xml', '.gml')):
            return self._safe_rename(dest_file, f"{dest_file}.xml")

        return dest_file

    def _extract_archive_recursively(self, zip_path, extract_root, progress_callback=None):
        """
        Extrait une archive ZIP de manière sécurisée et récursive (gère les ZIPs imbriqués comme *.shp.zip).
        """
        os.makedirs(extract_root, exist_ok=True)
        extract_root_abs = os.path.abspath(extract_root)

        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for member in zip_ref.infolist():
                    member_path = os.path.abspath(os.path.join(extract_root, member.filename))
                    if not member_path.startswith(extract_root_abs + os.sep) and member_path != extract_root_abs:
                        raise RuntimeError(f"Tentative de traversée de répertoire détectée : {member.filename}")
                    zip_ref.extract(member, extract_root)

            # Détection et extraction des ZIPs imbriqués
            nested_zips = []
            for root, dirs, files in os.walk(extract_root):
                for f in files:
                    if f.lower().endswith('.zip') and not f.startswith('._'):
                        nested_zips.append(os.path.join(root, f))

            for nzip in nested_zips:
                sub_dir = os.path.splitext(nzip)[0]
                try:
                    with zipfile.ZipFile(nzip, 'r') as sub_ref:
                        sub_ref.extractall(sub_dir)
                except Exception as sub_err:
                    QgsMessageLog.logMessage(f"Erreur extraction ZIP imbriqué {nzip}: {sub_err}", "OpenGeoDataFR", Qgis.MessageLevel.Warning)

        except Exception as zip_err:
            QgsMessageLog.logMessage(f"Erreur décompression archive {zip_path}: {zip_err}", "OpenGeoDataFR", Qgis.MessageLevel.Warning)

    def _parse_gtfs_to_layers(self, folder_or_zip, title_prefix="GTFS"):
        """
        Parse un dossier ou une archive GTFS (stops.txt, shapes.txt) et génère des GeoJSON d'arrêts et de tracés.
        """
        created_geojson_paths = []
        folder = folder_or_zip
        if not os.path.isdir(folder):
            return created_geojson_paths

        stops_file = None
        shapes_file = None

        for root, dirs, files in os.walk(folder):
            for f in files:
                f_lower = f.lower()
                if f_lower == 'stops.txt':
                    stops_file = os.path.join(root, f)
                elif f_lower == 'shapes.txt':
                    shapes_file = os.path.join(root, f)

        # 1. Parsing stops.txt -> Arrêts (Point)
        if stops_file and os.path.exists(stops_file):
            try:
                features = []
                with open(stops_file, 'r', encoding='utf-8-sig', errors='replace') as sf:
                    reader = csv.DictReader(sf)
                    for row in reader:
                        lat_val = row.get('stop_lat') or row.get('lat') or row.get('latitude')
                        lon_val = row.get('stop_lon') or row.get('lon') or row.get('longitude')
                        if lat_val and lon_val:
                            try:
                                lat = float(lat_val.strip())
                                lon = float(lon_val.strip())
                                stop_name = row.get('stop_name') or row.get('name') or row.get('stop_id') or 'Arrêt'
                                features.append({
                                    "type": "Feature",
                                    "geometry": {"type": "Point", "coordinates": [lon, lat]},
                                    "properties": {k: v for k, v in row.items() if k not in ('stop_lat', 'stop_lon', 'lat', 'lon')}
                                })
                            except ValueError:
                                continue

                if features:
                    out_stops = os.path.join(self.cache_dir, f"{title_prefix}_arrets.geojson")
                    with open(out_stops, 'w', encoding='utf-8') as of:
                        json.dump({"type": "FeatureCollection", "features": features}, of, ensure_ascii=False)
                    created_geojson_paths.append((out_stops, f"{title_prefix} - Arrêts"))
            except Exception as e:
                QgsMessageLog.logMessage(f"Erreur parsing GTFS stops: {e}", "OpenGeoDataFR", Qgis.MessageLevel.Warning)

        # 2. Parsing shapes.txt -> Tracés de lignes (LineString)
        if shapes_file and os.path.exists(shapes_file):
            try:
                shapes_dict = {}
                with open(shapes_file, 'r', encoding='utf-8-sig', errors='replace') as shf:
                    reader = csv.DictReader(shf)
                    for row in reader:
                        shape_id = row.get('shape_id', 'line')
                        lat_val = row.get('shape_pt_lat') or row.get('lat')
                        lon_val = row.get('shape_pt_lon') or row.get('lon')
                        seq_val = row.get('shape_pt_sequence', '0')
                        if lat_val and lon_val:
                            try:
                                lat = float(lat_val.strip())
                                lon = float(lon_val.strip())
                                seq = int(seq_val.strip()) if seq_val.strip().isdigit() else 0
                                if shape_id not in shapes_dict:
                                    shapes_dict[shape_id] = []
                                shapes_dict[shape_id].append((seq, [lon, lat]))
                            except ValueError:
                                continue

                features = []
                for shape_id, pts in shapes_dict.items():
                    pts.sort(key=lambda x: x[0])
                    coords = [p[1] for p in pts]
                    if len(coords) >= 2:
                        features.append({
                            "type": "Feature",
                            "geometry": {"type": "LineString", "coordinates": coords},
                            "properties": {"shape_id": shape_id}
                        })

                if features:
                    out_shapes = os.path.join(self.cache_dir, f"{title_prefix}_traces.geojson")
                    with open(out_shapes, 'w', encoding='utf-8') as of:
                        json.dump({"type": "FeatureCollection", "features": features}, of, ensure_ascii=False)
                    created_geojson_paths.append((out_shapes, f"{title_prefix} - Tracés"))
            except Exception as e:
                QgsMessageLog.logMessage(f"Erreur parsing GTFS shapes: {e}", "OpenGeoDataFR", Qgis.MessageLevel.Warning)

        return created_geojson_paths

    def _parse_netex_to_layers(self, folder_or_file, title_prefix="NeTEx"):
        """
        Parse des fichiers NeTEx XML / Transmodel (arrets.xml, *.xml avec StopPlace / Quay / Centroid)
        et génère un GeoJSON ponctuel propre d'arrêts et de pôles d'échange.
        """
        xml_files = []
        if os.path.isfile(folder_or_file) and folder_or_file.lower().endswith('.xml'):
            xml_files.append(folder_or_file)
        elif os.path.isdir(folder_or_file):
            for root, dirs, files in os.walk(folder_or_file):
                for f in files:
                    if f.lower().endswith('.xml') and not f.startswith('._'):
                        xml_files.append(os.path.join(root, f))

        features = []
        seen_coords = set()

        for xml_path in xml_files:
            try:
                tree = ET.parse(xml_path)  # nosec B314
                root = tree.getroot()

                for elem in root.iter():
                    tag_clean = elem.tag.split('}')[-1]
                    
                    lon_elem = None
                    lat_elem = None
                    for child in elem.iter():
                        ctag = child.tag.split('}')[-1].lower()
                        if ctag in ('longitude', 'lon', 'pos_x') and child.text:
                            lon_elem = child
                        elif ctag in ('latitude', 'lat', 'pos_y') and child.text:
                            lat_elem = child

                    if lon_elem is not None and lat_elem is not None and lon_elem.text and lat_elem.text:
                        try:
                            lon = float(lon_elem.text.strip())
                            lat = float(lat_elem.text.strip())
                            
                            coord_key = (round(lon, 5), round(lat, 5))
                            if coord_key in seen_coords:
                                continue
                            seen_coords.add(coord_key)

                            name = None
                            for child in elem.iter():
                                ctag = child.tag.split('}')[-1].lower()
                                if ctag in ('name', 'nom', 'label', 'description') and child.text:
                                    name = child.text.strip()
                                    break

                            elem_id = elem.get('id', '')
                            props = {
                                "id": elem_id or f"{tag_clean}_{len(features)+1}",
                                "nom": name or tag_clean,
                                "type": tag_clean
                            }

                            features.append({
                                "type": "Feature",
                                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                                "properties": props
                            })
                        except ValueError:
                            continue
            except Exception as e:
                QgsMessageLog.logMessage(f"Erreur parsing NeTEx XML {xml_path}: {e}", "OpenGeoDataFR", Qgis.MessageLevel.Warning)

        if features:
            out_geojson = os.path.join(self.cache_dir, f"{title_prefix}_arrets.geojson")
            with open(out_geojson, 'w', encoding='utf-8') as of:
                json.dump({"type": "FeatureCollection", "features": features}, of, ensure_ascii=False)
            return [(out_geojson, f"{title_prefix} - Arrêts & Pôles")]

        return []

    def _resolve_fallback_url(self, failed_url):
        """
        Interroge l'API live de data.gouv.fr / GeoAPI / SNCF pour retrouver automatiquement l'URL active
        lorsqu'un permalien direct renvoie une erreur HTTP 404.
        """
        try:
            if 'cyclable' in failed_url.lower() or 'amenagements-cyclables' in failed_url.lower():
                return "https://static.data.gouv.fr/resources/amenagements-cyclables-france-metropolitaine/20260807-093353/france-20260807.geojson"

            if 'formes-des-lignes-du-rfn' in failed_url.lower() or 'sncf' in failed_url.lower():
                return "https://ressources.data.sncf.com/api/explore/v2.1/catalog/datasets/formes-des-lignes-du-rfn/exports/geojson"

            if 'covoiturage' in failed_url.lower() or 'bnlc' in failed_url.lower():
                return "https://static.data.gouv.fr/resources/base-nationale-des-lieux-de-covoiturage/20260818-211131/bnlc.csv"

            if 'irve' in failed_url.lower():
                return "https://static.data.gouv.fr/resources/points-de-recharge-pour-vehicules-electriques-pour-1000-hab/20260414-110820/irve-coord.geojson"

            if 'synop' in failed_url.lower() or 'meteo' in failed_url.lower():
                return "https://www.infoclimat.fr/opendata/stations_xhr.php?format=geojson"

            if 'cog' in failed_url.lower() or 'communes' in failed_url.lower():
                return "https://geo.api.gouv.fr/communes?fields=nom,code,codeDepartement,codeRegion,population&format=json"

            if 'resources/' in failed_url:
                slug = failed_url.split('resources/')[1].split('/')[0]
                api_search_url = f"https://www.data.gouv.fr/api/1/datasets/{slug}/"
                content = fetch_url_bytes(api_search_url, timeout_ms=5000)
                data = json.loads(content.decode('utf-8'))
                for r in data.get('resources', []):
                    u = r.get('url', '')
                    fmt = (r.get('format') or '').lower()
                    if ('geojson' in fmt or 'json' in fmt or 'shp' in fmt or 'csv' in fmt) and u != failed_url:
                        return u
        except Exception as ex:
            QgsMessageLog.logMessage(f"Échec résolution fallback URL pour {failed_url}: {ex}", "OpenGeoDataFR", Qgis.MessageLevel.Warning)
        return None

    def _apply_automatic_symbology(self, layer, item):
        """
        Applique automatiquement la symbologie et le style cartographique officiel français :
        - Cadastre Parcelles : Contour marron/orange fin (#b45014), fond transparent
        - Cadastre Bâtiments : Remplissage marron/orange (#dca078)
        - Urbanisme GPU (Zonage) : Rendu catégorisé (U: Rouge, AU: Orange, A: Jaune, N: Vert)
        - Adresses BAN / Météo / IRVE : Marqueurs ponctuels circulaires colorés
        - Limites administratives : Contours bleus épurés (#1a73e8)
        - Transports / Pistes cyclables : Lignes vertes (#2e7d32) ou gares/arrêts (#0277bd)
        - Risques / Inondations : Polygones bleus/rouges semi-transparents
        """
        if not layer or not layer.isValid() or not isinstance(layer, QgsVectorLayer):
            return

        try:
            from qgis.PyQt.QtGui import QColor

            layer_type = item.extra.get('layer_type') if hasattr(item, 'extra') and item.extra else ''
            title_lower = (getattr(layer, 'name', lambda: '')() or item.title or '').lower()
            geom_type = layer.geometryType()

            # 1. Cadastre : Parcelles vs Bâtiments
            if 'parcelle' in title_lower or layer_type == 'parcelle':
                if geom_type == 2:  # Polygon
                    sym = QgsFillSymbol.createSimple({
                        'color': '0,0,0,0',
                        'outline_color': '180,80,20,255',
                        'outline_width': '0.3',
                        'outline_style': 'solid'
                    })
                    layer.setRenderer(QgsSingleSymbolRenderer(sym))
                    layer.triggerRepaint()
            elif 'batiment' in title_lower or 'bâti' in title_lower or layer_type == 'batiment':
                if geom_type == 2:
                    sym = QgsFillSymbol.createSimple({
                        'color': '220,160,120,200',
                        'outline_color': '150,60,20,255',
                        'outline_width': '0.3',
                        'outline_style': 'solid'
                    })
                    layer.setRenderer(QgsSingleSymbolRenderer(sym))
                    layer.triggerRepaint()

            # 2. Urbanisme GPU : Zonage (U, AU, A, N)
            elif 'zone_urba' in title_lower or 'zonage' in title_lower or 'plu' in title_lower:
                if geom_type == 2 and 'typezone' in [f.name().lower() for f in layer.fields()]:
                    field_name = next(f.name() for f in layer.fields() if f.name().lower() == 'typezone')
                    colors = {
                        'U': QColor(227, 26, 28, 120),
                        'AU': QColor(255, 127, 0, 120),
                        'A': QColor(255, 255, 51, 120),
                        'N': QColor(51, 160, 44, 120)
                    }
                    categories = []
                    for val, col in colors.items():
                        s = QgsFillSymbol.createSimple({
                            'color': f"{col.red()},{col.green()},{col.blue()},{col.alpha()}",
                            'outline_color': '80,80,80,255',
                            'outline_width': '0.2'
                        })
                        categories.append(QgsRendererCategory(val, s, f"Zone {val}"))
                    layer.setRenderer(QgsCategorizedSymbolRenderer(field_name, categories))
                    layer.triggerRepaint()

            # 3. Adresses BAN / Stations Météo / IRVE
            elif any(x in title_lower for x in ('adresse', 'ban', 'irve', 'borne', 'station', 'meteo')):
                if geom_type == 0:  # Point
                    sym = QgsSymbol.defaultSymbol(geom_type)
                    if 'meteo' in title_lower or 'station' in title_lower:
                        sym.setColor(QColor(2, 136, 209))
                    elif 'irve' in title_lower or 'borne' in title_lower:
                        sym.setColor(QColor(0, 150, 136))
                    else:
                        sym.setColor(QColor(26, 115, 232))
                    sym.setSize(2.8)
                    layer.setRenderer(QgsSingleSymbolRenderer(sym))
                    layer.triggerRepaint()

            # 4. Pistes cyclables / Voies vertes
            elif 'cyclable' in title_lower or 'velo' in title_lower:
                if geom_type == 1:
                    sym = QgsSymbol.defaultSymbol(geom_type)
                    sym.setColor(QColor(46, 125, 50))
                    sym.setWidth(0.8)
                    layer.setRenderer(QgsSingleSymbolRenderer(sym))
                    layer.triggerRepaint()

            # 5. Limites Administratives
            elif any(x in title_lower for x in ('commune', 'département', 'iris', 'region')):
                if geom_type == 2:
                    sym = QgsSymbol.defaultSymbol(geom_type)
                    sym.setColor(QColor(26, 115, 232, 20))
                    if sym.symbolLayerCount() > 0:
                        sym.symbolLayer(0).setStrokeColor(QColor(26, 115, 232))
                        sym.symbolLayer(0).setStrokeWidth(0.6)
                    layer.setRenderer(QgsSingleSymbolRenderer(sym))
                    layer.triggerRepaint()
        except Exception as style_err:
            QgsMessageLog.logMessage(f"Application symbologie automatique ignorée: {style_err}", "OpenGeoDataFR", Qgis.MessageLevel.Warning)

    def _apply_crs_and_filters(self, layer, item, target_crs=None, territory_filter=None):
        if not layer or not layer.isValid():
            return layer

        reprojected_layer = layer

        try:
            if target_crs and target_crs != "Native" and "Variable" not in target_crs:
                target_crs_obj = QgsCoordinateReferenceSystem(target_crs)
                if target_crs_obj.isValid():
                    current_crs = layer.crs()
                    if not current_crs.isValid():
                        layer.setCrs(target_crs_obj)
                    elif current_crs.authid().upper() != target_crs_obj.authid().upper() and isinstance(layer, QgsVectorLayer):
                        try:
                            from qgis import processing
                            res = processing.run("native:reprojectlayer", {
                                'INPUT': layer,
                                'TARGET_CRS': target_crs_obj,
                                'OUTPUT': 'memory:'
                            })
                            if res and 'OUTPUT' in res and res['OUTPUT'].isValid():
                                reprojected_layer = res['OUTPUT']
                                reprojected_layer.setName(layer.name())
                        except Exception as reproj_err:
                            QgsMessageLog.logMessage(f"Reprojection native non effectuée: {reproj_err}", "OpenGeoDataFR", Qgis.MessageLevel.Warning)
        except Exception as crs_err:
            QgsMessageLog.logMessage(f"Gestion du CRS ignorée: {crs_err}", "OpenGeoDataFR", Qgis.MessageLevel.Warning)

        if isinstance(reprojected_layer, QgsVectorLayer) and reprojected_layer.isValid():
            target_for_filters = reprojected_layer

            # NIVEAU 1 : FILTRAGE ATTRIBUTAIRE AUTOMATIQUE
            try:
                code_insee = item.extra.get('code_insee')
                raw_filter = str(territory_filter or code_insee or '').strip()

                if raw_filter and raw_filter.lower() not in ("france", "toutes les échelles", "all"):
                    filter_codes = [c.strip() for c in raw_filter.split(',') if c.strip()]
                    fields = [f.name() for f in target_for_filters.fields()]
                    subset_clauses = []

                    for raw_code in filter_codes:
                        clean_filter = raw_code.replace("epci:", "").replace("dep:", "").replace("reg:", "").replace("com:", "").strip()
                        dep_code = None
                        if clean_filter.isdigit() and len(clean_filter) == 5:
                            dep_code = clean_filter[:2]
                            if clean_filter.startswith('97'):
                                dep_code = clean_filter[:3]

                        for fname in fields:
                            fname_lower = fname.lower()
                            if fname_lower in ('insee_com', 'code_insee', 'insee', 'code_com', 'insee_commune', 'cd_insee', 'depcom', 'code'):
                                if clean_filter.isdigit() and len(clean_filter) == 5:
                                    subset_clauses.append(f"{fname} = '{clean_filter}'")
                            elif fname_lower in ('insee_dep', 'code_dep', 'dep', 'departement', 'code_dept', 'dpt', 'cd_dep'):
                                if dep_code:
                                    subset_clauses.append(f"{fname} = '{dep_code}'")
                                elif (clean_filter.isdigit() and (len(clean_filter) == 2 or len(clean_filter) == 3)) or clean_filter.upper() in ('2A', '2B'):
                                    subset_clauses.append(f"{fname} = '{clean_filter}'")
                            elif fname_lower in ('code_reg', 'reg', 'insee_reg', 'reg_code', 'region', 'cd_reg'):
                                if clean_filter.isdigit() and len(clean_filter) == 2:
                                    subset_clauses.append(f"{fname} = '{clean_filter}'")
                            elif fname_lower in ('nom_com', 'nom', 'commune', 'nom_commune', 'nom_dept', 'nom_dep', 'nom_reg', 'region', 'libelle', 'libgeo'):
                                escaped_val = clean_filter.replace("'", "''")
                                subset_clauses.append(f"{fname} ILIKE '%{escaped_val}%'")

                    if subset_clauses:
                        clause = " OR ".join(subset_clauses)
                        target_for_filters.setSubsetString(clause)
                        if target_for_filters.featureCount() == 0:
                            target_for_filters.setSubsetString("")
            except Exception as filter_err:
                QgsMessageLog.logMessage(f"Erreur d'application du filtre par attribut: {filter_err}", "OpenGeoDataFR", Qgis.MessageLevel.Warning)

            # NIVEAU 2 : DÉCOUPAGE GÉOMÉTRIQUE SPATIAL SELON LE TERRITOIRE
            if territory_filter and str(territory_filter).lower() not in ("france", "toutes les échelles", "all"):
                try:
                    terr_geom, terr_crs_str = self._get_territory_geometry(territory_filter)
                    if terr_geom and not terr_geom.isEmpty():
                        layer_crs = target_for_filters.crs()
                        terr_crs = QgsCoordinateReferenceSystem(terr_crs_str)

                        terr_geom_transformed = QgsGeometry(terr_geom)
                        if layer_crs.isValid() and terr_crs.isValid() and layer_crs != terr_crs:
                            xform = QgsCoordinateTransform(terr_crs, layer_crs, QgsProject.instance() if QgsProject else None)
                            terr_geom_transformed.transform(xform)

                        terr_bbox = terr_geom_transformed.boundingBox()
                        bbox_request = QgsFeatureRequest().setFilterRect(terr_bbox)
                        clipped_features = []
                        is_point_layer = target_for_filters.geometryType() == QgsWkbTypes.PointGeometry

                        for feat in target_for_filters.getFeatures(bbox_request):
                            if feat.hasGeometry():
                                g = feat.geometry()
                                if is_point_layer:
                                    if terr_geom_transformed.contains(g) or g.intersects(terr_geom_transformed):
                                        clipped_features.append(feat)
                                else:
                                    if g.intersects(terr_geom_transformed):
                                        try:
                                            inter_geom = g.intersection(terr_geom_transformed)
                                            if inter_geom and not inter_geom.isEmpty():
                                                new_feat = QgsFeature(feat)
                                                new_feat.setGeometry(inter_geom)
                                                clipped_features.append(new_feat)
                                            else:
                                                clipped_features.append(feat)
                                        except Exception:
                                            clipped_features.append(feat)

                        if clipped_features:
                            geom_type_str = QgsWkbTypes.displayString(target_for_filters.wkbType())
                            crs_authid = target_for_filters.crs().authid()
                            clipped_name = f"{target_for_filters.name()} (Découpé)"
                            
                            clipped_layer = QgsVectorLayer(f"{geom_type_str}?crs={crs_authid}", clipped_name, "memory")
                            dp = clipped_layer.dataProvider()
                            dp.addAttributes(target_for_filters.fields().toList())
                            clipped_layer.updateFields()
                            dp.addFeatures(clipped_features)
                            clipped_layer.updateExtents()

                            reprojected_layer = clipped_layer
                            target_for_filters = clipped_layer
                except Exception as spatial_err:
                    QgsMessageLog.logMessage(f"Erreur découpage spatial: {spatial_err}", "OpenGeoDataFR", Qgis.MessageLevel.Warning)

            self._apply_automatic_symbology(target_for_filters, item)

        return reprojected_layer

    def _import_file_resource(self, item, target_crs=None, territory_filter=None, progress_callback=None):
        """
        Importe une ressource fichier avec support universel de tous les formats (archives, GTFS, NeTEx, multi-couches).
        """
        format_hint = item.extra.get('format') or item.data_type
        local_path = self.download_file(item.url, filename_hint=item.id, format_hint=format_hint, progress_callback=progress_callback)

        if not os.path.exists(local_path):
            return False, f"Impossible d'accéder au fichier téléchargé : {local_path}"

        # 1. SI C'EST UN DOSSIER D'EXTRACTION D'ARCHIVE (ZIP / TAR / GTFS / NETEX)
        if os.path.isdir(local_path):
            if progress_callback:
                progress_callback("Analyse du contenu de l'archive...")

            loaded_count = 0

            # A. Recherche de transport GTFS
            gtfs_layers = self._parse_gtfs_to_layers(local_path, title_prefix=item.title)
            for gpath, gtitle in gtfs_layers:
                layer = QgsVectorLayer(gpath, gtitle, "ogr")
                if layer.isValid():
                    final_layer = self._apply_crs_and_filters(layer, item, target_crs=target_crs, territory_filter=territory_filter)
                    self._add_layer_safely(final_layer)
                    loaded_count += 1

            # B. Recherche de transport NeTEx XML
            netex_layers = self._parse_netex_to_layers(local_path, title_prefix=item.title)
            for npath, ntitle in netex_layers:
                layer = QgsVectorLayer(npath, ntitle, "ogr")
                if layer.isValid():
                    final_layer = self._apply_crs_and_filters(layer, item, target_crs=target_crs, territory_filter=territory_filter)
                    self._add_layer_safely(final_layer)
                    loaded_count += 1

            # C. Recherche de fichiers vectoriels et tabulaires standards
            vector_files = []
            raster_files = []
            csv_files = []
            sheet_files = []

            for root, dirs, files in os.walk(local_path):
                for f in files:
                    if f.startswith('._'):
                        continue
                    f_lower = f.lower()
                    f_path = os.path.join(root, f)
                    
                    if f_lower.endswith(('.shp', '.geojson', '.gpkg', '.kml', '.tab', '.gml', '.fgb', '.sqlite', '.db', '.dxf', '.gpx')):
                        vector_files.append(f_path)
                    elif f_lower.endswith(('.tif', '.tiff', '.geotiff', '.asc', '.ecw', '.jp2', '.xyz', '.dem', '.img')):
                        raster_files.append(f_path)
                    elif f_lower.endswith('.csv') or (f_lower.endswith('.txt') and 'stops' not in f_lower and 'shapes' not in f_lower):
                        csv_files.append(f_path)
                    elif f_lower.endswith(('.xlsx', '.xls', '.ods', '.parquet', '.dbf', '.tsv')):
                        sheet_files.append(f_path)

            for vpath in vector_files:
                base_name = os.path.splitext(os.path.basename(vpath))[0]
                layer_title = f"{item.title} ({base_name})" if len(vector_files) > 1 else item.title
                layer = QgsVectorLayer(vpath, layer_title, "ogr")
                if layer.isValid():
                    final_layer = self._apply_crs_and_filters(layer, item, target_crs=target_crs, territory_filter=territory_filter)
                    self._add_layer_safely(final_layer)
                    loaded_count += 1

            for rpath in raster_files:
                base_name = os.path.splitext(os.path.basename(rpath))[0]
                layer_title = f"{item.title} ({base_name})" if len(raster_files) > 1 else item.title
                layer = QgsRasterLayer(rpath, layer_title)
                if layer.isValid():
                    final_layer = self._apply_crs_and_filters(layer, item, target_crs=target_crs, territory_filter=territory_filter)
                    self._add_layer_safely(final_layer)
                    loaded_count += 1

            for cpath in csv_files:
                success, _ = self._import_csv_layer(cpath, item, target_crs=target_crs, territory_filter=territory_filter)
                if success:
                    loaded_count += 1

            for spath in sheet_files:
                base_name = os.path.splitext(os.path.basename(spath))[0]
                layer_title = f"{item.title} ({base_name})" if len(sheet_files) > 1 else item.title
                layer = QgsVectorLayer(spath, layer_title, "ogr")
                if layer.isValid():
                    self._add_layer_safely(layer)
                    loaded_count += 1

            if loaded_count > 0:
                return True, f"{loaded_count} couche(s) extraite(s) et ajoutée(s) avec succès depuis l'archive."
            return False, f"Aucun fichier spatial ou tabulaire directement exploitable trouvé dans l'archive : {local_path}"

        # 2. FICHIER UNIQUE INDIVIDUEL
        ext = os.path.splitext(local_path)[1].lower()

        # A. Raster (GeoTIFF, ECW, etc.)
        if ext in ('.tif', '.tiff', '.geotiff', '.asc', '.ecw', '.jp2', '.xyz', '.dem'):
            layer = QgsRasterLayer(local_path, item.title)
            if layer.isValid():
                final_layer = self._apply_crs_and_filters(layer, item, target_crs=target_crs)
                self._add_layer_safely(final_layer)
                return True, f"Couche raster '{item.title}' ajoutée avec succès."
            return False, "Échec de chargement de la couche raster."

        # B. Tableaux & Tableurs Excel / LibreOffice (XLSX, XLS, ODS, Parquet, DBF, TSV)
        if ext in ('.xlsx', '.xls', '.ods', '.parquet', '.dbf', '.tsv') or any(k in str(format_hint).lower() for k in ('xlsx', 'xls', 'ods', 'excel', 'spreadsheet', 'parquet')):
            layer = QgsVectorLayer(local_path, item.title, "ogr")
            if layer.isValid():
                self._add_layer_safely(layer)
                return True, f"Table de données '{item.title}' (Excel/ODS) ajoutée avec succès dans QGIS."

        # C. Tableaux CSV / Délimités
        if ext == '.csv' or item.data_type == 'table' or (format_hint and 'csv' in format_hint.lower()):
            success, msg = self._import_csv_layer(local_path, item, target_crs=target_crs, territory_filter=territory_filter)
            if success:
                return True, msg

        # D. Vecteur OGR standard (Shapefile, GeoPackage, GeoJSON, KML, GML, TAB, GPX, etc.)
        layer = QgsVectorLayer(local_path, item.title, "ogr")
        if layer.isValid():
            final_layer = self._apply_crs_and_filters(layer, item, target_crs=target_crs, territory_filter=territory_filter)
            self._add_layer_safely(final_layer)
            return True, f"Couche vectorielle '{item.title}' ajoutée avec succès."

        # E. Fichiers XML / NeTEx autonomes
        if ext in ('.xml', '.gml'):
            netex_res = self._parse_netex_to_layers(local_path, title_prefix=item.title)
            if netex_res:
                gpath, gtitle = netex_res[0]
                layer = QgsVectorLayer(gpath, gtitle, "ogr")
                if layer.isValid():
                    final_layer = self._apply_crs_and_filters(layer, item, target_crs=target_crs, territory_filter=territory_filter)
                    self._add_layer_safely(final_layer)
                    return True, f"Couche NeTEx '{item.title}' extraite et ajoutée avec succès."

        # F. JSON / APIs REST à convertir en GeoJSON ou Table CSV
        if ext in ('.json', '.dat') or 'json' in ext:
            converted_path, convert_msg, is_table = self._try_convert_json_to_spatial_or_table(local_path)
            if converted_path and os.path.exists(converted_path):
                if is_table:
                    success, msg = self._import_csv_layer(converted_path, item, target_crs=target_crs, territory_filter=territory_filter)
                    if success:
                        return True, f"Table attributaire '{item.title}' ajoutée avec succès."
                else:
                    layer = QgsVectorLayer(converted_path, item.title, "ogr")
                    if layer.isValid():
                        final_layer = self._apply_crs_and_filters(layer, item, target_crs=target_crs, territory_filter=territory_filter)
                        self._add_layer_safely(final_layer)
                        return True, f"Couche vectorielle '{item.title}' convertie et ajoutée avec succès."

            return False, f"Le fichier ne contient pas de données exploitables.\nDétail: {convert_msg}"

        return False, f"Format non valide pour le fichier : {local_path}"

    def _import_csv_layer(self, local_path, item, target_crs=None, territory_filter=None):
        """
        Importe un fichier CSV avec détection intelligente des coordonnées (Lon/Lat, X/Y Lambert-93, WKT, geo_point_2d).
        """
        try:
            from qgis.PyQt.QtWidgets import QApplication
            from qgis.PyQt.QtCore import QThread
            from ..ui.csv_import_dialog import CSVImportDialog
            from ..ui import qt_compat

            if QApplication.instance() and QThread.currentThread() == QApplication.instance().thread():
                dlg = CSVImportDialog(local_path, layer_title=item.title)
                res = qt_compat.exec_dialog(dlg)
                if res == qt_compat.DialogAccepted:
                    if dlg.selected_uri:
                        layer = QgsVectorLayer(dlg.selected_uri, item.title, "delimitedtext")
                        if layer.isValid():
                            final_layer = self._apply_crs_and_filters(layer, item, target_crs=target_crs, territory_filter=territory_filter)
                            self._add_layer_safely(final_layer)
                            return True, f"Couche CSV '{item.title}' configurée et ajoutée avec succès !"
                        else:
                            return False, "Impossible de charger la couche CSV avec la configuration sélectionnée."
                    return False, "Aucune configuration de géométrie sélectionnée."
                elif res == qt_compat.DialogRejected:
                    return False, "Importation CSV annulée par l'utilisateur."
        except Exception as dialog_err:
            QgsMessageLog.logMessage(f"CSVImportDialog non exécuté: {dialog_err}", "OpenGeoDataFR", Qgis.MessageLevel.Warning)

        delimiter = ";"
        encoding = "utf-8-sig"
        x_field, y_field, wkt_field = None, None, None
        is_lambert93 = False

        try:
            with open(local_path, 'r', encoding='utf-8-sig', errors='replace') as f:
                first_lines = [f.readline() for _ in range(3)]
                sample_text = "".join(first_lines)

                # Comptage robuste des délimiteurs
                counts = {
                    ';': sample_text.count(';'),
                    ',': sample_text.count(','),
                    '\t': sample_text.count('\t'),
                    '|': sample_text.count('|')
                }
                delimiter = max(counts, key=counts.get) if max(counts.values()) > 0 else ","

                first_line = first_lines[0] if first_lines else ""
                raw_headers = [h.strip().strip('"').strip("'") for h in first_line.split(delimiter)]
                headers = [h.lower() for h in raw_headers]

                # Dictionnaire de correspondance exacte pour préserver la casse originale
                header_map = {h.lower(): orig for h, orig in zip(headers, raw_headers)}

                # Détection WKT
                for h in headers:
                    if h in ('wkt', 'geom', 'geometry', 'the_geom', 'geometrie', 'shape'):
                        wkt_field = header_map[h]
                        break

                # Détection X / Longitude et Y / Latitude
                lon_candidates = ('lon', 'lng', 'longitude', 'x', 'x_coord', 'xlongitude', 'x_longitude', 'xlong', 'x_long', 'long', 'coord_x', 'longitude_wgs84', 'lon_wgs84', 'x_wgs84', 'x_centroid', 'lon_dd', 'lon_pt')
                lat_candidates = ('lat', 'latitude', 'y', 'y_coord', 'ylatitude', 'y_latitude', 'ylat', 'y_lat', 'coord_y', 'latitude_wgs84', 'lat_wgs84', 'y_wgs84', 'y_centroid', 'lat_dd', 'lat_pt')
                l93_x_candidates = ('x_l93', 'x_lambert93', 'x_lambert_93', 'coord_x_l93', 'epsg_2154_x')
                l93_y_candidates = ('y_l93', 'y_lambert93', 'y_lambert_93', 'coord_y_l93', 'epsg_2154_y')

                if not wkt_field:
                    for h in headers:
                        if h in lon_candidates:
                            x_field = header_map[h]
                        elif h in lat_candidates:
                            y_field = header_map[h]
                        elif h in l93_x_candidates:
                            x_field = header_map[h]
                            is_lambert93 = True
                        elif h in l93_y_candidates:
                            y_field = header_map[h]
                            is_lambert93 = True

                # Détection de colonne composite geo_point_2d ou coordonnees
                if not (x_field and y_field) and not wkt_field:
                    for h in headers:
                        if h in ('geo_point_2d', 'coordonnees', 'coordinates', 'position', 'geom_x_y', 'coordonnees_xy', 'lat_lon'):
                            converted_csv = self._expand_composite_coords_csv(local_path, delimiter, header_map[h])
                            if converted_csv:
                                return self._import_csv_layer(converted_csv, item, target_crs=target_crs, territory_filter=territory_filter)

        except Exception as e:
            QgsMessageLog.logMessage(f"Erreur analyse CSV: {e}", "OpenGeoDataFR", Qgis.MessageLevel.Warning)

        csv_crs = "EPSG:2154" if is_lambert93 else (target_crs if (target_crs and "Native" not in target_crs) else "EPSG:4326")
        delim_encoded = urllib.parse.quote(delimiter)

        if x_field and y_field:
            uri = f"file:///{local_path}?delimiter={delim_encoded}&useHeader=yes&xField={urllib.parse.quote(x_field)}&yField={urllib.parse.quote(y_field)}&crs={csv_crs}&encoding={encoding}"
            layer = QgsVectorLayer(uri, item.title, "delimitedtext")
            if layer.isValid() and layer.featureCount() > 0:
                final_layer = self._apply_crs_and_filters(layer, item, target_crs=target_crs, territory_filter=territory_filter)
                self._add_layer_safely(final_layer)
                return True, f"Couche ponctuelle CSV '{item.title}' [{layer.featureCount()} entités] ajoutée avec succès."

        if wkt_field:
            uri = f"file:///{local_path}?delimiter={delim_encoded}&useHeader=yes&wktField={urllib.parse.quote(wkt_field)}&crs={csv_crs}&encoding={encoding}"
            layer = QgsVectorLayer(uri, item.title, "delimitedtext")
            if layer.isValid() and layer.featureCount() > 0:
                final_layer = self._apply_crs_and_filters(layer, item, target_crs=target_crs, territory_filter=territory_filter)
                self._add_layer_safely(final_layer)
                return True, f"Couche vectorielle WKT CSV '{item.title}' ajoutée avec succès."

        # Import en tant que table attributaire (sans géométrie)
        uri = f"file:///{local_path}?delimiter={delim_encoded}&useHeader=yes&type=csv&geometry=none&encoding={encoding}"
        layer = QgsVectorLayer(uri, item.title, "delimitedtext")
        if not layer.isValid():
            layer = QgsVectorLayer(local_path, item.title, "ogr")

        if layer.isValid():
            final_layer = self._apply_crs_and_filters(layer, item, target_crs=target_crs, territory_filter=territory_filter)
            self._add_layer_safely(final_layer)
            return True, f"Table attributaire CSV '{item.title}' ajoutée avec succès au projet."

        return False, "Échec de lecture du fichier CSV."

    def _expand_composite_coords_csv(self, local_path, delimiter, coord_col_name):
        """
        Extrait les coordonnées d'une colonne composite (ex: '48.8566, 2.3522' ou '[2.3522, 48.8566]')
        et génère un CSV propre avec colonnes latitude et longitude.
        """
        try:
            out_path = local_path + ".split_coords.csv"
            with open(local_path, 'r', encoding='utf-8-sig', errors='replace') as in_f, open(out_path, 'w', encoding='utf-8', newline='') as out_f:
                reader = csv.DictReader(in_f, delimiter=delimiter)
                if not reader.fieldnames:
                    return None
                
                fieldnames = list(reader.fieldnames) + ['calculated_latitude', 'calculated_longitude']
                writer = csv.DictWriter(out_f, fieldnames=fieldnames, delimiter=delimiter)
                writer.writeheader()

                for row in reader:
                    raw_val = row.get(coord_col_name, '') or ''
                    clean_val = raw_val.replace('[', '').replace(']', '').replace('(', '').replace(')', '').strip()
                    parts = re.split(r'[,;\s]+', clean_val)
                    if len(parts) >= 2:
                        try:
                            v1 = float(parts[0])
                            v2 = float(parts[1])
                            if -10 <= v1 <= 15 and 35 <= v2 <= 55:
                                lon, lat = v1, v2
                            else:
                                lat, lon = v1, v2
                            row['calculated_latitude'] = str(lat)
                            row['calculated_longitude'] = str(lon)
                        except ValueError:
                            pass
                    writer.writerow(row)

            return out_path
        except Exception as e:
            QgsMessageLog.logMessage(f"Erreur expansion composite coords CSV: {e}", "OpenGeoDataFR", Qgis.MessageLevel.Warning)
            return None

    def _try_convert_json_to_spatial_or_table(self, filepath):
        """
        Analyse un JSON pour déterminer s'il s'agit d'un GeoJSON ou d'une table d'attributs (ex: COG Communes INSEE).
        Retourne (out_path, message, is_table).
        """
        content = None
        try:
            with open(filepath, 'r', encoding='utf-8-sig', errors='replace') as f:
                content = json.load(f)
        except Exception as e:
            return None, f"JSON illisible : {e}", False

        if isinstance(content, dict) and content.get('type') in ('FeatureCollection', 'Feature'):
            return filepath, "GeoJSON valide.", False

        # GBFS Feeds (vélos / trottinettes)
        if isinstance(content, dict) and 'data' in content and isinstance(content['data'], dict) and 'feeds' in content['data']:
            feeds = content['data']['feeds']
            target_feed_url = None
            for feed in feeds:
                fname = feed.get('name', '').lower()
                if fname in ('station_information', 'geofencing_zones', 'free_bike_status', 'stations', 'vehicles'):
                    target_feed_url = feed.get('url')
                    break
            
            if not target_feed_url and len(feeds) > 0:
                target_feed_url = feeds[0].get('url')

            if target_feed_url:
                try:
                    with self._fetch_url(target_feed_url, timeout=10) as resp:
                        sub_content = json.loads(resp.read().decode('utf-8-sig'))
                        return self._parse_json_features(sub_content, filepath)
                except Exception as ex:
                    QgsMessageLog.logMessage(f"Erreur téléchargement sub-feed GBFS: {ex}", "OpenGeoDataFR", Qgis.MessageLevel.Warning)

        return self._parse_json_features(content, filepath)

    def _parse_json_features(self, content, orig_filepath):
        features = []
        items = []

        if isinstance(content, list):
            items = content
        elif isinstance(content, dict):
            if 'features' in content and isinstance(content['features'], list):
                items = content['features']
            elif 'results' in content and isinstance(content['results'], list):
                items = content['results']
            elif 'records' in content and isinstance(content['records'], list):
                items = content['records']
            elif 'data' in content:
                d = content['data']
                if isinstance(d, list):
                    items = d
                elif isinstance(d, dict):
                    for k in ('stations', 'vehicles', 'geofencing_zones', 'items', 'features', 'results'):
                        if k in d and isinstance(d[k], list):
                            items = d[k]
                            break
                    if not items:
                        for v in d.values():
                            if isinstance(v, list):
                                items = v
                                break

        for item in items:
            if not isinstance(item, dict):
                continue

            geom = None
            props = dict(item)

            if 'geometry' in item and isinstance(item['geometry'], dict):
                geom = item['geometry']
                props.pop('geometry', None)

            elif 'geo_point_2d' in item and isinstance(item['geo_point_2d'], dict):
                g2d = item['geo_point_2d']
                if 'lon' in g2d and 'lat' in g2d:
                    geom = {"type": "Point", "coordinates": [float(g2d['lon']), float(g2d['lat'])]}

            elif any(k in item for k in ('lat', 'latitude', 'LAT', 'LATITUDE', 'lat_wgs84')) and any(k in item for k in ('lon', 'lng', 'longitude', 'LON', 'LONGITUDE', 'lon_wgs84')):
                try:
                    lat_k = next(k for k in ('lat', 'latitude', 'LAT', 'LATITUDE', 'lat_wgs84') if k in item)
                    lon_k = next(k for k in ('lon', 'lng', 'longitude', 'LON', 'LONGITUDE', 'lon_wgs84') if k in item)
                    lat = float(item[lat_k])
                    lon = float(item[lon_k])
                    geom = {
                        "type": "Point",
                        "coordinates": [lon, lat]
                    }
                except (ValueError, TypeError):
                    geom = None

            if geom:
                features.append({
                    "type": "Feature",
                    "geometry": geom,
                    "properties": props
                })

        if features:
            geojson_data = {
                "type": "FeatureCollection",
                "features": features
            }
            out_path = orig_filepath + ".converted.geojson"
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(geojson_data, f, ensure_ascii=False)
            return out_path, f"{len(features)} entités spatiales extraites avec succès.", False

        # Si aucune géométrie n'est présente, conversion en table CSV propre
        if items and isinstance(items[0], dict):
            try:
                csv_path = orig_filepath + ".converted_table.csv"
                fieldnames = list(items[0].keys())
                with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f_out:
                    writer = csv.DictWriter(f_out, fieldnames=fieldnames, delimiter=';')
                    writer.writeheader()
                    for row in items:
                        clean_row = {}
                        for k in fieldnames:
                            v = row.get(k, '')
                            if isinstance(v, (list, dict)):
                                clean_row[k] = json.dumps(v, ensure_ascii=False)
                            else:
                                clean_row[k] = str(v) if v is not None else ''
                        writer.writerow(clean_row)
                return csv_path, f"{len(items)} enregistrements tabulaires extraits.", True
            except Exception as tab_err:
                QgsMessageLog.logMessage(f"Erreur conversion JSON en table CSV: {tab_err}", "OpenGeoDataFR", Qgis.MessageLevel.Warning)

        return None, "Aucune donnée géographique ni tabulaire exploitable trouvée.", False

    def _clean_ogc_url(self, raw_url):
        if not raw_url:
            return "", None

        try:
            parsed = urllib.parse.urlparse(raw_url)
            qs = urllib.parse.parse_qs(parsed.query)

            extracted_layers = (
                qs.get('LAYERS') or qs.get('layers') or qs.get('layer') or
                qs.get('TYPENAME') or qs.get('typename') or qs.get('typeName') or qs.get('typenames')
            )
            layer_name = extracted_layers[0] if extracted_layers else None

            reserved_keys = {'SERVICE', 'REQUEST', 'VERSION', 'FORMAT', 'LAYERS', 'LAYER', 'TYPENAME', 'TYPENAMES', 'STYLES', 'STYLE', 'SRS', 'CRS', 'BBOX', 'MAXFEATURES', 'SRSNAME'}
            for k in list(qs.keys()):
                if k.upper() in reserved_keys:
                    del qs[k]

            new_query = urllib.parse.urlencode(qs, doseq=True)
            clean_url = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))
            return clean_url, layer_name
        except Exception:
            return raw_url, None

    def _discover_wms_layer_name(self, raw_url):
        try:
            sep = "&" if "?" in raw_url else "?"
            capabilities_url = f"{raw_url}{sep}SERVICE=WMS&REQUEST=GetCapabilities" if "GetCapabilities" not in raw_url else raw_url
            with self._fetch_url(capabilities_url, timeout=8) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)  # nosec B314
                for elem in root.iter():
                    if elem.tag.endswith('Name') and elem.text and elem.text.strip():
                        name = elem.text.strip()
                        if name.upper() not in ('WMS', 'WFS', 'GETCAPABILITIES', 'WMS_CAPABILITIES', 'DEFAULT', 'GEORISQUES_SERVICES') and not name.startswith('http'):
                            return name
        except Exception as e:
            QgsMessageLog.logMessage(f"Impossible d'extraire la couche WMS: {e}", "OpenGeoDataFR", Qgis.MessageLevel.Warning)
        return None

    def _discover_wfs_layer_name(self, raw_url, search_title=None):
        try:
            sep = "&" if "?" in raw_url else "?"
            capabilities_url = f"{raw_url}{sep}SERVICE=WFS&REQUEST=GetCapabilities" if "GetCapabilities" not in raw_url else raw_url
            with self._fetch_url(capabilities_url, timeout=10) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)  # nosec B314

                best_name = None
                for ft in root.iter():
                    if ft.tag.endswith('FeatureType'):
                        name_elem = None
                        title_elem = None
                        for child in ft:
                            if child.tag.endswith('Name'):
                                name_elem = child.text.strip() if child.text else None
                            elif child.tag.endswith('Title'):
                                title_elem = child.text.strip() if child.text else None

                        if name_elem and name_elem.upper() not in ('WFS', 'WMS', 'DEFAULT'):
                            if not best_name:
                                best_name = name_elem
                            if search_title and title_elem and (search_title.lower() in title_elem.lower() or title_elem.lower() in search_title.lower()):
                                return name_elem

                if best_name:
                    return best_name

                for elem in root.iter():
                    if elem.tag.endswith('Name') and elem.text and elem.text.strip():
                        name = elem.text.strip()
                        if name.upper() not in ('WFS', 'WMS', 'GETCAPABILITIES', 'WFS_CAPABILITIES', 'DEFAULT') and not name.startswith('http'):
                            return name
        except Exception as e:
            QgsMessageLog.logMessage(f"Impossible d'extraire la couche WFS: {e}", "OpenGeoDataFR", Qgis.MessageLevel.Warning)
        return None

    def _import_wms_layer(self, item, target_crs=None, territory_filter=None):
        raw_url = item.extra.get('wms_url') or item.url or "https://data.geopf.fr/wms-r/ows"

        # 1. Gestion des couches XYZ (OpenStreetMap, RainViewer Radar Météo Temps Réel, etc.)
        if '{z}' in raw_url or 'tile.openstreetmap' in raw_url.lower() or 'rainviewer' in raw_url.lower() or 'xyz' in str(item.extra.get('format', '')).lower():
            xyz_url = raw_url
            if 'rainviewer' in raw_url.lower() or 'radar' in item.id.lower() or 'satellite' in item.id.lower():
                try:
                    with self._fetch_url("https://api.rainviewer.com/public/weather-maps.json", timeout=5) as rv_resp:
                        if rv_resp.status == 200:
                            rv_data = json.loads(rv_resp.read().decode('utf-8'))
                            host = rv_data.get('host', 'https://tilecache.rainviewer.com')
                            if 'satellite' in item.id.lower() or 'satellite' in item.title.lower():
                                sat_past = rv_data.get('satellite', {}).get('infrared', [])
                                if sat_past:
                                    latest_path = sat_past[-1].get('path')
                                    xyz_url = f"{host}{latest_path}/256/{{z}}/{{x}}/{{y}}/0/1_1.png"
                            else:
                                radar_past = rv_data.get('radar', {}).get('past', [])
                                if radar_past:
                                    latest_path = radar_past[-1].get('path')
                                    xyz_url = f"{host}{latest_path}/256/{{z}}/{{x}}/{{y}}/2/1_1.png"
                except Exception as rv_err:
                    QgsMessageLog.logMessage(f"RainViewer dynamic radar fetch: {rv_err}", "OpenGeoDataFR", Qgis.MessageLevel.Warning)

            if '{z}' not in xyz_url:
                xyz_url = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
            
            is_rainviewer = 'rainviewer' in xyz_url.lower() or 'radar' in item.id.lower() or 'satellite' in item.id.lower()
            zmax_val = 12 if is_rainviewer else 19
            encoded_url = urllib.parse.quote(xyz_url, safe=':/?&=%-')
            uri = f"type=xyz&url={encoded_url}&zmax={zmax_val}&zmin=0"
            layer = QgsRasterLayer(uri, item.title, "wms")
            if layer.isValid():
                final_layer = self._apply_crs_and_filters(layer, item, target_crs=target_crs, territory_filter=territory_filter)
                self._add_layer_safely(final_layer)
                if territory_filter and str(territory_filter).lower() not in ("france", "toutes les échelles", "all"):
                    self._create_and_add_wms_mask(item, territory_filter)
                return True, f"Couche dynamique XYZ '{item.title}' ajoutée avec succès."

        clean_url, url_layer_name = self._clean_ogc_url(raw_url)

        layer_name = item.extra.get('layer_name')
        if not layer_name and item.extra.get('wms_layers'):
            layer_name = item.extra.get('wms_layers')[0]
        if not layer_name:
            layer_name = url_layer_name
        if not layer_name:
            layer_name = self._discover_wms_layer_name(raw_url)

        if not layer_name:
            if 'geopf' in raw_url or 'geoportail' in raw_url:
                layer_name = "CADASTRALPARCELS.PARCELLAIRE_EXPRESS" if "cadastre" in item.title.lower() else "document"
            elif 'georisques' in raw_url:
                layer_name = "ALEARG" if "argile" in item.title.lower() else "MASQ_EAIP"
            elif 'brgm' in raw_url:
                layer_name = "SCAN_D_GEOL50" if "geol" in item.title.lower() else "GEOLOGIE"
            else:
                return False, f"Impossible de déterminer le nom de la couche WMS pour : {raw_url}"

        crs_code = target_crs if (target_crs and "Native" not in target_crs) else "EPSG:3857"
        candidate_urls = [clean_url]

        if 'data.geopf.fr' in clean_url:
            raster_indicators = ('PARCELLAIRE_EXPRESS', 'CADASTRALPARCELS', 'ORTHOIMAGERY', 'ORTHOPHOTOS', 'PLANIGN', 'MAPS', 'ELEVATION', 'SHADOW', 'CONTOUR')
            if any(ind in layer_name.upper() for ind in raster_indicators):
                if "https://data.geopf.fr/wms-r/ows" not in candidate_urls:
                    candidate_urls.insert(0, "https://data.geopf.fr/wms-r/ows")
            elif any(ind in layer_name.lower() for ind in ('document', 'zone_secteur', 'prescription')):
                if "https://data.geopf.fr/wms-v/ows" not in candidate_urls:
                    candidate_urls.insert(0, "https://data.geopf.fr/wms-v/ows")

        for endpoint_url in candidate_urls:
            uri = f"contextualWMSLegend=0&crs={crs_code}&dpiMode=7&featureCount=10&format=image/png&layers={layer_name}&styles=&url={urllib.parse.quote(endpoint_url, safe=':/?&=%-')}"
            layer = QgsRasterLayer(uri, item.title, "wms")

            if layer.isValid():
                final_layer = self._apply_crs_and_filters(layer, item, target_crs=target_crs, territory_filter=territory_filter)
                self._add_layer_safely(final_layer)

                if territory_filter and str(territory_filter).lower() not in ("france", "toutes les échelles", "all"):
                    self._create_and_add_wms_mask(item, territory_filter, raster_layer=final_layer)

                return True, f"Flux WMS '{item.title}' [{layer_name}, {crs_code}] ajouté avec succès."

        return False, f"Impossible de se connecter au flux WMS : {clean_url}"

    def _create_and_add_wms_mask(self, item, territory_filter, raster_layer=None):
        try:
            terr_geom, terr_crs_str = self._get_territory_geometry(territory_filter)
            if not terr_geom or terr_geom.isEmpty():
                return

            dest_crs_str = "EPSG:3857"
            if raster_layer and raster_layer.crs().isValid():
                dest_crs_str = raster_layer.crs().authid()

            dest_crs = QgsCoordinateReferenceSystem(dest_crs_str)
            terr_crs = QgsCoordinateReferenceSystem(terr_crs_str)

            geom_trans = QgsGeometry(terr_geom)
            if dest_crs.isValid() and terr_crs.isValid() and dest_crs != terr_crs:
                xform = QgsCoordinateTransform(terr_crs, dest_crs, QgsProject.instance() if QgsProject else None)
                geom_trans.transform(xform)

            mask_layer = QgsVectorLayer(f"Polygon?crs={dest_crs_str}", f"Emprise - {territory_filter}", "memory")
            dp = mask_layer.dataProvider()
            feat = QgsFeature()
            feat.setGeometry(geom_trans)
            dp.addFeatures([feat])
            mask_layer.updateExtents()

            fill_sym = QgsFillSymbol.createSimple({
                'color': '255,255,255,255',
                'outline_color': '217,4,41,255',
                'outline_width': '0.8',
                'outline_style': 'solid'
            })
            inv_renderer = QgsInvertedPolygonRenderer()
            inv_renderer.setEmbeddedRenderer(QgsSingleSymbolRenderer(fill_sym))
            mask_layer.setRenderer(inv_renderer)

            self._add_layer_safely(mask_layer)
        except Exception as mask_err:
            QgsMessageLog.logMessage(f"Erreur création masque WMS: {mask_err}", "OpenGeoDataFR", Qgis.MessageLevel.Warning)

    def _import_wfs_layer(self, item, target_crs=None, territory_filter=None, progress_callback=None):
        try:
            raw_url = item.extra.get('wfs_url') or item.url or "https://data.geopf.fr/wfs/ows"
            clean_url, url_layer_name = self._clean_ogc_url(raw_url)

            typename = item.extra.get('layer_name')
            if not typename and item.extra.get('wfs_layers'):
                typename = item.extra.get('wfs_layers')[0]
            if not typename:
                typename = url_layer_name

            if typename and (any(c in typename for c in (' ', '’', '\'', 'à', 'é', 'è', 'ê', 'ô')) or not any(c.isalnum() for c in typename)):
                discovered = self._discover_wfs_layer_name(raw_url, search_title=typename) or self._discover_wfs_layer_name(raw_url, search_title=item.title)
                if discovered:
                    typename = discovered

            if not typename or any(c in typename for c in (' ', '’', '\'')):
                typename = self._discover_wfs_layer_name(raw_url, search_title=item.title)

            if not typename:
                if 'geopf.fr' in raw_url or 'geoportail-urbanisme' in raw_url:
                    typename = "wfs_du:zone_urba"
                else:
                    typename = self._discover_wfs_layer_name(raw_url)

            if not typename:
                return False, f"Impossible de déterminer le nom technique WFS pour : {raw_url}"

            srs_code = target_crs if (target_crs and "Native" not in target_crs) else "EPSG:4326"
            code_insee = item.extra.get('code_insee')
            tf = (territory_filter or code_insee or '').strip()

            # 1. TENTATIVE D'IMPORT DIRECT GEOJSON WFS AVEC BBOX SPATIAL TERRITORIAL
            if tf and str(tf).lower() not in ("france", "toutes les échelles", "all"):
                try:
                    terr_geom, terr_crs_str = self._get_territory_geometry(tf)
                    if terr_geom and not terr_geom.isEmpty():
                        bb = terr_geom.boundingBox()
                        bbox_param = f"{bb.yMinimum()},{bb.xMinimum()},{bb.yMaximum()},{bb.xMaximum()},urn:ogc:def:crs:EPSG::4326"

                        wfs_base = clean_url.split('?')[0]
                        params = {
                            "SERVICE": "WFS",
                            "REQUEST": "GetFeature",
                            "VERSION": "2.0.0",
                            "TYPENAMES": typename,
                            "OUTPUTFORMAT": "application/json",
                            "BBOX": bbox_param
                        }
                        direct_url = f"{wfs_base}?{urllib.parse.urlencode(params)}"
                        safe_file_id = "".join([c for c in f"wfs_{typename}_{hash(bbox_param)}" if c.isalnum() or c == '_'])
                        cache_file = os.path.join(self.cache_dir, f"{safe_file_id}.geojson")

                        if progress_callback:
                            progress_callback(f"Téléchargement WFS optimisé ({item.title})...")

                        with self._fetch_url(direct_url, timeout=15) as resp:
                            if resp.status == 200:
                                payload = resp.read()
                                if payload and not payload.strip().startswith(b'<?xml') and not payload.strip().startswith(b'<ows:ExceptionReport'):
                                    with open(cache_file, 'wb') as f_out:
                                        f_out.write(payload)

                                    layer_direct = QgsVectorLayer(cache_file, item.title, "ogr")
                                    if layer_direct.isValid() and layer_direct.featureCount() > 0:
                                        final_layer = self._apply_crs_and_filters(layer_direct, item, target_crs=target_crs, territory_filter=territory_filter)
                                        self._add_layer_safely(final_layer)
                                        return True, f"Couche WFS '{item.title}' [{layer_direct.featureCount()} entité(s)] découpée et ajoutée avec succès !"
                except Exception as direct_err:
                    QgsMessageLog.logMessage(f"Import direct GeoJSON WFS ignoré: {direct_err}", "OpenGeoDataFR", Qgis.MessageLevel.Warning)

            # 2. CHARGEMENT WFS NATIVE VIA QGIS
            uri_clean_wfs = f"pagingEnabled='true' preferCoordinatesForWfsT11='false' srsname='{srs_code}' typename='{typename}' url='{clean_url}' version='auto'"
            layer_wfs = QgsVectorLayer(uri_clean_wfs, item.title, "WFS")
            if layer_wfs.isValid():
                final_layer = self._apply_crs_and_filters(layer_wfs, item, target_crs=target_crs, territory_filter=territory_filter)
                self._add_layer_safely(final_layer)
                return True, f"Flux WFS '{item.title}' [{typename}, {srs_code}] ajouté avec succès au projet."

            return False, f"Impossible de se connecter au flux WFS '{typename}' sur {clean_url}"
        except Exception as err:
            return False, f"Erreur lors de l'import WFS: {err}"

    def _import_urban_doc(self, item, as_wms=False, target_crs=None, territory_filter=None, progress_callback=None):
        wms_url = item.extra.get('wms_url', 'https://data.geopf.fr/wms-v/ows')
        wfs_url = item.extra.get('wfs_url', 'https://data.geopf.fr/wfs/ows')

        clean_wms_url, _ = self._clean_ogc_url(wms_url)
        clean_wfs_url, _ = self._clean_ogc_url(wfs_url)

        added_count = 0
        srs_code = target_crs if (target_crs and "Native" not in target_crs) else "EPSG:3857"

        if as_wms or not item.wfs_layers:
            wms_layers_to_load = item.wms_layers or ["document", "zone_secteur", "prescription"]
            for lyr_name in wms_layers_to_load:
                uri = f"contextualWMSLegend=0&crs={srs_code}&dpiMode=7&featureCount=10&format=image/png&layers={lyr_name}&styles=&url={urllib.parse.quote(clean_wms_url, safe=':/?&=%-')}"
                layer = QgsRasterLayer(uri, f"{item.title} - {lyr_name}", "wms")
                if layer.isValid():
                    final_layer = self._apply_crs_and_filters(layer, item, target_crs=target_crs, territory_filter=territory_filter)
                    self._add_layer_safely(final_layer)
                    added_count += 1

            if added_count > 0:
                if territory_filter and str(territory_filter).lower() not in ("france", "toutes les échelles", "all"):
                    self._create_and_add_wms_mask(item, territory_filter)
                return True, f"{added_count} couche(s) WMS GPU ajoutée(s) avec succès."
            return False, "Impossible de charger les couches WMS GPU."

        for lyr_name in item.wfs_layers:
            sub_item = DataItem(
                item_id=f"{item.id}_{lyr_name}",
                title=f"{item.title} - {lyr_name}",
                source=item.source,
                data_type="wfs",
                territory=item.territory,
                scale=item.scale,
                crs=item.crs,
                date=item.date,
                url=clean_wfs_url,
                service_type="WFS",
                extra={
                    'layer_name': lyr_name,
                    'wfs_url': clean_wfs_url,
                    'code_insee': item.extra.get('code_insee')
                }
            )
            success, _, _ = self.import_item(sub_item, target_crs=target_crs, territory_filter=territory_filter, progress_callback=progress_callback)
            if success:
                added_count += 1

        if added_count > 0:
            return True, f"{added_count} couche(s) vectorielle(s) WFS GPU ajoutée(s) avec succès."
        return False, "Échec de chargement des couches vectorielles GPU."
