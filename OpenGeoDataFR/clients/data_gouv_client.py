# -*- coding: utf-8 -*-
"""
Client API pour data.gouv.fr (API Catalogue Datasets, Resources & Dataservices).
Prend en charge tous les formats géographiques, tables CSV/Excel, archives GZ/ZIP, WFS et WMS.
Permet également l'accès à l'API Tabulaire de data.gouv.fr pour l'exploration instantanée.
"""

import json
import urllib.parse
from ..models import DataItem
from ..utils.ssl_helper import fetch_url_bytes


class DataGouvClient:
    """Client de recherche étendu et optimisé sur l'API data.gouv.fr."""

    BASE_DATASETS_URL = "https://www.data.gouv.fr/api/1/datasets/"
    BASE_DATASERVICES_URL = "https://www.data.gouv.fr/api/1/dataservices/"
    TABULAR_API_BASE = "https://tabular-api.data.gouv.fr/api/resources/"

    def __init__(self, timeout=5):
        self.timeout = timeout

    def _detect_format_type(self, fmt_raw, res_url):
        fmt = (fmt_raw or '').lower().strip()
        url_lower = (res_url or '').lower()

        if any(x in fmt or x in url_lower for x in ('geojson', 'shp', 'shapefile', 'gpkg', 'geopackage', 'kml', 'kmz', 'gml', 'fgb', 'flatgeobuf', 'topojson')):
            return 'file_vector'
        if any(x in fmt or x in url_lower for x in ('csv', 'excel', 'xlsx', 'xls', 'tsv', 'parquet')):
            return 'table'
        if any(x in fmt or x in url_lower for x in ('tif', 'tiff', 'geotiff', 'jp2', 'ecw', 'asc', 'xyz', 'dem')):
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
        """Recherche sur data.gouv.fr avec gestion du tri et extraction complète des formats."""
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

        try:
            content = fetch_url_bytes(url, timeout_ms=self.timeout * 1000)
            data = json.loads(content.decode('utf-8'))
            datasets = data.get('data', [])
            for ds in datasets:
                items = self._parse_dataset(ds)
                results.extend(items)
        except Exception as e:
            print(f"[OpenGeoDataFR] Erreur DataGouvClient search datasets: {e}")

        # Recherche complémentaire sur les dataservices (APIs publiques)
        try:
            ds_url = f"{self.BASE_DATASERVICES_URL}?{urllib.parse.urlencode({'q': clean_query, 'page_size': 5})}"
            ds_content = fetch_url_bytes(ds_url, timeout_ms=self.timeout * 1000)
            ds_data = json.loads(ds_content.decode('utf-8'))
            dataservices = ds_data.get('data', [])
            for s in dataservices:
                item = self._parse_dataservice(s)
                if item:
                    results.append(item)
        except Exception:
            pass

        return results

    def _parse_dataset(self, ds):
        items = []
        dataset_id = ds.get('id', '')
        dataset_title = ds.get('title', 'Jeu de données')
        dataset_slug = ds.get('slug', dataset_id)
        web_url = f"https://www.data.gouv.fr/fr/datasets/{dataset_slug}/" if dataset_slug else ""
        
        org_name = ds.get('organization', {}).get('name') if ds.get('organization') else "data.gouv.fr"
        license_title = ds.get('license', 'Licence Ouverte')
        last_modified = ds.get('last_modified', '')[:10] if ds.get('last_modified') else '2025'
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
        clean_desc = (raw_desc[:250] + '...') if len(raw_desc) > 250 else raw_desc

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
        desc = (s.get('description') or '')[:200]
        
        return DataItem(
            item_id=f"dataservice_{s.get('id', hash(base_url))}",
            title=f"API : {title}",
            source=f"API Publique ({org_name})",
            data_type="file_vector",
            territory="France",
            scale="france",
            crs="EPSG:4326",
            date="2025 (API)",
            url=base_url,
            service_type="API",
            extra={
                'format': 'API REST',
                'organization': org_name,
                'description': desc,
                'web_url': f"https://www.data.gouv.fr/fr/dataservices/{s.get('id', '')}/"
            }
        )
