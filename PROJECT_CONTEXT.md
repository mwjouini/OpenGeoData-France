# OpenGeoData France - Documentation & Historique du Projet

Ce document récapitule l'architecture, l'historique complet des développements, les configurations MCP et les procédures à suivre pour reprendre le travail lors d'une nouvelle session.

---

## 1. Vue d'ensemble du projet

**OpenGeoData France** est une extension QGIS (Python / PyQt) permettant de rechercher, explorer, filtrer et importer facilement l'ensemble des données géographiques ouvertes françaises :
- **GéoPlateforme IGN** : Flux WMS-Raster (Ortho HR, Plan IGN V2, Cadastre WMS Parcellaire Express, SCAN 25, MNT/Relief ombré, Courbes de niveau), Flux WFS (Admin Express, IRIS, BD TOPO bâti/routes/hydro/végétation).
- **data.gouv.fr / INSEE** : Jeux de données nationaux (SIRENE géocodé, COG, IRVE bornes de recharge, Registre EnR, Aménagements cyclables BNLC, Risques PPRN, TRI, Argiles RGA).
- **Cadastre PCI Etalab / DGFiP** : Parcelles cadastrales, bâtiments, sections (GeoJSON vectoriel communal ou flux WMS).
- **GPU (Géoportail de l'Urbanisme)** : Documents d'urbanisme (PLU, PLUi, SCOT, POS, CC), zonages CNIG (`zone_urba`), servitudes (`sup_assiette`).
- **BAN (Base Adresse Nationale)** : Adresses et lieux-dits géocodés.
- **BRGM (Géoservices)** : Carte géologique de la France au 1/50 000 (WMS).
- **SNCF Réseau** : Tracé géométrique du Réseau Ferré National.

---

## 2. Emplacements des fichiers et synchronisation QGIS

- **Dépôt source de développement** : `e:\OpenGeoData France\OpenGeoDataFR`
- **Répertoire d'installation actif dans QGIS** :
  `C:\Users\mjouini\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\OpenGeoDataFR`
- **Archive de déploiement** : `e:\OpenGeoData France\OpenGeoDataFR.zip`
- **Interpréteur Python QGIS (PyQGIS 3.40.5)** :
  `C:\Program Files\QGIS 3.40.5\bin\python-qgis-ltr.bat`

> **Règle essentielle** : Toute modification apportée dans `e:\OpenGeoData France\OpenGeoDataFR` doit être synchronisée dans le dossier du profil QGIS pour être prise en compte dans l'application.

---

## 3. Historique détaillé des développements réalisés

### A. Intégration du serveur MCP data.gouv.fr
- **Configuration** : Enregistrement de l'endpoint SSE `https://mcp.data.gouv.fr/mcp` dans `~/.gemini/config/mcp_config.json` et `.agents/mcp_config.json`.
- **Schémas d'outils** : 10 outils MCP lazy-loaded créés dans `C:\Users\mjouini\.gemini\antigravity-ide\mcp\datagouv\`.
- **Skill dédiée** : Création de la skill `C:\Users\mjouini\.gemini\config\skills\data-gouv-fr\SKILL.md`.

### B. Évolution de l'interface & Ergonomie native (v1.1.0)
- **Barre de catégories sobres** : Tous les jeux, Administratif, Cadastre, Urbanisme, Environnement, Risques, Énergie, Transports, Fonds IGN.
- **Volet d'inspection latéral (Splitter)** : Affiche en temps réel la source, le territoire, la projection, la date, la taille, la licence et la description, avec boutons "Ajouter au projet", "Fiche Web" et "Copier l'URL".
- **Design sobre QGIS natif** : Suppression de tous les emojis et couleurs artificielles ; utilisation du style sobre Qt/QGIS.
- **Autocomplétion intelligente** : Plus de 60 suggestions géographiques et thématiques instantanées.

### C. Corrections techniques et résolutions de bugs
1. **Compatibilité Qt (PyQt5 / PyQt6)** :
   - Ajout des énumérations `Horizontal`, `Vertical` et `AlignCenter` dans `OpenGeoDataFR/ui/qt_compat.py`.
2. **Correction des flux WMS GéoPlateforme IGN** :
   - Routage automatique vers `https://data.geopf.fr/wms-r/ows` pour les rasters IGN (Plan Cadastral WMS, Ortho HR, Plan IGN V2, SCAN 25, MNT).
   - Routage vers `https://data.geopf.fr/wms-v/ows` pour les couches vectorielles GPU.
   - Prise en charge des tuiles XYZ (`tile.openstreetmap.org`).
3. **Résolution dynamique des erreurs 404 (data.gouv.fr)** :
   - Mise à jour des millésimes actifs pour les aménagements cyclables BNLC et les lignes SNCF.
   - Intégration de `_resolve_fallback_url` interrogeant automatiquement l'API data.gouv.fr en cas de changement de permalien.

### D. Système complet de découpage spatial et de filtrage
1. **Dialogue de confirmation préalable (`ImportFilterOptionDialog`)** :
   - Demande systématique avant l'importation :
     - *Importer avec découpage territorial* (utilise le filtre ou ouvre le sélecteur en cascade).
     - *Importer la couche entière (sans filtre)*.
     - *Annuler*.
2. **Extraction des contours réels multi-communes** :
   - Utilisation de `geometry=contour` sur l'API GeoAPI (`geo.api.gouv.fr`).
   - Parsing robuste via `QgsJsonUtils.geometryFromGeoJson(json_str)`.
   - Fusion géométrique `QgsGeometry.unaryUnion` pour les listes de codes multiples (ex : communes de l'Oise).
3. **Découpage vectoriel haute performance** :
   - Utilisation de `QgsFeatureRequest().setFilterRect(terr_geom.boundingBox())` pour filtrer instantanément les entités via l'index spatial R-Tree.
   - Découpe géométrique par `geom.intersection(terr_geom)` créant une couche mémoire propre `[Nom] (Découpé)`.
4. **Matérialisation du Périmètre des Fonds IGN / WMS & Centrage Sécurisé** :
   - Résolution du problème d'écran bleu : exécution du centrage de la caméra exclusivement sur le thread principal (GUI) dans `on_import_finished`.
   - Reprojection dynamique de l'emprise du territoire dans le CRS actif du projet (`EPSG:3857`, `EPSG:2154`) avec marge de 5%.
   - Génération d'une couche vectorielle de délimitation `Périmètre - [Nom]` (remplissage 100% transparent, contour rouge fin 0.8 mm) qui met en valeur le territoire sélectionné sans masquer aucune donnée.
5. **Résolution du point d'accès GeoAPI pour les communes de région** :
   - Correction de l'URL dans `TerritoryFilterDialog` : `/communes?codeRegion={code}&fields=nom,code`.
6. **Mise à jour des Presets vers les API actives** :
   - `preset_pprn_georisques` mis à jour vers l'API officielle nationale GASPAR (`https://georisques.gouv.fr/api/v1/gaspar/pprn`).

### E. Moteur de Recherche Sémantique NLP Local (100% Gratuit & Autonome)
1. **Module `NLPSearchEngine` (`services/nlp_search_engine.py`)** :
   - Moteur d'analyse du langage naturel en pur Python, sans aucun modèle payant ni clé API externe.
   - **Reconnaissance d'entités territoriales (NER)** : Détecte les codes postaux, numéros et noms des 101 départements, 18 régions et résout les 35 000 communes françaises via GeoAPI en temps réel.
   - **Classification d'intentions multi-thématiques** : Détecte les thèmes demandés (*Cadastre, Bâtiments, PLU, Mobilités, Risques, Environnement, Énergie, Fonds IGN*) et résout les requêtes multi-couches (ex : *"parcelles et plu à Beauvais"*).
   - **Intégration transparente dans l'interface** : Pré-remplit automatiquement le filtre territorial et classe les couches recommandées au sommet des résultats.
2. **Nouveau Preset Officiel "BD TOPO Bâtiments & Hauteurs 3D (IGN)"** :
   - Accès direct aux 50 millions de bâtiments de l'IGN avec hauteur réelle au faîtage, nombre d'étages, typologie d'usage et identifiant unique `cleabs`.

### F. Prévisualisation en Temps Réel & Sécurisation Anti-Table Vide
1. **Prévisualisation en Temps Réel (3 Onglets dans l'Inspecteur)** :
   - **Onglet 1 `Fiche & Métadonnées`** : Métadonnées exhaustives (Source, Territoire, CRS, Taille, Date, Licence) avec boutons d'action.
   - **Onglet 2 `Aperçu Carte` (Mini-SIG interactif)** : Intègre un `QgsMapCanvas` avec outils de navigation (Pan, Zoom+, Zoom-, Vue globale) permettant de visualiser instantanément les couches WMS, XYZ et vecteurs avant import.
   - **Onglet 3 `Aperçu Données` (Tableau)** : `QTableWidget` affichant en temps réel les 25 premières lignes et les colonnes des fichiers tabulaires (CSV, TSV, GeoJSON) avec détection automatique du séparateur.
2. **Sécurisation Anti-Table Vide (Gestion des Projections et Filtres)** :
   - **Réinitialisation automatique si 0 résultat par attribut** : Si `setSubsetString` ne renvoie aucune entité (nom de champ ou code différent), la clause est réinitialisée à blanc et bascule automatiquement vers le découpage spatial géométrique.
   - **Découpage spatial géométrique robuste** : Reprojection systématique du polygone de découpage (`terr_geom`) dans le CRS de la couche (`EPSG:2154`, `EPSG:4326`, `EPSG:3857`), évitant tout échec d'intersection d'échelles.
   - **Préservation des données** : Si aucune entité n'est contenue dans le périmètre territorial exact, la couche complète d'origine est conservée au lieu de générer une table vide.

---

## 4. Structure de l'arborescence du code

```
OpenGeoData France/
├── OpenGeoDataFR/
│   ├── __init__.py                # Point d'entrée du plugin QGIS
│   ├── opengeodata_fr.py          # Classe principale du plugin (actions menus, dock)
│   ├── metadata.txt               # Métadonnées QGIS (version 1.1.0, auteur, description)
│   ├── icon.png                   # Icône officielle du plugin
│   ├── models.py                  # Modèles de données (DataItem, UrbanDocItem)
│   ├── clients/
│   │   ├── __init__.py
│   │   ├── data_gouv_client.py    # Client API data.gouv.fr (formats, dataservices, tabular API)
│   │   ├── cadastre_client.py     # Client Cadastre PCI Etalab & WMS DGFiP
│   │   ├── gpu_client.py          # Client Géoportail de l'Urbanisme (WMS/WFS/Fichiers)
│   │   ├── ban_client.py          # Client Base Adresse Nationale (BAN)
│   │   └── geoplateforme_client.py# Client GéoPlateforme IGN (Admin, BD TOPO, WMS-R, WFS)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── import_manager.py      # Import, réprojection, découpage spatial, masque WMS, symbologie
│   │   ├── preset_library.py      # 27 pré-réglages nationaux dans 8 catégories
│   │   └── export_service.py      # Exportation des résultats (CSV, GeoJSON)
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── qt_compat.py           # Couche universelle de compatibilité Qt5/Qt6
│   │   ├── opengeodata_fr_dock.py # Fenêtre principale (recherche, table, inspecteur, workers)
│   │   ├── import_option_dialog.py# Dialogue préalable : découpage territorial vs couche entière
│   │   ├── territory_filter_dialog.py # Sélecteur en cascade (Région -> Dépt -> EPCI -> Communes)
│   │   └── csv_import_dialog.py   # Assistant de configuration pour fichiers tabulaires CSV
│   └── utils/
│       ├── __init__.py
│       └── ssl_helper.py          # Gestion des contextes SSL et requêtes HTTP sécurisées
├── PROJECT_CONTEXT.md             # Ce document de contexte global
└── OpenGeoDataFR.zip              # Archive d'installation prête pour QGIS
```

---

## 5. Commandes utiles pour la suite

### 1. Synchroniser les modifications vers le profil QGIS actif
Exécuter le script Python suivant :
```python
import os, shutil, zipfile

src_dir = r"e:\OpenGeoData France\OpenGeoDataFR"
dst_dir = r"C:\Users\mjouini\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\OpenGeoDataFR"
zip_path = r"e:\OpenGeoData France\OpenGeoDataFR.zip"

os.makedirs(dst_dir, exist_ok=True)
exclude_ext = ('.pyc', '.git', '.cache')
exclude_dirs = ('__pycache__', '.git', '.idea', '.vscode')

for root, dirs, files in os.walk(src_dir):
    dirs[:] = [d for d in dirs if d not in exclude_dirs]
    rel_root = os.path.relpath(root, src_dir)
    target_root = os.path.join(dst_dir, rel_root) if rel_root != '.' else dst_dir
    os.makedirs(target_root, exist_ok=True)
    for f in files:
        if not any(f.endswith(ext) for ext in exclude_ext):
            shutil.copy2(os.path.join(root, f), os.path.join(target_root, f))

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(src_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for f in files:
            if not any(f.endswith(ext) for ext in exclude_ext):
                zf.write(os.path.join(root, f), os.path.relpath(os.path.join(root, f), os.path.dirname(src_dir)))

print("Synchronisation et Zip terminés !")
```

### 2. Tester avec l'environnement PyQGIS réel
Exécuter un script via PowerShell :
```powershell
& "C:\Program Files\QGIS 3.40.5\bin\python-qgis-ltr.bat" "chemin\vers\script_test.py"
```

---

## 6. Guide pour les futures sessions

Lors du démarrage d'une nouvelle conversation, le prochain agent doit :
1. Consulter ce fichier `PROJECT_CONTEXT.md` pour comprendre l'état actuel et l'architecture.
2. Toujours effectuer les tests de géométrie et de découpage avec `python-qgis-ltr.bat`.
3. Conserver le design sobre et professionnel natif de QGIS (aucun emoji, pas de styles saturés).
4. Synchroniser systématiquement les fichiers modifiés vers `C:\Users\mjouini\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\OpenGeoDataFR`.
