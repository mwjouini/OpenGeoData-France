# Sources de référence pour l’extension "OpenGeoData France"

Ce document rassemble les **sources techniques officielles** à consulter avant ou pendant le développement de l’extension OpenGeoData France. Il ne contient pas de tutoriels, uniquement des documents de référence et pages de documentation.

---

## 1. QGIS – développement de plugins

### 1.1. Documentation officielle PyQGIS (plugins)

- **Structuring Python Plugins** (PyQGIS Developer Cookbook)
  - URL : https://docs.qgis.org/latest/en/docs/pyqgis_developer_cookbook/plugins/plugins.html
  - Contient : structure d’un plugin, rôle de `metadata.txt`, cycle de vie du plugin.[web:26]

### 1.2. Releasing your plugin / contraintes de nommage

- **Releasing your plugin**
  - URL : https://docs.qgis.org/latest/en/docs/pyqgis_developer_cookbook/plugins/releasing.html
  - Contient : contraintes sur le nom de dossier (ASCII, chiffres, `_` et `-`), bonnes pratiques de publication.[web:111]

### 1.3. Guides sur les plugins et metadata

- Exemple de description du fichier `metadata.txt` et catégories de plugin
  - URL : https://www.giswiki.ch/QGIS_Plugins_mit_Python
  - Contient : description détaillée du rôle de `metadata.txt`, champs obligatoires et optionnels.[web:137]

---

## 2. data.gouv.fr – API catalogue et datasets

### 2.1. Documentation de référence de l’API data.gouv.fr

- **Référence API data.gouv.fr**
  - URL : https://doc.data.gouv.fr/api/reference/
  - Contient : description globale de l’API, endpoints principaux, authentification, format des réponses.[web:133]

- **Référence API – section datasets**
  - URL : https://guides.data.gouv.fr/api-de-data.gouv.fr/reference/datasets
  - Contient : endpoints pour lister/rechercher des jeux de données (`/datasets`), paramètres de recherche, champs JSON.[web:135]

- **Référence API – page principale**
  - URL : https://guides.data.gouv.fr/api-de-data.gouv.fr/reference
  - Contient : index des différentes sections de l’API (datasets, resources, organizations, etc.).[web:138]

### 2.2. API catalogue des données ouvertes

- **API catalogue des données ouvertes data.gouv.fr**
  - URL : https://www.data.gouv.fr/dataservices/api-catalogue-des-donnees-ouvertes-data-gouv-fr
  - Contient : description fonctionnelle de l’API catalogue (recherche de datasets, métadonnées, filtres).[web:140]

### 2.3. Base Adresse Nationale (BAN) – données et API

- **Dataset "Base Adresse Nationale"**
  - URL : https://www.data.gouv.fr/datasets/base-adresse-nationale
  - Contient : description des fichiers BAN, formats disponibles, flux et API liés.[web:139]

---

## 3. API Adresse / BAN – IGN

- **API Adresse (Base Adresse Nationale)**
  - URL : https://www.data.gouv.fr/dataservices/api-adresse-base-adresse-nationale-ban
  - Contient : description des fonctionnalités (autocomplétion, vérification, géolocalisation d’adresse, recherche textuelle).[web:134]

- **Prendre en main l’API "Adresse" portée par l’IGN**
  - URL : https://guide.datasud.fr/reutiliser-des-donnees/prendre-en-main-lapi-adresse-portee-par-lign
  - Contient : guide technique sur les paramètres, formats de réponse et bonnes pratiques d’utilisation de l’API Adresse.[web:136]

- **Organisation GitHub Base Adresse Nationale**
  - URL : https://github.com/BaseAdresseNationale
  - Contient : code source et outils autour de la BAL/BAN.[web:141]

---

## 4. Géoportail de l’urbanisme (GPU) – services et API

### 4.1. Page "services" du GPU

- **Services WMS/WFS GPU**
  - URL : https://www.geoportail-urbanisme.gouv.fr/services/
  - Contient :
    - URLs des endpoints WMS vecteur (`https://data.geopf.fr/wms-v/ows`) et WFS (`https://data.geopf.fr/wfs/ows`) ;
    - liens vers les fichiers de capacités spécifiques GPU (`gpu.xml`) ;
    - mentions des limitations WFS (pagination, 5 000 objets par requête) ;
    - liens vers la documentation d’utilisation dans QGIS.[web:96]

### 4.2. Documentation utilisation WFS/WMS GPU dans QGIS

- **"Utilisation des flux WFS du GPU dans Qgis" (PDF)**
  - URL directe : https://www.geoportail-urbanisme.gouv.fr/image/UtilisationWFS_GPU_Qgis_1-0.pdf
  - Contient :
    - explication des restrictions de téléchargement WFS (pagination, limites d’objets) ;
    - configuration des connexions WFS dans QGIS (proxy, CRS, propriétés du flux) ;
    - exemples de requêtes et conseils pratiques.[web:98]

- **"Utilisation des flux WMS du GPU dans Qgis" (PDF)**
  - URL directe : https://www.geoportail-urbanisme.gouv.fr/image/UtilisationWMS_GPU_Qgis_1-0.pdf
  - Contient :
    - procédures pour créer des connexions WMS vers la GéoPlateforme ;
    - conseils sur l’utilisation de la couche "document" pour visualiser l’emprise et le type des documents d’urbanisme ;
    - remarques sur la projection WMS (souvent WGS84) et le paramétrage général.[web:105]

### 4.3. API GPU

- **Page API GPU**
  - URL : https://www.geoportail-urbanisme.gouv.fr/api/
  - Contient :
    - description de l’API GPU, avertissement sur son usage principalement interne ;
    - lien vers l’API Carto ;
    - liens vers la documentation Swagger (`swagger.yaml`).[web:142]

- **Discussion GeoRezo sur l’utilisation des flux WMS/WFS GPU**
  - URL : https://georezo.net/forum/viewtopic.php?id=128644
  - Contient : exemples concrets d’appels API (`/api/document?grid=...`, `/api/document/<id>/details`), structure JSON retournée, liens vers fichiers et services.[web:102]

---

## 5. GéoPlateforme / Géoportail – flux WMS/WMTS/WFS

- **Guide "QGIS - Utiliser les données libres en flux WMS/WMTS"**
  - URL : https://cartes.gouv.fr/aide/fr/guides-utilisateur/utiliser-les-services-de-la-geoplateforme/tutoriels-api/qgis/
  - Contient :
    - mode d’emploi pour consommer les flux WMS/WMTS/WFS de la GéoPlateforme dans QGIS ;
    - rappel des limitations WFS (nombre d’objets par requête) ;
    - configuration dans QGIS (ajout de couches, paramètres réseau).[web:108]

---

## 6. Références complémentaires utiles

Même si tu ne veux pas de tutoriels, ces pages peuvent servir de référence lorsque tu souhaites vérifier des comportements ou des exemples :

- **GeoRezo – flux WMS/WFS GPU et QGIS 3.22**
  - URL : https://georezo.net/forum/viewtopic.php?id=128644
  - Contient : échanges techniques sur les flux GPU dans QGIS, exemples de paramètres et problèmes fréquents.[web:102]

- **Ministère de la Transition Écologique – extensions QGIS**
  - URL : http://piece-jointe-carto.developpement-durable.gouv.fr/NAT002/QGIS/formations/FOAD_PEM_QGIS34/pdf/M10_ExtensionsPlugins_papier.pdf
  - Contient : description générale des extensions QGIS et mode d’ajout via le gestionnaire, utile pour valider la structure de ton plugin.[web:45]

Ce fichier `.md` peut servir de "liste de lecture" technique avant et pendant le développement d’OpenGeoData France.