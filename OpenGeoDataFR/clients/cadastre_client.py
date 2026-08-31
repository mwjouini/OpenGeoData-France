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
        if ',' in q or 'epci:' in q or 'dep:' in q or 'reg:' in q:
            return query.strip()
        q = re.sub(r'\b(cadastre|parcelle|parcelles|pci|etalab|batiment|batiments|section|sections|lieux-dits)\b', '', q, flags=re.IGNORECASE)
        return q.strip() or query.strip()

    def _search_communes(self, query_text):
        if not query_text or not query_text.strip():
            return []

        q = query_text.strip()

        # 1. Liste de communes multiples séparées par des virgules
        if ',' in q:
            raw_codes = [c.replace("epci:", "").replace("dep:", "").replace("reg:", "").replace("com:", "").strip() for c in q.split(',') if c.strip()]
            results = []
            for code in raw_codes[:25]:
                if code.isdigit() and len(code) == 5:
                    url = f"{self.GEO_API_URL}/{code}?fields=nom,code,codeDepartement"
                    try:
                        content = fetch_url_bytes(url, timeout_ms=3000)
                        results.append(json.loads(content.decode('utf-8')))
                    except Exception:
                        results.append({"code": code, "nom": f"Commune {code}", "codeDepartement": code[:2]})
                elif code:
                    results.append({"code": code, "nom": f"Territoire {code}", "codeDepartement": code[:2] if len(code) >= 2 else ""})
            return results

        # 2. EPCI (ex: epci:200067098 ou 9 chiffres)
        if q.startswith("epci:") or (q.isdigit() and len(q) == 9):
            epci_code = q.replace("epci:", "").strip()
            url = f"https://geo.api.gouv.fr/communes?codeEpci={epci_code}&fields=nom,code,codeDepartement"
            try:
                content = fetch_url_bytes(url, timeout_ms=5000)
                return json.loads(content.decode('utf-8'))
            except Exception:
                return []

        # 3. Département (ex: dep:60 ou 2/3 chiffres)
        if q.startswith("dep:") or (len(q) in (2, 3) and (q.isdigit() or q.upper() in ('2A', '2B'))):
            dep_code = q.replace("dep:", "").strip().upper()
            url = f"https://geo.api.gouv.fr/departements/{dep_code}/communes?fields=nom,code,codeDepartement&limit=20"
            try:
                content = fetch_url_bytes(url, timeout_ms=5000)
                return json.loads(content.decode('utf-8'))
            except Exception:
                return []

        # 4. Commune unique (Nom ou Code Postal ou Code INSEE)
        clean_q = q.replace("com:", "").strip()
        if clean_q.isdigit() and len(clean_q) == 5:
            url = f"{self.GEO_API_URL}/{clean_q}?fields=nom,code,codeDepartement"
            try:
                content = fetch_url_bytes(url, timeout_ms=3500)
                data = json.loads(content.decode('utf-8'))
                return [data] if isinstance(data, dict) else (data if isinstance(data, list) else [])
            except Exception:
                return [{"code": clean_q, "nom": f"Commune {clean_q}", "codeDepartement": clean_q[:2]}]

        params = {
            "nom": clean_q,
            "fields": "nom,code,codeDepartement",
            "boost": "population",
            "limit": 4
        }
        url = f"{self.GEO_API_URL}?{urllib.parse.urlencode(params)}"
        try:
            content = fetch_url_bytes(url, timeout_ms=3500)
            return json.loads(content.decode('utf-8'))
        except Exception:
            return [{"code": clean_q, "nom": clean_q, "codeDepartement": ""}]

        return []
