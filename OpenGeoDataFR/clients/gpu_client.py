# -*- coding: utf-8 -*-
"""
Client API pour le Géoportail de l'urbanisme (GPU).
Gère la recherche de documents d'urbanisme (PLU, PLUi, SCOT, CC, SUP) et l'accès aux flux WMS/WFS de la GéoPlateforme.
"""

import json
import urllib.parse
import re
from ..models import DataItem, UrbanDocItem
from ..utils.ssl_helper import fetch_url_bytes


class GPUClient:
    """Client API et services WMS/WFS du Géoportail de l'urbanisme (GPU)."""

    GPU_API_BASE = "https://www.geoportail-urbanisme.gouv.fr/api"
    GEO_API_URL = "https://geo.api.gouv.fr/communes"
    
    WMS_URL = "https://data.geopf.fr/wms-v/ows"
    WFS_URL = "https://data.geopf.fr/wfs/ows"

    def __init__(self, timeout=4):
        self.timeout = timeout

    def search(self, query):
        if not query or not query.strip():
            return []

        results = []
        clean_query = self._clean_query(query)
        q_lower = query.lower()

        # Cas 1: Couche globale "document" GPU
        if 'document' in q_lower or 'carte' in q_lower or 'emprise' in q_lower:
            results.append(UrbanDocItem(
                item_id="gpu_document_layer",
                title="Carte nationale des documents d'urbanisme (GPU)",
                doc_type="Document",
                territory="France",
                scale="france",
                crs="EPSG:3857",
                date="2025",
                url=self.WMS_URL,
                service_type="WMS",
                wms_layers=["document"],
                wfs_layers=["wfs_du:document"],
                extra={'date': '2025'}
            ))

        # Cas 2: Recherche par commune / CP / INSEE
        communes = self._search_communes(clean_query)

        for commune in communes:
            code_insee = commune.get('code')
            nom_commune = commune.get('nom')

            if not code_insee:
                continue

            doc_info = self._get_grid_document(code_insee)

            if doc_info and doc_info.get('duType'):
                du_type = doc_info.get('duType', 'PLU')
                doc_id = doc_info.get('gridId') or f"gpu_{code_insee}"
                doc_date = doc_info.get('gridDate') or '2025'

                item = UrbanDocItem(
                    item_id=f"gpu_doc_{code_insee}",
                    title=f"Document d'urbanisme {du_type} - {nom_commune} ({code_insee})",
                    doc_type=du_type,
                    territory=f"{nom_commune} ({code_insee})",
                    scale="commune",
                    crs="EPSG:3857",
                    date=doc_date,
                    url=self.WMS_URL,
                    service_type="WMS",
                    wms_layers=["document", "zone_secteur", "prescription"],
                    wfs_layers=["wfs_du:zone_urba", "wfs_du:prescription_pct"],
                    cql_filter=f"partition='DU_{code_insee}'",
                    extra={
                        'code_insee': code_insee,
                        'du_type': du_type,
                        'grid_id': doc_id,
                        'date': doc_date,
                        'wms_url': self.WMS_URL,
                        'wfs_url': self.WFS_URL
                    }
                )
                results.append(item)
            else:
                # Ajout par défaut de la couverture d'urbanisme de la commune
                results.append(UrbanDocItem(
                    item_id=f"gpu_doc_def_{code_insee}",
                    title=f"Document d'Urbanisme & ZONAGE - {nom_commune} ({code_insee})",
                    doc_type="PLU/CC",
                    territory=f"{nom_commune} ({code_insee})",
                    scale="commune",
                    crs="EPSG:3857",
                    date="2025",
                    url=self.WMS_URL,
                    service_type="WMS",
                    wms_layers=["document", "zone_secteur", "prescription"],
                    wfs_layers=["wfs_du:zone_urba", "wfs_du:prescription_pct"],
                    cql_filter=f"code_insee='{code_insee}'",
                    extra={
                        'code_insee': code_insee,
                        'date': '2025',
                        'wms_url': self.WMS_URL,
                        'wfs_url': self.WFS_URL
                    }
                ))

        return results

    def _clean_query(self, query):
        q = query.lower()
        q = re.sub(r'\b(gpu|plu|plui|scot|urbanisme|pos|cc|sup|zonage|zone)\b', '', q, flags=re.IGNORECASE)
        return q.strip() or query.strip()

    def _search_communes(self, query_text):
        params = {
            "nom": query_text,
            "fields": "nom,code,codeDepartement",
            "boost": "population",
            "limit": 4
        }
        if query_text.isdigit() and len(query_text) == 5:
            params = {"code": query_text, "fields": "nom,code,codeDepartement", "limit": 4}
        elif query_text.isdigit() and (len(query_text) == 2 or len(query_text) == 3):
            params = {"codeDepartement": query_text, "fields": "nom,code,codeDepartement", "limit": 4}

        url = f"{self.GEO_API_URL}?{urllib.parse.urlencode(params)}"
        try:
            content = fetch_url_bytes(url, timeout_ms=self.timeout * 1000)
            return json.loads(content.decode('utf-8'))
        except Exception as e:
            print(f"[OpenGeoDataFR] Erreur GPUClient (communes search): {e}")

        return []

    def _get_grid_document(self, code_insee):
        url = f"{self.GPU_API_BASE}/document?municipality={code_insee}"
        try:
            content = fetch_url_bytes(url, timeout_ms=self.timeout * 1000)
            data = json.loads(content.decode('utf-8'))
            if isinstance(data, list) and len(data) > 0:
                return data[0]
            elif isinstance(data, dict):
                return data
        except Exception as e:
            print(f"[OpenGeoDataFR] Erreur GPUClient (document): {e}")

        return None
