# -*- coding: utf-8 -*-
"""
Client API pour data.gouv.fr (API Catalogue Datasets, Resources & Dataservices).
Prend en charge tous les formats géographiques, tables CSV/Excel, archives GZ/ZIP,
données de transport GTFS et NeTEx, OpenDataSoft APIs, WFS et WMS.
Connecte plus de 1 200 dataservices (APIs) et 47 000 jeux de données.
"""

import json
import urllib.parse
from ..models import DataItem
from ..utils.ssl_helper import fetch_url_bytes


class DataGouvClient:
    """Client de recherche étendu et optimisé sur l'API data.gouv.fr (Datasets & Dataservices)."""

    BASE_DATASETS_URL = "https://www.data.gouv.fr/api/1/datasets/"
    BASE_DATASERVICES_URL = "https://www.data.gouv.fr/api/1/dataservices/"
    TABULAR_API_BASE = "https://tabular-api.data.gouv.fr/api/resources/"

    def __init__(self, timeout=6):
        self.timeout = timeout

    def _detect_format_type(self, fmt_raw, res_url):
        fmt = (fmt_raw or '').lower().strip()
        url_lower = (res_url or '').lower()

        if any(x in fmt or x in url_lower for x in ('geojson', 'shp', 'shapefile', 'gpkg', 'geopackage', 'kml', 'kmz', 'gml', 'fgb', 'flatgeobuf', 'topojson', 'gtfs', 'netex', 'gbfs', 'gpx', 'dxf', 'tab')):
            return 'file_vector'
        if any(x in fmt or x in url_lower for x in ('csv', 'excel', 'xlsx', 'xls', 'tsv', 'parquet')):
            return 'table'
        if any(x in fmt or x in url_lower for x in ('tif', 'tiff', 'geotiff', 'jp2', 'ecw', 'asc', 'xyz', 'dem', 'cog')):
            return 'file_raster'
        if 'wms' in fmt or 'wms' in url_lower or 'wmts' in fmt or 'wmts' in url_lower:
            return 'wms'
        if 'wfs' in fmt or 'wfs' in url_lower or 'ogcapi' in fmt:
            return 'wfs'
        if any(x in fmt or x in url_lower for x in ('zip', 'gz', 'tar.gz', '7z')):
            return 'file_vector'
        if 'json' in fmt or 'json' in url_lower:
            return 'file_vector'
        return None

    def _detect_category(self, title, desc, org):
        """Catégorise automatiquement le jeu de données pour les filtres de l'interface."""
        text = f"{title} {desc} {org}".lower()
        if any(w in text for w in ('cadastre', 'parcelle', 'foncier', 'pci', 'dgfip')):
            return 'cadastre'
        if any(w in text for w in ('plu', 'plui', 'pos', 'urbanisme', 'gpu', 'zonage', 'servitude', 'sup')):
            return 'urbanisme'
        if any(w in text for w in ('velo', 'cyclable', 'gare', 'sncf', 'train', 'bus', 'transport', 'gtfs', 'netex', 'covoiturage', 'route', 'pan')):
            return 'transport'
        if any(w in text for w in ('znieff', 'natura', 'biodiversite', 'eau', 'riviere', 'foret', 'inpn', 'ofb', 'patrinat', 'climat', 'espece')):
            return 'environnement'
        if any(w in text for w in ('inondation', 'pprn', 'argile', 'seisme', 'radon', 'alea', 'risque', 'geologie', 'brgm', 'georisques', 'tri')):
            return 'risques'
        if any(w in text for w in ('irve', 'recharge', 'enr', 'photovoltaique', 'eolien', 'electricite', 'rte', 'enedis', 'sdes', 'energie')):
            return 'energie'
        if any(w in text for w in ('commune', 'departement', 'region', 'epci', 'iris', 'insee', 'sirene', 'population', 'adminexpress', 'cog')):
            return 'admin'
        if any(w in text for w in ('ortho', 'scan 25', 'plan ign', 'raster', 'mnt', 'altitude', 'rge alti')):
            return 'raster'
        return 'admin'

    def _format_size(self, size_bytes):
        if not size_bytes or not isinstance(size_bytes, (int, float)):
            return ""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

    def search(self, query, page_size=40, sort=None):
        """Recherche combinée sur data.gouv.fr : Datasets (jeux de données) et Dataservices (APIs publiques)."""
        if not query or not query.strip():
            return []

        clean_query = query.strip()
        params = {
            "q": clean_query,
            "page_size": page_size
        }
        if sort:
            params["sort"] = sort

        url = f"{self.BASE_DATASETS_URL}?{urllib.parse.urlencode(params)}"
        results = []

        # 1. Recherche Datasets (Jeux de données et ressources téléchargeables)
        try:
            content = fetch_url_bytes(url, timeout_ms=self.timeout * 1000)
            data = json.loads(content.decode('utf-8'))
            datasets = data.get('data', [])
            for ds in datasets:
                items = self._parse_dataset(ds)
                results.extend(items)
        except Exception as e:
            print(f"[OpenGeoDataFR] Erreur DataGouvClient search datasets: {e}")

        # 2. Recherche Dataservices (Plus de 1 200 APIs publiques françaises)
        try:
            ds_url = f"{self.BASE_DATASERVICES_URL}?{urllib.parse.urlencode({'q': clean_query, 'page_size': 15})}"
            ds_content = fetch_url_bytes(ds_url, timeout_ms=self.timeout * 1000)
            ds_data = json.loads(ds_content.decode('utf-8'))
            dataservices = ds_data.get('data', [])
            for s in dataservices:
                item = self._parse_dataservice(s)
                if item:
                    results.append(item)
        except Exception as ds_err:
            print(f"[OpenGeoDataFR] Recherche dataservices ignorée : {ds_err}")

        return results

    def _parse_dataset(self, ds):
        items = []
        dataset_id = ds.get('id', '')
        dataset_title = ds.get('title', 'Jeu de données')
        dataset_slug = ds.get('slug', dataset_id)
        web_url = f"https://www.data.gouv.fr/fr/datasets/{dataset_slug}/" if dataset_slug else ""
        
        org_name = ds.get('organization', {}).get('name') if ds.get('organization') else "data.gouv.fr"
        license_title = ds.get('license', 'Licence Ouverte')
        last_modified = ds.get('last_modified', '')[:10] if ds.get('last_modified') else '2026'
        spatial_granularity = ds.get('spatial', {}).get('granularity', 'france') if ds.get('spatial') else 'france'

        scale = "france"
        if "commune" in spatial_granularity.lower():
            scale = "commune"
        elif "departement" in spatial_granularity.lower():
            scale = "departement"
        elif "region" in spatial_granularity.lower():
            scale = "region"
        elif "epci" in spatial_granularity.lower():
            scale = "epci"

        raw_desc = ds.get('description', '') or ''
        clean_desc = (raw_desc[:300] + '...') if len(raw_desc) > 300 else raw_desc
        category = self._detect_category(dataset_title, raw_desc, org_name)

        resources = ds.get('resources', [])
        for res in resources:
            if not isinstance(res, dict):
                continue
            fmt_raw = res.get('format') or ''
            res_url = res.get('url')
            res_id = res.get('id', '')

            if not res_url:
                continue

            data_type = self._detect_format_type(fmt_raw, res_url)
            if not data_type:
                continue

            res_title = res.get('title') or ''
            if res_title and res_title != dataset_title and dataset_title not in res_title:
                title = f"{dataset_title} - {res_title}"
            else:
                title = dataset_title

            size_bytes = res.get('filesize') or res.get('size')
            size_str = self._format_size(size_bytes)
            if size_str:
                res_fmt_label = f"{fmt_raw.upper()} ({size_str})"
            else:
                res_fmt_label = fmt_raw.upper() if fmt_raw else "AUTO"

            service_type = 'WMS' if data_type == 'wms' else ('WFS' if data_type == 'wfs' else 'HTTP')
            tabular_api_url = f"{self.TABULAR_API_BASE}{res_id}/data/" if data_type == 'table' and res_id else None

            items.append(DataItem(
                item_id=f"datagouv_{res_id or hash(res_url)}",
                title=title,
                source=f"data.gouv.fr ({org_name})",
                data_type=data_type,
                territory="France",
                scale=scale,
                crs="EPSG:4326",
                date=last_modified,
                url=res_url,
                service_type=service_type,
                extra={
                    'dataset_id': dataset_id,
                    'resource_id': res_id,
                    'organization': org_name,
                    'category': category,
                    'format': res_fmt_label,
                    'format_raw': fmt_raw,
                    'size': size_str,
                    'license': license_title,
                    'description': clean_desc,
                    'web_url': web_url,
                    'tabular_api_url': tabular_api_url,
                    'date': last_modified
                }
            ))

        return items

    def _parse_dataservice(self, s):
        title = s.get('title')
        if not title:
            return None
        base_url = s.get('base_api_url') or s.get('self_web_url')
        if not base_url:
            return None

        org_name = s.get('organization', {}).get('name') if s.get('organization') else "data.gouv.fr"
        desc = (s.get('description') or '')[:300]
        category = self._detect_category(title, desc, org_name)

        service_type = "API"
        data_type = "file_vector"
        url_lower = base_url.lower()

        if 'wms' in url_lower:
            data_type = 'wms'
            service_type = 'WMS'
        elif 'wfs' in url_lower:
            data_type = 'wfs'
            service_type = 'WFS'
        elif 'wmts' in url_lower:
            data_type = 'wms'
            service_type = 'WMTS'

        return DataItem(
            item_id=f"dataservice_{s.get('id', hash(base_url))}",
            title=f"API : {title}",
            source=f"API Publique ({org_name})",
            data_type=data_type,
            territory="France",
            scale="france",
            crs="EPSG:4326",
            date="2026 (API)",
            url=base_url,
            service_type=service_type,
            extra={
                'format': f'API {service_type}',
                'category': category,
                'organization': org_name,
                'description': desc,
                'web_url': f"https://www.data.gouv.fr/fr/dataservices/{s.get('id', '')}/"
            }
        )
