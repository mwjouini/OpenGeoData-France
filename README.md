# OpenGeoData France - Extension QGIS

Moteur unifié de recherche, d'exploration et d'importation de données géographiques françaises dans QGIS.

## Fonctionnalités principales

- **Recherche globale et multicritères** : Interroge en parallèle la GéoPlateforme IGN, data.gouv.fr, le Cadastre PCI Etalab / DGFiP, le Géoportail de l'Urbanisme (GPU), la Base Adresse Nationale (BAN), le BRGM et la SNCF.
- **Catégories thématiques sobres** : Administratif, Cadastre, Urbanisme, Environnement, Risques, Énergie, Transports, Fonds IGN.
- **Découpage territorial intelligent** :
  - Découpage vectoriel géométrique automatique selon les communes ou départements sélectionnés.
  - Détourage automatique des fonds cartographiques WMS/IGN par masque de polygone inversé (`Masque - ...`).
- **Choix du mode d'import** : Dialogue interactif proposant l'importation avec découpage territorial ou l'import complet de la couche nationale.
- **Gestion des projections (CRS)** : Reprojection automatique (Lambert-93, WGS 84, Web Mercator, DOM-TOM).
- **Volet d'inspection latéral** : Métadonnées détaillées, accès aux fiches web officielles et copie de l'URL.
- **Export des résultats** : Export en CSV (Excel) ou GeoJSON.

## Documentation technique

Pour le détail de l'architecture, l'historique complet des développements et les instructions de reprise, consultez le fichier :
👉 **[PROJECT_CONTEXT.md](PROJECT_CONTEXT.md)**
