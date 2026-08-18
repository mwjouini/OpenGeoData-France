# -*- coding: utf-8 -*-
"""
Dialogue modale interactif de prévisualisation et de configuration d'importation de fichiers CSV/Excel.
Permet de choisir le délimiteur, l'encodage, les champs géométriques X/Y (Lon/Lat) ou WKT
et offre une prévisualisation en direct de la table d'attributs.
Compatible 100% avec QGIS 3 (PyQt5) et QGIS 4 (PyQt6).
"""

import os
import csv
import urllib.parse
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QRadioButton, QTableWidget, QTableWidgetItem, QGroupBox,
    QDialogButtonBox, QMessageBox, QHeaderView
)
from qgis.PyQt.QtCore import Qt
from . import qt_compat


class CSVImportDialog(QDialog):
    """Dialogue de configuration et prévisualisation avant import d'un fichier CSV dans QGIS."""

    DELIMITERS = [
        ("Point-virgule (;)", ";"),
        ("Virgule (,)", ","),
        ("Tabulation (Tab)", "\t"),
        ("Barre verticale (|)", "|"),
        ("Deux-points (:)", ":")
    ]

    ENCODINGS = [
        ("UTF-8 / UTF-8-SIG (Standard)", "utf-8-sig"),
        ("ISO-8859-1 (Latin-1 Europe)", "iso-8859-1"),
        ("Windows-1252 (Excel FR)", "cp1252")
    ]

    def __init__(self, filepath, layer_title="Couche CSV", parent=None):
        super().__init__(parent)
        self.filepath = filepath
        self.layer_title = layer_title
        self.selected_uri = None
        self.headers = []

        self.setWindowTitle(f"Import & Prévisualisation CSV - {os.path.basename(filepath)}")
        self.resize(760, 600)

        self._setup_ui()
        self._auto_detect_params()
        self._update_preview()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        lbl_info = QLabel(f"<b>Fichier CSV :</b> {self.filepath}")
        lbl_info.setWordWrap(True)
        layout.addWidget(lbl_info)

        # Section 1: Délimiteur et Encodage
        format_group = QGroupBox("Format de Fichier & Séparateur de colonnes")
        format_layout = QHBoxLayout(format_group)

        lbl_delim = QLabel("Séparateur :")
        format_layout.addWidget(lbl_delim)

        self.cmb_delimiter = QComboBox()
        for label, val in self.DELIMITERS:
            self.cmb_delimiter.addItem(label, val)
        self.cmb_delimiter.currentIndexChanged.connect(self._update_preview)
        format_layout.addWidget(self.cmb_delimiter)

        lbl_enc = QLabel("Encodage :")
        format_layout.addWidget(lbl_enc)

        self.cmb_encoding = QComboBox()
        for label, val in self.ENCODINGS:
            self.cmb_encoding.addItem(label, val)
        self.cmb_encoding.currentIndexChanged.connect(self._update_preview)
        format_layout.addWidget(self.cmb_encoding)

        layout.addWidget(format_group)

        # Section 2: Définition de la Géométrie
        geom_group = QGroupBox("Définition de la Géométrie")
        geom_layout = QVBoxLayout(geom_group)

        # Option Point X/Y
        point_row = QHBoxLayout()
        self.rad_point = QRadioButton("Point (Coordonnées X / Y ou Longitude / Latitude)")
        self.rad_point.setChecked(True)
        self.rad_point.toggled.connect(self._on_geom_type_changed)
        point_row.addWidget(self.rad_point)

        lbl_x = QLabel("Champ X (Lon) :")
        point_row.addWidget(lbl_x)
        self.cmb_field_x = QComboBox()
        point_row.addWidget(self.cmb_field_x)

        lbl_y = QLabel("Champ Y (Lat) :")
        point_row.addWidget(lbl_y)
        self.cmb_field_y = QComboBox()
        point_row.addWidget(self.cmb_field_y)
        geom_layout.addLayout(point_row)

        # Option WKT
        wkt_row = QHBoxLayout()
        self.rad_wkt = QRadioButton("Well Known Text (WKT)")
        self.rad_wkt.toggled.connect(self._on_geom_type_changed)
        wkt_row.addWidget(self.rad_wkt)

        lbl_wkt = QLabel("Champ WKT :")
        wkt_row.addWidget(lbl_wkt)
        self.cmb_field_wkt = QComboBox()
        wkt_row.addWidget(self.cmb_field_wkt)
        wkt_row.addStretch()
        geom_layout.addLayout(wkt_row)

        # Option Pas de Géométrie (Table seule)
        self.rad_none = QRadioButton("Pas de géométrie (Table attributaire seule)")
        self.rad_none.toggled.connect(self._on_geom_type_changed)
        geom_layout.addWidget(self.rad_none)

        layout.addWidget(geom_group)

        # Section 3: Échantillon de Données (Prévisualisation en Direct)
        preview_group = QGroupBox("Échantillon de Données (Prévisualisation en direct)")
        preview_layout = QVBoxLayout(preview_group)

        self.preview_table = QTableWidget()
        self.preview_table.setEditTriggers(qt_compat.NoEditTriggers)
        self.preview_table.horizontalHeader().setSectionResizeMode(qt_compat.HeaderInteractive)
        preview_layout.addWidget(self.preview_table)

        layout.addWidget(preview_group)

        # Boutons Ok / Annuler (Compatibilité PyQt5 / PyQt6)
        button_box = QDialogButtonBox(qt_compat.ButtonOk | qt_compat.ButtonCancel)
        button_box.accepted.connect(self.on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _auto_detect_params(self):
        """Détecte automatiquement le séparateur et les colonnes spatiales."""
        delimiter = ";"
        try:
            with open(self.filepath, 'r', encoding='utf-8-sig', errors='replace') as f:
                first_line = f.readline()
                if first_line.count(';') > first_line.count(','):
                    delimiter = ";"
                elif first_line.count('\t') > first_line.count(','):
                    delimiter = "\t"
                elif first_line.count('|') > first_line.count(','):
                    delimiter = "|"
                else:
                    delimiter = ","
        except Exception:
            pass

        idx = self.cmb_delimiter.findData(delimiter)
        if idx >= 0:
            self.cmb_delimiter.setCurrentIndex(idx)

    def _on_geom_type_changed(self):
        self.cmb_field_x.setEnabled(self.rad_point.isChecked())
        self.cmb_field_y.setEnabled(self.rad_point.isChecked())
        self.cmb_field_wkt.setEnabled(self.rad_wkt.isChecked())

    def _update_preview(self):
        """Met à jour l'échantillon du tableau et remplit les listes déroulantes de colonnes."""
        delimiter = self.cmb_delimiter.currentData()
        encoding = self.cmb_encoding.currentData()

        self.preview_table.setRowCount(0)
        self.preview_table.setColumnCount(0)

        rows = []
        try:
            with open(self.filepath, 'r', encoding=encoding, errors='replace') as f:
                reader = csv.reader(f, delimiter=delimiter)
                for i, row in enumerate(reader):
                    if i == 0:
                        self.headers = [h.strip() for h in row]
                    else:
                        rows.append(row)
                    if i >= 30:
                        break
        except Exception as e:
            print(f"[OpenGeoDataFR] Erreur lecture preview CSV: {e}")
            return

        if not self.headers:
            return

        curr_x = self.cmb_field_x.currentText()
        curr_y = self.cmb_field_y.currentText()

        self.cmb_field_x.blockSignals(True)
        self.cmb_field_y.blockSignals(True)
        self.cmb_field_wkt.blockSignals(True)

        self.cmb_field_x.clear()
        self.cmb_field_y.clear()
        self.cmb_field_wkt.clear()

        for h in self.headers:
            self.cmb_field_x.addItem(h)
            self.cmb_field_y.addItem(h)
            self.cmb_field_wkt.addItem(h)

        # Auto-sélection intelligente des colonnes géométriques
        for h in self.headers:
            hl = h.lower()
            if hl in ('lon', 'lng', 'longitude', 'x', 'x_coord'):
                self.cmb_field_x.setCurrentText(h)
            elif hl in ('lat', 'latitude', 'y', 'y_coord'):
                self.cmb_field_y.setCurrentText(h)
            elif hl in ('wkt', 'geom', 'geometry', 'the_geom'):
                self.cmb_field_wkt.setCurrentText(h)
                self.rad_wkt.setChecked(True)

        self.cmb_field_x.blockSignals(False)
        self.cmb_field_y.blockSignals(False)
        self.cmb_field_wkt.blockSignals(False)

        # Remplissage du tableau d'échantillon
        self.preview_table.setColumnCount(len(self.headers))
        self.preview_table.setHorizontalHeaderLabels(self.headers)
        self.preview_table.setRowCount(len(rows))

        for r_idx, row in enumerate(rows):
            for c_idx, val in enumerate(row):
                if c_idx < len(self.headers):
                    item = QTableWidgetItem(val)
                    self.preview_table.setItem(r_idx, c_idx, item)

    def on_accept(self):
        """Génère l'URI QGIS délimitée finale exacte pour le fournisseur QGIS delimitedtext."""
        delimiter = self.cmb_delimiter.currentData()
        encoding = self.cmb_encoding.currentData()

        escaped_filepath = self.filepath.replace('\\', '/')

        # Formatage propre du délimiteur pour le driver delimitedtext de QGIS (encodage URL requis)
        if delimiter == "\t":
            raw_delim = "\\t"
        else:
            raw_delim = delimiter

        encoded_delim = urllib.parse.quote(raw_delim)

        if self.rad_point.isChecked():
            x_field = urllib.parse.quote(self.cmb_field_x.currentText())
            y_field = urllib.parse.quote(self.cmb_field_y.currentText())
            if not x_field or not y_field:
                QMessageBox.warning(self, "Erreur Géométrie", "Veuillez sélectionner les colonnes X et Y.")
                return
            self.selected_uri = f"file:///{escaped_filepath}?delimiter={encoded_delim}&useHeader=yes&xField={x_field}&yField={y_field}&crs=EPSG:4326&encoding={encoding}"

        elif self.rad_wkt.isChecked():
            wkt_field = urllib.parse.quote(self.cmb_field_wkt.currentText())
            if not wkt_field:
                QMessageBox.warning(self, "Erreur Géométrie", "Veuillez sélectionner la colonne WKT.")
                return
            self.selected_uri = f"file:///{escaped_filepath}?delimiter={encoded_delim}&useHeader=yes&wktField={wkt_field}&crs=EPSG:4326&encoding={encoding}"

        else:
            self.selected_uri = f"file:///{escaped_filepath}?delimiter={encoded_delim}&useHeader=yes&type=csv&geometry=none&encoding={encoding}"

        self.accept()
