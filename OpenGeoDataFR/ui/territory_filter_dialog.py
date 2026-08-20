# -*- coding: utf-8 -*-
"""
Dialogue interactif de filtrage territorial avancé en cascade pour OpenGeoData France.
Permet de filtrer progressivement par :
1. Région (ex: Hauts-de-France)
2. Département (filtre selon la région)
3. EPCI / Intercommunalité (filtre selon le département)
4. Communes (sélection unique ou multiple avec cases à cocher)
Compatible 100% avec QGIS 3 (PyQt5) et QGIS 4 (PyQt6).
"""

import urllib.request
import urllib.parse
import json
import ssl
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QListWidget, QListWidgetItem, QRadioButton,
    QGroupBox, QDialogButtonBox, QMessageBox
)
from qgis.PyQt.QtCore import Qt
from . import qt_compat
from ..utils.ssl_helper import fetch_url_bytes


class TerritoryFilterDialog(QDialog):
    """Fenêtre modale interactive pour la sélection et le filtrage en cascade des territoires français."""

    GEO_API_URL = "https://geo.api.gouv.fr"

    REGIONS_FRANCE = [
        ("11", "Île-de-France"), ("24", "Centre-Val de Loire"), ("27", "Bourgogne-Franche-Comté"),
        ("28", "Normandie"), ("32", "Hauts-de-France"), ("44", "Grand Est"),
        ("52", "Pays de la Loire"), ("53", "Bretagne"), ("75", "Nouvelle-Aquitaine"),
        ("76", "Occitanie"), ("84", "Auvergne-Rhône-Alpes"), ("93", "Provence-Alpes-Côte d'Azur"),
        ("94", "Corse"), ("01", "Guadeloupe"), ("02", "Martinique"), ("03", "Guyane"),
        ("04", "La Réunion"), ("06", "Mayotte")
    ]

    DEPARTEMENTS_ALL = [
        ("01", "Ain", "84"), ("02", "Aisne", "32"), ("03", "Allier", "84"), ("04", "Alpes-de-Haute-Provence", "93"),
        ("05", "Hautes-Alpes", "93"), ("06", "Alpes-Maritimes", "93"), ("07", "Ardèche", "84"), ("08", "Ardennes", "44"),
        ("09", "Ariège", "76"), ("10", "Aube", "44"), ("11", "Aude", "76"), ("12", "Aveyron", "76"), ("13", "Bouches-du-Rhône", "93"),
        ("14", "Calvados", "28"), ("15", "Cantal", "84"), ("16", "Charente", "75"), ("17", "Charente-Maritime", "75"),
        ("18", "Cher", "24"), ("19", "Corrèze", "75"), ("2A", "Corse-du-Sud", "94"), ("2B", "Haute-Corse", "94"),
        ("21", "Côte-d'Or", "27"), ("22", "Côtes-d'Armor", "53"), ("23", "Creuse", "75"), ("24", "Dordogne", "75"),
        ("25", "Doubs", "27"), ("26", "Drôme", "84"), ("27", "Eure", "28"), ("28", "Eure-et-Loir", "24"), ("29", "Finistère", "53"),
        ("30", "Gard", "76"), ("31", "Haute-Garonne", "76"), ("32", "Gers", "76"), ("33", "Gironde", "75"), ("34", "Hérault", "76"),
        ("35", "Ille-et-Vilaine", "53"), ("36", "Indre", "24"), ("37", "Indre-et-Loire", "24"), ("38", "Isère", "84"),
        ("39", "Jura", "27"), ("40", "Landes", "75"), ("41", "Loir-et-Cher", "24"), ("42", "Loire", "84"), ("43", "Haute-Loire", "84"),
        ("44", "Loire-Atlantique", "52"), ("45", "Loiret", "24"), ("46", "Lot", "76"), ("47", "Lot-et-Garonne", "75"),
        ("48", "Lozère", "76"), ("49", "Maine-et-Loire", "52"), ("50", "Manche", "28"), ("51", "Marne", "44"),
        ("52", "Haute-Marne", "44"), ("53", "Mayenne", "52"), ("54", "Meurthe-et-Moselle", "44"), ("55", "Meuse", "44"),
        ("56", "Morbihan", "53"), ("57", "Moselle", "44"), ("58", "Nièvre", "27"), ("59", "Nord", "32"), ("60", "Oise", "32"),
        ("61", "Orne", "28"), ("62", "Pas-de-Calais", "32"), ("63", "Puy-de-Dôme", "84"), ("64", "Pyrénées-Atlantiques", "75"),
        ("65", "Hautes-Pyrénées", "76"), ("66", "Pyrénées-Orientales", "76"), ("67", "Bas-Rhin", "44"),
        ("68", "Haut-Rhin", "44"), ("69", "Rhône", "84"), ("70", "Haute-Saône", "27"), ("71", "Saône-et-Loire", "27"),
        ("72", "Sarthe", "52"), ("73", "Savoie", "84"), ("74", "Haute-Savoie", "84"), ("75", "Paris", "11"),
        ("76", "Seine-Maritime", "28"), ("77", "Seine-et-Marne", "11"), ("78", "Yvelines", "11"), ("79", "Deux-Sèvres", "75"),
        ("80", "Somme", "32"), ("81", "Tarn", "76"), ("82", "Tarn-et-Garonne", "76"), ("83", "Var", "93"), ("84", "Vaucluse", "93"),
        ("85", "Vendée", "52"), ("86", "Vienne", "75"), ("87", "Haute-Vienne", "75"), ("88", "Vosges", "44"),
        ("89", "Yonne", "27"), ("90", "Territoire de Belfort", "27"), ("91", "Essonne", "11"), ("92", "Hauts-de-Seine", "11"),
        ("93", "Seine-Saint-Denis", "11"), ("94", "Val-de-Marne", "11"), ("95", "Val-d'Oise", "11"),
        ("971", "Guadeloupe", "01"), ("972", "Martinique", "02"), ("973", "Guyane", "03"),
        ("974", "La Réunion", "04"), ("976", "Mayotte", "06")
    ]

    def __init__(self, layer_title="Couche géographique", parent=None):
        super().__init__(parent)
        self.layer_title = layer_title
        self.setWindowTitle(f"Sélection Territorial & Périmètre - {layer_title}")
        self.resize(540, 520)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        lbl_info = QLabel(f"<b>Périmètre d'importation pour :</b> {self.layer_title}<br>"
                          "<i>Sélectionnez le niveau géographique souhaité pour limiter le téléchargement.</i>")
        lbl_info.setWordWrap(True)
        layout.addWidget(lbl_info)

        # 1. Option Radio National vs Territoire
        self.rad_national = QRadioButton("Importer toute la France (Sans filtre)")
        self.rad_territorial = QRadioButton("Filtrer par Région -> Département -> EPCI -> Commune(s)")
        self.rad_national.setChecked(True)
        self.rad_national.toggled.connect(self._on_radio_changed)

        layout.addWidget(self.rad_national)
        layout.addWidget(self.rad_territorial)

        # 2. Groupe de sélection en cascade
        self.group_cascade = QGroupBox("Sélection Territorial en Cascade")
        cascade_layout = QVBoxLayout(self.group_cascade)
        cascade_layout.setSpacing(8)

        # Région
        row_reg = QHBoxLayout()
        lbl_reg = QLabel("1. Région :")
        lbl_reg.setFixedWidth(110)
        row_reg.addWidget(lbl_reg)
        self.cmb_regions = QComboBox()
        self.cmb_regions.addItem("--- Toutes les Régions ---", "")
        for code, nom in self.REGIONS_FRANCE:
            self.cmb_regions.addItem(f"{nom} ({code})", code)
        self.cmb_regions.currentIndexChanged.connect(self._on_region_changed)
        row_reg.addWidget(self.cmb_regions)
        cascade_layout.addLayout(row_reg)

        # Département
        row_dep = QHBoxLayout()
        lbl_dep = QLabel("2. Département :")
        lbl_dep.setFixedWidth(110)
        row_dep.addWidget(lbl_dep)
        self.cmb_departements = QComboBox()
        self.cmb_departements.addItem("--- Tous les Départements ---", "")
        self.cmb_departements.currentIndexChanged.connect(self._on_dept_changed)
        row_dep.addWidget(self.cmb_departements)
        cascade_layout.addLayout(row_dep)

        # EPCI
        row_epci = QHBoxLayout()
        lbl_epci = QLabel("3. EPCI / Interco :")
        lbl_epci.setFixedWidth(110)
        row_epci.addWidget(lbl_epci)
        self.cmb_epcis = QComboBox()
        self.cmb_epcis.addItem("--- Tous les EPCI ---", "")
        self.cmb_epcis.currentIndexChanged.connect(self._on_epci_changed)
        row_epci.addWidget(self.cmb_epcis)
        cascade_layout.addLayout(row_epci)

        # Communes (Sélection Multiple avec cases à cocher)
        cascade_layout.addWidget(QLabel("4. Commune(s) (Sélectionnez une ou plusieurs communes) :"))
        
        commune_actions = QHBoxLayout()
        self.txt_filter_communes = QLineEdit()
        self.txt_filter_communes.setPlaceholderText("Rechercher une commune...")
        self.txt_filter_communes.textChanged.connect(self._filter_communes_list)
        commune_actions.addWidget(self.txt_filter_communes)

        btn_check_all = QPushButton("Tout cocher")
        btn_check_all.clicked.connect(lambda: self._set_all_communes_checked(True))
        commune_actions.addWidget(btn_check_all)

        btn_uncheck_all = QPushButton("Tout décocher")
        btn_uncheck_all.clicked.connect(lambda: self._set_all_communes_checked(False))
        commune_actions.addWidget(btn_uncheck_all)
        cascade_layout.addLayout(commune_actions)

        self.list_communes = QListWidget()
        cascade_layout.addWidget(self.list_communes)

        layout.addWidget(self.group_cascade)

        # Boutons Ok / Annuler (Compatibilité PyQt5 / PyQt6)
        button_box = QDialogButtonBox(qt_compat.ButtonOk | qt_compat.ButtonCancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.group_cascade.setEnabled(False)
        self._populate_departements()

    def _on_radio_changed(self):
        self.group_cascade.setEnabled(self.rad_territorial.isChecked())

    def _populate_departements(self, region_code=None):
        self.cmb_departements.blockSignals(True)
        self.cmb_departements.clear()
        self.cmb_departements.addItem("--- Tous les Départements ---", "")

        for code, nom, reg_id in self.DEPARTEMENTS_ALL:
            if not region_code or reg_id == region_code:
                self.cmb_departements.addItem(f"{code} - {nom}", code)

        self.cmb_departements.blockSignals(False)

    def _on_region_changed(self):
        region_code = self.cmb_regions.currentData()
        self._populate_departements(region_code)
        self._load_epcis()
        self._load_communes()

    def _on_dept_changed(self):
        self._load_epcis()
        self._load_communes()

    def _on_epci_changed(self):
        self._load_communes()

    def _load_epcis(self):
        dep_code = self.cmb_departements.currentData()
        self.cmb_epcis.blockSignals(True)
        self.cmb_epcis.clear()
        self.cmb_epcis.addItem("--- Tous les EPCI ---", "")

        if dep_code:
            url = f"{self.GEO_API_URL}/epcis?codeDepartement={dep_code}"
            try:
                content = fetch_url_bytes(url, timeout_ms=5000)
                epcis = json.loads(content.decode('utf-8'))
                for ep in sorted(epcis, key=lambda x: x.get('nom', '')):
                    code = ep.get('code', '')
                    nom = ep.get('nom', '')
                    self.cmb_epcis.addItem(f"{nom} ({code})", code)
            except Exception as e:
                print(f"[OpenGeoDataFR] Erreur chargement EPCI dept {dep_code}: {e}")

        self.cmb_epcis.blockSignals(False)

    def _load_communes(self):
        dep_code = self.cmb_departements.currentData()
        epci_code = self.cmb_epcis.currentData()
        region_code = self.cmb_regions.currentData()

        self.list_communes.clear()

        url = None
        if epci_code:
            url = f"{self.GEO_API_URL}/epcis/{epci_code}/communes?fields=nom,code"
        elif dep_code:
            url = f"{self.GEO_API_URL}/departements/{dep_code}/communes?fields=nom,code"
        elif region_code:
            url = f"{self.GEO_API_URL}/communes?codeRegion={region_code}&fields=nom,code"

        if not url:
            return

        try:
            content = fetch_url_bytes(url, timeout_ms=6000)
            communes = json.loads(content.decode('utf-8'))
            for c in sorted(communes, key=lambda x: x.get('nom', '')):
                nom = c.get('nom', '')
                code = c.get('code', '')
                item = QListWidgetItem(f"{nom} ({code})")
                item.setData(qt_compat.UserRole, code)
                item.setFlags(item.flags() | qt_compat.ItemIsUserCheckable)
                item.setCheckState(qt_compat.Unchecked)
                self.list_communes.addItem(item)
        except Exception as e:
            print(f"[OpenGeoDataFR] Erreur chargement communes ({url}): {e}")

    def _set_all_communes_checked(self, checked):
        state = qt_compat.Checked if checked else qt_compat.Unchecked
        for i in range(self.list_communes.count()):
            item = self.list_communes.item(i)
            if not item.isHidden():
                item.setCheckState(state)

    def _filter_communes_list(self, text):
        search_txt = text.strip().lower()
        for i in range(self.list_communes.count()):
            item = self.list_communes.item(i)
            item.setHidden(search_txt not in item.text().lower())

    def get_selected_filter(self):
        """
        Retourne la valeur du filtre territorial sélectionné (ex: '60057', '60057,60395', '60', '32').
        Priorité : Communes cochées > EPCI > Département > Région > France Entière.
        """
        if self.rad_national.isChecked():
            return ""

        # 1. Vérification des communes cochées (sélection multiple)
        checked_communes = []
        for i in range(self.list_communes.count()):
            item = self.list_communes.item(i)
            if item.checkState() == qt_compat.Checked:
                code = item.data(qt_compat.UserRole)
                if code:
                    checked_communes.append(code)

        if checked_communes:
            return ",".join(checked_communes)

        # 2. EPCI sélectionné
        epci_code = self.cmb_epcis.currentData()
        if epci_code:
            return epci_code

        # 3. Département sélectionné
        dep_code = self.cmb_departements.currentData()
        if dep_code:
            return dep_code

        # 4. Région sélectionnée
        region_code = self.cmb_regions.currentData()
        if region_code:
            return region_code

        return ""
