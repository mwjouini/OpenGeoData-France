# -*- coding: utf-8 -*-
"""
Bibliothèque de pré-réglages (Presets) de référence pour la France.
Accès en 1 clic aux données ouvertes officielles et pérennes :
IGN GéoPlateforme, INSEE, Cadastre DGFiP, GPU, INPN/OFB, BRGM, Géorisques,
Infoclimat / Météo-France SYNOP, transport.data.gouv.fr, RTE, Enedis, SNCF, et CRIGEs régionaux.
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
                date="2026 (IGN)",
                url="https://data.geopf.fr/wfs/ows",
                service_type="WFS",
                extra={
                    'layer_name': 'ADMINEXPRESS-COG-CARTO.LATEST:commune',
                    'wfs_url': 'https://data.geopf.fr/wfs/ows',
                    'category': 'admin',
                    'format': 'Flux WFS',
                    'description': 'Limites géographiques officielles des 35 000 communes (Admin Express)'
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
                date="2026 (IGN)",
                url="https://data.geopf.fr/wfs/ows",
                service_type="WFS",
                extra={
                    'layer_name': 'ADMINEXPRESS-COG-CARTO.LATEST:departement',
                    'wfs_url': 'https://data.geopf.fr/wfs/ows',
                    'category': 'admin',
                    'format': 'Flux WFS',
                    'description': 'Limites des 101 départements français et collectivités d\'outre-mer'
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
                date="2026 (IGN)",
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
                date="2026 (IGN)",
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
                date="2026 (IGN)",
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
                date="2026 (INSEE)",
                url="https://geo.api.gouv.fr/communes?fields=nom,code,codeDepartement,codeRegion,population&format=json",
                service_type="HTTP",
                extra={
                    'format': 'Table JSON / CSV',
                    'category': 'admin',
                    'description': 'Répertoire cartographique et démographique officiel des 35 000 communes'
                }
            ),
            DataItem(
                item_id="preset_insee_sirene",
                title="Base SIRENE des Entreprises & Établissements (API DINUM / INSEE)",
                source="API Recherche Entreprises (DINUM / INSEE)",
                data_type="table",
                territory="France",
                scale="france",
                crs="EPSG:4326",
                date="2026 (API SIRENE)",
                url="https://recherche-entreprises.api.gouv.fr/search?per_page=50",
                service_type="HTTP",
                extra={
                    'format': 'API REST JSON',
                    'category': 'admin',
                    'description': 'Répertoire officiel géocodé des entreprises et établissements actifs'
                }
            ),

            # =========================================================================
            # 2. CADASTRE & ADRESSES (DGFiP, IGN, BAN)
            # =========================================================================
            DataItem(
                item_id="preset_pci_wms_ign",
                title="Plan Cadastral WMS - Parcellaire Express (DGFiP / IGN)",
                source="GéoPlateforme IGN",
                data_type="wms",
                territory="France",
                scale="france",
                crs="EPSG:3857",
                date="2026 (IGN/DGFiP)",
                url="https://data.geopf.fr/wms-r/ows",
                service_type="WMS",
                extra={
                    'layer_name': 'CADASTRALPARCELS.PARCELLAIRE_EXPRESS',
                    'wms_url': 'https://data.geopf.fr/wms-r/ows',
                    'category': 'cadastre',
                    'format': 'Flux WMS',
                    'description': 'Flux WMS officiel du plan cadastral vectoriel assemblé national'
                }
            ),
            DataItem(
                item_id="preset_ban_nationale",
                title="Base Adresse Nationale BAN - France Complète",
                source="data.gouv.fr (IGN / DINUM)",
                data_type="table",
                territory="France",
                scale="france",
                crs="EPSG:4326",
                date="2026 (BAN)",
                url="https://adresse.data.gouv.fr/data/ban/adresses/latest/csv/adresses-france.csv.gz",
                service_type="HTTP",
                extra={
                    'format': 'CSV.GZ',
                    'category': 'admin',
                    'description': 'Référentiel national officiel des adresses postales géolocalisées'
                }
            ),

            # =========================================================================
            # 3. URBANISME & PLANIFICATION (GPU)
            # =========================================================================
            UrbanDocItem(
                item_id="preset_gpu_carte_nationale",
                title="Documents d'Urbanisme & Zonages Réglementaires (GPU)",
                doc_type="DU",
                territory="France",
                scale="commune",
                crs="EPSG:3857",
                date="2026",
                url="https://data.geopf.fr/wms-v/ows",
                service_type="GPU",
                wms_layers=["document", "zone_secteur", "prescription"],
                wfs_layers=["wfs_du:zone_urba", "wfs_du:prescription_pct"],
                extra={
                    'category': 'urbanisme',
                    'format': 'WMS/WFS GPU',
                    'description': 'Documents d\'urbanisme numérisés (PLU, PLUi, POS, Cartes Communales) du Géoportail de l\'Urbanisme'
                }
            ),
            DataItem(
                item_id="preset_gpu_zones_urba",
                title="Zonages d'Urbanisme (PLU/PLUi/POS) - WFS National",
                source="Géoportail de l'Urbanisme (GPU)",
                data_type="wfs",
                territory="France",
                scale="commune",
                crs="EPSG:4326",
                date="2026 (GPU)",
                url="https://data.geopf.fr/wfs/ows",
                service_type="WFS",
                extra={
                    'layer_name': 'wfs_du:zone_urba',
                    'wfs_url': 'https://data.geopf.fr/wfs/ows',
                    'category': 'urbanisme',
                    'format': 'Flux WFS',
                    'description': 'Couche vectorielle nationale des zones U, AU, A et N des PLU'
                }
            ),
            DataItem(
                item_id="preset_gpu_sup",
                title="Servitudes d'Utilité Publique (SUP) - WFS National",
                source="Géoportail de l'Urbanisme (GPU)",
                data_type="wfs",
                territory="France",
                scale="commune",
                crs="EPSG:4326",
                date="2026 (GPU)",
                url="https://data.geopf.fr/wfs/ows",
                service_type="WFS",
                extra={
                    'layer_name': 'wfs_sup:assiette_sup_s',
                    'wfs_url': 'https://data.geopf.fr/wfs/ows',
                    'category': 'urbanisme',
                    'format': 'Flux WFS',
                    'description': 'Assiettes des servitudes d\'utilité publique impactant l\'occupation des sols'
                }
            ),

            # =========================================================================
            # 4. TOPOGRAPHIE & RÉFÉRENTIELS IGN
            # =========================================================================
            DataItem(
                item_id="preset_bdtopo_batiments",
                title="Bâtiments 3D / Emprise du bâti (BD TOPO IGN)",
                source="GéoPlateforme IGN",
                data_type="wfs",
                territory="France",
                scale="commune",
                crs="EPSG:4326",
                date="2026 (IGN)",
                url="https://data.geopf.fr/wfs/ows",
                service_type="WFS",
                extra={
                    'layer_name': 'BDTOPO_V3:batiment',
                    'wfs_url': 'https://data.geopf.fr/wfs/ows',
                    'category': 'admin',
                    'format': 'Flux WFS',
                    'description': 'Emprises et hauteurs réelles des bâtiments (BD TOPO)'
                }
            ),
            DataItem(
                item_id="preset_bdtopo_routes",
                title="Réseau routier et voies de circulation (BD TOPO IGN)",
                source="GéoPlateforme IGN",
                data_type="wfs",
                territory="France",
                scale="commune",
                crs="EPSG:4326",
                date="2026 (IGN)",
                url="https://data.geopf.fr/wfs/ows",
                service_type="WFS",
                extra={
                    'layer_name': 'BDTOPO_V3:troncon_de_route',
                    'wfs_url': 'https://data.geopf.fr/wfs/ows',
                    'category': 'transport',
                    'format': 'Flux WFS',
                    'description': 'Voies, rues, routes nationales et départementales'
                }
            ),
            DataItem(
                item_id="preset_cours_d_eau",
                title="Réseau hydrographique & Cours d'eau (BD TOPO / TOPAGE)",
                source="GéoPlateforme IGN / OFB",
                data_type="wfs",
                territory="France",
                scale="commune",
                crs="EPSG:4326",
                date="2026 (IGN)",
                url="https://data.geopf.fr/wfs/ows",
                service_type="WFS",
                extra={
                    'layer_name': 'BDTOPO_V3:cours_d_eau',
                    'wfs_url': 'https://data.geopf.fr/wfs/ows',
                    'category': 'environnement',
                    'format': 'Flux WFS',
                    'description': 'Rivières, cours d\'eau et masses d\'eau de surface'
                }
            ),
            DataItem(
                item_id="preset_bd_foret",
                title="Forêts et Couverture Végétale (BD Forêt / BD TOPO IGN)",
                source="GéoPlateforme IGN",
                data_type="wfs",
                territory="France",
                scale="commune",
                crs="EPSG:4326",
                date="2026 (IGN)",
                url="https://data.geopf.fr/wfs/ows",
                service_type="WFS",
                extra={
                    'layer_name': 'BDTOPO_V3:zone_de_vegetation',
                    'wfs_url': 'https://data.geopf.fr/wfs/ows',
                    'category': 'environnement',
                    'format': 'Flux WFS',
                    'description': 'Zones boisées, forêts domaniales et végétation'
                }
            ),

            # =========================================================================
            # 5. ENVIRONNEMENT & BIODIVERSITÉ (INPN, OFB, PatriNat, AEE)
            # =========================================================================
            DataItem(
                item_id="preset_natura2000",
                title="Réseau Natura 2000 - SIC/ZSC & ZPS (INPN / OFB)",
                source="GéoPlateforme IGN / INPN",
                data_type="wfs",
                territory="France",
                scale="france",
                crs="EPSG:4326",
                date="2026 (PatriNat)",
                url="https://data.geopf.fr/wfs/ows",
                service_type="WFS",
                extra={
                    'layer_name': 'patrinat:sic',
                    'wfs_url': 'https://data.geopf.fr/wfs/ows',
                    'category': 'environnement',
                    'format': 'Flux WFS',
                    'description': 'Sites d\'Intérêt Communautaire et Zones de Protection Spéciale'
                }
            ),
            DataItem(
                item_id="preset_znieff1",
                title="ZNIEFF Type 1 - Espaces de grand intérêt écologique (INPN)",
                source="GéoPlateforme IGN / INPN",
                data_type="wfs",
                territory="France",
                scale="france",
                crs="EPSG:4326",
                date="2026 (INPN)",
                url="https://data.geopf.fr/wfs/ows",
                service_type="WFS",
                extra={
                    'layer_name': 'patrinat:znieff1',
                    'wfs_url': 'https://data.geopf.fr/wfs/ows',
                    'category': 'environnement',
                    'format': 'Flux WFS',
                    'description': 'Zones Naturelles d\'Intérêt Écologique, Faunistique et Floristique (Type 1)'
                }
            ),
            DataItem(
                item_id="preset_znieff2",
                title="ZNIEFF Type 2 - Grands ensembles naturels (INPN)",
                source="GéoPlateforme IGN / INPN",
                data_type="wfs",
                territory="France",
                scale="france",
                crs="EPSG:4326",
                date="2026 (INPN)",
                url="https://data.geopf.fr/wfs/ows",
                service_type="WFS",
                extra={
                    'layer_name': 'patrinat:znieff2',
                    'wfs_url': 'https://data.geopf.fr/wfs/ows',
                    'category': 'environnement',
                    'format': 'Flux WFS',
                    'description': 'Grands ensembles naturels riches et peu modifiés (Type 2)'
                }
            ),

            # =========================================================================
            # 6. RISQUES NATURELS & GÉOLOGIE (BRGM, Géorisques)
            # =========================================================================
            DataItem(
                item_id="preset_pprn_georisques",
                title="Risque Inondation - EAIP & PPRN (Géorisques / BRGM)",
                source="Géorisques / BRGM",
                data_type="wms",
                territory="France",
                scale="france",
                crs="EPSG:3857",
                date="2026",
                url="https://georisques.gouv.fr/services",
                service_type="WMS",
                extra={
                    'layer_name': 'MASQ_EAIP',
                    'wms_url': 'https://georisques.gouv.fr/services',
                    'category': 'risques',
                    'format': 'Flux WMS',
                    'description': 'Enveloppes Approchées des Inondations Potentielles cours d\'eau et submersion marine'
                }
            ),
            DataItem(
                item_id="preset_argiles_rga",
                title="Aléa Retrait-Gonflement des Argiles RGA (BRGM / Géorisques)",
                source="BRGM / Géorisques",
                data_type="wms",
                territory="France",
                scale="france",
                crs="EPSG:3857",
                date="2026",
                url="https://georisques.gouv.fr/services",
                service_type="WMS",
                extra={
                    'layer_name': 'ALEARG',
                    'wms_url': 'https://georisques.gouv.fr/services',
                    'category': 'risques',
                    'format': 'Flux WMS',
                    'description': 'Exposition officielle au retrait-gonflement des sols argileux'
                }
            ),
            DataItem(
                item_id="preset_carte_geologique_brgm",
                title="Carte Géologique de la France 1/50 000 (BRGM)",
                source="BRGM",
                data_type="wms",
                territory="France",
                scale="france",
                crs="EPSG:3857",
                date="2026",
                url="https://geoservices.brgm.fr/geologie",
                service_type="WMS",
                extra={
                    'layer_name': 'SCAN_D_GEOL50',
                    'wms_url': 'https://geoservices.brgm.fr/geologie',
                    'category': 'risques',
                    'format': 'Flux WMS',
                    'description': 'Carte géologique harmonisée au 1/50 000 du BRGM'
                }
            ),

            # =========================================================================
            # 7. TRANSPORTS & MOBILITÉS (PAN, SNCF, BNLC)
            # =========================================================================
            DataItem(
                item_id="preset_reseau_cyclable_bnlc",
                title="Aménagements cyclables et Véloroutes (BNLC France)",
                source="data.gouv.fr (BNLC / Cerema)",
                data_type="file_vector",
                territory="France",
                scale="france",
                crs="EPSG:4326",
                date="2026",
                url="https://static.data.gouv.fr/resources/amenagements-cyclables-france-metropolitaine/20260807-093353/france-20260807.geojson",
                service_type="HTTP",
                extra={
                    'format': 'GeoJSON',
                    'category': 'transport',
                    'description': 'Base Nationale des Aménagements Cyclables (Pistes, bandes, voies vertes)'
                }
            ),
            DataItem(
                item_id="preset_reseau_ferre_sncf",
                title="Réseau Ferré National & Gares de Voyageurs (SNCF Réseau)",
                source="SNCF Réseau Open Data",
                data_type="file_vector",
                territory="France",
                scale="france",
                crs="EPSG:4326",
                date="2026",
                url="https://ressources.data.sncf.com/api/explore/v2.1/catalog/datasets/formes-des-lignes-du-rfn/exports/geojson",
                service_type="HTTP",
                extra={
                    'format': 'GeoJSON',
                    'category': 'transport',
                    'description': 'Tracé officiel des voies ferrées, lignes et gares SNCF'
                }
            ),
            DataItem(
                item_id="preset_covoiturage_pan",
                title="Lieux et Aires de Covoiturage (Point d'Accès National)",
                source="transport.data.gouv.fr",
                data_type="table",
                territory="France",
                scale="france",
                crs="EPSG:4326",
                date="2026",
                url="https://static.data.gouv.fr/resources/base-nationale-des-lieux-de-covoiturage/20260818-211131/bnlc.csv",
                service_type="HTTP",
                extra={
                    'format': 'CSV',
                    'category': 'transport',
                    'description': 'Base nationale consolidée des aires et points de covoiturage'
                }
            ),

            # =========================================================================
            # 8. ÉNERGIE & RÉSEAUX (ODRE, RTE, SDES)
            # =========================================================================
            DataItem(
                item_id="preset_bornes_irve",
                title="Bornes de Recharge Véhicules Électriques IRVE",
                source="data.gouv.fr (Etalab / Ministère)",
                data_type="file_vector",
                territory="France",
                scale="france",
                crs="EPSG:4326",
                date="2026",
                url="https://static.data.gouv.fr/resources/points-de-recharge-pour-vehicules-electriques-pour-1000-hab/20260414-110820/irve-coord.geojson",
                service_type="HTTP",
                extra={
                    'format': 'GeoJSON',
                    'category': 'energie',
                    'description': 'Fichier consolidé national géoréférencé des stations et bornes de recharge électrique'
                }
            ),
            DataItem(
                item_id="preset_registre_enr",
                title="Registre des Installations de Production d'Électricité EnR",
                source="data.gouv.fr (ODRE / Enedis / RTE)",
                data_type="table",
                territory="France",
                scale="france",
                crs="EPSG:4326",
                date="2026",
                url="https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/registre-national-installation-production-stockage-electricite-agrege-commune/exports/csv",
                service_type="HTTP",
                extra={
                    'format': 'CSV',
                    'category': 'energie',
                    'description': 'Installations solaires, éoliennes, hydrauliques et bioénergies par commune'
                }
            ),

            # =========================================================================
            # 9. MÉTÉOROLOGIE, CLIMAT & RADAR TEMPS RÉEL (Météo-France / RainViewer)
            # =========================================================================
            DataItem(
                item_id="preset_radar_pluie_temps_reel",
                title="Radar de Pluie & Précipitations en Temps Réel (France / Europe)",
                source="RainViewer / Radar Météo Direct",
                data_type="wms",
                territory="France",
                scale="france",
                crs="EPSG:3857",
                date="Temps Réel (10 min)",
                url="https://tilecache.rainviewer.com/v2/radar/nowcast_0/256/{z}/{x}/{y}/2/1_1.png",
                service_type="WMS",
                extra={
                    'format': 'Tuiles XYZ Temps Réel',
                    'category': 'meteo',
                    'description': 'Échos radar de pluie et précipitations en direct actualisés toutes les 10 minutes avec palette d\'intensité'
                }
            ),
            DataItem(
                item_id="preset_satellite_infrarouge_temps_reel",
                title="Imagerie Satellite Nuages & Infrarouge (Temps Réel)",
                source="EUMETSAT / Satellite Météo Direct",
                data_type="wms",
                territory="France",
                scale="france",
                crs="EPSG:3857",
                date="Temps Réel",
                url="https://tilecache.rainviewer.com/v2/satellite/nowcast_0/256/{z}/{x}/{y}/0/1_1.png",
                service_type="WMS",
                extra={
                    'format': 'Tuiles XYZ Temps Réel',
                    'category': 'meteo',
                    'description': 'Couverture nuageuse et masses d\'air observées par satellite météorologique géostationnaire en direct'
                }
            ),
            DataItem(
                item_id="preset_meteo_stations",
                title="Stations Météorologiques & Climatologiques (Météo-France / SYNOP)",
                source="Infoclimat / Météo-France",
                data_type="file_vector",
                territory="France",
                scale="france",
                crs="EPSG:4326",
                date="2026",
                url="https://www.infoclimat.fr/opendata/stations_xhr.php?format=geojson",
                service_type="HTTP",
                extra={
                    'format': 'GeoJSON',
                    'category': 'meteo',
                    'description': 'Réseau officiel des 600+ stations météorologiques SYNOP et StatIC avec température, vent, humidité, coordonnées et altitude'
                }
            ),

            # =========================================================================
            # 10. IMAGERIE AÉRIENNE, SATELLITE & HISTORIQUE (GéoPlateforme IGN / CNES)
            # =========================================================================
            DataItem(
                item_id="preset_ortho_ign",
                title="Photographies Aériennes Haute Résolution Ortho HR® (IGN GéoPlateforme)",
                source="GéoPlateforme IGN",
                data_type="wms",
                territory="France",
                scale="france",
                crs="EPSG:3857",
                date="2024-2026",
                url="https://data.geopf.fr/wms-r/ows",
                service_type="WMS",
                extra={
                    'layer_name': 'HR.ORTHOIMAGERY.ORTHOPHOTOS',
                    'wms_url': 'https://data.geopf.fr/wms-r/ows',
                    'category': 'raster',
                    'format': 'Flux WMS',
                    'description': 'Orthophotographie aérienne la plus récente et précise (résolution 20 cm) sur l\'ensemble du territoire français'
                }
            ),
            DataItem(
                item_id="preset_ortho_1950_1965",
                title="Photographies Aériennes Historiques 1950-1965 (IGN Remonter le Temps)",
                source="IGN / Remonter le Temps",
                data_type="wms",
                territory="France",
                scale="france",
                crs="EPSG:3857",
                date="1950-1965",
                url="https://data.geopf.fr/wms-r/ows",
                service_type="WMS",
                extra={
                    'layer_name': 'ORTHOIMAGERY.ORTHOPHOTOS.1950-1965',
                    'wms_url': 'https://data.geopf.fr/wms-r/ows',
                    'category': 'raster',
                    'format': 'Flux WMS',
                    'description': 'Mosaïque nationale de clichés aériens argentiques historiques des années 1950-1965 pour le suivi de l\'évolution du territoire et de l\'urbanisation'
                }
            ),
            DataItem(
                item_id="preset_pleiades_sat",
                title="Imagerie Satellite Très Haute Résolution Pléiades 50 cm (CNES / IGN)",
                source="CNES / GéoPlateforme IGN",
                data_type="wms",
                territory="France",
                scale="france",
                crs="EPSG:3857",
                date="2025-2026",
                url="https://data.geopf.fr/wms-r/ows",
                service_type="WMS",
                extra={
                    'layer_name': 'ORTHOIMAGERY.ORTHO-SAT.PLEIADES.2025',
                    'wms_url': 'https://data.geopf.fr/wms-r/ows',
                    'category': 'raster',
                    'format': 'Flux WMS',
                    'description': 'Imagerie spatiale optique satellitaire Pléiades à très haute résolution (50 cm)'
                }
            ),
            DataItem(
                item_id="preset_spot_sat",
                title="Imagerie Satellite SPOT 6-7 (CNES / IGN)",
                source="CNES / GéoPlateforme IGN",
                data_type="wms",
                territory="France",
                scale="france",
                crs="EPSG:3857",
                date="2025",
                url="https://data.geopf.fr/wms-r/ows",
                service_type="WMS",
                extra={
                    'layer_name': 'ORTHOIMAGERY.ORTHO-SAT.SPOT.2025',
                    'wms_url': 'https://data.geopf.fr/wms-r/ows',
                    'category': 'raster',
                    'format': 'Flux WMS',
                    'description': 'Couverture satellitaire optique haute résolution SPOT 6-7 pour l\'observation de la Terre'
                }
            ),
            DataItem(
                item_id="preset_ortho_irc",
                title="Orthophotos Infrarouge Couleur IRC (IGN - Santé de la Végétation)",
                source="GéoPlateforme IGN",
                data_type="wms",
                territory="France",
                scale="france",
                crs="EPSG:3857",
                date="2024-2026",
                url="https://data.geopf.fr/wms-r/ows",
                service_type="WMS",
                extra={
                    'layer_name': 'ORTHOIMAGERY.ORTHOPHOTOS.IRC',
                    'wms_url': 'https://data.geopf.fr/wms-r/ows',
                    'category': 'raster',
                    'format': 'Flux WMS',
                    'description': 'Imagerie fausses couleurs proche infrarouge (PIR) pour l\'analyse de la vigueur végétale, des forêts et des zones humides'
                }
            ),
            DataItem(
                item_id="preset_etat_major",
                title="Carte de l'État-Major 1820-1866 (IGN)",
                source="GéoPlateforme IGN",
                data_type="wms",
                territory="France",
                scale="france",
                crs="EPSG:3857",
                date="1820-1866",
                url="https://data.geopf.fr/wms-r/ows",
                service_type="WMS",
                extra={
                    'layer_name': 'GEOGRAPHICALGRIDSYSTEMS.ETATMAJOR40',
                    'wms_url': 'https://data.geopf.fr/wms-r/ows',
                    'category': 'raster',
                    'format': 'Flux WMS',
                    'description': 'Cartes historiques militaires d\'État-Major gravées au 1/40 000 (XIXe siècle)'
                }
            ),
            DataItem(
                item_id="preset_scan50_1950",
                title="SCAN 50® Historique de 1950 (IGN)",
                source="GéoPlateforme IGN",
                data_type="wms",
                territory="France",
                scale="france",
                crs="EPSG:3857",
                date="1950",
                url="https://data.geopf.fr/wms-r/ows",
                service_type="WMS",
                extra={
                    'layer_name': 'GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN50.1950',
                    'wms_url': 'https://data.geopf.fr/wms-r/ows',
                    'category': 'raster',
                    'format': 'Flux WMS',
                    'description': 'Cartographie topographique historique de référence au 1/50 000 de l\'année 1950'
                }
            ),
            DataItem(
                item_id="preset_plan_ign",
                title="Plan IGN V2 Multi-échelles (IGN GéoPlateforme)",
                source="GéoPlateforme IGN",
                data_type="wms",
                territory="France",
                scale="france",
                crs="EPSG:3857",
                date="2026",
                url="https://data.geopf.fr/wms-r/ows",
                service_type="WMS",
                extra={
                    'layer_name': 'GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2',
                    'wms_url': 'https://data.geopf.fr/wms-r/ows',
                    'category': 'raster',
                    'format': 'Flux WMS',
                    'description': 'Fond de carte vectoriel cartographique optimisé pour toutes les échelles'
                }
            ),
            DataItem(
                item_id="preset_scan25",
                title="Cartes Topographiques IGN SCAN 25® (IGN GéoPlateforme)",
                source="GéoPlateforme IGN",
                data_type="wms",
                territory="France",
                scale="france",
                crs="EPSG:3857",
                date="2026",
                url="https://data.geopf.fr/wms-r/ows",
                service_type="WMS",
                extra={
                    'layer_name': 'GEOGRAPHICALGRIDSYSTEMS.MAPS.BDUNI.J1',
                    'wms_url': 'https://data.geopf.fr/wms-r/ows',
                    'category': 'raster',
                    'format': 'Flux WMS',
                    'description': 'Cartes topographiques de randonnée et de référence au 1/25 000'
                }
            ),
            DataItem(
                item_id="preset_relief_ombre",
                title="Relief ombré & MNT RGE ALTI® (IGN GéoPlateforme)",
                source="GéoPlateforme IGN",
                data_type="wms",
                territory="France",
                scale="france",
                crs="EPSG:3857",
                date="2026",
                url="https://data.geopf.fr/wms-r/ows",
                service_type="WMS",
                extra={
                    'layer_name': 'ELEVATION.ELEVATIONGRIDCOVERAGE.SHADOW',
                    'wms_url': 'https://data.geopf.fr/wms-r/ows',
                    'category': 'raster',
                    'format': 'Flux WMS',
                    'description': 'Modèle Numérique de Terrain ombré issu du RGE ALTI'
                }
            ),
            DataItem(
                item_id="preset_osm_france",
                title="Fond de carte OpenStreetMap France (XYZ)",
                source="OpenStreetMap",
                data_type="wms",
                territory="France",
                scale="france",
                crs="EPSG:3857",
                date="2026",
                url="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                service_type="WMS",
                extra={
                    'format': 'Tuiles XYZ',
                    'category': 'raster',
                    'description': 'Tuiles cartographiques mondiales et collaboratives OpenStreetMap'
                }
            ),

            # =========================================================================
            # 11. RÉGIONS & CATALOGUES CRIGE (PIGMA, GéoBretagne, Geo2France, CRAIG...)
            # =========================================================================
            DataItem(
                item_id="preset_crige_pigma",
                title="PIGMA - Plateforme Publique Nouvelle-Aquitaine (WMS)",
                source="PIGMA (CRIGE Nouvelle-Aquitaine)",
                data_type="wms",
                territory="Nouvelle-Aquitaine",
                scale="region",
                crs="EPSG:3857",
                date="2026",
                url="https://www.pigma.org/geoserver/ows",
                service_type="WMS",
                extra={
                    'layer_name': 'pigma:pigma_default',
                    'wms_url': 'https://www.pigma.org/geoserver/ows',
                    'category': 'admin',
                    'format': 'Flux WMS',
                    'description': 'Plateforme d\'échange de données géographiques de Nouvelle-Aquitaine'
                }
            ),
            DataItem(
                item_id="preset_crige_geobretagne",
                title="GéoBretagne - Plateforme Régionale d'Information Géographique (WMS)",
                source="GéoBretagne (Région Bretagne)",
                data_type="wms",
                territory="Bretagne",
                scale="region",
                crs="EPSG:3857",
                date="2026",
                url="https://geobretagne.fr/geoserver/ows",
                service_type="WMS",
                extra={
                    'layer_name': 'bretagne_default',
                    'wms_url': 'https://geobretagne.fr/geoserver/ows',
                    'category': 'admin',
                    'format': 'Flux WMS',
                    'description': 'Infrastructure de données spatiales partenariale en Bretagne'
                }
            ),
            DataItem(
                item_id="preset_crige_geo2france",
                title="Geo2France - Plateforme Régionale Hauts-de-France (WMS)",
                source="Geo2France (Région Hauts-de-France)",
                data_type="wms",
                territory="Hauts-de-France",
                scale="region",
                crs="EPSG:3857",
                date="2026",
                url="https://www.geo2france.fr/geoserver/ows",
                service_type="WMS",
                extra={
                    'layer_name': 'geo2france_default',
                    'wms_url': 'https://www.geo2france.fr/geoserver/ows',
                    'category': 'admin',
                    'format': 'Flux WMS',
                    'description': 'Plateforme régionale de données géographiques des Hauts-de-France'
                }
            ),
            DataItem(
                item_id="preset_crige_craig",
                title="CRAIG - Centre Régional Auvergne-Rhône-Alpes (WMS)",
                source="CRAIG (Auvergne-Rhône-Alpes)",
                data_type="wms",
                territory="Auvergne-Rhône-Alpes",
                scale="region",
                crs="EPSG:3857",
                date="2026",
                url="https://www.craig.fr/geoserver/ows",
                service_type="WMS",
                extra={
                    'layer_name': 'craig_default',
                    'wms_url': 'https://www.craig.fr/geoserver/ows',
                    'category': 'admin',
                    'format': 'Flux WMS',
                    'description': 'Données géographiques de référence pour Auvergne-Rhône-Alpes'
                }
            )
        ]
        return presets
