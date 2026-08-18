# -*- coding: utf-8 -*-
"""
Modèles de données pour OpenGeoData France.
Contient la classe générique DataItem et la classe spécialisée UrbanDocItem.
"""

class DataItem:
    """Représente un résultat de recherche unifié pour tout type de données (open data, cadastre, BAN, WMS/WFS)."""

    def __init__(self, item_id, title, source, data_type, territory="France", scale="france", crs="EPSG:4326", date="2025", url="", service_type="HTTP", extra=None):
        """
        :param item_id: Identifiant unique de la ressource
        :param title: Titre lisible pour l'utilisateur
        :param source: Nom du catalogue ou de la source (ex: 'data.gouv.fr', 'Cadastre PCI', 'BAN', 'GPU', 'GéoPlateforme')
        :param data_type: Type de donnée ('file_vector', 'file_raster', 'wms', 'wfs', 'table')
        :param territory: Portée ou périmètre territorial (ex: 'France', 'Oise', 'Beauvais')
        :param scale: Échelle géographique ('france', 'region', 'departement', 'epci', 'commune')
        :param crs: Système de coordonnées / projection d'origine (ex: 'EPSG:4326', 'EPSG:2154', 'EPSG:3857')
        :param date: Date de mise à jour / de diffusion de l'information (ex: '2025-01-15', '2024')
        :param url: URL de téléchargement ou d'accès au flux
        :param service_type: Type de service technique ('HTTP', 'WMS', 'WFS', 'API')
        :param extra: Dictionnaire facultatif de métadonnées complémentaires
        """
        self.id = str(item_id)
        self.title = title
        self.source = source
        self.data_type = data_type
        self.territory = territory
        self.scale = scale
        self.crs = crs if crs else "EPSG:4326"
        self.date = date if date else "2025"
        self.url = url
        self.service_type = service_type
        self.extra = extra if extra is not None else {}

    def __repr__(self):
        return f"<DataItem [{self.source}] {self.title} ({self.data_type}) - CRS:{self.crs} - Date:{self.date}>"


class UrbanDocItem(DataItem):
    """Spécialisation pour les documents d'urbanisme et SUP du Géoportail de l'urbanisme (GPU)."""

    def __init__(self, item_id, title, doc_type, territory="France", scale="commune", crs="EPSG:4326", date="2025", url="", service_type="GPU", wms_layers=None, wfs_layers=None, cql_filter=None, files=None, extra=None):
        super().__init__(
            item_id=item_id,
            title=title,
            source="Géoportail de l'urbanisme (GPU)",
            data_type="urban_doc",
            territory=territory,
            scale=scale,
            crs=crs,
            date=date,
            url=url,
            service_type=service_type,
            extra=extra
        )
        self.doc_type = doc_type
        self.wms_layers = wms_layers if wms_layers is not None else []
        self.wfs_layers = wfs_layers if wfs_layers is not None else []
        self.cql_filter = cql_filter
        self.files = files if files is not None else []
