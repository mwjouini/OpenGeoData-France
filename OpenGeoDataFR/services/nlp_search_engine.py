# -*- coding: utf-8 -*-
"""
Moteur de Recherche Sémantique & Traitement du Langage Naturel (NLP) Local pour OpenGeoData France.
100% Autonome, Gratuit et Intégré en Python (aucun modèle payant, aucune clé API requise).
Comprend des phrases complètes, extrait automatiquement les entités géographiques
(communes, codes postaux, départements, régions) et identifie les intentions multi-couches
(Cadastre, Bâtiments BD TOPO, PLU, Risques, Mobilités, Environnement, Énergie, Fonds IGN).
"""

import re
import json
import urllib.request
import urllib.parse
import unicodedata
from ..utils.ssl_helper import fetch_url_bytes


def normalize_string(text):
    """Supprime les accents, met en minuscules et nettoie la ponctuation."""
    if not text:
        return ""
    text = unicodedata.normalize('NFD', text.lower())
    text = "".join(c for c in text if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9\s]', ' ', text).strip()


class NLPQueryResult:
    """Résultat structuré de l'interprétation sémantique d'une phrase."""

    def __init__(self, raw_query, territory_code="", territory_label="", territory_scale="",
                 matched_themes=None, matched_presets=None, search_keywords="", explanation=""):
        self.raw_query = raw_query
        self.territory_code = territory_code
        self.territory_label = territory_label
        self.territory_scale = territory_scale
        self.matched_themes = matched_themes or []
        self.matched_presets = matched_presets or []
        self.search_keywords = search_keywords
        self.explanation = explanation

    def has_territory(self):
        return bool(self.territory_code)

    def has_presets(self):
        return len(self.matched_presets) > 0


class NLPSearchEngine:
    """Moteur d'intelligence sémantique et d'extraction spatiale en langage naturel."""

    GEO_API_URL = "https://geo.api.gouv.fr"

    # Dictionnaire des départements français (Code -> Nom normalisé)
    DEPARTEMENTS = {
        "01": "ain", "02": "aisne", "03": "allier", "04": "alpes de haute provence",
        "05": "hautes alpes", "06": "alpes maritimes", "07": "ardeche", "08": "ardennes",
        "09": "ariege", "10": "aube", "11": "aude", "12": "aveyron", "13": "bouches du rhone",
        "14": "calvados", "15": "cantal", "16": "charente", "17": "charente maritime",
        "18": "cher", "19": "correze", "2a": "corse du sud", "2b": "haute corse",
        "21": "cote d or", "22": "cotes d armor", "23": "creuse", "24": "dordogne",
        "25": "doubs", "26": "drome", "27": "eure", "28": "eure et loir", "29": "finistere",
        "30": "gard", "31": "haute garonne", "32": "gers", "33": "gironde", "34": "herault",
        "35": "ille et vilaine", "36": "indre", "37": "indre et loire", "38": "isere",
        "39": "jura", "40": "landes", "41": "loir et cher", "42": "loire", "43": "haute loire",
        "44": "loire atlantique", "45": "loiret", "46": "lot", "47": "lot et garonne",
        "48": "lozere", "49": "maine et loire", "50": "manche", "51": "marne",
        "52": "haute marne", "53": "mayenne", "54": "meurthe et moselle", "55": "meuse",
        "56": "morbihan", "57": "moselle", "58": "nievre", "59": "nord", "60": "oise",
        "61": "orne", "62": "pas de calais", "63": "puy de dome", "64": "pyrenees atlantiques",
        "65": "hautes pyrenees", "66": "pyrenees orientales", "67": "bas rhin", "68": "haut rhin",
        "69": "rhone", "70": "haute saone", "71": "saone et loire", "72": "sarthe",
        "73": "savoie", "74": "haute savoie", "75": "paris", "76": "seine maritime",
        "77": "seine et marne", "78": "yvelines", "79": "deux sevres", "80": "somme",
        "81": "tarn", "82": "tarn et garonne", "83": "var", "84": "vaucluse",
        "85": "vendee", "86": "vienne", "87": "haute vienne", "88": "vosges",
        "89": "yonne", "90": "territoire de belfort", "91": "essonne", "92": "hauts de seine",
        "93": "seine saint denis", "94": "val de marne", "95": "val d oise",
        "971": "guadeloupe", "972": "martinique", "973": "guyane", "974": "la reunion", "976": "mayotte"
    }

    # Dictionnaire des 18 Régions françaises
    REGIONS = {
        "84": "auvergne rhone alpes", "27": "bourgogne franche comte", "53": "bretagne",
        "24": "centre val de loire", "94": "corse", "44": "grand est", "32": "hauts de france",
        "11": "ile de france", "28": "normandie", "75": "nouvelle aquitaine", "76": "occitanie",
        "52": "pays de la loire", "93": "provence alpes cote d azur",
        "01": "guadeloupe", "02": "martinique", "03": "guyane", "04": "la reunion", "06": "mayotte"
    }

    # Taxonomie sémantique des intentions thématiques (Mots-clés -> Identifiants de Presets)
    THEMES_INTENTS = {
        "cadastre": {
            "keywords": ["cadastre", "cadastral", "parcelle", "parcelles", "parcellaire", "section", "foncier", "propriete", "terrain", "terrains"],
            "presets": ["preset_pci_wms_ign", "preset_pci_beauvais"],
            "label": "Foncier & Cadastre"
        },
        "urbanisme": {
            "keywords": ["plu", "plui", "pos", "zonage", "zone urba", "zone urbaine", "reglement", "urbanisme", "scot", "sup", "servitude", "servitudes"],
            "presets": ["preset_gpu_zones_urba", "preset_gpu_sup", "preset_gpu_carte_nationale"],
            "label": "Urbanisme & Zonages PLU"
        },
        "batiment": {
            "keywords": ["batiment", "batiments", "hauteur", "hauteurs", "immeuble", "immeubles", "construction", "constructions", "bati", "maison", "maisons", "rnb"],
            "presets": ["preset_bdtopo_batiments"],
            "label": "Bâtiments & Hauteurs 3D"
        },
        "transport": {
            "keywords": ["velo", "velos", "cyclable", "cyclables", "piste", "pistes", "voie verte", "veloroute", "gare", "gares", "train", "trains", "sncf", "ferroviaire", "transport", "transports", "bus"],
            "presets": ["preset_reseau_cyclable_bnlc", "preset_reseau_ferre_sncf"],
            "label": "Transports & Mobilités"
        },
        "environnement": {
            "keywords": ["znieff", "natura", "natura2000", "biodiversite", "ecologique", "cours d eau", "cours d'eau", "riviere", "fleuve", "eau", "foret", "naturel", "nature"],
            "presets": ["preset_znieff1", "preset_znieff2", "preset_natura2000", "preset_cours_d_eau"],
            "label": "Environnement & Biodiversité"
        },
        "risques": {
            "keywords": ["risque", "risques", "inondation", "inondations", "pprn", "argile", "argiles", "rga", "seisme", "mouvement de terrain", "geologie", "geologique"],
            "presets": ["preset_pprn_georisques", "preset_argiles_rga", "preset_carte_geologique_brgm"],
            "label": "Risques Naturels & Géologie"
        },
        "energie": {
            "keywords": ["borne", "bornes", "recharge", "irve", "electrique", "solaire", "photovoltaique", "eolien", "eoliens", "enr", "energie", "electricite"],
            "presets": ["preset_bornes_irve", "preset_registre_enr"],
            "label": "Énergie & Réseaux"
        },
        "admin": {
            "keywords": ["commune", "communes", "departement", "departements", "region", "regions", "epci", "intercommunalite", "iris", "population", "insee", "sirene", "entreprise"],
            "presets": ["preset_communes_france", "preset_departements_france", "preset_regions_france", "preset_epci_france", "preset_iris_france", "preset_insee_cog"],
            "label": "Administratif & Démographie"
        },
        "raster": {
            "keywords": ["ortho", "orthophoto", "photo", "photos", "aerienne", "aeriennes", "satellite", "fond", "fond de carte", "scan25", "topographique", "osm", "openstreetmap", "plan ign"],
            "presets": ["preset_ortho_ign", "preset_plan_ign_v2", "preset_scan25_ign", "preset_osm_france"],
            "label": "Fonds de Carte & Imagerie"
        }
    }

    def __init__(self, all_presets=None):
        self.presets_dict = {p.id: p for p in (all_presets or [])}

    def update_presets(self, all_presets):
        self.presets_dict = {p.id: p for p in all_presets}

    def parse(self, raw_query):
        """
        Analyse une requête complète en langage naturel, extrait le territoire et associe les couches correspondantes.
        """
        if not raw_query or not raw_query.strip():
            return NLPQueryResult(raw_query)

        norm_q = normalize_string(raw_query)
        words = norm_q.split()

        # 1. Extraction d'entités territoriales
        terr_code, terr_label, terr_scale, terr_tokens = self._extract_territory(raw_query, norm_q, words)

        # 2. Nettoyage des mots-clés thématiques (en retirant les mots du territoire et les stop-words)
        stop_words = {
            "le", "la", "les", "un", "une", "des", "du", "de", "d", "a", "au", "aux",
            "en", "dans", "sur", "vers", "pour", "par", "avec", "sans", "sous",
            "donne", "moi", "cherche", "trouve", "affiche", "importe", "charge", "je", "veux", "voudrais",
            "s'il", "te", "plait", "svp", "merci", "tout", "tous", "toutes", "quel", "quelle", "quels",
            "commune", "ville", "secteur", "territoire", "carte", "couche", "couches", "donnees", "data"
        }

        theme_words = [w for w in words if w not in terr_tokens and w not in stop_words and len(w) > 1]

        # 3. Identification des thèmes et presets correspondants
        matched_themes = []
        matched_preset_ids = []

        for theme_key, theme_data in self.THEMES_INTENTS.items():
            hit = False
            for kw in theme_data["keywords"]:
                norm_kw = normalize_string(kw)
                if norm_kw in norm_q or any(w == norm_kw for w in theme_words):
                    hit = True
                    break
            if hit:
                matched_themes.append(theme_data["label"])
                matched_preset_ids.extend(theme_data["presets"])

        # Dédoublonnage des presets ordonnés
        matched_presets = []
        seen_ids = set()
        for pid in matched_preset_ids:
            if pid in self.presets_dict and pid not in seen_ids:
                matched_presets.append(self.presets_dict[pid])
                seen_ids.add(pid)

        # 4. Formulation de l'explication en français
        explanation_parts = []
        if terr_label:
            explanation_parts.append(f"Territoire détecté : **{terr_label}**")
        if matched_themes:
            explanation_parts.append(f"Thèmes : **{', '.join(matched_themes[:3])}**")
        if matched_presets:
            explanation_parts.append(f"{len(matched_presets)} couche(s) officielle(s) recommandée(s)")

        explanation = " | ".join(explanation_parts) if explanation_parts else "Recherche globale"

        search_keywords = " ".join(theme_words)

        return NLPQueryResult(
            raw_query=raw_query,
            territory_code=terr_code,
            territory_label=terr_label,
            territory_scale=terr_scale,
            matched_themes=matched_themes,
            matched_presets=matched_presets,
            search_keywords=search_keywords,
            explanation=explanation
        )

    def _extract_territory(self, raw_query, norm_q, words):
        """Détecte les codes postaux, départements, régions ou noms de communes dans la phrase."""
        terr_tokens = set()

        # 1. Détection de code postal ou code INSEE (5 chiffres)
        cp_match = re.search(r'\b([0-9]{5})\b', raw_query)
        if cp_match:
            cp = cp_match.group(1)
            terr_tokens.add(cp)
            commune_info = self._query_geoapi_commune(code_insee=cp) or self._query_geoapi_commune(code_postal=cp)
            if commune_info:
                return commune_info['code'], f"{commune_info['nom']} ({commune_info['code']})", "commune", terr_tokens

        # 2. Détection de numéro de département explicite ("dans le 60", "dept 33", "60")
        dep_match = re.search(r'\b(?:dans le|dept|département|dép\.?|le)\s*([0-9]{2,3}|2a|2b)\b', raw_query, re.IGNORECASE)
        if dep_match:
            dep_code = dep_match.group(1).lower()
            if dep_code in self.DEPARTEMENTS:
                terr_tokens.update(dep_match.group(0).lower().split())
                nom_dep = self.DEPARTEMENTS[dep_code].capitalize()
                return dep_code.upper(), f"Département {nom_dep} ({dep_code.upper()})", "departement", terr_tokens

        # 3. Détection par nom de département dans la phrase
        for dep_code, dep_nom in self.DEPARTEMENTS.items():
            if f" {dep_nom} " in f" {norm_q} " or norm_q.endswith(f" {dep_nom}") or norm_q.startswith(f"{dep_nom} "):
                for tok in dep_nom.split():
                    terr_tokens.add(tok)
                return dep_code.upper(), f"Département {dep_nom.capitalize()} ({dep_code.upper()})", "departement", terr_tokens

        # 4. Détection par nom de région
        for reg_code, reg_nom in self.REGIONS.items():
            if f" {reg_nom} " in f" {norm_q} " or norm_q.endswith(f" {reg_nom}") or norm_q.startswith(f"{reg_nom} "):
                for tok in reg_nom.split():
                    terr_tokens.add(tok)
                return reg_code, f"Région {reg_nom.capitalize()}", "region", terr_tokens

        # 5. Détection par préposition spatiale + nom de ville ("à Beauvais", "de Méru", "sur Nantes", "autour de Lyon")
        spatial_patterns = [
            r'(?:à|a|de|sur|vers|dans|autour de|près de|commune de|ville de)\s+([a-zA-ZÀ-ÿ\-\'\s]{2,25})'
        ]
        for pat in spatial_patterns:
            m = re.search(pat, raw_query, re.IGNORECASE)
            if m:
                candidate = m.group(1).strip()
                # Éviter les faux positifs sur des mots thématiques
                cand_norm = normalize_string(candidate)
                if not any(cand_norm.startswith(kw) for kw in ["cadastre", "plu", "batiment", "velo", "train", "photo", "risque"]):
                    commune_info = self._query_geoapi_commune(nom=candidate)
                    if commune_info:
                        for tok in cand_norm.split():
                            terr_tokens.add(tok)
                        return commune_info['code'], f"{commune_info['nom']} ({commune_info['code']})", "commune", terr_tokens

        # 6. Dernier recours : tester les mots en fin de phrase pour voir si c'est une commune connue
        if words:
            last_word = words[-1]
            if len(last_word) >= 3 and last_word not in {"france", "carte", "donnees", "couche", "plu", "wms", "wfs"}:
                commune_info = self._query_geoapi_commune(nom=last_word)
                if commune_info and normalize_string(commune_info['nom']) == last_word:
                    terr_tokens.add(last_word)
                    return commune_info['code'], f"{commune_info['nom']} ({commune_info['code']})", "commune", terr_tokens

        return "", "", "", terr_tokens

    def _query_geoapi_commune(self, nom=None, code_postal=None, code_insee=None):
        """Interroge l'API GeoAPI gratuite pour résoudre une commune avec son code INSEE officiel."""
        try:
            if code_insee:
                url = f"{self.GEO_API_URL}/communes/{code_insee}?fields=nom,code,codeDepartement"
                content = fetch_url_bytes(url, timeout_ms=3000)
                data = json.loads(content.decode('utf-8'))
                if data and isinstance(data, dict) and data.get('code'):
                    return data
            elif code_postal:
                url = f"{self.GEO_API_URL}/communes?codePostal={code_postal}&fields=nom,code,codeDepartement&boost=population&limit=1"
                content = fetch_url_bytes(url, timeout_ms=3000)
                data = json.loads(content.decode('utf-8'))
                if data and isinstance(data, list) and len(data) > 0:
                    return data[0]
            elif nom:
                clean_nom = urllib.parse.quote(nom.strip())
                url = f"{self.GEO_API_URL}/communes?nom={clean_nom}&fields=nom,code,codeDepartement&boost=population&limit=1"
                content = fetch_url_bytes(url, timeout_ms=3000)
                data = json.loads(content.decode('utf-8'))
                if data and isinstance(data, list) and len(data) > 0:
                    return data[0]
        except Exception:
            pass
        return None
