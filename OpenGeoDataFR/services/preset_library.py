# -*- coding: utf-8 -*-
"""
Bibliothèque de pré-réglages (Presets) standards pour la France.
Permet d'accéder en 1 clic aux grands jeux de données de référence nationaux
(IGN, INSEE, Cadastre, GPU, CEREMA, OFB, INPN, BRGM, ADEME, RTE, SNCF).
"""

from ..models import DataItem, UrbanDocItem


class PresetLibrary:
    """Fournit les jeux de données géographiques prédéfinis pour la France."""

    @staticmethod
    def get_presets():
        presets = [
            # =========================================================================
            # 1. ADMINISTRATIF & DÉMOGRAPHIE (IGN, INSEE, GeoAPI)
            # =========================================================================
            DataItem(
                item_id="preset_communes_france",
                title="Communes de France (Admin Express IGN)",
                source="GéoPlateforme IGN",
                data_type="wfs",
                territory="France",
                scale="france",
                crs="EPSG:4326",
                date="2025 (IGN)",
                url="https://data.geopf.fr/wfs/ows",
                service_type="WFS",
                extra={
                    'layer_name': 'ADMINEXPRESS-COG-CARTO.LATEST:commune',
                    'wfs_url': 'https://data.geopf.fr/wfs/ows',
                    'category': 'admin',
                    'format': 'Flux WFS',
                    'description': 'Limites géographiques des communes métropolitaines et DROM (Admin Express)'
                }
            ),
            DataItem(
                item_id="preset_departements_france",
                title="Départements de France (Admin Express IGN)",
                source="GéoPlateforme IGN",
                data_type="wfs",
                territory="France",
                scale="france",
                crs="EPSG:4326",
                date="2025 (IGN)",
                url="https://data.geopf.fr/wfs/ows",
                service_type="WFS",
                extra={
                    'layer_name': 'ADMINEXPRESS-COG-CARTO.LATEST:departement',
                    'wfs_url': 'https://data.geopf.fr/wfs/ows',
                    'category': 'admin',
                    'format': 'Flux WFS',
                    'description': 'Limites des départements français et collectivités d\'outre-mer'
                }
            ),
            DataItem(
                item_id="preset_regions_france",
                title="Régions de France (Admin Express IGN)",
                source="GéoPlateforme IGN",
                data_type="wfs",
                territory="France",
                scale="france",
                crs="EPSG:4326",
                date="2025 (IGN)",
                url="https://data.geopf.fr/wfs/ows",
                service_type="WFS",
                extra={
                    'layer_name': 'ADMINEXPRESS-COG-CARTO.LATEST:region',
                    'wfs_url': 'https://data.geopf.fr/wfs/ows',
                    'category': 'admin',
                    'format': 'Flux WFS',
                    'description': 'Contours officiels des 18 régions françaises'
                }
            ),
            DataItem(
                item_id="preset_epci_france",
                title="Intercommunalités EPCI (Admin Express IGN)",
                source="GéoPlateforme IGN",
                data_type="wfs",
                territory="France",
                scale="epci",
                crs="EPSG:4326",
                date="2025 (IGN)",
                url="https://data.geopf.fr/wfs/ows",
                service_type="WFS",
                extra={
                    'layer_name': 'ADMINEXPRESS-COG-CARTO.LATEST:epci',
                    'wfs_url': 'https://data.geopf.fr/wfs/ows',
                    'category': 'admin',
                    'format': 'Flux WFS',
                    'description': 'Établissements Publics de Coopération Intercommunale à fiscalité propre (Métropoles, CA, CC)'
                }
            ),
            DataItem(
                item_id="preset_iris_france",
                title="Contours des IRIS (INSEE / IGN GéoPlateforme)",
                source="GéoPlateforme IGN / INSEE",
                data_type="wfs",
                territory="France",
                scale="france",
                crs="EPSG:4326",
                date="2025 (IGN)",
                url="https://data.geopf.fr/wfs/ows",
                service_type="WFS",
                extra={
                    'layer_name': 'STATISTICALUNITS.IRIS.PE:contours_iris_pe',
                    'wfs_url': 'https://data.geopf.fr/wfs/ows',
                    'category': 'admin',
                    'format': 'Flux WFS',
                    'description': 'Découpage infra-communal statistique IRIS officiel de l\'INSEE'
                }
            ),
            DataItem(
                item_id="preset_insee_cog",
                title="Code Officiel Géographique COG - Communes (INSEE)",
                source="GeoAPI / INSEE",
                data_type="table",
                territory="France",
                scale="france",
                crs="EPSG:4326",
                date="2025 (INSEE)",
                url="https://geo.api.gouv.fr/communes?fields=nom,code,codeDepartement,codeRegion,population",
                service_type="HTTP",
                extra={
                    'format': 'JSON API',
                    'category': 'admin',
                    'description': 'Référentiel cartographique officiel des communes et collectivités territoriales'
                }
            ),
            DataItem(
                item_id="preset_insee_sirene",
                title="Base SIRENE Géocodée des Entreprises & Établissements (INSEE)",
                source="data.gouv.fr (INSEE)",
                data_type="table",
                territory="France",
                scale="france",
                crs="EPSG:4326",
                date="2026 (INSEE)",
                url="https://static.data.gouv.fr/resources/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/20260801-073219/stock-stocketablissement-csv.zip",
                service_type="HTTP",
                extra={
                    'format': 'CSV.ZIP',
                    'category': 'admin',
                    'description': 'Répertoire national officiel des entreprises et établissements actifs en France'
                }
            ),

            # =========================================================================
            # 2. FONCIER & CADASTRE (PCI Etalab / DGFiP / IGN)
            # =========================================================================
            DataItem(
                item_id="preset_pci_wms_ign",
                title="Plan Cadastral WMS - Parcellaire Express (DGFiP / IGN)",
                source="GéoPlateforme IGN",
                data_type="wms",
                territory="France",
                scale="france",
                crs="EPSG:3857",
                date="Temps Réel (2025)",
                url="https://data.geopf.fr/wms-r/ows",
                service_type="WMS",
                extra={
                    'layer_name': 'CADASTRALPARCELS.PARCELLAIRE_EXPRESS',
                    'wms_url': 'https://data.geopf.fr/wms-r/ows',
                    'category': 'cadastre',
                    'format': 'Flux WMS',
                    'description': 'Plan cadastral unifié national DGFiP / IGN en flux cartographique haute résolution'
                }
            ),
            DataItem(
                item_id="preset_pci_beauvais",
                title="Parcelles Cadastrales PCI Etalab - Beauvais (60057)",
                source="Cadastre PCI Etalab",
                data_type="file_vector",
                territory="Beauvais (60057)",
                scale="commune",
                crs="EPSG:4326",
                date="2025",
                url="https://cadastre.data.gouv.fr/data/etalab-cadastre/latest/geojson/communes/60/60057/cadastre-60057-parcelles.json.gz",
                service_type="HTTP",
                extra={
                    'code_insee': '60057',
                    'format': 'GEOJSON.GZ',
                    'category': 'cadastre',
                    'description': 'Parcelles cadastrales vectorielles complètes de la commune de Beauvais'
                }
            ),

            # =========================================================================
            # 3. URBANISME & FONCIER (GPU - Géoportail de l'Urbanisme)
            # =========================================================================
            UrbanDocItem(
                item_id="preset_gpu_carte_nationale",
                title="Carte nationale des documents d'urbanisme (GPU)",
                doc_type="Carte globale",
                territory="France",
                scale="france",
                crs="EPSG:3857 (WMS) / EPSG:4326 (WFS)",
                date="2025 (GPU)",
                url="https://data.geopf.fr/wms-v/ows",
                service_type="WMS",
                wms_layers=["document"],
                wfs_layers=["wfs_du:doc_urba"],
                files=[],
                extra={
                    'wms_url': 'https://data.geopf.fr/wms-v/ows',
                    'wfs_url': 'https://data.geopf.fr/wfs/ows',
                    'category': 'urbanisme',
                    'format': 'WMS/WFS',
                    'description': 'Emprises et état d\'avancement des documents PLU, PLUi, SCOT, POS et CC en France'
                }
            ),
            DataItem(
                item_id="preset_gpu_zones_urba",
                title="Zones d'Urbanisme PLU/PLUi (GPU WFS)",
                source="Géoportail de l'urbanisme (GPU)",
                data_type="wfs",
                territory="France",
                scale="commune",
                crs="EPSG:4326",
                date="2025 (GPU)",
                url="https://data.geopf.fr/wfs/ows",
                service_type="WFS",
                extra={
                    'layer_name': 'wfs_du:zone_urba',
                    'wfs_url': 'https://data.geopf.fr/wfs/ows',
                    'category': 'urbanisme',
                    'format': 'Flux WFS',
                    'description': 'Zonages réglementaires (U, AU, A, N) issus des PLU et PLUi numérisés au standard CNIG'
                }
            ),
            DataItem(
                item_id="preset_gpu_sup",
                title="Servitudes d'Utilité Publique SUP (GPU WFS)",
                source="Géoportail de l'urbanisme (GPU)",
                data_type="wfs",
                territory="France",
                scale="commune",
                crs="EPSG:4326",
                date="2025 (GPU)",
                url="https://data.geopf.fr/wfs/ows",
                service_type="WFS",
                extra={
                    'layer_name': 'wfs_sup:sup_assiette',
                    'wfs_url': 'https://data.geopf.fr/wfs/ows',
                    'category': 'urbanisme',
                    'format': 'Flux WFS',
                    'description': 'Assiettes et générateurs des servitudes d\'utilité publique (patrimoine, risques, canalisations)'
                }
            ),

            # =========================================================================
            # 4. ENVIRONNEMENT & BIODIVERSITÉ (INPN / OFB / IGN)
            # =========================================================================
            DataItem(
                item_id="preset_znieff1",
                title="ZNIEFF Type 1 - Espaces de grand intérêt écologique (INPN / OFB)",
                source="data.gouv.fr (INPN / MNHN / OFB)",
                data_type="file_vector",
                territory="France",
                scale="france",
                crs="EPSG:4326",
                date="2025",
                url="https://inpn.mnhn.fr/docs/shape/ZNIEFF1_FR.zip",
                service_type="HTTP",
                extra={
                    'format': 'SHAPEFILE (ZIP)',
                    'category': 'environnement',
                    'description': 'Zones Naturelles d\'Intérêt Écologique, Faunistique et Floristique de type 1'
                }
            ),
            DataItem(
                item_id="preset_znieff2",
                title="ZNIEFF Type 2 - Grands ensembles naturels (INPN / OFB)",
                source="data.gouv.fr (INPN / MNHN / OFB)",
                data_type="file_vector",
                territory="France",
                scale="france",
                crs="EPSG:4326",
                date="2025",
                url="https://inpn.mnhn.fr/docs/shape/ZNIEFF2_FR.zip",
                service_type="HTTP",
                extra={
                    'format': 'SHAPEFILE (ZIP)',
                    'category': 'environnement',
                    'description': 'Grands ensembles naturels paysagers et écologiques riches de type 2'
                }
            ),
            DataItem(
                item_id="preset_natura2000",
                title="Réseau Natura 2000 - SIC/ZSC & ZPS (INPN / OFB)",
                source="data.gouv.fr (INPN / OFB)",
                data_type="file_vector",
                territory="France",
                scale="france",
                crs="EPSG:4326",
                date="2025",
                url="https://inpn.mnhn.fr/docs/shape/NATURA2000_FR.zip",
                service_type="HTTP",
                extra={
                    'format': 'SHAPEFILE (ZIP)',
                    'category': 'environnement',
                    'description': 'Sites d\'Intérêt Communautaire (SIC/ZSC) et Zones de Protection Spéciale (ZPS)'
                }
            ),
            DataItem(
                item_id="preset_cours_d_eau",
                title="Réseau Hydrographique & Cours d'eau BD TOPAGE (IGN / OFB)",
                source="GéoPlateforme IGN / OFB",
                data_type="wfs",
                territory="France",
                scale="commune",
                crs="EPSG:4326",
                date="2025 (IGN)",
                url="https://data.geopf.fr/wfs/ows",
                service_type="WFS",
                extra={
                    'layer_name': 'BDTOPO_V3:cours_d_eau',
                    'wfs_url': 'https://data.geopf.fr/wfs/ows',
                    'category': 'environnement',
                    'format': 'Flux WFS',
                    'description': 'Tronçons hydrographiques et cours d\'eau de la BD TOPAGE'
                }
            ),

            # =========================================================================
            # 5. RISQUES & GÉOLOGIE (Géorisques / BRGM)
            # =========================================================================
            DataItem(
                item_id="preset_pprn_georisques",
                title="Plans de Prévention des Risques Naturels PPRN (Géorisques / GASPAR)",
                source="data.gouv.fr (Géorisques / BRGM)",
                data_type="table",
                territory="France",
                scale="commune",
                crs="EPSG:4326",
                date="2025 (Temps Réel)",
                url="https://georisques.gouv.fr/api/v1/gaspar/pprn",
                service_type="HTTP",
                extra={
                    'format': 'JSON API',
                    'category': 'risques',
                    'description': 'Base nationale GASPAR des Plans de Prévention des Risques Naturels (inondation, argiles, séisme)'
                }
            ),
            DataItem(
                item_id="preset_carte_geologique_brgm",
                title="Carte Géologique de la France au 1/50 000 (BRGM WMS)",
                source="BRGM (Géoservices)",
                data_type="wms",
                territory="France",
                scale="france",
                crs="EPSG:3857",
                date="2025 (BRGM)",
                url="https://geoservices.brgm.fr/geologie",
                service_type="WMS",
                extra={
                    'layer_name': 'GEOLOGIE',
                    'wms_url': 'https://geoservices.brgm.fr/geologie',
                    'category': 'risques',
                    'format': 'Flux WMS',
                    'description': 'Carte géologique vectorielle et harmonisée de la France métropolitaine au 1/50 000'
                }
            ),
            DataItem(
                item_id="preset_argiles_rga",
                title="Aléa Retrait-Gonflement des Argiles RGA (DGALN / BRGM)",
                source="data.gouv.fr (DGALN / BRGM)",
                data_type="table",
                territory="France",
                scale="departement",
                crs="EPSG:4326",
                date="2025",
                url="https://data.statistiques.developpement-durable.gouv.fr/dido/api/v1/datafiles/1d6ff531-fe68-4102-9591-8da9ffdf8300/csv",
                service_type="HTTP",
                extra={
                    'format': 'CSV',
                    'category': 'risques',
                    'description': 'Niveau d\'exposition et de vulnérabilité des communes au retrait-gonflement des sols argileux'
                }
            ),

            # =========================================================================
            # 6. ÉNERGIE & RÉSEAUX (SDES, RTE, AVERE)
            # =========================================================================
            DataItem(
                item_id="preset_bornes_irve",
                title="Bornes de Recharge Véhicules Électriques IRVE (data.gouv.fr)",
                source="data.gouv.fr (Etalab / AVERE)",
                data_type="table",
                territory="France",
                scale="france",
                crs="EPSG:4326",
                date="2026 (Quotidien)",
                url="https://static.data.gouv.fr/resources/bornes-de-recharge-de-laube-irve/20180503-181544/IRVE_SDEA_20180503.csv",
                service_type="HTTP",
                extra={
                    'format': 'CSV',
                    'category': 'energie',
                    'description': 'Fichier consolidé des points de recharge pour véhicules électriques ouverts au public'
                }
            ),
            DataItem(
                item_id="preset_registre_enr",
                title="Installations de Production d'Énergie Renouvelable EnR (SDES)",
                source="data.gouv.fr (SDES / RTE)",
                data_type="table",
                territory="France",
                scale="commune",
                crs="EPSG:4326",
                date="2025",
                url="https://opendata.edf.fr/data-fair/api/v1/datasets/registre-national-des-installations-de-production-et-de-stockage-d-electricite/convert",
                service_type="HTTP",
                extra={
                    'format': 'CSV',
                    'category': 'energie',
                    'description': 'Parcs solaires photovoltaïques, éoliens, hydroélectriques et biométhanation géolocalisés'
                }
            ),

            # =========================================================================
            # 7. MOBILITÉS & TRANSPORTS (SNCF, CEREMA, Vélo & Territoires)
            # =========================================================================
            DataItem(
                item_id="preset_reseau_cyclable_bnlc",
                title="Aménagements Cyclables & Véloroutes BNLC (Vélo & Territoires)",
                source="data.gouv.fr (BNLC / Cerema)",
                data_type="file_vector",
                territory="France",
                scale="france",
                crs="EPSG:4326",
                date="2026",
                url="https://static.data.gouv.fr/resources/amenagements-cyclables-france-metropolitaine/20260807-093353/france-20260807.geojson",
                service_type="HTTP",
                extra={
                    'format': 'GEOJSON',
                    'category': 'transport',
                    'description': 'Base Nationale des Lieux Cyclables (pistes, bandes cyclables, voies vertes, véloroutes)'
                }
            ),
            DataItem(
                item_id="preset_reseau_ferre_sncf",
                title="Réseau Ferré National & Gares Voyageurs (SNCF Réseau)",
                source="data.gouv.fr (SNCF Réseau)",
                data_type="file_vector",
                territory="France",
                scale="france",
                crs="EPSG:4326",
                date="2025",
                url="https://ressources.data.sncf.com/api/explore/v2.1/catalog/datasets/formes-des-lignes-du-rfn/exports/geojson",
                service_type="HTTP",
                extra={
                    'format': 'GEOJSON',
                    'category': 'transport',
                    'description': 'Tracé géométrique précis des lignes ferroviaires du Réseau Ferré National'
                }
            ),

            # =========================================================================
            # 8. FONDS DE CARTE & IMAGERIE (IGN, OpenStreetMap)
            # =========================================================================
            DataItem(
                item_id="preset_plan_ign_v2",
                title="Plan IGN V2 Multi-échelles (GéoPlateforme WMS)",
                source="GéoPlateforme IGN",
                data_type="wms",
                territory="France",
                scale="france",
                crs="EPSG:3857",
                date="2025",
                url="https://data.geopf.fr/wms-r/ows",
                service_type="WMS",
                extra={
                    'layer_name': 'GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2',
                    'wms_url': 'https://data.geopf.fr/wms-r/ows',
                    'category': 'raster',
                    'format': 'Flux WMS',
                    'description': 'Fond cartographique moderne multi-échelles officiel de l\'IGN'
                }
            ),
            DataItem(
                item_id="preset_ortho_ign",
                title="Photographies Aériennes Ortho HR (GéoPlateforme WMS)",
                source="GéoPlateforme IGN",
                data_type="wms",
                territory="France",
                scale="france",
                crs="EPSG:3857",
                date="2024-2025",
                url="https://data.geopf.fr/wms-r/ows",
                service_type="WMS",
                extra={
                    'layer_name': 'ORTHOIMAGERY.ORTHOPHOTOS',
                    'wms_url': 'https://data.geopf.fr/wms-r/ows',
                    'category': 'raster',
                    'format': 'Flux WMS',
                    'description': 'Orthophotographies aériennes haute résolution (20 cm) de la France entière'
                }
            ),
            DataItem(
                item_id="preset_scan25_ign",
                title="Cartes Topographiques IGN SCAN 25 (GéoPlateforme WMS)",
                source="GéoPlateforme IGN",
                data_type="wms",
                territory="France",
                scale="france",
                crs="EPSG:3857",
                date="2025",
                url="https://data.geopf.fr/wms-r/ows",
                service_type="WMS",
                extra={
                    'layer_name': 'GEOGRAPHICALGRIDSYSTEMS.MAPS.BDUNI.J1',
                    'wms_url': 'https://data.geopf.fr/wms-r/ows',
                    'category': 'raster',
                    'format': 'Flux WMS',
                    'description': 'Cartes topographiques traditionnelles IGN au 1/25 000 et 1/100 000'
                }
            ),
            DataItem(
                item_id="preset_osm_france",
                title="Fond de carte OpenStreetMap (XYZ Standard)",
                source="OpenStreetMap Community",
                data_type="wms",
                territory="France",
                scale="france",
                crs="EPSG:3857",
                date="Temps Réel",
                url="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                service_type="WMS",
                extra={
                    'layer_name': 'osm',
                    'wms_url': 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                    'category': 'raster',
                    'format': 'Tuiles XYZ',
                    'description': 'Fond de plan cartographique mondial et communautaire OpenStreetMap'
                }
            )
        ]
        return presets
