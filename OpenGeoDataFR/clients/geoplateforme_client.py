# -*- coding: utf-8 -*-
"""
Client pour la GéoPlateforme IGN (Flux WMS, WFS, WMTS).
Fournit les accès directs aux référentiels administratifs, BD TOPO, BD FORET, MNT et fonds d'imagerie IGN.
"""

from ..models import DataItem


class GeoplateformeClient:
    """Client pour les services Web et référentiels officiels de la GéoPlateforme IGN."""

    WMS_RASTER_URL = "https://data.geopf.fr/wms-r/ows"
    WMS_VECTOR_URL = "https://data.geopf.fr/wms-v/ows"
    WFS_URL = "https://data.geopf.fr/wfs/ows"

    PREDEFINED_LAYERS = [
        # Référentiel Administratif (Admin Express)
        {
            'id': 'geopf_communes',
            'title': 'Communes de France (Admin Express IGN)',
            'type': 'wfs',
            'layer_name': 'ADMINEXPRESS-COG-CARTO.LATEST:commune',
            'source': 'GéoPlateforme IGN',
            'territory': 'France',
            'scale': 'france',
            'crs': 'EPSG:4326',
            'date': '2025 (IGN)',
            'service_type': 'WFS',
            'category': 'admin'
        },
        {
            'id': 'geopf_departements',
            'title': 'Départements de France (Admin Express IGN)',
            'type': 'wfs',
            'layer_name': 'ADMINEXPRESS-COG-CARTO.LATEST:departement',
            'source': 'GéoPlateforme IGN',
            'territory': 'France',
            'scale': 'france',
            'crs': 'EPSG:4326',
            'date': '2025 (IGN)',
            'service_type': 'WFS',
            'category': 'admin'
        },
        {
            'id': 'geopf_regions',
            'title': 'Régions de France (Admin Express IGN)',
            'type': 'wfs',
            'layer_name': 'ADMINEXPRESS-COG-CARTO.LATEST:region',
            'source': 'GéoPlateforme IGN',
            'territory': 'France',
            'scale': 'france',
            'crs': 'EPSG:4326',
            'date': '2025 (IGN)',
            'service_type': 'WFS',
            'category': 'admin'
        },
        {
            'id': 'geopf_epci',
            'title': 'Intercommunalités EPCI (Admin Express IGN)',
            'type': 'wfs',
            'layer_name': 'ADMINEXPRESS-COG-CARTO.LATEST:epci',
            'source': 'GéoPlateforme IGN',
            'territory': 'France',
            'scale': 'epci',
            'crs': 'EPSG:4326',
            'date': '2025 (IGN)',
            'service_type': 'WFS',
            'category': 'admin'
        },
        {
            'id': 'geopf_arrondissements',
            'title': 'Arrondissements départementaux (Admin Express IGN)',
            'type': 'wfs',
            'layer_name': 'ADMINEXPRESS-COG-CARTO.LATEST:arrondissement',
            'source': 'GéoPlateforme IGN',
            'territory': 'France',
            'scale': 'departement',
            'crs': 'EPSG:4326',
            'date': '2025 (IGN)',
            'service_type': 'WFS',
            'category': 'admin'
        },
        {
            'id': 'geopf_cantons',
            'title': 'Cantons électoraux (Admin Express IGN)',
            'type': 'wfs',
            'layer_name': 'ADMINEXPRESS-COG-CARTO.LATEST:canton',
            'source': 'GéoPlateforme IGN',
            'territory': 'France',
            'scale': 'departement',
            'crs': 'EPSG:4326',
            'date': '2025 (IGN)',
            'service_type': 'WFS',
            'category': 'admin'
        },

        # Référentiel Topographique (BD TOPO IGN)
        {
            'id': 'geopf_bdtopo_batiment',
            'title': 'Bâtiments 3D / Emprise du bâti (BD TOPO IGN)',
            'type': 'wfs',
            'layer_name': 'BDTOPO_V3:batiment',
            'source': 'GéoPlateforme IGN',
            'territory': 'France',
            'scale': 'commune',
            'crs': 'EPSG:4326',
            'date': '2025 (IGN)',
            'service_type': 'WFS',
            'category': 'topo'
        },
        {
            'id': 'geopf_bdtopo_routes',
            'title': 'Réseau routier et voies (BD TOPO IGN)',
            'type': 'wfs',
            'layer_name': 'BDTOPO_V3:troncon_de_route',
            'source': 'GéoPlateforme IGN',
            'territory': 'France',
            'scale': 'commune',
            'crs': 'EPSG:4326',
            'date': '2025 (IGN)',
            'service_type': 'WFS',
            'category': 'transport'
        },
        {
            'id': 'geopf_bdtopo_hydro',
            'title': 'Réseau hydrographique & Cours d\'eau (BD TOPO IGN)',
            'type': 'wfs',
            'layer_name': 'BDTOPO_V3:cours_d_eau',
            'source': 'GéoPlateforme IGN',
            'territory': 'France',
            'scale': 'commune',
            'crs': 'EPSG:4326',
            'date': '2025 (IGN)',
            'service_type': 'WFS',
            'category': 'environnement'
        },
        {
            'id': 'geopf_bdtopo_vegetation',
            'title': 'Zones de végétation et Forêts (BD TOPO IGN)',
            'type': 'wfs',
            'layer_name': 'BDTOPO_V3:zone_de_vegetation',
            'source': 'GéoPlateforme IGN',
            'territory': 'France',
            'scale': 'commune',
            'crs': 'EPSG:4326',
            'date': '2025 (IGN)',
            'service_type': 'WFS',
            'category': 'environnement'
        },

        # Fonds Raster & Cartographiques (WMS-R)
        {
            'id': 'geopf_cadastre_express',
            'title': 'Plan Cadastral WMS - Parcellaire Express (DGFiP / IGN)',
            'type': 'wms',
            'layer_name': 'CADASTRALPARCELS.PARCELLAIRE_EXPRESS',
            'source': 'GéoPlateforme IGN',
            'territory': 'France',
            'scale': 'france',
            'crs': 'EPSG:3857',
            'date': '2025',
            'service_type': 'WMS',
            'category': 'cadastre'
        },
        {
            'id': 'geopf_ortho',
            'title': 'Photographies aériennes Ortho HR (GéoPlateforme WMS)',
            'type': 'wms',
            'layer_name': 'ORTHOIMAGERY.ORTHOPHOTOS',
            'source': 'GéoPlateforme IGN',
            'territory': 'France',
            'scale': 'france',
            'crs': 'EPSG:3857',
            'date': '2024-2025',
            'service_type': 'WMS',
            'category': 'raster'
        },
        {
            'id': 'geopf_plan_ign',
            'title': 'Plan IGN V2 Multi-échelles (GéoPlateforme WMS)',
            'type': 'wms',
            'layer_name': 'GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2',
            'source': 'GéoPlateforme IGN',
            'territory': 'France',
            'scale': 'france',
            'crs': 'EPSG:3857',
            'date': '2025',
            'service_type': 'WMS',
            'category': 'raster'
        },
        {
            'id': 'geopf_scan25',
            'title': 'Cartes Topographiques IGN SCAN 25 (GéoPlateforme WMS)',
            'type': 'wms',
            'layer_name': 'GEOGRAPHICALGRIDSYSTEMS.MAPS.BDUNI.J1',
            'source': 'GéoPlateforme IGN',
            'territory': 'France',
            'scale': 'france',
            'crs': 'EPSG:3857',
            'date': '2025',
            'service_type': 'WMS',
            'category': 'raster'
        },
        {
            'id': 'geopf_relief_ombre',
            'title': 'Relief ombré & MNT RGE ALTI (GéoPlateforme WMS)',
            'type': 'wms',
            'layer_name': 'ELEVATION.ELEVATIONGRIDCOVERAGE.SHADOW',
            'source': 'GéoPlateforme IGN',
            'territory': 'France',
            'scale': 'france',
            'crs': 'EPSG:3857',
            'date': '2025',
            'service_type': 'WMS',
            'category': 'raster'
        },
        {
            'id': 'geopf_parcelles',
            'title': 'Plan Cadastral - Parcelles Cadastrales (Parcellaire Express IGN)',
            'type': 'wms',
            'layer_name': 'CADASTRALPARCELS.PARCELLAIRE_EXPRESS',
            'source': 'GéoPlateforme IGN',
            'territory': 'France',
            'scale': 'france',
            'crs': 'EPSG:3857',
            'date': '2026',
            'service_type': 'WMS',
            'category': 'cadastre'
        },
        {
            'id': 'geopf_batiments_cadastre',
            'title': 'Plan Cadastral - Bâtiments Cadastraux (Parcellaire Express IGN)',
            'type': 'wms',
            'layer_name': 'BUILDINGS.PARCELLAIRE_EXPRESS',
            'source': 'GéoPlateforme IGN',
            'territory': 'France',
            'scale': 'france',
            'crs': 'EPSG:3857',
            'date': '2026',
            'service_type': 'WMS',
            'category': 'cadastre'
        },
        {
            'id': 'geopf_ortho_hr',
            'title': 'Photographies Aériennes Haute Résolution Ortho HR® 20 cm (IGN)',
            'type': 'wms',
            'layer_name': 'HR.ORTHOIMAGERY.ORTHOPHOTOS',
            'source': 'GéoPlateforme IGN',
            'territory': 'France',
            'scale': 'france',
            'crs': 'EPSG:3857',
            'date': '2024-2026',
            'service_type': 'WMS',
            'category': 'raster'
        },
        {
            'id': 'geopf_ortho_1950',
            'title': 'Photographies Aériennes Historiques 1950-1965 (IGN Remonter le Temps)',
            'type': 'wms',
            'layer_name': 'ORTHOIMAGERY.ORTHOPHOTOS.1950-1965',
            'source': 'GéoPlateforme IGN',
            'territory': 'France',
            'scale': 'france',
            'crs': 'EPSG:3857',
            'date': '1950-1965',
            'service_type': 'WMS',
            'category': 'raster'
        },
        {
            'id': 'geopf_pleiades',
            'title': 'Imagerie Satellite Très Haute Résolution Pléiades 50 cm (CNES / IGN)',
            'type': 'wms',
            'layer_name': 'ORTHOIMAGERY.ORTHO-SAT.PLEIADES.2025',
            'source': 'GéoPlateforme IGN',
            'territory': 'France',
            'scale': 'france',
            'crs': 'EPSG:3857',
            'date': '2025-2026',
            'service_type': 'WMS',
            'category': 'raster'
        },
        {
            'id': 'geopf_spot',
            'title': 'Imagerie Satellite SPOT 6-7 (CNES / IGN)',
            'type': 'wms',
            'layer_name': 'ORTHOIMAGERY.ORTHO-SAT.SPOT.2025',
            'source': 'GéoPlateforme IGN',
            'territory': 'France',
            'scale': 'france',
            'crs': 'EPSG:3857',
            'date': '2025',
            'service_type': 'WMS',
            'category': 'raster'
        },
        {
            'id': 'geopf_ortho_irc',
            'title': 'Orthophotos Infrarouge Couleur IRC - Végétation (IGN)',
            'type': 'wms',
            'layer_name': 'ORTHOIMAGERY.ORTHOPHOTOS.IRC',
            'source': 'GéoPlateforme IGN',
            'territory': 'France',
            'scale': 'france',
            'crs': 'EPSG:3857',
            'date': '2024-2026',
            'service_type': 'WMS',
            'category': 'raster'
        },
        {
            'id': 'geopf_etat_major',
            'title': 'Carte de l\'État-Major 1820-1866 (IGN)',
            'type': 'wms',
            'layer_name': 'GEOGRAPHICALGRIDSYSTEMS.ETATMAJOR40',
            'source': 'GéoPlateforme IGN',
            'territory': 'France',
            'scale': 'france',
            'crs': 'EPSG:3857',
            'date': '1820-1866',
            'service_type': 'WMS',
            'category': 'raster'
        },
        {
            'id': 'geopf_scan50_1950',
            'title': 'SCAN 50® Historique de 1950 (IGN)',
            'type': 'wms',
            'layer_name': 'GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN50.1950',
            'source': 'GéoPlateforme IGN',
            'territory': 'France',
            'scale': 'france',
            'crs': 'EPSG:3857',
            'date': '1950',
            'service_type': 'WMS',
            'category': 'raster'
        },
        {
            'id': 'geopf_courbes_niveau',
            'title': 'Courbes de niveau altimétriques (GéoPlateforme WMS)',
            'type': 'wms',
            'layer_name': 'ELEVATION.CONTOUR.LINE',
            'source': 'GéoPlateforme IGN',
            'territory': 'France',
            'scale': 'france',
            'crs': 'EPSG:3857',
            'date': '2025',
            'service_type': 'WMS',
            'category': 'raster'
        }
    ]

    def search(self, query):
        if not query or not query.strip():
            return []

        q_lower = query.lower().strip()
        results = []

        keywords = [t for t in q_lower.split() if len(t) > 2]
        if not keywords:
            return []

        for layer in self.PREDEFINED_LAYERS:
            title_lower = layer['title'].lower()
            source_lower = layer['source'].lower()
            cat = layer.get('category', '')
            
            if any(kw in title_lower or kw in source_lower or kw in cat for kw in keywords):
                if layer['type'] == 'wfs':
                    url = self.WFS_URL
                elif layer['type'] == 'wms':
                    url = self.WMS_RASTER_URL
                else:
                    url = self.WMS_VECTOR_URL

                item = DataItem(
                    item_id=layer['id'],
                    title=layer['title'],
                    source=layer['source'],
                    data_type=layer['type'],
                    territory=layer['territory'],
                    scale=layer.get('scale', 'france'),
                    crs=layer.get('crs', 'EPSG:4326'),
                    date=layer.get('date', '2025'),
                    url=url,
                    service_type=layer['service_type'],
                    extra={
                        'layer_name': layer['layer_name'],
                        'wms_url': url if layer['type'] == 'wms' else None,
                        'wfs_url': url if layer['type'] == 'wfs' else None,
                        'format': 'Flux ' + layer['service_type'],
                        'category': cat,
                        'date': layer.get('date', '2025')
                    }
                )
                results.append(item)

        return results
