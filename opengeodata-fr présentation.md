# Extension QGIS "OpenGeoData France" – moteur de recherche de données françaises

## 1. Contexte et objectif

L’idée est de créer une extension QGIS jouant le rôle de **moteur de recherche et d’import de données open data françaises** directement depuis l’interface QGIS.

Elle doit permettre, via une simple barre de recherche, de trouver et charger :
- des couches administratives (communes, départements, régions, EPCI, IRIS, pays, etc.) ;
- des données cadastrales (parcelles, bâtiments, lieux‑dits) ;
- des données d’adresses (BAN/BANO/BAL) ;
- des documents et zonages d’urbanisme (PLU/PLUi, SCOT, cartes communales, SUP) du Géoportail de l’urbanisme ;
- des données thématiques open data (logement, biodiversité, transports, météo, etc.) via data.gouv.fr.

L’objectif principal : **remplacer la recherche manuelle sur divers sites (data.gouv.fr, GPU, BAN, GéoPlateforme, IGN, INSEE, etc.) par une recherche intégrée dans QGIS** suivie d’un import automatique.[web:83][web:93][web:79]

---

## 2. État de l’existant côté QGIS et données françaises

### 2.1. Plugins QGIS déjà disponibles

Plusieurs extensions QGIS couvrent des besoins spécifiques en France :

- **Plugin Cadastre** : permet d’utiliser le Plan Cadastral Informatisé (PCI) dans QGIS, avec import des données EDIGEO ou via des flux, et création d’une base de travail (SpatiaLite ou PostGIS). Il est utile mais centré uniquement sur le cadastre et demande des réglages (choix de la base, schéma, etc.).[web:80][web:84][web:90][web:93]

- **Plugins BAN / géocodage** :
  - GBAN, qui permet le géocodage et le reverse géocodage en France via l’API de la BAN.[web:81]
  - QBAN(O), plugin expérimental pour géocoder des fichiers Excel/CSV à partir de la Base Adresse Nationale.[web:89][web:85]
  - Ban Adresse Locator, qui fournit un locateur d’adresses basé sur BAN.[web:91]
  Ces plugins se concentrent sur le **géocodage d’adresses ou de noms de lieux**, pas sur une recherche globale de jeux de données.[web:81][web:89]

- **Plugin QGIS Géoplateforme** : un plugin récent qui permet une connexion directe entre QGIS et les services de la GéoPlateforme (dont la BAN), via des flux WMS/WFS, facilitant l’intégration de certains services nationaux.[web:79]

- **Autres plugins liés à la France** : le tag "france/french" du dépôt QGIS recense notamment le plugin Cadastre et des extensions liées à l’urbanisme (openADS, Lizmap, etc.), mais elles restent très thématiques.[web:82][web:92]

Conclusion : il existe plusieurs extensions pour **un type de données précis**, mais rien de vraiment unifié faisant office de **barre de recherche globale des données géographiques françaises** dans QGIS.

### 2.2. Plateformes open data

Les principales sources exploitables via API ou flux sont :

- **data.gouv.fr** : plateforme nationale d’open data, avec API pour lister jeux de données et ressources (par organisation, mots‑clés, thèmes, etc.).[web:83]
- **cadastre.data.gouv.fr** : fournit l’accès au PCI, avec feuilles cadastrales, parcelles, bâtiments et objets d’habillage.[web:93]
- **BAN/BANO/BAL** : Base Adresse Nationale et variantes, via API et réutilisations (plugins QBAN(O), GBAN, etc.).[web:81][web:89]
- **GéoPlateforme / Géoportail** : services WMS/WFS pour différents référentiels (fonds IGN, limites administratives, BD Topo…), avec documentation usage dans QGIS.[web:79][web:108]

L’utilisateur doit aujourd’hui savoir où chercher et comment importer chaque type de donnée. OpenGeoData France vise à **masquer cette complexité** derrière une seule interface.

---

## 3. Rôle du Géoportail de l’urbanisme (GPU)

### 3.1. GPU comme portail officiel

Le Géoportail de l’urbanisme (GPU) est le portail officiel donnant accès centralisé aux informations d’urbanisme de tout le territoire français : documents d’urbanisme (PLU, PLUi, SCOT, POS, cartes communales) et servitudes d’utilité publique (SUP).[web:100][web:103][web:109]

Il permet à tout citoyen ou professionnel :
- de localiser sa parcelle et de consulter les zonages PLU/PLUi ;
- de consulter les SUP s’appliquant à un terrain ;
- de télécharger les données géographiques et les pièces écrites pour réutilisation dans un SIG ou une étude.[web:103][web:109]

Les documents respectent les **standards CNIG** (PLU v2024, cartes communales, SUP, SCOT), assurant une homogénéité des schémas de données et des métadonnées.[web:97][web:104]

### 3.2. Services WMS/WFS GPU utilisables dans QGIS

Le GPU s’appuie sur la **GéoPlateforme** pour exposer ses données sous forme de services :

- **Flux WMS vecteur** :
  - Endpoint générique : `https://data.geopf.fr/wms-v/ows`.[web:96]
  - Fichier de capacités spécifique GPU : `https://data.geopf.fr/annexes/ressources/wms-v/gpu.xml`, listant les couches liées aux documents d’urbanisme.[web:96]

- **Flux WFS** :
  - Endpoint générique : `https://data.geopf.fr/wfs/ows`.[web:96][web:108]
  - Capacités GPU : `https://data.geopf.fr/annexes/ressources/wfs/gpu.xml`, décrivant les types de couches exportables (documents, zonages, prescriptions, SUP, etc.).[web:96]
  - Les requêtes WFS sont paginées et limitées à **5 000 objets** par requête, ce qui implique un filtrage spatial ou attributaire pour de grands territoires.[web:96][web:108]

Deux documents PDF détaillent l’**utilisation des flux WMS et WFS GPU dans QGIS** : création de connexion, ajout de couches, contraintes sur la projection (souvent WGS84 pour l’affichage WMS) et gestion des limitations WFS.[web:98][web:105]

Le GPU met également à disposition des **fichiers de symbolisation** (QML) permettant de reproduire dans QGIS le style utilisé sur le portail.[web:98]

### 3.3. API de documents d’urbanisme

Une API spécifique permet de lister et détailler les documents d’urbanisme :

- Une première requête (avec paramètre de type "grid" ou territoire) renvoie la liste des documents (PLU/PLUi, SCOT, cartes communales, SUP) présents sur un périmètre (département, commune, etc.), chaque document étant identifié par un ID.[web:102][web:100]
- Une requête de détail sur cet ID renvoie les métadonnées complètes, ainsi que les liens vers :
  - les archives CNIG (zip de données géographiques) ;
  - les pièces écrites (règlements au format PDF) ;
  - éventuellement des liens vers les services WMS/WFS correspondants.[web:102][web:97][web:104]

Un miroir opendatarchives héberge aussi les fichiers GPU (archives) de manière plus "fichier‑orientée", ce qui peut être exploité pour des imports massifs.[web:102]

---

## 4. Concept détaillé d’OpenGeoData France

### 4.1. Fonction principale : moteur de recherche intégré

OpenGeoData France offre un **dock unique dans QGIS** avec :

- une barre de recherche textuelle (par exemple "PLU Beauvais", "parcelles Oise", "communes France", "ZNIEFF Oise") ;
- des cases à cocher pour activer/désactiver des sources :
  - "Admin & Open Data (data.gouv.fr, cadastre, INSEE)" ;
  - "Urbanisme (Géoportail de l’urbanisme – GPU)" ;
  - "Adresses (BAN/BANO/BAL)" ;
  - éventuellement "Référentiels IGN/GéoPlateforme".[web:83][web:93][web:100][web:81][web:79]

Un clic sur "Chercher" déclenche des requêtes vers les différentes APIs et catalogues, et agrège les résultats dans une liste homogène.

### 4.2. Résultats affichés simplement

Les résultats sont présentés sous forme de tableau :

- **Titre** (ex. "Communes France – INSEE", "PLU de Beauvais", "Parcelles PCI – Beauvais", "Znieff – Oise") ;
- **Source** (data.gouv.fr, GPU, BAN, Cadastre, etc.) ;
- **Type** (vecteur fichier, vecteur WFS, raster WMS, table CSV, etc.) ;
- **Territoire / Périmètre** (France, département, commune) ;
- **Actions** : boutons "Afficher" (pour WMS), "Ajouter" (pour WFS/fichier), "Télécharger" (pour archives CNIG ou fichiers open data).

Un clic sur un résultat peut aussi ouvrir une petite fiche détaillée avec description, licence et liens bruts si l’utilisateur veut voir l’origine.

### 4.3. Import automatique dans QGIS

Selon le type de ressource :

- **Fichier (GeoJSON, SHP, CSV, GeoPackage)** : OpenGeoData France télécharge le fichier dans un cache local QGIS, puis crée une couche (vecteur ou table) avec le bon encodage et CRS.
- **Service WMS/WFS** : l’extension crée (ou réutilise) une connexion dans QGIS, puis ajoute la couche correspondante, en appliquant si possible :
  - la symbologie QML fournie (par ex. pour les couches GPU) ;[web:98]
  - les filtres WFS nécessaires (limite de 5 000 objets pour GPU, filtrage par commune ou emprise).[web:96][web:108]

Pour l’utilisateur, le flux devient : **"Rechercher → Ajouter → couche prête"**, sans manipulation directe des URLs ou des sources QGIS.[web:99][web:86]

---

## 5. Intégration spécifique du Géoportail de l’urbanisme

### 5.1. Cas d’usage typiques

L’intégration GPU rend possibles des scénarios fréquents en urbanisme :

- Charger rapidement le **PLU d’une commune** :
  - Recherche "PLU Beauvais" ;
  - L’API GPU retourne le document PLU/PLUi correspondant sur la commune ;[web:102][web:100]
  - OpenGeoData France propose "Afficher (WMS)" pour visualiser les documents et zonages, et "Télécharger (WFS/fichiers)" pour exploiter les données vecteur localement.

- Consulter les **SUP (servitudes d’utilité publique)** sur un territoire :
  - Recherche "SUP AC4 Jura" ;
  - L’API GPU renvoie les servitudes AC4 (sites patrimoniaux remarquables) présentes ;[web:1][web:100]
  - L’utilisateur peut afficher ou importer les polygonales SUP dans QGIS.

- Travailler sur un **SCOT ou PLUi à l’échelle EPCI** :
  - Recherche "SCOT Oise" ou "PLUi Laval Agglomération" ;
  - L’extension découvre les documents et leurs couches associés via l’API et les capacités WMS/WFS GPU ;[web:100][web:103]
  - Import direct dans QGIS pour étude ou cartographie.

### 5.2. Composants techniques côté GPU

Pour rester simple à l’usage tout en étant robuste techniquement, l’extension peut inclure :

- **GPUCatalogClient** :
  - Interroge l’API GPU pour lister les documents d’urbanisme et SUP sur un périmètre (code commune, code département, type de document, etc.).[web:102][web:100]
  - Expose des objets `UrbanDocItem` avec ID, type (PLU, PLUi, SCOT, CC, SUP), territoire, liens WMS/WFS, lien zip CNIG, lien PDF.

- **GPUWmsWfsManager** :
  - Gère les connexions WMS/WFS vers la GéoPlateforme (`https://data.geopf.fr/wms-v/ows` et `https://data.geopf.fr/wfs/ows`).[web:96][web:108]
  - Utilise les fichiers gpu.xml pour identifier les couches GPU à afficher/charger.[web:96]
  - Ajoute les couches dans QGIS en respectant le CRS recommandé (souvent WGS84 en WMS) et en appliquant les styles GPU (QML).[web:98][web:105]
  - Implémente le filtrage WFS (limite 5 000 objets), par exemple en limitant aux communes ou à l’emprise du projet.[web:96][web:108]

- **GPUFileDownloader (optionnel)** :
  - Télécharge les archives CNIG des documents (zip) via les liens fournis par l’API ou le miroir opendatarchives ;[web:102][web:97]
  - Décompresse, puis crée des couches locales (GeoPackage, etc.) pour un usage hors‑ligne ou intensif.

Ainsi, toute la logique API/WMS/WFS est cachée derrière des boutons simples pour l’utilisateur.

---

## 6. Architecture globale de l’extension

### 6.1. Structure côté QGIS

OpenGeoData France pourrait se structurer autour de :

- Un **dock principal** (`OpenGeoDataFRDock`) contenant :
  - Champ de recherche ;
  - Options de sources (France Admin, Urbanisme GPU, Adresses BAN, etc.) ;
  - Liste de résultats ;
  - Boutons "Afficher", "Ajouter", "Télécharger".

- Des **clients de catalogue** spécialisés :
  - `DataGouvClient` : interroge data.gouv.fr pour jeux de données géospatiaux (format GeoJSON, SHP, services WFS/WMS).[web:83]
  - `CadastreClient` : exploite cadastre.data.gouv.fr et/ou plugin Cadastre pour simplifier l’accès aux parcelles et lieux‑dits.[web:93][web:90]
  - `BanClient` : interroge BAN/BANO/BAL ou s’appuie sur GBAN/QBAN(O)/Ban Adresse Locator comme backend.[web:81][web:89][web:91]
  - `GPUCatalogClient` : dédié à l’urbanisme (documents d’urbanisme, SUP via GPU).[web:102][web:96][web:100]

- Un **ImportManager** :
  - Télécharge les fichiers (HTTP) vers un cache local ;
  - Crée les couches QGIS correspondantes ;
  - Gère la création ou la réutilisation de connexions WMS/WFS.[web:99][web:108]

- Une **PresetLibrary** :
  - Liste des "datasets standard" : Communes, Départements, Régions, IRIS, PCI, etc., accessibles via boutons ou menus rapides.[web:83][web:93]

### 6.2. Philosophie d’interface utilisateur

Pour garder l’extension très simple :

- Un seul dock avec des labels explicites ("Rechercher des données", "Source : France – Urbanisme", "Ajouter dans QGIS").
- Paramètres techniques (URLs, proxies, CRS, limites WFS) gérés en coulisses.[web:96][web:98][web:105][web:108]
- Section "Données standard France" avec des raccourcis pour :
  - Communes France ;
  - Départements/Régions ;
  - PCI (par département ou commune) ;
  - Carte des documents d’urbanisme GPU (couche "document").[web:93][web:96][web:100]

---

## 7. Valeur ajoutée d’OpenGeoData France

OpenGeoData France apporte plusieurs bénéfices :

- **Unification** : elle réunit en une seule interface l’accès à des sources dispersées (data.gouv.fr, cadastre, BAN, GéoPlateforme, GPU), alors qu’aujourd’hui il faut connaître chaque portail et plugin séparément.[web:79][web:81][web:90][web:89][web:83][web:96]
- **Gain de temps** : elle évite les allers‑retours vers le navigateur, le copier/coller d’URLs, la création manuelle de connexions WMS/WFS, et les téléchargements manuels de fichiers.[web:86][web:99][web:108]
- **France‑centrée et extensible** : elle est conçue pour tirer parti du fort écosystème d’open data français, mais peut évoluer vers d’autres catalogues européens (INSPIRE, Eurostat, etc.).[web:83][web:97][web:104]
- **Adaptée aux usages territoriaux** : pour un analyste SIG en collectivité (urbanisme, aménagement, biodiversité, logement), elle peut devenir l’outil quotidien pour monter rapidement des projets QGIS avec les bonnes couches de référence.

Ce rapport peut servir de base à un cahier des charges ou à un premier MVP, en commençant par quelques sources clés (data.gouv.fr pour communes/départements/régions, cadastre PCI, GPU pour PLU/PLUi/SUP) et une interface minimaliste centrée sur la recherche et l’ajout de couches.
