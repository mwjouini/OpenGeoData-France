# OpenGeoData France - Extension QGIS

[![QGIS](https://img.shields.io/badge/QGIS-3.22%20à%203.40+-589632.svg?logo=qgis&logoColor=white)](https://qgis.org/)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/Licence-GPL--2.0%2B-blue.svg)](LICENSE)
[![GitHub release](https://img.shields.io/badge/Version-1.0.1-orange.svg)](https://github.com/mwjouini/OpenGeoData-France/releases)

**OpenGeoData France** est une extension QGIS conçue pour rechercher, explorer, découper et importer facilement toutes les données géographiques ouvertes françaises directement dans votre projet SIG.

---

## Fonctionnalités principales (v1.0.1)

### 1. Moteur de recherche unifié & filtres territoriaux multi-échelles
- **Recherche par mots-clés et référentiels** : Accès direct et instantané à plus de 1 200 API et services ouverts nationaux et régionaux.
- **Sélecteur territorial intelligent en cascade** :
  - Sélection par **Région**, **Département**, **EPCI (Intercommunalité)** ou **liste de communes multiples**.
  - Cache disque local persistant des contours (`<0.001s`) et téléchargement parallèle multithreadé.
  - Découpage vectoriel et masquage d'emprise adaptatifs (points, lignes, polygones et flux WMS raster).

### 2. Catalogue enrichi de 45 préréglages officiels prêts à l'emploi
- **Foncier & Cadastre** : Parcelles cadastrales (PCI Etalab / DGFiP), bâti, sections, lieux-dits, plan cadastral WMS Parcellaire Express.
- **Urbanisme réglementaire (GPU)** : Documents d'urbanisme (PLU/PLUi/POS), zonages (Zones U, AU, A, N), prescriptions et Servitudes d'Utilité Publique (SUP).
- **Adresses & Référentiels** : Base Adresse Nationale (BAN) et géocodage haute performance.
- **Météorologie & Climat en direct** :
  - **Radar de pluie & précipitations en temps réel** (actualisé toutes les 10 minutes).
  - **Imagerie satellite nuages & infrarouge** en continu.
  - **Réseau des stations météo SYNOP** et climatologiques (Météo-France / Infoclimat).
- **Imagerie spatiale, aérienne & historique** *(Suivi de l'évolution du territoire)* :
  - **Photographies aériennes haute résolution Ortho HR® 20 cm** (IGN).
  - **Photos aériennes historiques 1950-1965** (*IGN Remonter le Temps*).
  - **Imagerie satellite très haute résolution Pléiades 50 cm** et **SPOT 6-7** (CNES / IGN).
  - **Orthophotos Infrarouge Couleur (IRC)** pour l'analyse de la vigueur végétale et des forêts.
  - **Cartes historiques d'État-Major (1820-1866)** et **SCAN 50 (1950)**.
- **Environnement & Risques** : Natura 2000, ZNIEFF 1 & 2, Réserves naturelles, PPRN Inondations (EAIP), Aléa retrait-gonflement des argiles (RGA), Géologie 1/50 000 (BRGM).
- **Transports & Mobilités** : Voies BD TOPO®, aménagements cyclables (BNLC), réseau ferré et gares (SNCF), aires de covoiturage et bornes de recharge IRVE.
- **Logement & Données tabulaires** : Logements sociaux (RPLS), tables INSEE et conversion de données tabulaires (XLSX, XLS, ODS, CSV, Parquet).

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

