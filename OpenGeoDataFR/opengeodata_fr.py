# -*- coding: utf-8 -*-
"""
Classe principale de l'extension QGIS OpenGeoData France.
Gère l'intégration dans les menus QGIS, la barre d'outils et le cycle de vie de la fenêtre flottante.
Compatible QGIS 3 (PyQt5) et QGIS 4 (PyQt6).
"""

import os
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon

from .ui.opengeodata_fr_dock import OpenGeoDataFRDock
from .ui import qt_compat


class OpenGeoDataFR:
    """Classe principale du plugin OpenGeoData France."""

    def __init__(self, iface):
        """
        :param iface: Interface QGIS (QgsInterface)
        """
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)

        self.action = None
        self.dock = None

    def initGui(self):
        """Méthode appelée par QGIS à l'activation du plugin pour créer le menu et les boutons."""
        icon_path = os.path.join(self.plugin_dir, "icon.png")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(self.plugin_dir, "resources", "icon.png")

        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
        else:
            icon = QIcon()

        self.action = QAction(icon, "OpenGeoData France", self.iface.mainWindow())
        self.action.setObjectName("actionOpenGeoDataFR")
        self.action.setToolTip("Rechercher et importer des données géographiques françaises (data.gouv.fr, Cadastre, BAN, GPU, GéoPlateforme)")
        self.action.triggered.connect(self.run)

        # Ajout au menu Web, Vecteur et à la barre d'outils Web de QGIS
        self.iface.addWebToolBarIcon(self.action)
        self.iface.addPluginToWebMenu("OpenGeoData France", self.action)
        self.iface.addPluginToVectorMenu("OpenGeoData France", self.action)

    def unload(self):
        """Méthode appelée par QGIS au désabonnement / rechargement du plugin."""
        if self.action:
            self.iface.removePluginVectorMenu("OpenGeoData France", self.action)
            self.iface.removePluginWebMenu("OpenGeoData France", self.action)
            self.iface.removeWebToolBarIcon(self.action)
            del self.action
            self.action = None

        if self.dock:
            if hasattr(self.dock, 'cleanup'):
                try:
                    self.dock.cleanup()
                except Exception as err:
                    print(f"[OpenGeoDataFR] Nettoyage dock ignoré: {err}")
            self.iface.removeDockWidget(self.dock)
            self.dock.deleteLater()
            self.dock = None

    def run(self):
        """Affiche l'interface OpenGeoData France sous forme de fenêtre flottante grande et claire."""
        if not self.dock:
            self.dock = OpenGeoDataFRDock(self.iface, self.iface.mainWindow())
            self.iface.addDockWidget(qt_compat.RightDockWidgetArea, self.dock)
        
        # Passage systématique en fenêtre flottante spacieuse (920x680)
        self.dock.setFloating(True)
        self.dock.resize(920, 680)
        self.dock.show()
        self.dock.raise_()
        self.dock.activateWindow()
