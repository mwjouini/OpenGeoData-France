# -*- coding: utf-8 -*-
"""
Service d'exportation des résultats de recherche et métadonnées d'OpenGeoData France.
Supporte l'export vers CSV (compatible Excel), JSON / GeoJSON.
"""

import os
import csv
import json


class ExportService:
    """Gestionnaire d'exportation des résultats de recherche."""

    @staticmethod
    def export_to_csv(items, output_filepath):
        """
        Exporte la liste des DataItem / UrbanDocItem vers un fichier CSV encodé en UTF-8-SIG (lisible sous Excel).
        """
        fieldnames = [
            'ID', 'Titre', 'Source', 'Type_Donnee', 'CRS_Origine',
            'Territoire', 'Echelle', 'Date_Mise_A_Jour', 'Type_Service', 'URL', 'Code_INSEE', 'Extra'
        ]

        with open(output_filepath, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f, delimiter=';', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(fieldnames)

            for item in items:
                code_insee = item.extra.get('code_insee', '') if hasattr(item, 'extra') and item.extra else ''
                extra_str = json.dumps(item.extra, ensure_ascii=False, default=str) if hasattr(item, 'extra') and item.extra else ''
                
                writer.writerow([
                    getattr(item, 'id', ''),
                    getattr(item, 'title', ''),
                    getattr(item, 'source', ''),
                    getattr(item, 'data_type', ''),
                    getattr(item, 'crs', 'EPSG:4326'),
                    getattr(item, 'territory', ''),
                    getattr(item, 'scale', ''),
                    getattr(item, 'date', '2025'),
                    getattr(item, 'service_type', ''),
                    getattr(item, 'url', ''),
                    code_insee,
                    extra_str
                ])

        return True, f"Fichier CSV exporté avec succès dans :\n{output_filepath}"

    @staticmethod
    def export_to_geojson(items, output_filepath):
        """
        Exporte la liste des résultats vers une collection GeoJSON.
        """
        features = []

        for item in items:
            props = {
                'id': getattr(item, 'id', ''),
                'title': getattr(item, 'title', ''),
                'source': getattr(item, 'source', ''),
                'data_type': getattr(item, 'data_type', ''),
                'crs_origine': getattr(item, 'crs', 'EPSG:4326'),
                'territory': getattr(item, 'territory', ''),
                'scale': getattr(item, 'scale', ''),
                'date_mise_a_jour': getattr(item, 'date', '2025'),
                'service_type': getattr(item, 'service_type', ''),
                'url': getattr(item, 'url', '')
            }

            if hasattr(item, 'extra') and item.extra:
                props.update({k: (v if isinstance(v, (str, int, float, bool, list, dict)) else str(v)) for k, v in item.extra.items()})

            geom = None
            if hasattr(item, 'extra') and item.extra:
                raw_lat = item.extra.get('lat') or item.extra.get('latitude')
                raw_lon = item.extra.get('lon') or item.extra.get('longitude')
                if raw_lat and raw_lon:
                    try:
                        clean_lat = float(str(raw_lat).replace(',', '.'))
                        clean_lon = float(str(raw_lon).replace(',', '.'))
                        geom = {
                            "type": "Point",
                            "coordinates": [clean_lon, clean_lat]
                        }
                    except (ValueError, TypeError):
                        geom = None

            features.append({
                "type": "Feature",
                "geometry": geom,
                "properties": props
            })

        geojson_payload = {
            "type": "FeatureCollection",
            "name": "Export_OpenGeoDataFR",
            "features": features
        }

        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(geojson_payload, f, ensure_ascii=False, indent=2, default=str)

        return True, f"Fichier GeoJSON exporté avec succès dans :\n{output_filepath}"
