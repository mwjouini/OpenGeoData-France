# -*- coding: utf-8 -*-
"""
Client API pour la Base Adresse Nationale (BAN) et API Adresse.
"""

import json
import urllib.parse
import re
from ..models import DataItem
from ..utils.ssl_helper import fetch_url_bytes


class BanClient:
    """Client de recherche sur l'API Adresse et les jeux de données BAN/BAL."""

    API_ADRESSE_URL = "https://api-adresse.data.gouv.fr/search/"
    GEO_API_URL = "https://geo.api.gouv.fr/communes"

    def __init__(self, timeout=4):
        self.timeout = timeout

    def search(self, query):
        if not query or not query.strip():
            return []

        results = []
        clean_query = self._clean_query(query)

        # 1. API Adresse
        api_item = self._search_api_adresse(clean_query)
        if api_item:
            results.append(api_item)

        # 2. Recherche par commune / CP / INSEE
        communes = self._search_communes(clean_query)
        for commune in communes:
            code_insee = commune.get('code')
            nom_commune = commune.get('nom')

            if not code_insee:
                continue

            url_ban_commune = f"https://adresse.data.gouv.fr/api-gestion/dag/downloads/csv-bal/latest/communes/{code_insee}/ban-{code_insee}.csv"
            results.append(DataItem(
                item_id=f"ban_csv_{code_insee}",
                title=f"Base Adresse Nationale (BAN) - {nom_commune} ({code_insee})",
                source="Base Adresse Nationale (BAN)",
                data_type="table",
                territory=f"{nom_commune} ({code_insee})",
                scale="commune",
                crs="EPSG:4326",
                date="2025 (Flux BAN direct)",
                url=url_ban_commune,
                service_type="HTTP",
                extra={
                    'code_insee': code_insee,
                    'format': 'csv',
                    'delimiter': ';',
                    'date': '2025'
                }
            ))

        # 3. Jeu complet BAN France
        if 'france' in query.lower() or 'national' in query.lower():
            results.append(DataItem(
                item_id="ban_france_csv",
                title="Base Adresse Nationale (BAN) - France Entière",
                source="Base Adresse Nationale (BAN)",
                data_type="table",
                territory="France",
                scale="france",
                crs="EPSG:4326",
                date="2025",
                url="https://adresse.data.gouv.fr/data/ban/adresses/latest/csv/adresses-france.csv.gz",
                service_type="HTTP",
                extra={'format': 'csv.gz', 'date': '2025'}
            ))

        return results

    def _clean_query(self, query):
        q = query.lower()
        if ',' in q or 'epci:' in q or 'dep:' in q or 'reg:' in q:
            return query.strip()
        q = re.sub(r'\b(adresse|adresses|ban|bano|bal)\b', '', q, flags=re.IGNORECASE)
        return q.strip() or query.strip()

    def _search_api_adresse(self, query_text):
        params = {
            "q": query_text,
            "limit": 15
        }
        url = f"{self.API_ADRESSE_URL}?{urllib.parse.urlencode(params)}"
        try:
            content = fetch_url_bytes(url, timeout_ms=self.timeout * 1000)
            return DataItem(
                item_id=f"api_adresse_{hash(query_text)}",
                title=f"Géocodage API Adresse BAN : '{query_text}'",
                source="API Adresse (BAN)",
                data_type="file_vector",
                territory="France",
                scale="commune",
                crs="EPSG:4326",
                date="Temps Réel (2025)",
                url=url,
                service_type="HTTP",
                extra={
                    'is_geojson_url': True,
                    'query': query_text,
                    'date': '2025'
                }
            )
        except Exception as e:
            print(f"[OpenGeoDataFR] Erreur BanClient (API adresse): {e}")

        return None

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
        params = {
            "fields": "nom,code,codeDepartement",
            "limit": 4
        }
        if clean_q.isdigit() and len(clean_q) == 5:
            params["code"] = clean_q
        else:
            params["nom"] = clean_q
            params["boost"] = "population"

        url = f"{self.GEO_API_URL}?{urllib.parse.urlencode(params)}"
        try:
            content = fetch_url_bytes(url, timeout_ms=self.timeout * 1000)
            return json.loads(content.decode('utf-8'))
        except Exception as e:
            print(f"[OpenGeoDataFR] Erreur BanClient (communes search): {e}")

        return []


BANClient = BanClient
