# 🗺️ OpenGeoData France - Extension QGIS

[![QGIS](https://img.shields.io/badge/QGIS-3.22%20à%203.40+-589632.svg?logo=qgis&logoColor=white)](https://qgis.org/)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/Licence-GPL--2.0%2B-blue.svg)](LICENSE)
[![GitHub release](https://img.shields.io/badge/Version-1.0.0-orange.svg)](https://github.com/mwjouini/OpenGeoData-France/releases)

**OpenGeoData France** est une extension QGIS complète, moderne et ergonomique pour rechercher, explorer et importer instantanément les données géographiques ouvertes françaises directement dans votre projet SIG.

---

## ✨ Fonctionnalités Principales

### 1. 🔍 Moteur de Recherche Sémantique & NLP Local (100% Gratuit & Autonome)
- **Compréhension du langage naturel** : Saisissez des phrases complètes telles que :
  - *« Je veux le cadastre et le PLU de Beauvais »*
  - *« Pistes cyclables et gares dans l'Oise »*
  - *« Zones inondables et ZNIEFF à Bordeaux »*
- **Reconnaissance d'entités territoriales (NER)** : Détection automatique des 35 000 communes françaises, codes postaux, codes INSEE et 101 départements.
- **Indexation vectorielle & synonymes** : Recherche tolérante aux fautes de frappe et enrichie par l'ontologie géomatique française (*parcelle, zonage, faune, risques, réseaux...*).
- **Zéro coût / Zéro API externe payante** : Tout s'exécute en local dans QGIS.

### 2. 📚 Catalogue de 28 Presets Officiels Prêts à l'Emploi
Accédez en un clic aux jeux de données de référence nationaux :
- **Cadastre & Foncier** : Parcelles cadastrales (PCI Etalab / DGFiP), Bâtiments cadastraux, Plan cadastral WMS.
- **Bâti & Topographie** : BD TOPO® Bâtiments avec hauteurs réelles et attributs détaillés (IGN).
- **Adresses** : Base Adresse Nationale (BAN) complète.
- **Urbanisme & Planification** : Documents d'urbanisme (PLU/PLUi/POS) et Servitudes d'Utilité Publique (SUP) du Géoportail de l'Urbanisme.
- **Environnement & Biodiversité** : Réseau Natura 2000 (SIC/ZSC & ZPS), ZNIEFF Type 1 et Type 2 (INPN / OFB / PatriNat).
- **Risques & Géologie** : Plans de Prévention des Risques Naturels (PPRN Géorisques), Cavités souterraines et mouvements de terrain (BRGM).
- **Transports & Mobilités** : Aménagements cyclables nationaux (BNLC), Réseau ferré et gares (SNCF Réseau).
- **Énergie & Réseaux** : Bornes de recharge pour véhicules électriques (IRVE), Registre des installations de production d'électricité EnR.
- **Imagerie & Fonds Raster** : Photographies aériennes Ortho HR®, Carte IGN classique, Plan IGN vecteur, Scan 25, Relief ombré (GéoPlateforme).

### 3. ✂️ Découpage Territorial Intelligent & Masques Cartographiques
- **Découpage vectoriel géométrique** : Intersection polygonale exacte selon les limites officielles des communes (via GeoAPI contour).
- **Détourage des fonds WMS/Raster** : Génération automatique d'un masque en polygone inversé (`Masque Découpage - ...`) pour détourer proprement vos orthophotos et cartes.
- **Dialogue interactif** : Choix à l'importation entre le découpage territorial et le jeu national complet.

### 4. 🧭 Gestion des Systèmes de Coordonnées (CRS)
- Reprojection automatique à la volée vers **Lambert-93 (EPSG:2154)**, **WGS 84 (EPSG:4326)**, **Web Mercator (EPSG:3857)** ou les projections officielles d'Outre-Mer (**RGAF09, RGM04, UTM**).

### 5. ⚡ Performance & Stabilité Multi-Threading
- Téléchargements et traitements asynchrones en arrière-plan sans bloquer l'interface QGIS.
- Ajout sécurisé des couches sur le thread graphique principal (100% sans plantage).
- Volet d'inspection rapide **Fiche & Métadonnées** avec accès direct aux fiches sources et copie des URLs.

---

## 📥 Installation

### Méthode 1 : Depuis le fichier ZIP (Recommandé)
1. Téléchargez la dernière version : [**OpenGeoDataFR.zip**](https://github.com/mwjouini/OpenGeoData-France/raw/main/OpenGeoDataFR.zip).
2. Dans QGIS, allez dans le menu : **Extensions** > **Installer/Gérer les extensions**.
3. Sélectionnez l'onglet **Installer depuis un ZIP**.
4. Pointez vers le fichier `OpenGeoDataFR.zip` téléchargé et cliquez sur **Installer l'extension**.

### Méthode 2 : Clonage direct dans le dossier de plugins QGIS
Sous Windows (PowerShell) :
```powershell
cd "$env:APPDATA\QGIS\QGIS3\profiles\default\python\plugins"
git clone https://github.com/mwjouini/OpenGeoData-France.git OpenGeoDataFR
```

Sous Linux :
```bash
cd ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins
git clone https://github.com/mwjouini/OpenGeoData-France.git OpenGeoDataFR
```

Sous macOS :
```bash
cd ~/Library/Application\ Support/QGIS/QGIS3/profiles/default/python/plugins
git clone https://github.com/mwjouini/OpenGeoData-France.git OpenGeoDataFR
```

---

## 🚀 Utilisation Rapide

1. Activez l'extension via la barre d'outils ou le menu **Extensions > OpenGeoData France**.
2. Dans le panneau latéral :
   - Tapez votre recherche (mots-clés ou phrase en langage naturel).
   - Définissez éventuellement un filtre territorial (ex: nom de commune ou code INSEE).
   - Sélectionnez votre projection cible (ex: `EPSG:2154 - Lambert-93`).
3. Double-cliquez sur une donnée ou cliquez sur **Ajouter au projet** pour l'intégrer instantanément à votre carte.

---

## 🌐 Plateformes et Services Connectés

- [**GéoPlateforme IGN**](https://geoservices.ign.fr/) : Flux WMS-R, WMS-V, WFS et WMTS.
- [**data.gouv.fr**](https://www.data.gouv.fr/) : Plateforme nationale des données publiques ouvertes.
- [**Cadastre PCI Etalab / DGFiP**](https://cadastre.data.gouv.fr/) : Données cadastrales vectorielles.
- [**Géoportail de l'Urbanisme (GPU)**](https://www.geoportail-urbanisme.gouv.fr/) : PLU, PLUi, Cartes Communales, SUP.
- [**Base Adresse Nationale (BAN)**](https://adresse.data.gouv.fr/) : Référentiel national des adresses.
- [**INPN / PatriNat / OFB**](https://inpn.mnhn.fr/) : Espaces naturels, ZNIEFF, Natura 2000.
- [**BRGM / Géorisques**](https://www.georisques.gouv.fr/) : Risques naturels, PPRN, cavités, aléas mouvements de terrain.
- [**SNCF Réseau Open Data**](https://data.sncf.com/) : Infrastructures ferroviaires et gares.
- [**geo.api.gouv.fr**](https://geo.api.gouv.fr/) : Découpage administratif et géométries des communes.

---

## 👤 Auteur & Contact

- **Auteur** : Mohamed Wael JOUINI
- **Email** : [mohamed.wael.jouini@gmail.com](mailto:mohamed.wael.jouini@gmail.com)
- **Dépôt GitHub** : [https://github.com/mwjouini/OpenGeoData-France](https://github.com/mwjouini/OpenGeoData-France)
- **Signalement de bugs** : [https://github.com/mwjouini/OpenGeoData-France/issues](https://github.com/mwjouini/OpenGeoData-France/issues)

---

## 📄 Licence

Ce projet est distribué sous licence libre **GNU General Public License v2.0 or later (GPL-2.0+)**.
