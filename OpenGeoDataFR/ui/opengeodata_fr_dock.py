# -*- coding: utf-8 -*-
"""
Dock Widget principal d'OpenGeoData France.
Offre une interface de recherche unifiée ultra-rapide (multithreadée),
de filtres par catégories thématiques (Admin, Cadastre, Urbanisme, Environnement, Risques, Énergie, Transport, Fonds IGN),
de filtres par échelles territoriales, de filtres par formats (Vectoriel, Tables CSV/Excel, WFS/WMS/WMTS),
de choix du CRS, d'importation filtrée (attributs + découpage géométrique spatial) et réprojetée dans QGIS,
d'autocomplétion / suggestions en temps réel, d'un volet d'inspection des métadonnées avec liens web officiels
et d'exportation des résultats (CSV/Excel, GeoJSON).
S'ouvre par défaut sous forme de fenêtre flottante claire, spacieuse et indépendante.
Compatible 100% avec QGIS 3 (PyQt5) et QGIS 4 (PyQt6).
"""

import os
import concurrent.futures
from qgis.PyQt.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QCheckBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QProgressBar, QMessageBox, QComboBox, QFileDialog, QDialog, QScrollArea, QFrame,
    QCompleter, QApplication, QSplitter, QTextEdit, QButtonGroup
)
from qgis.PyQt.QtCore import Qt, QThread, pyqtSignal, QMutex, QUrl
from qgis.PyQt.QtGui import QIcon, QPixmap, QFont, QDesktopServices, QColor

from ..clients.data_gouv_client import DataGouvClient
from ..clients.cadastre_client import CadastreClient
from ..clients.ban_client import BanClient
from ..clients.gpu_client import GPUClient
from ..clients.geoplateforme_client import GeoplateformeClient
from ..services.import_manager import ImportManager
from ..services.preset_library import PresetLibrary
from ..services.export_service import ExportService
from ..services.nlp_search_engine import NLPSearchEngine
from qgis.core import (
    QgsProject,
    QgsRectangle,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform
)
from .territory_filter_dialog import TerritoryFilterDialog
from .import_option_dialog import ImportFilterOptionDialog
from . import qt_compat


# Cache mémoire statique thread-safe pour un retour de recherche instantané (0 ms)
SEARCH_MEMORY_CACHE = {}
CACHE_MUTEX = QMutex()

# Dictionnaire riche de suggestions d'autocomplétion en temps réel
SEARCH_SUGGESTIONS = [
    # Couches administratives & Presets
    "Communes de France (Admin Express)",
    "Départements de France (Admin Express)",
    "Régions de France (Admin Express)",
    "EPCI Intercommunalités de France",
    "Arrondissements départementaux",
    "Cantons électoraux",
    "Limites administratives ADMIN EXPRESS IGN",
    
    # Cadastre PCI
    "Parcelles cadastrales (PCI Cadastre)",
    "Feuilles cadastrales",
    "Sections cadastrales",
    "Bâtiments du Cadastre",
    "Lieux-dits Cadastre",
    "Subdivisions fiscales Cadastre",
    "Plan Cadastral WMS Parcellaire Express",
    
    # Urbanisme (GPU)
    "Carte nationale des documents d'urbanisme (GPU)",
    "PLU Beauvais",
    "PLU Méru",
    "PLUi Beauvaisis",
    "PLU Paris",
    "PLU Lyon",
    "PLU Marseille",
    "Document d'urbanisme GPU",
    "Zones d'urbanisme (ZONE_URBA)",
    "Prescriptions d'urbanisme",
    "Servitudes d'utilité publique (SUP)",
    
    # Adresses BAN
    "Base Adresse Nationale (BAN)",
    "Adresses Oise (60)",
    "Adresses Beauvais (60000)",
    "Adresses Méru (60110)",
    "Adresses Paris (75)",
    
    # Données INSEE & SIRENE
    "Contours IRIS INSEE",
    "Code Officiel Géographique COG INSEE",
    "Base SIRENE Entreprises INSEE",
    "Population et Recensement INSEE",

    # Environnement, Eau & Biodiversité
    "ZNIEFF Type 1 (INPN / OFB)",
    "ZNIEFF Type 2 (INPN / OFB)",
    "Réseau Natura 2000 (SIC/ZSC/ZPS)",
    "Espaces Naturels Sensibles (ENS)",
    "Réseau hydrographique BD TOPAGE",
    "Cours d'eau et rivières IGN",
    "Surfaces en eau et lacs",
    "Zones de végétation et Forêts",

    # Risques majeurs & Géologie
    "PPRN Plan de prévention des risques (Géorisques)",
    "Carte géologique de la France 1/50 000 BRGM",
    "Aléa Retrait-Gonflement des Argiles RGA",
    "Cavités souterraines et Mouvements de terrain",
    "Territoires à Risque Important d'Inondation TRI",

    # Énergie & Mobilités
    "Bornes de recharge véhicules électriques IRVE",
    "Installations de production EnR Électricité",
    "Réseau de transport d'électricité RTE",
    "Aménagements cyclables et véloroutes BNLC",
    "Réseau Ferré National et Gares SNCF",
    "Réseau Routier National et Autoroutes",

    # Fonds IGN & Imagerie
    "Plan IGN V2 Multi-échelles",
    "Photographies aériennes Ortho HR IGN",
    "Cartes Topographiques SCAN 25 IGN",
    "Relief ombré et MNT RGE ALTI IGN",
    "Courbes de niveau IGN",
    "Fond de carte OpenStreetMap France",

    # Départements & Villes
    "60 - Oise", "59 - Nord", "80 - Somme", "75 - Paris", "13 - Bouches-du-Rhône",
    "69 - Rhône", "33 - Gironde", "44 - Loire-Atlantique", "31 - Haute-Garonne", "06 - Alpes-Maritimes",
    "Beauvais (60000)", "Méru (60110)", "Compiègne (60200)", "Creil (60100)", "Senlis (60300)",
    "Paris (75000)", "Lyon (69000)", "Marseille (13000)", "Lille (59000)", "Toulouse (31000)",
    "Bordeaux (33000)", "Nantes (44000)", "Strasbourg (67000)", "Rennes (35000)", "Montpellier (34000)"
]


class SearchWorker(QThread):
    """Worker multithreadé haute performance exécutant les requêtes API en parallèle."""
    
    results_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, query, active_sources, scale_filter="all", territory_filter=""):
        super().__init__()
        self.query = query
        self.active_sources = active_sources
        self.scale_filter = scale_filter.lower()
        self.territory_filter = territory_filter.lower().strip()

        self.data_gouv_client = DataGouvClient(timeout=5)
        self.cadastre_client = CadastreClient(timeout=4)
        self.ban_client = BanClient(timeout=4)
        self.gpu_client = GPUClient(timeout=4)
        self.geoplateforme_client = GeoplateformeClient()

    def run(self):
        cache_key = f"{self.query}|{self.territory_filter}|{sorted(self.active_sources.items())}"
        
        CACHE_MUTEX.lock()
        cached = SEARCH_MEMORY_CACHE.get(cache_key)
        CACHE_MUTEX.unlock()

        if cached is not None:
            self.results_ready.emit(cached)
            return

        all_results = []
        tasks = []

        try:
            search_term = self.query if self.query else self.territory_filter

            if self.active_sources.get('admin', True):
                tasks.append(lambda: self.data_gouv_client.search(search_term))
                tasks.append(lambda: self.cadastre_client.search(search_term))

            if self.active_sources.get('gpu', True):
                tasks.append(lambda: self.gpu_client.search(search_term))

            if self.active_sources.get('ban', True):
                tasks.append(lambda: self.ban_client.search(search_term))

            if self.active_sources.get('geopf', True):
                tasks.append(lambda: self.geoplateforme_client.search(search_term))

            with concurrent.futures.ThreadPoolExecutor(max_workers=len(tasks) or 1) as executor:
                futures = [executor.submit(t) for t in tasks]
                for f in concurrent.futures.as_completed(futures):
                    try:
                        res = f.result()
                        if res:
                            all_results.extend(res)
                    except Exception as ex:
                        print(f"[OpenGeoDataFR Worker] Task error: {ex}")

            CACHE_MUTEX.lock()
            SEARCH_MEMORY_CACHE[cache_key] = all_results
            CACHE_MUTEX.unlock()

            self.results_ready.emit(all_results)

        except Exception as e:
            self.error_occurred.emit(str(e))


class ImportWorker(QThread):
    """Worker multithreadé exécutant l'importation et le téléchargement en arrière-plan sans JAMAIS figer QGIS."""

    import_finished = pyqtSignal(bool, str, object)
    progress_updated = pyqtSignal(str)

    def __init__(self, import_manager, item, as_wms, target_crs, territory_filter):
        super().__init__()
        self.import_manager = import_manager
        self.item = item
        self.as_wms = as_wms
        self.target_crs = target_crs
        self.territory_filter = territory_filter

    def run(self):
        try:
            def report_progress(msg):
                self.progress_updated.emit(msg)

            success, msg = self.import_manager.import_item(
                item=self.item,
                as_wms=self.as_wms,
                target_crs=self.target_crs,
                territory_filter=self.territory_filter,
                progress_callback=report_progress
            )

            extent_info = None
            if success and self.territory_filter and str(self.territory_filter).lower() not in ("france", "toutes les échelles", "all"):
                try:
                    terr_geom, terr_crs_str = self.import_manager._get_territory_geometry(self.territory_filter)
                    if terr_geom and not terr_geom.isEmpty():
                        bb = terr_geom.boundingBox()
                        extent_info = (bb.xMinimum(), bb.yMinimum(), bb.xMaximum(), bb.yMaximum(), terr_crs_str)
                except Exception:
                    pass

            self.import_finished.emit(success, msg, extent_info)
        except Exception as e:
            self.import_finished.emit(False, f"Erreur lors de l'importation : {e}", None)


class OpenGeoDataFRDock(QDockWidget):
    """Dock Widget principal pour la recherche, la projection, l'export et l'import de données géographiques françaises."""

    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.import_manager = ImportManager()
        self.nlp_engine = NLPSearchEngine(all_presets=PresetLibrary.get_presets())
        self.last_nlp_res = None
        self.all_raw_results = []
        self.displayed_results = []
        self.current_selected_item = None
        self.search_worker = None
        self.import_worker = None
        self.active_category = "all"

        self.setWindowTitle("OpenGeoData France")
        self.setObjectName("OpenGeoDataFRDock")

        allowed_areas = qt_compat.LeftDockWidgetArea | qt_compat.RightDockWidgetArea | qt_compat.TopDockWidgetArea | qt_compat.BottomDockWidgetArea
        self.setAllowedAreas(allowed_areas)

        dock_features = qt_compat.DockWidgetClosable | qt_compat.DockWidgetMovable | qt_compat.DockWidgetFloatable
        self.setFeatures(dock_features)

        self.setFloating(True)
        self.resize(1020, 740)

        self._setup_ui()
        self._apply_stylesheet()
        self.show_all_presets()

    def _setup_ui(self):
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # 1. En-tête avec Logo Officiel et Titre
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        plugin_dir = os.path.dirname(os.path.dirname(__file__))
        logo_path = os.path.join(plugin_dir, "icon.png")
        if not os.path.exists(logo_path):
            logo_path = os.path.join(plugin_dir, "resources", "icon.png")

        lbl_logo = QLabel()
        if os.path.exists(logo_path):
            lbl_logo.setPixmap(QPixmap(logo_path).scaled(40, 40, qt_compat.KeepAspectRatio, qt_compat.SmoothTransformation))
        header_layout.addWidget(lbl_logo)

        header_title_layout = QVBoxLayout()
        lbl_title = QLabel("OpenGeoData France")
        lbl_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        lbl_subtitle = QLabel("Accès direct aux référentiels IGN, Cadastre, GPU et data.gouv.fr")
        lbl_subtitle.setStyleSheet("font-size: 11px; color: #555555;")
        header_title_layout.addWidget(lbl_title)
        header_title_layout.addWidget(lbl_subtitle)
        header_layout.addLayout(header_title_layout)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # 2. Barre de recherche textuelle globale
        search_layout = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Rechercher un jeu de données, une commune, un département ou un thème...")
        self.txt_search.setClearButtonEnabled(True)
        self.txt_search.returnPressed.connect(self.on_search_clicked)

        self.completer = QCompleter(SEARCH_SUGGESTIONS, self.txt_search)
        self.completer.setCaseSensitivity(qt_compat.CaseInsensitive)
        self.completer.setFilterMode(qt_compat.MatchContains)
        self.completer.setMaxVisibleItems(12)
        self.completer.activated.connect(self.on_suggestion_selected)
        self.txt_search.setCompleter(self.completer)

        search_layout.addWidget(self.txt_search)

        self.btn_search = QPushButton("Rechercher")
        self.btn_search.setObjectName("btnSearch")
        self.btn_search.clicked.connect(self.on_search_clicked)
        search_layout.addWidget(self.btn_search)
        layout.addLayout(search_layout)

        # 3. Barre de catégories thématiques sobres
        cat_layout = QHBoxLayout()
        cat_layout.setSpacing(4)
        self.cat_button_group = QButtonGroup(self)
        self.cat_button_group.setExclusive(True)

        categories = [
            ("all", "Tous les jeux"),
            ("admin", "Administratif"),
            ("cadastre", "Cadastre"),
            ("urbanisme", "Urbanisme"),
            ("environnement", "Environnement"),
            ("risques", "Risques"),
            ("energie", "Énergie"),
            ("transport", "Transports"),
            ("raster", "Fonds IGN")
        ]

        for cat_id, cat_label in categories:
            btn = QPushButton(cat_label)
            btn.setCheckable(True)
            btn.setProperty("cat_id", cat_id)
            if cat_id == "all":
                btn.setChecked(True)
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 11px;
                    padding: 3px 8px;
                    border: 1px solid #c0c0c0;
                    border-radius: 3px;
                    background-color: #fafafa;
                    color: #333333;
                }
                QPushButton:checked {
                    background-color: #e4ecf7;
                    color: #154b8c;
                    border: 1px solid #154b8c;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #f0f0f0;
                }
            """)
            btn.clicked.connect(lambda _, cid=cat_id: self.on_category_changed(cid))
            self.cat_button_group.addButton(btn)
            cat_layout.addWidget(btn)

        cat_layout.addStretch()
        layout.addLayout(cat_layout)

        # 4. Section Paramètres d'import, Projections & Filtres
        settings_group = QGroupBox("Options & Filtres avancés")
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.setContentsMargins(8, 6, 8, 6)
        settings_layout.setSpacing(4)

        row1 = QHBoxLayout()
        lbl_crs = QLabel("Projection cible :")
        lbl_crs.setStyleSheet("font-weight: bold; color: #1967d2; font-size: 11px;")
        row1.addWidget(lbl_crs)

        self.cmb_target_crs = QComboBox()
        self.cmb_target_crs.addItems([
            "EPSG:2154 (RGF93 / Lambert-93 - France Métro.)",
            "EPSG:4326 (WGS 84 - GPS Mondial)",
            "EPSG:3857 (Web Mercator - Cartes Web)",
            "EPSG:3949 (RGF93 / CC49)",
            "EPSG:2975 (RGR92 / UTM 40S - La Réunion)",
            "EPSG:5490 (RGAF09 / UTM 20N - Guadeloupe/Martinique)",
            "EPSG:2972 (RGFG95 / UTM 22N - Guyane)",
            "EPSG:4471 (RGM04 / UTM 38S - Mayotte)",
            "Projection source (Native)"
        ])
        row1.addWidget(self.cmb_target_crs)

        lbl_fmt = QLabel("Format :")
        lbl_fmt.setStyleSheet("font-weight: bold; color: #1967d2; font-size: 11px;")
        row1.addWidget(lbl_fmt)

        self.cmb_format = QComboBox()
        self.cmb_format.addItems([
            "Tous les formats",
            "Vectoriel (SHP, GPKG, GeoJSON, KML)",
            "Tableaux (CSV, Excel)",
            "Services Web (WFS, WMS, WMTS)"
        ])
        self.cmb_format.currentIndexChanged.connect(self.apply_post_search_filters)
        row1.addWidget(self.cmb_format)

        settings_layout.addLayout(row1)

        sources_row = QHBoxLayout()
        self.chk_admin = QCheckBox("data.gouv.fr / INSEE")
        self.chk_admin.setChecked(True)
        sources_row.addWidget(self.chk_admin)

        self.chk_gpu = QCheckBox("Urbanisme (GPU)")
        self.chk_gpu.setChecked(True)
        sources_row.addWidget(self.chk_gpu)

        self.chk_ban = QCheckBox("Adresses (BAN)")
        self.chk_ban.setChecked(True)
        sources_row.addWidget(self.chk_ban)

        self.chk_geopf = QCheckBox("GéoPlateforme IGN")
        self.chk_geopf.setChecked(True)
        sources_row.addWidget(self.chk_geopf)
        settings_layout.addLayout(sources_row)

        geo_filter_layout = QHBoxLayout()
        geo_filter_layout.setSpacing(6)

        lbl_scale = QLabel("Échelle :")
        geo_filter_layout.addWidget(lbl_scale)

        self.cmb_scale = QComboBox()
        self.cmb_scale.addItems([
            "Toutes les échelles",
            "Pays (France)",
            "Région",
            "Département",
            "Collectivité / EPCI",
            "Commune"
        ])
        self.cmb_scale.currentIndexChanged.connect(self.apply_post_search_filters)
        geo_filter_layout.addWidget(self.cmb_scale)

        lbl_terr = QLabel("Territoire :")
        geo_filter_layout.addWidget(lbl_terr)

        self.txt_territory = QLineEdit()
        self.txt_territory.setPlaceholderText("Département (60), INSEE (60057) ou Nom")
        self.txt_territory.textChanged.connect(self.apply_post_search_filters)
        geo_filter_layout.addWidget(self.txt_territory)

        btn_filter_dialog = QPushButton("Sélecteur...")
        btn_filter_dialog.setToolTip("Ouvrir le sélecteur interactif de départements et communes françaises")
        btn_filter_dialog.setStyleSheet("font-size: 11px; font-weight: bold; background-color: #e8f0fe; color: #1a73e8; border: 1px solid #1a73e8; border-radius: 4px; padding: 3px 6px;")
        btn_filter_dialog.clicked.connect(self.open_territory_dialog)
        geo_filter_layout.addWidget(btn_filter_dialog)

        btn_clear_filters = QPushButton("Réinitialiser")
        btn_clear_filters.setToolTip("Réinitialiser tous les filtres de recherche")
        btn_clear_filters.setStyleSheet("font-size: 11px; font-weight: bold; background-color: #fce8e6; color: #c5221f; border: 1px solid #c5221f; border-radius: 4px; padding: 3px 6px;")
        btn_clear_filters.clicked.connect(self.reset_all_filters)
        geo_filter_layout.addWidget(btn_clear_filters)

        settings_layout.addLayout(geo_filter_layout)
        layout.addWidget(settings_group)

        # 5. Splitter avec Tableau des résultats à gauche et Volet d'inspection à droite
        splitter = QSplitter(qt_compat.Horizontal)

        # Tableau des résultats
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(4)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Titre", "Source", "Type / Format", "CRS", "Territoire", "Date Maj", "Actions"])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(qt_compat.HeaderInteractive)
        header.setStretchLastSection(False)
        header.setDefaultAlignment(qt_compat.AlignLeft | qt_compat.AlignVCenter)
        
        self.table.setColumnWidth(0, 240)
        self.table.setColumnWidth(1, 140)
        self.table.setColumnWidth(2, 110)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 110)
        self.table.setColumnWidth(5, 80)
        self.table.setColumnWidth(6, 130)

        self.table.setSelectionBehavior(qt_compat.SelectRows)
        self.table.setEditTriggers(qt_compat.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.setWordWrap(True)
        self.table.itemSelectionChanged.connect(self.on_table_selection_changed)
        self.table.itemDoubleClicked.connect(self.on_table_double_clicked)
        table_layout.addWidget(self.table)

        # Barre d'export
        export_bar = QHBoxLayout()
        export_bar.setSpacing(6)
        btn_export_csv = QPushButton("Exporter CSV/Excel")
        btn_export_csv.clicked.connect(self.export_results_csv)
        export_bar.addWidget(btn_export_csv)

        btn_export_geojson = QPushButton("Exporter GeoJSON")
        btn_export_geojson.clicked.connect(self.export_results_geojson)
        export_bar.addWidget(btn_export_geojson)
        export_bar.addStretch()
        table_layout.addLayout(export_bar)

        splitter.addWidget(table_container)

        # Volet d'inspection des métadonnées
        self.inspector_panel = QGroupBox("Fiche & Métadonnées")
        self.inspector_panel.setMinimumWidth(260)
        inspector_layout = QVBoxLayout(self.inspector_panel)
        inspector_layout.setContentsMargins(8, 8, 8, 8)
        inspector_layout.setSpacing(6)

        self.lbl_insp_title = QLabel("Sélectionnez une couche")
        self.lbl_insp_title.setWordWrap(True)
        self.lbl_insp_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #1a73e8;")
        inspector_layout.addWidget(self.lbl_insp_title)

        self.lbl_insp_meta = QLabel("Aucune sélection")
        self.lbl_insp_meta.setWordWrap(True)
        self.lbl_insp_meta.setStyleSheet("font-size: 11px; color: #3c4043;")
        inspector_layout.addWidget(self.lbl_insp_meta)

        self.txt_insp_desc = QTextEdit()
        self.txt_insp_desc.setReadOnly(True)
        self.txt_insp_desc.setPlaceholderText("Description détaillée de la ressource...")
        self.txt_insp_desc.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dadce0; border-radius: 4px; font-size: 11px;")
        inspector_layout.addWidget(self.txt_insp_desc)

        insp_buttons_layout = QVBoxLayout()
        insp_buttons_layout.setSpacing(4)

        self.btn_insp_add = QPushButton("Ajouter au projet")
        self.btn_insp_add.setStyleSheet("font-weight: bold; padding: 6px;")
        self.btn_insp_add.clicked.connect(self.on_inspector_add_clicked)
        insp_buttons_layout.addWidget(self.btn_insp_add)

        insp_actions_row = QHBoxLayout()
        self.btn_insp_web = QPushButton("Fiche Web")
        self.btn_insp_web.setToolTip("Ouvrir la page officielle data.gouv.fr / GPU dans le navigateur")
        self.btn_insp_web.clicked.connect(self.on_inspector_web_clicked)
        insp_actions_row.addWidget(self.btn_insp_web)

        self.btn_insp_copy = QPushButton("Copier l'URL")
        self.btn_insp_copy.setToolTip("Copier l'adresse de téléchargement ou du flux dans le presse-papier")
        self.btn_insp_copy.clicked.connect(self.on_inspector_copy_clicked)
        insp_actions_row.addWidget(self.btn_insp_copy)

        insp_buttons_layout.addLayout(insp_actions_row)
        inspector_layout.addLayout(insp_buttons_layout)

        splitter.addWidget(self.inspector_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.lbl_status = QLabel("Prêt. Saisissez une recherche ou cliquez sur un pré-réglage.")
        self.lbl_status.setStyleSheet("color: #5f6368; font-size: 11px;")
        layout.addWidget(self.lbl_status)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(qt_compat.NoFrame)
        scroll_area.setWidget(main_widget)

        self.setWidget(scroll_area)

    def _apply_stylesheet(self):
        qss = """
        QGroupBox {
            font-weight: bold;
            border: 1px solid #d0d0d0;
            border-radius: 4px;
            margin-top: 6px;
            padding-top: 8px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 8px;
            padding: 0 4px;
            color: #333333;
        }
        QLineEdit {
            padding: 4px 6px;
            border: 1px solid #c0c0c0;
            border-radius: 3px;
            background: #ffffff;
        }
        QPushButton#btnSearch {
            background-color: #f5f5f5;
            border: 1px solid #b0b0b0;
            font-weight: bold;
            border-radius: 3px;
            padding: 4px 12px;
        }
        QPushButton#btnSearch:hover {
            background-color: #e5e5e5;
        }
        QTableWidget {
            border: 1px solid #d0d0d0;
            gridline-color: #f0f0f0;
        }
        QHeaderView::section {
            background-color: #f0f0f0;
            color: #333333;
            font-weight: bold;
            padding: 3px 5px;
            border: 1px solid #d0d0d0;
        }
        """
        self.setStyleSheet(qss)

    def on_category_changed(self, cat_id):
        self.active_category = cat_id
        self.apply_post_search_filters()

    def on_suggestion_selected(self, selected_text):
        self.txt_search.setText(selected_text)
        self.on_search_clicked()

    def open_territory_dialog(self, layer_title="Couche géographique"):
        dlg = TerritoryFilterDialog(layer_title=layer_title, parent=self)
        if qt_compat.exec_dialog(dlg) == qt_compat.DialogAccepted:
            selected_code = dlg.get_selected_filter()
            self.txt_territory.setText(selected_code)
            self.apply_post_search_filters()

    def reset_all_filters(self):
        self.txt_search.clear()
        self.cmb_scale.setCurrentIndex(0)
        self.cmb_format.setCurrentIndex(0)
        self.txt_territory.clear()
        self.active_category = "all"

        for btn in self.cat_button_group.buttons():
            if btn.property("cat_id") == "all":
                btn.setChecked(True)

        self.chk_admin.setChecked(True)
        self.chk_gpu.setChecked(True)
        self.chk_ban.setChecked(True)
        self.chk_geopf.setChecked(True)
        self.cmb_target_crs.setCurrentIndex(0)

        self.show_all_presets()
        self.lbl_status.setText("Tous les filtres ont été réinitialisés.")

    def get_selected_target_crs(self):
        val = self.cmb_target_crs.currentText()
        if "EPSG:2154" in val:
            return "EPSG:2154"
        if "EPSG:4326" in val:
            return "EPSG:4326"
        if "EPSG:3857" in val:
            return "EPSG:3857"
        if "EPSG:3949" in val:
            return "EPSG:3949"
        if "EPSG:2975" in val:
            return "EPSG:2975"
        if "EPSG:5490" in val:
            return "EPSG:5490"
        if "EPSG:2972" in val:
            return "EPSG:2972"
        if "EPSG:4471" in val:
            return "EPSG:4471"
        return "Native"

    def on_search_clicked(self):
        query = self.txt_search.text().strip()
        territory_val = self.txt_territory.text().strip()

        if not query and not territory_val and self.cmb_scale.currentIndex() == 0:
            self.lbl_status.setText("Veuillez saisir un terme de recherche ou un territoire.")
            return

        # Analyse sémantique en langage naturel (NLP local)
        self.last_nlp_res = self.nlp_engine.parse(query) if query else None

        if self.last_nlp_res and self.last_nlp_res.has_territory() and not territory_val:
            self.txt_territory.setText(self.last_nlp_res.territory_code)
            territory_val = self.last_nlp_res.territory_code

        effective_query = query
        if self.last_nlp_res and self.last_nlp_res.search_keywords:
            effective_query = self.last_nlp_res.search_keywords

        active_sources = {
            'admin': self.chk_admin.isChecked(),
            'gpu': self.chk_gpu.isChecked(),
            'ban': self.chk_ban.isChecked(),
            'geopf': self.chk_geopf.isChecked()
        }

        if not any(active_sources.values()):
            self.lbl_status.setText("Veuillez cocher au moins une source de données.")
            return

        scale_val = self.cmb_scale.currentText()
        scale_key = "all"
        if "Pays" in scale_val:
            scale_key = "france"
        elif "Région" in scale_val:
            scale_key = "region"
        elif "Département" in scale_val:
            scale_key = "departement"
        elif "Collectivité" in scale_val:
            scale_key = "epci"
        elif "Commune" in scale_val:
            scale_key = "commune"

        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.quit()
            self.search_worker.wait(1000)

        self.btn_search.setEnabled(False)
        self.progress_bar.setVisible(True)
        if self.last_nlp_res and self.last_nlp_res.explanation:
            self.lbl_status.setText(f"Analyse IA : {self.last_nlp_res.explanation}...")
        else:
            self.lbl_status.setText("Recherche rapide parallèle en cours...")

        self.search_worker = SearchWorker(
            query=effective_query,
            active_sources=active_sources,
            scale_filter=scale_key,
            territory_filter=territory_val
        )
        self.search_worker.results_ready.connect(self.on_results_received)
        self.search_worker.error_occurred.connect(self.on_search_error)
        self.search_worker.start()

    def on_results_received(self, results):
        self.progress_bar.setVisible(False)
        self.btn_search.setEnabled(True)

        combined_results = []
        seen_ids = set()

        # Priorité aux couches identifiées par l'analyse sémantique
        if self.last_nlp_res and self.last_nlp_res.has_presets():
            for p in self.last_nlp_res.matched_presets:
                if p.id not in seen_ids:
                    combined_results.append(p)
                    seen_ids.add(p.id)

        for r in results:
            if r.id not in seen_ids:
                combined_results.append(r)
                seen_ids.add(r.id)

        self.all_raw_results = combined_results if combined_results else results
        self.apply_post_search_filters()

        if self.last_nlp_res and self.last_nlp_res.explanation:
            self.lbl_status.setText(f"Intention : {self.last_nlp_res.explanation}")

    def apply_post_search_filters(self):
        if not self.all_raw_results:
            self.table.setRowCount(0)
            self.update_inspector(None)
            return

        scale_val = self.cmb_scale.currentText()
        scale_key = "all"
        if "Pays" in scale_val:
            scale_key = "france"
        elif "Région" in scale_val:
            scale_key = "region"
        elif "Département" in scale_val:
            scale_key = "departement"
        elif "Collectivité" in scale_val:
            scale_key = "epci"
        elif "Commune" in scale_val:
            scale_key = "commune"

        terr_filter = self.txt_territory.text().strip().lower()
        selected_fmt = self.cmb_format.currentText()

        filtered = []
        for item in self.all_raw_results:
            # 1. Filtre par catégorie thématique
            if self.active_category != "all":
                item_cat = str(item.extra.get('category', '')).lower() if hasattr(item, 'extra') and item.extra else ''
                item_title = item.title.lower()
                item_src = item.source.lower()
                
                cat_match = False
                if self.active_category == "admin" and (item_cat == "admin" or "admin" in item_src or "insee" in item_src):
                    cat_match = True
                elif self.active_category == "cadastre" and (item_cat == "cadastre" or "cadastre" in item_title or "cadastre" in item_src or "parcelle" in item_title):
                    cat_match = True
                elif self.active_category == "urbanisme" and (item_cat == "urbanisme" or "gpu" in item_src or "plu" in item_title or "urbanisme" in item_title):
                    cat_match = True
                elif self.active_category == "environnement" and (item_cat == "environnement" or any(k in item_title for k in ("znieff", "natura", "eau", "foret", "biodiversite", "inpn", "ofb"))):
                    cat_match = True
                elif self.active_category == "risques" and (item_cat == "risques" or any(k in item_title for k in ("pprn", "argile", "geologique", "inondation", "brgm", "georisques"))):
                    cat_match = True
                elif self.active_category == "energie" and (item_cat == "energie" or any(k in item_title for k in ("irve", "recharge", "enr", "electr", "rte", "sdes"))):
                    cat_match = True
                elif self.active_category == "transport" and (item_cat == "transport" or any(k in item_title for k in ("route", "cyclable", "velo", "ferre", "sncf", "train", "bus"))):
                    cat_match = True
                elif self.active_category == "raster" and (item_cat == "raster" or item.data_type == "wms" or any(k in item_title for k in ("plan ign", "ortho", "scan 25", "osm"))):
                    cat_match = True

                if not cat_match:
                    continue

            # 2. Filtre par format / type de fichier
            d_type = getattr(item, 'data_type', '').lower()
            s_type = getattr(item, 'service_type', '').lower()

            is_vector = d_type in ('file_vector', 'geojson', 'shp', 'gpkg', 'kml', 'kmz') or 'vector' in d_type
            is_table = d_type in ('table', 'csv', 'excel') or 'csv' in d_type
            is_ogc = d_type in ('wfs', 'wms', 'wmts', 'urban_doc') or s_type in ('wfs', 'wms', 'wmts')

            if "Vectoriel" in selected_fmt and not is_vector:
                continue
            if "Tableaux" in selected_fmt and not is_table:
                continue
            if "Services Web" in selected_fmt and not is_ogc:
                continue

            # 3. Filtre par échelle
            item_scale = getattr(item, 'scale', 'france').lower()
            item_terr = (getattr(item, 'territory', '') or '').lower()

            if scale_key != "all":
                if scale_key not in item_scale and item_scale not in scale_key and item_scale != "france" and item_terr != "france":
                    continue

            # 4. Filtre par territoire
            if terr_filter:
                title_text = (getattr(item, 'title', '') or '').lower()
                code_insee = str(item.extra.get('code_insee', '')).lower() if hasattr(item, 'extra') and item.extra else ''
                dep_code = str(item.extra.get('dep_code', '')).lower() if hasattr(item, 'extra') and item.extra else ''

                is_national_layer = item_scale == "france" or item_terr == "france"

                matched = (
                    is_national_layer or
                    terr_filter in item_terr or
                    terr_filter in title_text or
                    terr_filter == code_insee or
                    terr_filter == dep_code or
                    (len(terr_filter) == 5 and code_insee.startswith(terr_filter[:2]))
                )
                if not matched:
                    continue

            filtered.append(item)

        self.displayed_results = filtered
        self.display_results(filtered)
        self.lbl_status.setText(f"Affichage : {len(filtered)} / {len(self.all_raw_results)} résultat(s).")

    def on_search_error(self, err_msg):
        self.progress_bar.setVisible(False)
        self.btn_search.setEnabled(True)
        self.lbl_status.setText(f"Erreur de recherche : {err_msg}")

    def show_all_presets(self):
        presets = PresetLibrary.get_presets()
        self.all_raw_results = presets
        self.apply_post_search_filters()

    def display_results(self, items):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        self.table.setRowCount(len(items))

        for row, item in enumerate(items):
            title_item = QTableWidgetItem(item.title)
            title_item.setToolTip(item.title)
            self.table.setItem(row, 0, title_item)

            source_item = QTableWidgetItem(item.source)
            source_item.setToolTip(item.source)
            self.table.setItem(row, 1, source_item)

            # Badge de format
            fmt_label = item.extra.get('format', '') if hasattr(item, 'extra') and item.extra else ''
            if not fmt_label:
                fmt_label = item.data_type.upper()
                if hasattr(item, 'doc_type'):
                    fmt_label = f"GPU ({item.doc_type})"
            
            type_item = QTableWidgetItem(str(fmt_label))
            self.table.setItem(row, 2, type_item)

            crs_str = getattr(item, 'crs', 'EPSG:4326')
            crs_item = QTableWidgetItem(crs_str)
            crs_item.setToolTip(f"Projection : {crs_str}")
            self.table.setItem(row, 3, crs_item)

            territory_item = QTableWidgetItem(item.territory)
            territory_item.setToolTip(item.territory)
            self.table.setItem(row, 4, territory_item)

            date_str = getattr(item, 'date', '2025')
            date_item = QTableWidgetItem(date_str)
            date_item.setToolTip(f"Mise à jour : {date_str}")
            self.table.setItem(row, 5, date_item)

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            actions_layout.setSpacing(4)

            if item.data_type in ('wms', 'urban_doc') or item.service_type == 'WMS':
                btn_wms = QPushButton("WMS")
                btn_wms.setToolTip("Charger le flux WMS")
                btn_wms.setStyleSheet("font-size: 11px; padding: 2px 6px;")
                btn_wms.clicked.connect(lambda _, it=item: self.import_item(it, as_wms=True))
                actions_layout.addWidget(btn_wms)

            btn_add = QPushButton("Ajouter")
            btn_add.setToolTip("Ajouter la couche au projet QGIS")
            btn_add.setStyleSheet("font-size: 11px; font-weight: bold; padding: 2px 8px;")
            btn_add.clicked.connect(lambda _, it=item: self.import_item(it, as_wms=False))
            actions_layout.addWidget(btn_add)

            self.table.setCellWidget(row, 6, actions_widget)

        self.table.setSortingEnabled(True)

        if items:
            self.table.selectRow(0)
            self.update_inspector(items[0])
        else:
            self.update_inspector(None)

    def on_table_selection_changed(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            if 0 <= row < len(self.displayed_results):
                self.update_inspector(self.displayed_results[row])

    def update_inspector(self, item):
        self.current_selected_item = item
        if not item:
            self.lbl_insp_title.setText("Aucune couche sélectionnée")
            self.lbl_insp_meta.setText("")
            self.txt_insp_desc.clear()
            self.btn_insp_add.setEnabled(False)
            self.btn_insp_web.setEnabled(False)
            self.btn_insp_copy.setEnabled(False)
            return

        self.btn_insp_add.setEnabled(True)
        self.btn_insp_copy.setEnabled(bool(item.url))

        web_url = item.extra.get('web_url') if hasattr(item, 'extra') and item.extra else ''
        self.btn_insp_web.setEnabled(bool(web_url))

        self.lbl_insp_title.setText(item.title)

        meta_lines = [
            f"<b>Source :</b> {item.source}",
            f"<b>Territoire :</b> {item.territory} ({item.scale})",
            f"<b>Projection :</b> {getattr(item, 'crs', 'EPSG:4326')}",
            f"<b>Date :</b> {getattr(item, 'date', '2025')}"
        ]
        if hasattr(item, 'extra') and item.extra:
            if item.extra.get('format'):
                meta_lines.append(f"<b>Format :</b> {item.extra.get('format')}")
            if item.extra.get('size'):
                meta_lines.append(f"<b>Taille :</b> {item.extra.get('size')}")
            if item.extra.get('license'):
                meta_lines.append(f"<b>Licence :</b> {item.extra.get('license')}")

        self.lbl_insp_meta.setText("<br>".join(meta_lines))

        desc = ""
        if hasattr(item, 'extra') and item.extra and item.extra.get('description'):
            desc = item.extra.get('description')
        elif item.url:
            desc = f"URL de la ressource : {item.url}"
        self.txt_insp_desc.setText(desc)

    def on_inspector_add_clicked(self):
        if self.current_selected_item:
            self.import_item(self.current_selected_item)

    def on_inspector_web_clicked(self):
        if self.current_selected_item and hasattr(self.current_selected_item, 'extra'):
            web_url = self.current_selected_item.extra.get('web_url')
            if web_url:
                QDesktopServices.openUrl(QUrl(web_url))

    def on_inspector_copy_clicked(self):
        if self.current_selected_item and self.current_selected_item.url:
            QApplication.clipboard().setText(self.current_selected_item.url)
            self.lbl_status.setText("URL copiée dans le presse-papier !")

    def export_results_csv(self):
        if not self.displayed_results:
            QMessageBox.information(self, "Exportation", "Aucun résultat à exporter. Veuillez effectuer une recherche d'abord.")
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Exporter les résultats en CSV (Excel)", "resultats_opengeodata.csv", "Fichiers CSV (*.csv)"
        )
        if filepath:
            success, msg = ExportService.export_to_csv(self.displayed_results, filepath)
            if success:
                QMessageBox.information(self, "Exportation réussie", msg)
            else:
                QMessageBox.critical(self, "Erreur d'exportation", msg)

    def export_results_geojson(self):
        if not self.displayed_results:
            QMessageBox.information(self, "Exportation", "Aucun résultat à exporter. Veuillez effectuer une recherche d'abord.")
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Exporter les résultats en GeoJSON", "resultats_opengeodata.geojson", "Fichiers GeoJSON (*.geojson *.json)"
        )
        if filepath:
            success, msg = ExportService.export_to_geojson(self.displayed_results, filepath)
            if success:
                QMessageBox.information(self, "Exportation réussie", msg)
            else:
                QMessageBox.critical(self, "Erreur d'exportation", msg)

    def on_table_double_clicked(self, item_widget):
        if not item_widget:
            return
        row = item_widget.row()
        if 0 <= row < len(self.displayed_results):
            target_item = self.displayed_results[row]
            self.import_item(target_item)

    def import_item(self, item, as_wms=False):
        """Lance l'importation de manière 100% multithreadée en arrière-plan sans JAMAIS figer QGIS."""
        if not item:
            return

        # 1. Demande systématique préalable : Importer avec découpage territorial ou sans filtre (France entière)
        current_terr = self.txt_territory.text().strip()
        dlg = ImportFilterOptionDialog(item=item, current_territory=current_terr, as_wms=as_wms, parent=self)
        if qt_compat.exec_dialog(dlg) != qt_compat.DialogAccepted:
            self.lbl_status.setText("Importation annulée par l'utilisateur.")
            return

        if dlg.import_mode == "filter":
            territory_filter = dlg.selected_territory
            self.txt_territory.setText(territory_filter)
        else:
            territory_filter = ""

        target_crs = self.get_selected_target_crs()

        if self.import_worker and self.import_worker.isRunning():
            self.import_worker.quit()
            self.import_worker.wait(500)

        filter_msg = f" avec découpage ({territory_filter})" if territory_filter else " (sans filtre / entier)"
        self.lbl_status.setText(f"Importation de '{item.title}'{filter_msg} en cours...")
        self.progress_bar.setVisible(True)

        self.import_worker = ImportWorker(
            import_manager=self.import_manager,
            item=item,
            as_wms=as_wms,
            target_crs=target_crs,
            territory_filter=territory_filter
        )
        self.import_worker.progress_updated.connect(self.on_import_progress)
        self.import_worker.import_finished.connect(self.on_import_finished)
        self.import_worker.start()

    def on_import_progress(self, msg):
        self.lbl_status.setText(msg)

    def on_import_finished(self, success, msg, extent_info=None):
        self.progress_bar.setVisible(False)
        if success:
            self.lbl_status.setText(f"Succès : {msg}")
            if self.iface and self.iface.mapCanvas():
                if extent_info:
                    try:
                        xmin, ymin, xmax, ymax, src_crs_str = extent_info
                        source_crs = QgsCoordinateReferenceSystem(src_crs_str)
                        canvas_crs = self.iface.mapCanvas().mapSettings().destinationCrs()
                        if not canvas_crs.isValid():
                            canvas_crs = QgsProject.instance().crs()
                        if not canvas_crs.isValid():
                            canvas_crs = QgsCoordinateReferenceSystem("EPSG:2154")

                        bbox = QgsRectangle(xmin, ymin, xmax, ymax)
                        if source_crs.isValid() and canvas_crs.isValid() and source_crs != canvas_crs:
                            xform = QgsCoordinateTransform(source_crs, canvas_crs, QgsProject.instance())
                            bbox = xform.transformBoundingBox(bbox)

                        # Marge de 5% pour un cadrage confortable
                        bbox.grow(bbox.width() * 0.05)
                        self.iface.mapCanvas().setExtent(bbox)
                    except Exception as ext_err:
                        print(f"[OpenGeoDataFR] Erreur centrage canvas: {ext_err}")
                self.iface.mapCanvas().refresh()
        else:
            self.lbl_status.setText(f"Erreur : {msg}")
            QMessageBox.warning(self, "Erreur d'importation", msg)

    def cleanup(self):
        """Arrête proprement les workers de recherche et d'importation s'ils sont en cours."""
        if hasattr(self, 'search_worker') and self.search_worker and self.search_worker.isRunning():
            self.search_worker.quit()
            self.search_worker.wait(500)
        if hasattr(self, 'import_worker') and self.import_worker and self.import_worker.isRunning():
            self.import_worker.quit()
            self.import_worker.wait(500)
