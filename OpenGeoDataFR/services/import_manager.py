# -*- coding: utf-8 -*-
"""
Service de gestion des téléchargements, de la gestion du système de coordonnées (CRS),
du décodage UTF-8-SIG (BOM) et de l'importation filtrée (Attributs + Découpage Géométrique Spatial) des couches dans QGIS.
Applique automatiquement la symbologie et le style cartographique officiel français (Cadastre, GPU, BAN, Admin Express, IRIS).
Supporte les fichiers (GeoJSON, Shapefile, CSV avec/sans géométrie, GeoPackage, .gz, .zip, JSON API/GBFS), les flux WMS et WFS.
Compatible 100% avec QGIS 3 (PyQt5) et QGIS 4 (PyQt6).
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
    QgsMessageLog,
    Qgis
)
from ..utils.ssl_helper import get_secure_ssl_context, fetch_url_bytes


class ImportManager:
    """Gestionnaire central d'importation, de réprojection, de filtrage spatial et de symbologie automatique."""

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

    def _fetch_url(self, req, timeout=30):
        return urllib.request.urlopen(req, timeout=timeout, context=self.ssl_ctx)

    def _get_territory_geometry(self, territory_filter):
        """
        Récupère la géométrie polygonale officielle du territoire (Commune(s) / Département / EPCI)
        avec geometry=contour depuis l'API GeoAPI (geo.api.gouv.fr) pour le découpage spatial géométrique.
        Gère les listes de codes multiples séparés par des virgules (ex: 60309, 60321, 60395...).
        """
        if not territory_filter or str(territory_filter).lower() in ("france", "toutes les échelles", "all"):
            return None, None

        tf = str(territory_filter).strip()
        cache_key = f"geom_{tf}"
        if cache_key in self._geom_cache:
            return self._geom_cache[cache_key]

        geom_crs = "EPSG:4326"
        codes = [c.strip() for c in tf.split(',') if c.strip()]
        collected_geoms = []

        for code in codes:
            try:
                if code.isdigit() and len(code) == 5:
                    url = f"https://geo.api.gouv.fr/communes/{code}?fields=nom,code&geometry=contour&format=geojson"
                elif code.isdigit() and (len(code) == 2 or len(code) == 3):
                    url = f"https://geo.api.gouv.fr/departements/{code}?fields=nom,code&geometry=contour&format=geojson"
                else:
                    clean_code = urllib.parse.quote(code)
                    url = f"https://geo.api.gouv.fr/communes?nom={clean_code}&fields=nom,code&geometry=contour&format=geojson&limit=1"

                req = urllib.request.Request(url, headers={'User-Agent': 'OpenGeoDataFR-QGIS/1.0'})
                with self._fetch_url(req, timeout=6) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode('utf-8'))
                        geom_dict = None
                        if isinstance(data, dict):
                            if 'geometry' in data and data['geometry']:
                                geom_dict = data['geometry']
                            elif 'features' in data and data['features']:
                                geom_dict = data['features'][0].get('geometry')
                        elif isinstance(data, list) and data:
                            geom_dict = data[0].get('geometry') if isinstance(data[0], dict) else None

                        if geom_dict:
                            g = QgsJsonUtils.geometryFromGeoJson(json.dumps(geom_dict))
                            if g and not g.isEmpty():
                                collected_geoms.append(g)
            except Exception as ex:
                QgsMessageLog.logMessage(f"Extraction du contour pour {code}: {ex}", "OpenGeoDataFR", Qgis.Warning)

        if not collected_geoms:
            self._geom_cache[cache_key] = (None, geom_crs)
            return None, geom_crs

        if len(collected_geoms) == 1:
            fused_geom = collected_geoms[0]
        else:
            try:
                fused_geom = QgsGeometry.unaryUnion(collected_geoms)
            except Exception:
                fused_geom = collected_geoms[0]
                for other in collected_geoms[1:]:
                    fused_geom = fused_geom.combine(other)

        self._geom_cache[cache_key] = (fused_geom, geom_crs)
        return fused_geom, geom_crs

    def import_item(self, item, as_wms=False, target_crs=None, territory_filter=None, progress_callback=None):
        """
        Importe un DataItem ou UrbanDocItem dans le projet QGIS actif avec gestion du CRS, filtre territorial et symbologie.
        """
        if not item:
            return False, "Élément d'import non valide."

        try:
            if hasattr(item, 'doc_type') and item.data_type == "urban_doc":
                return self._import_urban_doc(item, as_wms=as_wms, target_crs=target_crs, territory_filter=territory_filter, progress_callback=progress_callback)

            if item.data_type == 'wms' or item.service_type == 'WMS' or as_wms:
                return self._import_wms_layer(item, target_crs=target_crs, territory_filter=territory_filter)

            if item.data_type == 'wfs' or item.service_type == 'WFS':
                return self._import_wfs_layer(item, target_crs=target_crs, territory_filter=territory_filter, progress_callback=progress_callback)

            if item.url:
                return self._import_file_resource(item, target_crs=target_crs, territory_filter=territory_filter, progress_callback=progress_callback)

            return False, "Aucune URL ni service valide trouvé pour cet élément."
        except Exception as e:
            QgsMessageLog.logMessage(f"Erreur d'importation: {e}", "OpenGeoDataFR", Qgis.Critical)
            return False, f"Erreur lors de l'importation : {str(e)}"

    def download_file(self, url, filename_hint="downloaded_file", format_hint=None, progress_callback=None):
        try:
            url_clean = url.split('?')[0] if url else "file.dat"
            ext = os.path.splitext(url_clean)[1].lower()

            if not ext or len(ext) > 6 or ext in ('.dat', '.bin', '.tmp'):
                fmt = (format_hint or '').lower().strip()
                if 'csv' in fmt:
                    ext = '.csv'
                elif 'geojson' in fmt:
                    ext = '.geojson'
                elif 'json' in fmt:
                    ext = '.json'
                elif 'shp' in fmt or 'shape' in fmt or 'zip' in fmt:
                    ext = '.zip'
                elif 'gpkg' in fmt or 'geopackage' in fmt:
                    ext = '.gpkg'
                elif 'kml' in fmt:
                    ext = '.kml'
                else:
                    ext = '.csv' if 'table' in fmt else '.dat'

            safe_name = "".join([c for c in (filename_hint or "file") if c.isalnum() or c in ('_', '-')]).rstrip()
            if not safe_name:
                safe_name = "downloaded_file"

            dest_file = os.path.join(self.cache_dir, f"{safe_name}{ext}")

            if os.path.exists(dest_file) and os.path.getsize(dest_file) > 200:
                if progress_callback:
                    progress_callback(f"Utilisation du fichier local en cache : {safe_name}{ext}")
                if dest_file.endswith('.gz'):
                    uncompressed_path = dest_file[:-3]
                    if os.path.exists(uncompressed_path) and os.path.getsize(uncompressed_path) > 200:
                        return uncompressed_path
                    with gzip.open(dest_file, 'rb') as f_in, open(uncompressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                    return uncompressed_path
                return dest_file

            req = urllib.request.Request(url, headers={'User-Agent': 'OpenGeoDataFR-QGIS/1.0'})
            try:
                response = self._fetch_url(req, timeout=60)
            except Exception as http_err:
                QgsMessageLog.logMessage(f"Erreur HTTP sur {url}: {http_err}. Tentative de résolution de secours...", "OpenGeoDataFR", Qgis.Warning)
                fallback_url = self._resolve_fallback_url(url)
                if fallback_url and fallback_url != url:
                    if progress_callback:
                        progress_callback("Lien 404 détecté : Bascule automatique sur l'API live de secours...")
                    req = urllib.request.Request(fallback_url, headers={'User-Agent': 'OpenGeoDataFR-QGIS/1.0'})
                    response = self._fetch_url(req, timeout=60)
                else:
                    raise http_err

            with response:
                total_size = response.headers.get('content-length')
                total_bytes = int(total_size) if total_size and total_size.isdigit() else 0

                downloaded_bytes = 0
                block_size = 1024 * 64

                with open(dest_file, 'wb') as out_file:
                    while True:
                        buffer = response.read(block_size)
                        if not buffer:
                            break
                        out_file.write(buffer)
                        downloaded_bytes += len(buffer)

                        if progress_callback:
                            mb_dl = downloaded_bytes / (1024 * 1024)
                            if total_bytes > 0:
                                mb_total = total_bytes / (1024 * 1024)
                                pct = int((downloaded_bytes / total_bytes) * 100)
                                progress_callback(f"Téléchargement : {mb_dl:.1f} Mo / {mb_total:.1f} Mo ({pct}%)")
                            else:
                                progress_callback(f"Téléchargement : {mb_dl:.1f} Mo transférés...")

            if dest_file.endswith('.gz'):
                if progress_callback:
                    progress_callback("Décompression du fichier GZ en cours...")
                uncompressed_path = dest_file[:-3]
                try:
                    with gzip.open(dest_file, 'rb') as f_in, open(uncompressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                    return uncompressed_path
                except Exception as gz_err:
                    QgsMessageLog.logMessage(f"Erreur décompression GZ: {gz_err}", "OpenGeoDataFR", Qgis.Warning)
                    return dest_file

            if dest_file.endswith('.zip'):
                if progress_callback:
                    progress_callback("Décompression du fichier ZIP en cours...")
                extract_dir = os.path.join(self.cache_dir, safe_name)
                os.makedirs(extract_dir, exist_ok=True)
                try:
                    with zipfile.ZipFile(dest_file, 'r') as zip_ref:
                        extract_dir_abs = os.path.abspath(extract_dir)
                        for member in zip_ref.infolist():
                            member_path = os.path.abspath(os.path.join(extract_dir, member.filename))
                            if not member_path.startswith(extract_dir_abs + os.sep) and member_path != extract_dir_abs:
                                raise RuntimeError(f"Tentative de traversée de répertoire détectée : {member.filename}")
                            zip_ref.extract(member, extract_dir)
                    for root, dirs, files in os.walk(extract_dir):
                        for f in files:
                            if f.endswith(('.shp', '.geojson', '.gpkg', '.kml', '.tab', '.csv')):
                                return os.path.join(root, f)
                except Exception as zip_err:
                    QgsMessageLog.logMessage(f"Erreur décompression ZIP: {zip_err}", "OpenGeoDataFR", Qgis.Warning)
                return extract_dir

            return dest_file
        except Exception as e:
            QgsMessageLog.logMessage(f"Erreur de téléchargement: {e}", "OpenGeoDataFR", Qgis.Critical)
            raise e

    def _resolve_fallback_url(self, failed_url):
        """
        Interroge l'API live de data.gouv.fr / GeoAPI / SNCF pour retrouver automatiquement l'URL active
        lorsqu'un permalien direct renvoie une erreur HTTP 404.
        """
        try:
            # 1. Fallback Aménagements cyclables BNLC
            if 'cyclable' in failed_url.lower() or 'amenagements-cyclables' in failed_url.lower():
                return "https://static.data.gouv.fr/resources/amenagements-cyclables-france-metropolitaine/20260807-093353/france-20260807.geojson"

            # 2. Fallback Réseau ferré SNCF
            if 'formes-des-lignes-du-rfn' in failed_url.lower() or 'sncf' in failed_url.lower():
                return "https://ressources.data.sncf.com/api/explore/v2.1/catalog/datasets/formes-des-lignes-du-rfn/exports/geojson"

            # 3. Fallback pour le COG (Code Officiel Géographique)
            if 'cog' in failed_url.lower() or 'd066d962' in failed_url:
                return "https://geo.api.gouv.fr/communes?fields=nom,code,codeDepartement,codeRegion"

            # 4. Fallback pour les IRIS
            if 'iris' in failed_url.lower() or 'c9e99a84' in failed_url:
                return "https://geo.api.gouv.fr/communes?fields=nom,code,codeDepartement,codeRegion"

            # 5. Fallback pour la base SIRENE
            if 'sirene' in failed_url.lower():
                api_url = "https://www.data.gouv.fr/api/1/datasets/5b7ffc618b4c4169d30727e0/"
                content = fetch_url_bytes(api_url, timeout_ms=5000)
                data = json.loads(content.decode('utf-8'))
                for r in data.get('resources', []):
                    u = r.get('url')
                    if u and u.endswith(('.zip', '.csv.gz', '.csv')):
                        return u

            # 6. Fallback général pour tout dataset data.gouv.fr (/fr/datasets/r/... ou /resources/...)
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
            QgsMessageLog.logMessage(f"Échec résolution fallback URL pour {failed_url}: {ex}", "OpenGeoDataFR", Qgis.Warning)
        return None

    def _apply_automatic_symbology(self, layer, item):
        """
        Applique automatiquement la symbologie et le style QGIS officiel selon le type de données :
        - Cadastre Parcelles : Contour marron/orange fin (#b45014), fond transparent
        - Cadastre Bâtiments : Remplissage marron/orange (#dca078)
        - Urbanisme GPU (Zonage) : Rendu catégorisé (U: Rouge, AU: Orange, A: Jaune, N: Vert)
        - Adresses BAN : Marqueurs ponctuels circulaires bleus (#1a73e8)
        - Limites administratives (Communes/Départements/IRIS) : Contours bleus épurés (#1a73e8)
        """
        if not layer or not layer.isValid() or not isinstance(layer, QgsVectorLayer):
            return

        try:
            from qgis.core import (
                QgsSymbol, QgsRendererCategory, QgsCategorizedSymbolRenderer,
                QgsSingleSymbolRenderer
            )
            from qgis.PyQt.QtGui import QColor

            layer_type = item.extra.get('layer_type') if hasattr(item, 'extra') and item.extra else ''
            title_lower = (item.title or '').lower()
            geom_type = layer.geometryType()  # 0: Point, 1: Line, 2: Polygon

            # 1. Symbologie Cadastre Parcelles
            if 'parcelle' in title_lower or layer_type == 'cadastre_parcelles':
                if geom_type == 2:
                    sym = QgsSymbol.defaultSymbol(geom_type)
                    sym.setColor(QColor(0, 0, 0, 0))  # Fond transparent
                    if sym.symbolLayerCount() > 0:
                        sym.symbolLayer(0).setStrokeColor(QColor(180, 80, 20))
                        sym.symbolLayer(0).setStrokeWidth(0.4)
                    layer.setRenderer(QgsSingleSymbolRenderer(sym))
                    layer.triggerRepaint()

            # 2. Symbologie Cadastre Bâtiments
            elif 'bâtiment' in title_lower or 'batiment' in title_lower or layer_type == 'cadastre_batiments':
                if geom_type == 2:
                    sym = QgsSymbol.defaultSymbol(geom_type)
                    sym.setColor(QColor(220, 160, 120, 180))
                    if sym.symbolLayerCount() > 0:
                        sym.symbolLayer(0).setStrokeColor(QColor(140, 70, 20))
                        sym.symbolLayer(0).setStrokeWidth(0.5)
                    layer.setRenderer(QgsSingleSymbolRenderer(sym))
                    layer.triggerRepaint()

            # 3. Symbologie Urbanisme GPU (PLU / Zonage)
            elif 'urbanisme' in title_lower or 'zone_urba' in title_lower or hasattr(item, 'doc_type'):
                if geom_type == 2:
                    categories = []
                    color_map = {
                        'U': QColor(220, 40, 40, 140),     # Urbain (Rouge)
                        'AU': QColor(245, 140, 20, 140),  # À Urbaniser (Orange)
                        'A': QColor(245, 220, 30, 140),   # Agricole (Jaune)
                        'N': QColor(45, 160, 65, 140)     # Naturel (Vert)
                    }
                    for code, color in color_map.items():
                        sym = QgsSymbol.defaultSymbol(geom_type)
                        sym.setColor(color)
                        if sym.symbolLayerCount() > 0:
                            sym.symbolLayer(0).setStrokeColor(color.darker(130))
                        categories.append(QgsRendererCategory(code, sym, f"Zone {code}"))

                    target_field = None
                    for f in layer.fields():
                        if f.name().lower() in ('typezone', 'type_zone', 'code_zone', 'du_type'):
                            target_field = f.name()
                            break
                    if target_field:
                        renderer = QgsCategorizedSymbolRenderer(target_field, categories)
                        layer.setRenderer(renderer)
                        layer.triggerRepaint()

            # 4. Symbologie BAN / Adresses (Points)
            elif 'adresse' in title_lower or 'ban' in title_lower:
                if geom_type == 0:
                    sym = QgsSymbol.defaultSymbol(geom_type)
                    sym.setColor(QColor(26, 115, 232))
                    sym.setSize(2.5)
                    layer.setRenderer(QgsSingleSymbolRenderer(sym))
                    layer.triggerRepaint()

            # 5. Symbologie Limites Administratives (Communes / Départements / IRIS)
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
            QgsMessageLog.logMessage(f"Application symbologie automatique ignorée: {style_err}", "OpenGeoDataFR", Qgis.Warning)

    def _apply_crs_and_filters(self, layer, item, target_crs=None, territory_filter=None):
        if not layer or not layer.isValid():
            return layer

        reprojected_layer = layer

        try:
            if target_crs and target_crs != "Native" and "Variable" not in target_crs:
                target_crs_obj = QgsCoordinateReferenceSystem(target_crs)
                if target_crs_obj.isValid():
                    current_crs = layer.crs()
                    # 1. Si la couche n'a pas de CRS valide défini, on lui assigne le CRS cible
                    if not current_crs.isValid():
                        layer.setCrs(target_crs_obj)
                    # 2. Si la couche a un CRS différent du CRS cible choisi, on la réprojette réellement !
                    elif current_crs.authid().upper() != target_crs_obj.authid().upper() and isinstance(layer, QgsVectorLayer):
                        try:
                            from qgis import processing
                            res = processing.run("native:reprojectlayer", {
                                'INPUT': layer,
                                'TARGET_CRS': target_crs_obj,
                                'OUTPUT': 'memory:'
                            })
                            if res and 'OUTPUT' in res:
                                reprojected_layer = res['OUTPUT']
                                reprojected_layer.setName(layer.name())
                        except Exception as proc_err:
                            QgsMessageLog.logMessage(f"Processing reprojectlayer non exécuté: {proc_err}", "OpenGeoDataFR", Qgis.Warning)

                    # Aligner la carte et le canevas du projet QGIS sur la projection cible sélectionnée
                    QgsProject.instance().setCrs(target_crs_obj)
        except Exception as crs_err:
            QgsMessageLog.logMessage(f"Erreur d'application du CRS: {crs_err}", "OpenGeoDataFR", Qgis.Warning)

        target_for_filters = reprojected_layer if isinstance(reprojected_layer, QgsVectorLayer) else (layer if isinstance(layer, QgsVectorLayer) else None)
        if target_for_filters:
            attribute_filtered = False
            try:
                code_insee = item.extra.get('code_insee') if item and hasattr(item, 'extra') else None
                dep_code = item.extra.get('dep_code') if item and hasattr(item, 'extra') else None
                filter_val = territory_filter or code_insee or getattr(item, 'territory', None)

                if filter_val and str(filter_val).lower() not in ("france", "toutes les échelles", "all"):
                    clean_filter = str(filter_val).strip()
                    codes = [c.strip() for c in clean_filter.split(',') if c.strip()]
                    subset_clauses = []
                    field_names = [f.name() for f in target_for_filters.fields()]

                    for fname in field_names:
                        fname_lower = fname.lower()
                        if fname_lower in ('insee', 'code_insee', 'insee_com', 'code_com', 'insee_commune', 'codgeo', 'codeinsee', 'c_insee', 'insee_code', 'code_insee_commune', 'com_code', 'code_commune', 'insee_c'):
                            if len(codes) > 1 and all(c.isdigit() and len(c) == 5 for c in codes):
                                formatted_insee = ", ".join([f"'{c}'" for c in codes])
                                subset_clauses.append(f"{fname} IN ({formatted_insee})")
                            elif code_insee:
                                subset_clauses.append(f"{fname} = '{code_insee}'")
                            elif clean_filter.isdigit() and len(clean_filter) == 5:
                                subset_clauses.append(f"{fname} = '{clean_filter}'")
                            elif clean_filter.isdigit() and (len(clean_filter) == 2 or len(clean_filter) == 3):
                                subset_clauses.append(f"{fname} LIKE '{clean_filter}%'")
                        elif fname_lower in ('code_dep', 'dep', 'code_dept', 'insee_dep', 'dep_code', 'dpt', 'num_dep', 'departement', 'cd_dep'):
                            if dep_code:
                                subset_clauses.append(f"{fname} = '{dep_code}'")
                            elif clean_filter.isdigit() and (len(clean_filter) == 2 or len(clean_filter) == 3):
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
                        if target_for_filters.featureCount() > 0:
                            attribute_filtered = True
                        else:
                            # SÉCURITÉ ANTI-TABLE VIDE : Si le filtre par attribut renvoie 0 entité, on réinitialise immédiatement
                            target_for_filters.setSubsetString("")
                            QgsMessageLog.logMessage(f"Filtre attribut '{clause}' a donné 0 entité. Bascule automatique vers le découpage spatial géométrique.", "OpenGeoDataFR", Qgis.Info)
            except Exception as filter_err:
                QgsMessageLog.logMessage(f"Erreur d'application du filtre par attribut: {filter_err}", "OpenGeoDataFR", Qgis.Warning)

            # NIVEAU 2 : DÉCOUPAGE GÉOMÉTRIQUE SPATIAL SYSTÉMATIQUE SELON LE TERRITOIRE
            if territory_filter and str(territory_filter).lower() not in ("france", "toutes les échelles", "all"):
                try:
                    terr_geom, terr_crs_str = self._get_territory_geometry(territory_filter)
                    if terr_geom and not terr_geom.isEmpty():
                        layer_crs = target_for_filters.crs()
                        terr_crs = QgsCoordinateReferenceSystem(terr_crs_str)

                        terr_geom_transformed = QgsGeometry(terr_geom)
                        if layer_crs.isValid() and terr_crs.isValid() and layer_crs != terr_crs:
                            xform = QgsCoordinateTransform(terr_crs, layer_crs, QgsProject.instance())
                            terr_geom_transformed.transform(xform)

                        # Découpage géométrique réel des entités (spatial clip haute performance)
                        terr_bbox = terr_geom_transformed.boundingBox()
                        bbox_request = QgsFeatureRequest().setFilterRect(terr_bbox)
                        clipped_features = []
                        for feat in target_for_filters.getFeatures(bbox_request):
                            if feat.hasGeometry():
                                g = feat.geometry()
                                if g.intersects(terr_geom_transformed):
                                    try:
                                        inter_geom = g.intersection(terr_geom_transformed)
                                        if not inter_geom.isEmpty():
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
                        else:
                            QgsMessageLog.logMessage(f"Aucune entité géométrique dans le périmètre territorial {territory_filter}. Couche complète conservée.", "OpenGeoDataFR", Qgis.Info)
                except Exception as spatial_err:
                    QgsMessageLog.logMessage(f"Erreur lors du découpage spatial géométrique: {spatial_err}", "OpenGeoDataFR", Qgis.Warning)

            # Application de la Symbologie Officielle Automatique
            self._apply_automatic_symbology(target_for_filters, item)

        return reprojected_layer

    def _import_file_resource(self, item, target_crs=None, territory_filter=None, progress_callback=None):
        format_hint = item.extra.get('format') or item.data_type
        local_path = self.download_file(item.url, filename_hint=item.id, format_hint=format_hint, progress_callback=progress_callback)

        if not os.path.exists(local_path):
            return False, f"Impossible d'accéder au fichier téléchargé : {local_path}"

        ext = os.path.splitext(local_path)[1].lower()

        if ext in ('.tif', '.tiff', '.geotiff'):
            layer = QgsRasterLayer(local_path, item.title)
            if layer.isValid():
                final_layer = self._apply_crs_and_filters(layer, item, target_crs=target_crs)
                QgsProject.instance().addMapLayer(final_layer)
                return True, f"Couche raster '{item.title}' ajoutée avec succès."
            return False, "Échec de chargement de la couche raster."

        if ext == '.csv' or item.data_type == 'table' or (format_hint and 'csv' in format_hint.lower()):
            success, msg = self._import_csv_layer(local_path, item, target_crs=target_crs, territory_filter=territory_filter)
            if success:
                return True, msg

        layer = QgsVectorLayer(local_path, item.title, "ogr")
        if layer.isValid():
            final_layer = self._apply_crs_and_filters(layer, item, target_crs=target_crs, territory_filter=territory_filter)
            QgsProject.instance().addMapLayer(final_layer)
            return True, f"Couche vectorielle '{item.title}' ajoutée avec succès."

        if ext in ('.json', '.dat') or 'json' in ext:
            converted_path, convert_msg = self._try_convert_json_to_geojson(local_path)
            if converted_path and os.path.exists(converted_path):
                layer = QgsVectorLayer(converted_path, item.title, "ogr")
                if layer.isValid():
                    final_layer = self._apply_crs_and_filters(layer, item, target_crs=target_crs, territory_filter=territory_filter)
                    QgsProject.instance().addMapLayer(final_layer)
                    return True, f"Couche vectorielle '{item.title}' convertie et ajoutée avec succès."

            return False, f"Le fichier ne contient pas de géométries ou d'entités spatiales directement exploitables.\nDétail: {convert_msg}"

        return False, f"Format vectoriel non valide pour le fichier : {local_path}"

    def _import_csv_layer(self, local_path, item, target_crs=None, territory_filter=None):
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
                            QgsProject.instance().addMapLayer(final_layer)
                            return True, f"Couche CSV '{item.title}' configurée et ajoutée avec succès !"
                        else:
                            return False, f"Impossible de charger la couche CSV avec la configuration sélectionnée."
                    return False, "Aucune configuration de géométrie sélectionnée."
                elif res == qt_compat.DialogRejected:
                    return False, "Importation CSV annulée par l'utilisateur."
        except Exception as dialog_err:
            QgsMessageLog.logMessage(f"CSVImportDialog non exécuté: {dialog_err}", "OpenGeoDataFR", Qgis.Warning)

        delimiter = ";"
        encoding = "utf-8-sig"
        x_field, y_field, wkt_field = None, None, None

        try:
            with open(local_path, 'r', encoding='utf-8-sig', errors='replace') as f:
                first_line = f.readline()
                if first_line.count(';') > first_line.count(','):
                    delimiter = ";"
                elif first_line.count('\t') > first_line.count(','):
                    delimiter = "\t"
                elif first_line.count('|') > first_line.count(','):
                    delimiter = "|"
                else:
                    delimiter = ","

                headers = [h.strip().lower() for h in first_line.split(delimiter)]
                for h in headers:
                    if h in ('wkt', 'geom', 'geometry', 'the_geom'):
                        wkt_field = h
                        break
                    elif h in ('lon', 'lng', 'longitude', 'x', 'x_coord'):
                        x_field = h
                    elif h in ('lat', 'latitude', 'y', 'y_coord'):
                        y_field = h
        except Exception as e:
            QgsMessageLog.logMessage(f"Erreur analyse CSV: {e}", "OpenGeoDataFR", Qgis.Warning)

        csv_crs = target_crs if (target_crs and "Native" not in target_crs) else "EPSG:4326"

        if x_field and y_field:
            uri = f"file:///{local_path}?delimiter={urllib.parse.quote(delimiter)}&useHeader=yes&xField={x_field}&yField={y_field}&crs={csv_crs}&encoding={encoding}"
            layer = QgsVectorLayer(uri, item.title, "delimitedtext")
            if layer.isValid():
                final_layer = self._apply_crs_and_filters(layer, item, target_crs=target_crs, territory_filter=territory_filter)
                QgsProject.instance().addMapLayer(final_layer)
                return True, f"Couche ponctuelle CSV '{item.title}' ajoutée avec succès."

        if wkt_field:
            uri = f"file:///{local_path}?delimiter={urllib.parse.quote(delimiter)}&useHeader=yes&wktField={wkt_field}&crs={csv_crs}&encoding={encoding}"
            layer = QgsVectorLayer(uri, item.title, "delimitedtext")
            if layer.isValid():
                final_layer = self._apply_crs_and_filters(layer, item, target_crs=target_crs, territory_filter=territory_filter)
                QgsProject.instance().addMapLayer(final_layer)
                return True, f"Couche vectorielle WKT CSV '{item.title}' ajoutée avec succès."

        uri = f"file:///{local_path}?delimiter={urllib.parse.quote(delimiter)}&useHeader=yes&type=csv&geometry=none&encoding={encoding}"
        layer = QgsVectorLayer(uri, item.title, "delimitedtext")
        if not layer.isValid():
            layer = QgsVectorLayer(local_path, item.title, "ogr")

        if layer.isValid():
            final_layer = self._apply_crs_and_filters(layer, item, target_crs=target_crs, territory_filter=territory_filter)
            QgsProject.instance().addMapLayer(final_layer)
            return True, f"Table attributaire CSV '{item.title}' ajoutée avec succès au projet."

        return False, "Échec de lecture du fichier CSV."

    def _try_convert_json_to_geojson(self, filepath):
        content = None
        try:
            with open(filepath, 'r', encoding='utf-8-sig', errors='replace') as f:
                content = json.load(f)
        except Exception as e:
            return None, f"JSON illisible : {e}"

        if isinstance(content, dict) and content.get('type') in ('FeatureCollection', 'Feature'):
            return filepath, "GeoJSON valide."

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
                    req = urllib.request.Request(target_feed_url, headers={'User-Agent': 'OpenGeoDataFR-QGIS/1.0'})
                    with self._fetch_url(req, timeout=10) as resp:
                        sub_content = json.loads(resp.read().decode('utf-8-sig'))
                        return self._parse_json_features(sub_content, filepath)
                except Exception as ex:
                    QgsMessageLog.logMessage(f"Erreur téléchargement sub-feed GBFS: {ex}", "OpenGeoDataFR", Qgis.Warning)

        return self._parse_json_features(content, filepath)

    def _parse_json_features(self, content, orig_filepath):
        features = []
        items = []

        if isinstance(content, list):
            items = content
        elif isinstance(content, dict):
            if 'features' in content and isinstance(content['features'], list):
                items = content['features']
            elif 'data' in content:
                d = content['data']
                if isinstance(d, list):
                    items = d
                elif isinstance(d, dict):
                    for k in ('stations', 'vehicles', 'geofencing_zones', 'items', 'features'):
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

            elif any(k in item for k in ('lat', 'latitude', 'LAT', 'LATITUDE')) and any(k in item for k in ('lon', 'lng', 'longitude', 'LON', 'LONGITUDE')):
                try:
                    lat = float(item.get('lat') or item.get('latitude') or item.get('LAT') or item.get('LATITUDE'))
                    lon = float(item.get('lon') or item.get('lng') or item.get('longitude') or item.get('LON') or item.get('LONGITUDE'))
                    geom = {
                        "type": "Point",
                        "coordinates": [lon, lat]
                    }
                except (ValueError, TypeError):
                    pass

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
            return out_path, f"{len(features)} entités spatiales extraites avec succès."

        return None, "Aucune donnée géographique (lat/lon ou géométrie) trouvée dans la structure du fichier."

    def _clean_ogc_url(self, raw_url):
        if not raw_url:
            return "", None

        try:
            parsed = urllib.parse.urlparse(raw_url)
            qs = urllib.parse.parse_qs(parsed.query)

            extracted_layers = (
                qs.get('LAYERS') or qs.get('layers') or qs.get('layer') or
                qs.get('TYPENAME') or qs.get('typename') or qs.get('typeName')
            )
            layer_name = extracted_layers[0] if extracted_layers else None

            reserved_keys = {'SERVICE', 'REQUEST', 'VERSION', 'FORMAT', 'LAYERS', 'LAYER', 'TYPENAME', 'STYLES', 'STYLE', 'SRS', 'CRS', 'BBOX', 'MAXFEATURES', 'SRSNAME'}
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
            req = urllib.request.Request(capabilities_url, headers={'User-Agent': 'OpenGeoDataFR-QGIS/1.0'})
            with self._fetch_url(req, timeout=8) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                for elem in root.iter():
                    if elem.tag.endswith('Name') and elem.text and elem.text.strip():
                        name = elem.text.strip()
                        if name.upper() not in ('WMS', 'WFS', 'GETCAPABILITIES', 'WMS_CAPABILITIES', 'DEFAULT') and not name.startswith('http'):
                            return name
        except Exception as e:
            QgsMessageLog.logMessage(f"Impossible d'extraire la couche WMS: {e}", "OpenGeoDataFR", Qgis.Warning)
        return None

    def _discover_wfs_layer_name(self, raw_url, search_title=None):
        try:
            sep = "&" if "?" in raw_url else "?"
            capabilities_url = f"{raw_url}{sep}SERVICE=WFS&REQUEST=GetCapabilities" if "GetCapabilities" not in raw_url else raw_url
            req = urllib.request.Request(capabilities_url, headers={'User-Agent': 'OpenGeoDataFR-QGIS/1.0'})
            with self._fetch_url(req, timeout=10) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)

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
            QgsMessageLog.logMessage(f"Impossible d'extraire la couche WFS: {e}", "OpenGeoDataFR", Qgis.Warning)
        return None

    def _import_wms_layer(self, item, target_crs=None, territory_filter=None):
        raw_url = item.extra.get('wms_url') or item.url or "https://data.geopf.fr/wms-r/ows"

        # 1. Gestion des couches XYZ (OpenStreetMap, etc.)
        if '{z}' in raw_url or 'tile.openstreetmap' in raw_url.lower() or 'xyz' in str(item.extra.get('format', '')).lower():
            xyz_url = raw_url
            if '{z}' not in xyz_url:
                xyz_url = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
            encoded_url = urllib.parse.quote(xyz_url, safe=':/?&=%-')
            uri = f"type=xyz&url={encoded_url}&zmax=19&zmin=0"
            layer = QgsRasterLayer(uri, item.title, "wms")
            if layer.isValid():
                final_layer = self._apply_crs_and_filters(layer, item, target_crs=target_crs, territory_filter=territory_filter)
                QgsProject.instance().addMapLayer(final_layer)
                if territory_filter and str(territory_filter).lower() not in ("france", "toutes les échelles", "all"):
                    self._create_and_add_wms_mask(item, territory_filter)
                return True, f"Fond de carte XYZ '{item.title}' ajouté avec succès."

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
            else:
                return False, f"Impossible de déterminer le nom de la couche WMS pour : {raw_url}"

        crs_code = target_crs if (target_crs and "Native" not in target_crs) else "EPSG:3857"

        # Liste ordonnée d'URLs candidates pour la connexion WMS
        candidate_urls = [clean_url]

        # Détection intelligente pour la GéoPlateforme IGN (WMS-R pour rasters/ortho/cadastre, WMS-V pour vecteurs/GPU)
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
                QgsProject.instance().addMapLayer(final_layer)

                # Découpage du fond de carte raster par masque de polygone inversé
                if territory_filter and str(territory_filter).lower() not in ("france", "toutes les échelles", "all"):
                    self._create_and_add_wms_mask(item, territory_filter, raster_layer=final_layer)

                return True, f"Flux WMS '{item.title}' [couche {layer_name}, {crs_code}] ajouté avec succès."

        return False, f"Impossible de se connecter au flux WMS : {clean_url}"

    def _create_and_add_wms_mask(self, item, territory_filter, raster_layer=None):
        """
        Crée une couche vectorielle de découpage par masque en polygone inversé (fond blanc + contour rouge net)
        positionnée directement au-dessus du fond WMS/Raster pour masquer l'extérieur et ne laisser visible
        que l'emprise du territoire sélectionné.
        """
        try:
            from qgis.core import (
                QgsVectorLayer, QgsFeature, QgsInvertedPolygonRenderer,
                QgsSingleSymbolRenderer, QgsFillSymbol, QgsCoordinateTransform,
                QgsCoordinateReferenceSystem
            )
            terr_geom, terr_crs_str = self._get_territory_geometry(territory_filter)
            if not terr_geom or terr_geom.isEmpty():
                return

            # Utilise la projection du raster ou du projet pour éviter toute distorsion
            dest_crs_str = "EPSG:3857"
            if raster_layer and raster_layer.crs().isValid():
                dest_crs_str = raster_layer.crs().authid()
            elif QgsProject.instance().crs().isValid():
                dest_crs_str = QgsProject.instance().crs().authid()

            src_crs = QgsCoordinateReferenceSystem(terr_crs_str)
            dst_crs = QgsCoordinateReferenceSystem(dest_crs_str)

            geom_transformed = QgsGeometry(terr_geom)
            if src_crs.isValid() and dst_crs.isValid() and src_crs != dst_crs:
                xform = QgsCoordinateTransform(src_crs, dst_crs, QgsProject.instance())
                geom_transformed.transform(xform)

            mask_name = f"Masque Découpage - {item.title}"
            mask_layer = QgsVectorLayer(f"Polygon?crs={dest_crs_str}", mask_name, "memory")
            dp = mask_layer.dataProvider()
            feat = QgsFeature()
            feat.setGeometry(geom_transformed)
            dp.addFeatures([feat])
            mask_layer.updateExtents()

            fill_sym = QgsFillSymbol.createSimple({
                'color': '255,255,255,255',      # Masque blanc opaque à l'extérieur
                'outline_color': '217,4,41,255', # Contour rouge vif élégant
                'outline_width': '0.8',
                'outline_style': 'solid'
            })
            inv_renderer = QgsInvertedPolygonRenderer()
            inv_renderer.setEmbeddedRenderer(QgsSingleSymbolRenderer(fill_sym))
            mask_layer.setRenderer(inv_renderer)

            if raster_layer:
                root = QgsProject.instance().layerTreeRoot()
                raster_node = root.findLayer(raster_layer.id())
                if raster_node:
                    parent_group = raster_node.parent() or root
                    idx = parent_group.children().index(raster_node)
                    QgsProject.instance().addMapLayer(mask_layer, False)
                    parent_group.insertLayer(idx, mask_layer)
                else:
                    QgsProject.instance().addMapLayer(mask_layer)
            else:
                QgsProject.instance().addMapLayer(mask_layer)

        except Exception as mask_err:
            QgsMessageLog.logMessage(f"Erreur création masque WMS: {mask_err}", "OpenGeoDataFR", Qgis.Warning)

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
            codes = [c.strip() for c in tf.split(',') if c.strip()]

            # 1. TENTATIVE D'IMPORT DIRECT GEOJSON WFS AVEC CONVERSION DE PROJECTION CÔTÉ SERVEUR (SRSNAME)
            if codes:
                try:
                    if len(codes) > 1 and all(c.isdigit() and len(c) == 5 for c in codes):
                        formatted_insee = ", ".join([f"'{c}'" for c in codes])
                        direct_cql = f"code_insee IN ({formatted_insee})"
                    elif tf.isdigit() and len(tf) == 5:
                        direct_cql = f"code_insee='{tf}'"
                    elif tf.isdigit() and (len(tf) == 2 or len(tf) == 3):
                        direct_cql = f"code_dep='{tf}'"
                    else:
                        clean_tf = tf.replace("'", "''")
                        direct_cql = f"nom_com ILIKE '%{clean_tf}%'"

                    wfs_base = clean_url.split('?')[0]
                    params = {
                        "SERVICE": "WFS",
                        "REQUEST": "GetFeature",
                        "VERSION": "2.0.0",
                        "TYPENAMES": typename,
                        "OUTPUTFORMAT": "json",
                        "SRSNAME": srs_code,
                        "CQL_FILTER": direct_cql
                    }
                    direct_url = f"{wfs_base}?{urllib.parse.urlencode(params)}"
                    safe_file_id = "".join([c for c in f"wfs_{typename}_{srs_code}_{hash(direct_cql)}" if c.isalnum() or c == '_'])
                    cache_file = os.path.join(self.cache_dir, f"{safe_file_id}.geojson")

                    if progress_callback:
                        progress_callback(f"Téléchargement WFS réprojeté en {srs_code}...")

                    req = urllib.request.Request(direct_url, headers={'User-Agent': 'OpenGeoDataFR-QGIS/1.0'})
                    with self._fetch_url(req, timeout=12) as resp:
                        if resp.status == 200:
                            payload = resp.read()
                            with open(cache_file, 'wb') as f_out:
                                f_out.write(payload)

                            layer_direct = QgsVectorLayer(cache_file, item.title, "ogr")
                            if layer_direct.isValid() and layer_direct.featureCount() > 0:
                                final_layer = self._apply_crs_and_filters(layer_direct, item, target_crs=target_crs, territory_filter=territory_filter)
                                QgsProject.instance().addMapLayer(final_layer)
                                return True, f"Couche WFS '{item.title}' [{srs_code}, {layer_direct.featureCount()} entité(s)] ajoutée avec succès !"
                except Exception as direct_err:
                    QgsMessageLog.logMessage(f"Import direct GeoJSON ignoré: {direct_err}", "OpenGeoDataFR", Qgis.Warning)

            # 2. CHARGEMENT WFS NATIVE VIA QGIS AVEC REPROJECTION CÔTÉ SERVEUR (srsname)
            uri_clean_wfs = f"url='{clean_url}' typename='{typename}' srsname='{srs_code}' restrictToRequestBBOX='1' pagingEnabled='true' maxNumFeatures='5000'"
            layer_wfs = QgsVectorLayer(uri_clean_wfs, item.title, "WFS")
            if layer_wfs.isValid():
                final_layer = self._apply_crs_and_filters(layer_wfs, item, target_crs=target_crs, territory_filter=territory_filter)
                QgsProject.instance().addMapLayer(final_layer)
                return True, f"Flux WFS '{item.title}' [{typename}, {srs_code}] ajouté avec succès au projet."

            return self._import_wms_layer(item, target_crs=target_crs)
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
            layers_to_add = item.wms_layers or ["document", "zone_secteur", "prescription"]
            for lyr in layers_to_add:
                uri = f"contextualWMSLegend=0&crs={srs_code}&dpiMode=7&featureCount=10&format=image/png&layers={lyr}&styles=&url={urllib.parse.quote(clean_wms_url, safe=':/?&=%-')}"
                layer_title = f"{item.title} (WMS - {lyr})"
                layer = QgsRasterLayer(uri, layer_title, "wms")
                if layer.isValid():
                    final_layer = self._apply_crs_and_filters(layer, item, target_crs=target_crs)
                    QgsProject.instance().addMapLayer(final_layer)
                    added_count += 1

            if added_count > 0:
                return True, f"{added_count} couche(s) WMS GPU ({srs_code}) ajoutée(s) au projet."
            return False, "Échec de connexion WMS au Géoportail de l'Urbanisme."

        wfs_srs = target_crs if (target_crs and "Native" not in target_crs) else "EPSG:4326"
        for lyr in item.wfs_layers:
            uri = f"url='{clean_wfs_url}' typename='{lyr}' srsname='{wfs_srs}' restrictToRequestBBOX='1' pagingEnabled='true' maxNumFeatures='5000'"
            layer = QgsVectorLayer(uri, f"{item.title} (WFS - {lyr})", "WFS")
            if layer.isValid():
                final_layer = self._apply_crs_and_filters(layer, item, target_crs=target_crs, territory_filter=territory_filter)
                QgsProject.instance().addMapLayer(final_layer)
                added_count += 1

        if added_count > 0:
            return True, f"{added_count} couche(s) WFS GPU ({wfs_srs}) ajoutée(s) au projet."

        return self._import_urban_doc(item, as_wms=True, target_crs=target_crs, territory_filter=territory_filter, progress_callback=progress_callback)
