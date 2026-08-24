# -*- coding: utf-8 -*-
"""
Module de compatibilité Qt universel pour QGIS 3 (PyQt5 / Qt5) et QGIS 4 (PyQt6 / Qt6).
Résout dynamiquement toutes les énumérations et méthodes Qt quelle que soit la version de QGIS et PyQt.
"""

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QHeaderView, QTableWidget, QAbstractItemView,
    QFrame, QDialogButtonBox, QDialog, QDockWidget, QSplitter
)


def get_enum_val(parent_cls, enum_group, name, default=0):
    """
    Retourne la valeur d'une énumération compatible PyQt5 et PyQt6 avec valeur entière par défaut si non trouvée.
    Exemple: get_enum_val(QHeaderView, 'ResizeMode', 'Interactive')
    """
    if hasattr(parent_cls, name):
        val = getattr(parent_cls, name)
        if val is not None:
            return val
    if hasattr(parent_cls, enum_group):
        group_obj = getattr(parent_cls, enum_group)
        if hasattr(group_obj, name):
            val = getattr(group_obj, name)
            if val is not None:
                return val
    fallback = getattr(parent_cls, name, None)
    return fallback if fallback is not None else default


def get_qt_enum(enum_group, name, default=0):
    return get_enum_val(Qt, enum_group, name, default=default)


def exec_dialog(dlg):
    """Exécute une fenêtre modale de manière 100% compatible PyQt5 / PyQt6 / PySide6."""
    exec_method = getattr(dlg, 'exec', None) or getattr(dlg, 'exec_', None)
    if callable(exec_method):
        return exec_method()
    return 0


# --- Qt Core & Gui Enums ---
Horizontal = get_qt_enum('Orientation', 'Horizontal', 1)
Vertical = get_qt_enum('Orientation', 'Vertical', 2)

LeftDockWidgetArea = get_qt_enum('DockWidgetArea', 'LeftDockWidgetArea') or get_enum_val(QDockWidget, 'DockWidgetArea', 'LeftDockWidgetArea', 1)
RightDockWidgetArea = get_qt_enum('DockWidgetArea', 'RightDockWidgetArea') or get_enum_val(QDockWidget, 'DockWidgetArea', 'RightDockWidgetArea', 2)
TopDockWidgetArea = get_qt_enum('DockWidgetArea', 'TopDockWidgetArea') or get_enum_val(QDockWidget, 'DockWidgetArea', 'TopDockWidgetArea', 4)
BottomDockWidgetArea = get_qt_enum('DockWidgetArea', 'BottomDockWidgetArea') or get_enum_val(QDockWidget, 'DockWidgetArea', 'BottomDockWidgetArea', 8)

DockWidgetClosable = get_enum_val(QDockWidget, 'DockWidgetFeature', 'DockWidgetClosable', 1) or get_qt_enum('DockWidgetFeature', 'DockWidgetClosable', 1)
DockWidgetMovable = get_enum_val(QDockWidget, 'DockWidgetFeature', 'DockWidgetMovable', 2) or get_qt_enum('DockWidgetFeature', 'DockWidgetMovable', 2)
DockWidgetFloatable = get_enum_val(QDockWidget, 'DockWidgetFeature', 'DockWidgetFloatable', 4) or get_qt_enum('DockWidgetFeature', 'DockWidgetFloatable', 4)

KeepAspectRatio = get_qt_enum('AspectRatioMode', 'KeepAspectRatio', 1)
SmoothTransformation = get_qt_enum('TransformationMode', 'SmoothTransformation', 1)

AlignLeft = get_qt_enum('AlignmentFlag', 'AlignLeft', 1)
AlignVCenter = get_qt_enum('AlignmentFlag', 'AlignVCenter', 128)
AlignCenter = get_qt_enum('AlignmentFlag', 'AlignCenter', 132)

CaseInsensitive = get_qt_enum('CaseSensitivity', 'CaseInsensitive', 0)
MatchContains = get_qt_enum('MatchFlag', 'MatchContains', 1)

ItemIsUserCheckable = get_qt_enum('ItemFlag', 'ItemIsUserCheckable', 16)
ItemIsEnabled = get_qt_enum('ItemFlag', 'ItemIsEnabled', 1)
Checked = get_qt_enum('CheckState', 'Checked', 2)
Unchecked = get_qt_enum('CheckState', 'Unchecked', 0)
UserRole = get_qt_enum('ItemDataRole', 'UserRole', 256)

# --- QtWidgets Enums (PyQt6 Scoped Enums) ---
# QHeaderView
HeaderInteractive = get_enum_val(QHeaderView, 'ResizeMode', 'Interactive', 0)
HeaderStretch = get_enum_val(QHeaderView, 'ResizeMode', 'Stretch', 1)

# QTableWidget / QAbstractItemView
SelectRows = get_enum_val(QAbstractItemView, 'SelectionBehavior', 'SelectRows', 1) or get_enum_val(QTableWidget, 'SelectionBehavior', 'SelectRows', 1)
NoEditTriggers = get_enum_val(QAbstractItemView, 'EditTrigger', 'NoEditTriggers', 0) or get_enum_val(QTableWidget, 'EditTrigger', 'NoEditTriggers', 0)

# QFrame
NoFrame = get_enum_val(QFrame, 'Shape', 'NoFrame', 0)

# QDialogButtonBox
ButtonOk = get_enum_val(QDialogButtonBox, 'StandardButton', 'Ok', 1024)
ButtonCancel = get_enum_val(QDialogButtonBox, 'StandardButton', 'Cancel', 4194304)

# QDialog
DialogAccepted = get_enum_val(QDialog, 'DialogCode', 'Accepted', 1)
DialogRejected = get_enum_val(QDialog, 'DialogCode', 'Rejected', 0)
