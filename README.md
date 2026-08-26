# OpenGeoData France - Extension QGIS

[![QGIS](https://img.shields.io/badge/QGIS-3.22%20à%203.40+-589632.svg?logo=qgis&logoColor=white)](https://qgis.org/)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/Licence-GPL--2.0%2B-blue.svg)](LICENSE)
[![GitHub release](https://img.shields.io/badge/Version-1.0.0-orange.svg)](https://github.com/mwjouini/OpenGeoData-France/releases)

**OpenGeoData France** est une extension QGIS conçue pour rechercher, explorer et importer facilement les données géographiques ouvertes françaises directement dans votre projet SIG.

---

## Fonctionnalités principales

### 1. Moteur de recherche sémantique & NLP local
- **Compréhension du langage naturel** : Saisissez des requêtes en langage courant telles que :
  - *« Je veux le cadastre et le PLU de Beauvais »*
  - *« Pistes cyclables et gares dans l'Oise »*
  - *« Zones inondables et ZNIEFF à Bordeaux »*
- **Reconnaissance d'entités territoriales (NER)** : Détection automatique des communes françaises, codes postaux, codes INSEE et départements.
- **Indexation vectorielle et synonymes** : Recherche tolérante aux fautes de frappe et enrichie par un thésaurus géomatique (*parcelles, zonages, biodiversité, risques, transports...*).
- **Fonctionnement 100% local et gratuit** : Traitement en local dans QGIS, sans aucune clé API payante ou dépendance externe.

### 2. Catalogue de 28 presets officiels prêts à l'emploi
Accédez rapidement aux principaux jeux de données de référence :
- **Cadastre & foncier** : Parcelles cadastrales (PCI Etalab / DGFiP), bâtiments cadastraux, plan cadastral WMS.
- **Bâti & topographie** : BD TOPO® Bâtiments avec hauteurs et attributs (IGN).
- **Adresses** : Base Adresse Nationale (BAN).
- **Urbanisme & planification** : Documents d'urbanisme (PLU/PLUi/POS) et Servitudes d'Utilité Publique (SUP) du Géoportail de l'Urbanisme.
- **Environnement & biodiversité** : Réseau Natura 2000 (SIC/ZSC & ZPS), ZNIEFF Type 1 et Type 2 (INPN / OFB / PatriNat).
- **Risques & géologie** : Plans de Prévention des Risques Naturels (PPRN Géorisques), cavités souterraines et mouvements de terrain (BRGM).
- **Transports & mobilités** : Aménagements cyclables nationaux (BNLC), réseau ferré et gares (SNCF Réseau).
- **Énergie & réseaux** : Bornes de recharge pour véhicules électriques (IRVE), installations de production d'électricité EnR.
- **Imagerie & fonds raster** : Orthophotos Ortho HR®, carte IGN, plan IGN vecteur, Scan 25 et relief ombré (GéoPlateforme).

### 3. Découpage territorial intelligent & masques cartographiques
- **Découpage vectoriel exact** : Intersection géométrique selon les limites officielles des communes (via GeoAPI contour).
- **Masquage dynamique des fonds WMS/Raster** : Génération d'un masque inversé pour isoler proprement votre zone d'étude sur vos cartes et orthophotos.
- **Import à la carte** : Choix lors de l'import entre l'emprise communale découpée ou le jeu de données complet.

### 4. Gestion des systèmes de coordonnées (CRS)
- Reprojection automatique vers **Lambert-93 (EPSG:2154)**, **WGS 84 (EPSG:4326)**, **Web Mercator (EPSG:3857)** ou les projections officielles d'Outre-Mer (**RGAF09, RGM04, UTM**).

### 5. Performance & traitement asynchrone
- Téléchargements et traitements exécutés en arrière-plan pour conserver une interface fluide dans QGIS.
- Intégration sécurisée des couches sur le thread principal pour éviter tout blocage.
- Panneau d'information avec métadonnées, liens vers les fiches sources et copie rapide des URLs.

---

## Installation

### Méthode 1 : Depuis le fichier ZIP (Recommandé)
1. Téléchargez la dernière version : [**OpenGeoDataFR.zip**](https://github.com/mwjouini/OpenGeoData-France/raw/main/OpenGeoDataFR.zip).
2. Dans QGIS, ouvrez le menu : **Extensions** > **Installer/Gérer les extensions**.
3. Allez dans l'onglet **Installer depuis un ZIP**.
4. Sélectionnez le fichier `OpenGeoDataFR.zip` puis cliquez sur **Installer l'extension**.

### Méthode 2 : Installation manuelle via Git

**Sous Windows (PowerShell) :**
```powershell
cd "$env:APPDATA\QGIS\QGIS3\profiles\default\python\plugins"
git clone https://github.com/mwjouini/OpenGeoData-France.git OpenGeoDataFR
```

**Sous Linux :**
```bash
cd ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins
git clone https://github.com/mwjouini/OpenGeoData-France.git OpenGeoDataFR
```

**Sous macOS :**
```bash
cd ~/Library/Application\ Support/QGIS/QGIS3/profiles/default/python/plugins
git clone https://github.com/mwjouini/OpenGeoData-France.git OpenGeoDataFR
```

---

## Utilisation rapide

1. Activez l'extension depuis la barre d'outils ou via le menu **Extensions > OpenGeoData France**.
2. Dans le panneau latéral :
   - Saisissez votre recherche (mots-clés ou langage naturel).
   - Indiquez si besoin un filtre territorial (commune ou code INSEE).
   - Choisissez le système de projection souhaité (ex: `EPSG:2154 - Lambert-93`).
3. Double-cliquez sur un résultat ou cliquez sur **Ajouter au projet** pour charger la donnée.

---

## Services et données connectés

- [**GéoPlateforme IGN**](https://geoservices.ign.fr/) : Flux WMS-R, WMS-V, WFS et WMTS.
- [**data.gouv.fr**](https://www.data.gouv.fr/) : Plateforme nationale des données ouvertes.
- [**Cadastre PCI Etalab / DGFiP**](https://cadastre.data.gouv.fr/) : Plan cadastral informatisé.
- [**Géoportail de l'Urbanisme (GPU)**](https://www.geoportail-urbanisme.gouv.fr/) : Document d'urbanisme (PLU, PLUi, POS) et SUP.
- [**Base Adresse Nationale (BAN)**](https://adresse.data.gouv.fr/) : Référentiel des adresses.
- [**INPN / PatriNat / OFB**](https://inpn.mnhn.fr/) : Données de biodiversité et espaces protégés.
- [**BRGM / Géorisques**](https://www.georisques.gouv.fr/) : Risques naturels, PPRN et données géologiques.
- [**SNCF Réseau Open Data**](https://data.sncf.com/) : Réseau ferroviaire et gares.
- [**geo.api.gouv.fr**](https://geo.api.gouv.fr/) : Découpage administratif.

---

## Auteur & Contact

- **Auteur** : Mohamed Wael JOUINI
- **Contact** : [mohamed.wael.jouini@gmail.com](mailto:mohamed.wael.jouini@gmail.com)
- **Dépôt GitHub** : [https://github.com/mwjouini/OpenGeoData-France](https://github.com/mwjouini/OpenGeoData-France)
- **Signalement d'anomalies (Issues)** : [https://github.com/mwjouini/OpenGeoData-France/issues](https://github.com/mwjouini/OpenGeoData-France/issues)

---

## Licence

Ce projet est sous licence libre **GNU General Public License v2.0 or later (GPL-2.0+)**.

