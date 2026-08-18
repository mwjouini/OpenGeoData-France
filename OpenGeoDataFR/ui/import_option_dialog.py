# -*- coding: utf-8 -*-
"""
Dialogue de confirmation préalable au chargement d'une couche géographique.
Permet de choisir entre l'import découpé selon un territoire et l'import complet.
"""

from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QWidget
)
from qgis.PyQt.QtCore import Qt
from .territory_filter_dialog import TerritoryFilterDialog
from . import qt_compat


class ImportFilterOptionDialog(QDialog):
    """Dialogue sobre et professionnel de sélection du mode d'importation."""

    def __init__(self, item, current_territory="", as_wms=False, parent=None):
        super().__init__(parent)
        self.item = item
        self.selected_territory = (current_territory or "").strip()
        self.as_wms = as_wms
        self.import_mode = "full"

        self.setWindowTitle(f"Options d'importation - {item.title}")
        self.resize(500, 230)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # 1. Résumé de la couche
        header_frame = QFrame()
        header_frame.setFrameShape(QFrame.StyledPanel)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(8, 8, 8, 8)
        header_layout.setSpacing(3)

        lbl_layer = QLabel(f"<b>{self.item.title}</b>")
        lbl_layer.setWordWrap(True)
        header_layout.addWidget(lbl_layer)

        source_fmt = f"Source : {self.item.source}  |  Format : {getattr(self.item, 'service_type', '') or self.item.data_type.upper()}"
        lbl_source = QLabel(source_fmt)
        lbl_source.setStyleSheet("color: #666; font-size: 11px;")
        header_layout.addWidget(lbl_source)

        terr_display = self.selected_territory if self.selected_territory else "Aucun filtre (France entière)"
        lbl_terr = QLabel(f"Territoire sélectionné : <b>{terr_display}</b>")
        lbl_terr.setWordWrap(True)
        lbl_terr.setStyleSheet("font-size: 11px;")
        header_layout.addWidget(lbl_terr)

        layout.addWidget(header_frame)

        # 2. Question
        lbl_q = QLabel("Mode d'importation :")
        lbl_q.setStyleSheet("font-weight: bold;")
        layout.addWidget(lbl_q)

        # 3. Actions
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(6)

        self.btn_filter = QPushButton("Importer avec découpage territorial")
        self.btn_filter.setToolTip("Découpe géométriquement et filtre les données sur l'emprise du territoire sélectionné")
        self.btn_filter.setStyleSheet("padding: 7px; text-align: left; font-weight: bold;")
        self.btn_filter.clicked.connect(self.on_filter_clicked)
        actions_layout.addWidget(self.btn_filter)

        self.btn_full = QPushButton("Importer la couche entière (sans filtre)")
        self.btn_full.setToolTip("Charge le jeu de données complet sans aucun découpage territorial")
        self.btn_full.setStyleSheet("padding: 7px; text-align: left;")
        self.btn_full.clicked.connect(self.on_full_clicked)
        actions_layout.addWidget(self.btn_full)

        layout.addLayout(actions_layout)

        # 4. Annuler
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        btn_cancel = QPushButton("Annuler")
        btn_cancel.clicked.connect(self.reject)
        footer_layout.addWidget(btn_cancel)
        layout.addLayout(footer_layout)

    def on_filter_clicked(self):
        if not self.selected_territory:
            dlg = TerritoryFilterDialog(layer_title=self.item.title, parent=self)
            if qt_compat.exec_dialog(dlg) == qt_compat.DialogAccepted:
                self.selected_territory = dlg.get_selected_filter()
                if not self.selected_territory:
                    return
            else:
                return

        self.import_mode = "filter"
        self.accept()

    def on_full_clicked(self):
        self.import_mode = "full"
        self.selected_territory = ""
        self.accept()
