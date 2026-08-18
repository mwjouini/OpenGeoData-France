# -*- coding: utf-8 -*-
"""
Client de recherche et d'accès aux données du Plan Cadastral Informatisé (PCI).
Intègre l'intégralité des flux et couches GeoJSON / WMS de cadastre.data.gouv.fr et Etalab.
"""

import json
import urllib.parse
import re
from ..models import DataItem
from ..utils.ssl_helper import fetch_url_bytes


class CadastreClient:
    """Client d'accès complet aux 7 couches cadastrales officielles (cadastre.data.gouv.fr)."""

    GEO_API_URL = "https://geo.api.gouv.fr/communes"
    BASE_CADASTRE_URL = "https://cadastre.data.gouv.fr/data/etalab-cadastre/latest/geojson/communes"

    def __init__(self, timeout=4):
        self.timeout = timeout

    def search(self, query):
        if not query or not query.strip():
            return []

        clean_query = self._clean_query(query)
        communes = self._search_communes(clean_query)
        results = []

        for commune in communes:
            code_insee = commune.get('code')
            nom_commune = commune.get('nom')
            dep_code = commune.get('codeDepartement', '')

            if not code_insee:
                continue

            base_commune_url = f"{self.BASE_CADASTRE_URL}/{dep_code}/{code_insee}"

            # 1. Parcelles Cadastrales (PCI Etalab)
            results.append(DataItem(
                item_id=f"cadastre_parcelles_{code_insee}",
                title=f"Parcelles Cadastrales (PCI Etalab) - {nom_commune} ({code_insee})",
                source="cadastre.data.gouv.fr",
                data_type="file_vector",
                territory=f"{nom_commune} ({code_insee})",
                scale="commune",
                crs="EPSG:4326",
                date="2025 (PCI Etalab)",
                url=f"{base_commune_url}/cadastre-{code_insee}-parcelles.json.gz",
                service_type="HTTP",
                extra={
                    'code_insee': code_insee,
                    'dep_code': dep_code,
                    'layer_type': 'cadastre_parcelles',
                    'format': 'geojson.gz',
                    'date': '2025'
                }
            ))

            # 2. Bâtiments du Cadastre
            results.append(DataItem(
                item_id=f"cadastre_batiments_{code_insee}",
                title=f"Bâtiments du Cadastre (PCI Etalab) - {nom_commune} ({code_insee})",
                source="cadastre.data.gouv.fr",
                data_type="file_vector",
                territory=f"{nom_commune} ({code_insee})",
                scale="commune",
                crs="EPSG:4326",
                date="2025",
                url=f"{base_commune_url}/cadastre-{code_insee}-batiments.json.gz",
                service_type="HTTP",
                extra={
                    'code_insee': code_insee,
                    'dep_code': dep_code,
                    'layer_type': 'cadastre_batiments',
                    'format': 'geojson.gz',
                    'date': '2025'
                }
            ))

            # 3. Sections Cadastrales
            results.append(DataItem(
                item_id=f"cadastre_sections_{code_insee}",
                title=f"Sections Cadastrales (PCI Etalab) - {nom_commune} ({code_insee})",
                source="cadastre.data.gouv.fr",
                data_type="file_vector",
                territory=f"{nom_commune} ({code_insee})",
                scale="commune",
                crs="EPSG:4326",
                date="2025",
                url=f"{base_commune_url}/cadastre-{code_insee}-sections.json.gz",
                service_type="HTTP",
                extra={
                    'code_insee': code_insee,
                    'dep_code': dep_code,
                    'layer_type': 'cadastre_sections',
                    'format': 'geojson.gz',
                    'date': '2025'
                }
            ))

            # 4. Lieux-dits & Hameaux
            results.append(DataItem(
                item_id=f"cadastre_lieux_dits_{code_insee}",
                title=f"Lieux-dits Cadastratifs (PCI Etalab) - {nom_commune} ({code_insee})",
                source="cadastre.data.gouv.fr",
                data_type="file_vector",
                territory=f"{nom_commune} ({code_insee})",
                scale="commune",
                crs="EPSG:4326",
                date="2025",
                url=f"{base_commune_url}/cadastre-{code_insee}-lieux_dits.json.gz",
                service_type="HTTP",
                extra={
                    'code_insee': code_insee,
                    'dep_code': dep_code,
                    'format': 'geojson.gz',
                    'date': '2025'
                }
            ))

            # 5. Subdivisions Fiscales
            results.append(DataItem(
                item_id=f"cadastre_subdfisc_{code_insee}",
                title=f"Subdivisions Fiscales Cadastre - {nom_commune} ({code_insee})",
                source="cadastre.data.gouv.fr",
                data_type="file_vector",
                territory=f"{nom_commune} ({code_insee})",
                scale="commune",
                crs="EPSG:4326",
                date="2025",
                url=f"{base_commune_url}/cadastre-{code_insee}-subdfisc.json.gz",
                service_type="HTTP",
                extra={
                    'code_insee': code_insee,
                    'dep_code': dep_code,
                    'format': 'geojson.gz',
                    'date': '2025'
                }
            ))

            # 6. WMS Cadastre
            url_wms = "https://data.geopf.fr/wms-r/ows"
            results.append(DataItem(
                item_id=f"cadastre_wms_{code_insee}",
                title=f"Plan Cadastral WMS - {nom_commune} ({code_insee})",
                source="Cadastre PCI WMS (DGFiP / IGN)",
                data_type="wms",
                territory=f"{nom_commune} ({code_insee})",
                scale="commune",
                crs="EPSG:3857",
                date="Temps Réel",
                url=url_wms,
                service_type="WMS",
                extra={
                    'wms_url': 'https://data.geopf.fr/wms-r/ows',
                    'layer_name': 'CADASTRALPARCELS.PARCELLAIRE_EXPRESS',
                    'code_insee': code_insee,
                    'format': 'Flux WMS',
                    'date': '2025'
                }
            ))

        return results

    def _clean_query(self, query):
        q = query.lower()
        q = re.sub(r'\b(cadastre|parcelle|parcelles|pci|etalab|batiment|batiments|section|sections|lieux-dits)\b', '', q, flags=re.IGNORECASE)
        return q.strip() or query.strip()

    def _search_communes(self, query_text):
        params = {
            "nom": query_text,
            "fields": "nom,code,codeDepartement",
            "boost": "population",
            "limit": 3
        }
        if query_text.isdigit() and len(query_text) == 5:
            params = {"code": query_text, "fields": "nom,code,codeDepartement", "limit": 3}
        elif query_text.isdigit() and (len(query_text) == 2 or len(query_text) == 3):
            params = {"codeDepartement": query_text, "fields": "nom,code,codeDepartement", "limit": 3}

        url = f"{self.GEO_API_URL}?{urllib.parse.urlencode(params)}"
        try:
            content = fetch_url_bytes(url, timeout_ms=self.timeout * 1000)
            return json.loads(content.decode('utf-8'))
        except Exception as e:
            print(f"[OpenGeoDataFR] Erreur CadastreClient (communes search): {e}")

        return []
