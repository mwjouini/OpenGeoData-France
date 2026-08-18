# -*- coding: utf-8 -*-
"""
OpenGeoData France QGIS Plugin Init
"""

def classFactory(iface):
    """Factory function called by QGIS to instantiate the plugin.
    
    :param iface: QGIS Interface instance
    :type iface: QgsInterface
    """
    from .opengeodata_fr import OpenGeoDataFR
    return OpenGeoDataFR(iface)
