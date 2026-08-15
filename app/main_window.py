"""
MainWindow ties together the diagram view, object list dock, and
property panel dock around a ModelBridge (MELKIT-backed model).
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QPainter
from PySide6.QtWidgets import (
    QFileDialog,
    QGraphicsView,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QToolBar,
)

from .dialogs import NewCVDialog, NewFLDialog
from .melkit_bridge import ModelBridge
from .object_list import ObjectListDock
from .property_panel import PropertyPanel
from .scene import ModelScene


class ModelEditorWindow(QMainWindow):
    def __init__(self, filename: str | None = None):
        super().__init__()
        self.setWindowTitle("MELCOR Model Editor")
        self.resize(1280, 820)

        self.bridge: ModelBridge | None = None
        self.scene: ModelScene | None = None

        self.view = QGraphicsView()
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setDragMode(QGraphicsView.RubberBandDrag)
        self.setCentralWidget(self.view)

        self.object_dock: ObjectListDock | None = None
        self.property_dock: PropertyPanel | None = None

        self.status = QStatusBar()
        self.setStatusBar(self.status)

        self._build_menu()
        self._build_toolbar()

        if filename:
            self.load_file(filename)
        else:
            self.status.showMessage("Open a MELCOR .inp file to begin (File > Open).")

    # ------------------------------------------------------------------ #
    # Menu / toolbar
    # ------------------------------------------------------------------ #
    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")

        open_action = QAction("&Open...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._on_open)
        file_menu.addAction(open_action)

        reload_action = QAction("&Reload", self)
        reload_action.setShortcut("Ctrl+R")
        reload_action.triggered.connect(self._on_reload)
        file_menu.addAction(reload_action)

        file_menu.addSeparator()
        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        edit_menu = self.menuBar().addMenu("&Edit")
        new_cv_action = QAction("New Control Volume...", self)
        new_cv_action.triggered.connect(self._on_new_cv)
        edit_menu.addAction(new_cv_action)

        new_fl_action = QAction("New Flow Path...", self)
        new_fl_action.triggered.connect(self._on_new_fl)
        edit_menu.addAction(new_fl_action)

        view_menu = self.menuBar().addMenu("&View")
        fit_action = QAction("Zoom to &Fit", self)
        fit_action.setShortcut("Ctrl+0")
        fit_action.triggered.connect(self._on_fit)
        view_menu.addAction(fit_action)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main")
        self.addToolBar(toolbar)

        open_action = QAction("Open", self)
        open_action.triggered.connect(self._on_open)
        toolbar.addAction(open_action)

        new_cv_action = QAction("New CV", self)
        new_cv_action.triggered.connect(self._on_new_cv)
        toolbar.addAction(new_cv_action)

        new_fl_action = QAction("New FL", self)
        new_fl_action.triggered.connect(self._on_new_fl)
        toolbar.addAction(new_fl_action)

        fit_action = QAction("Zoom to Fit", self)
        fit_action.triggered.connect(self._on_fit)
        toolbar.addAction(fit_action)

    # ------------------------------------------------------------------ #
    # File operations
    # ------------------------------------------------------------------ #
    def _on_open(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open MELCOR Input File", "", "MELCOR Input (*.inp);;All Files (*)"
        )
        if filename:
            self.load_file(filename)

    def load_file(self, filename: str) -> None:
        try:
            self.bridge = ModelBridge(filename)
        except Exception as exc:  # noqa: BLE001 - surface any parse error to the user
            QMessageBox.critical(self, "Failed to load model", str(exc))
            return

        self.scene = ModelScene(self.bridge)
        self.scene.signals.cv_selected.connect(self._on_cv_selected)
        self.scene.signals.fl_selected.connect(self._on_fl_selected)
        self.view.setScene(self.scene)

        self._rebuild_docks()
        self.setWindowTitle(f"MELCOR Model Editor — {filename}")
        self.status.showMessage(
            f"Loaded {len(self.bridge.cv_list())} CVs, "
            f"{len(self.bridge.fl_list())} FLs, "
            f"{len(self.bridge.cf_list())} CFs from {filename}"
        )
        self._on_fit()

    def _on_reload(self) -> None:
        if not self.bridge:
            return
        self.bridge.reload()
        self.scene.refresh_after_edit()
        self.object_dock.refresh()
        self.property_dock.clear()
        self.status.showMessage("Model reloaded from disk.")

    def _rebuild_docks(self) -> None:
        if self.object_dock:
            self.removeDockWidget(self.object_dock)
        if self.property_dock:
            self.removeDockWidget(self.property_dock)

        self.object_dock = ObjectListDock(self.bridge)
        self.object_dock.cv_activated.connect(lambda cid: self._select_and_show("CV", cid))
        self.object_dock.fl_activated.connect(lambda fid: self._select_and_show("FL", fid))
        self.object_dock.cf_activated.connect(lambda fid: self._select_and_show("CF", fid))
        self.addDockWidget(Qt.LeftDockWidgetArea, self.object_dock)

        self.property_dock = PropertyPanel(self.bridge)
        self.property_dock.object_changed.connect(self._on_model_edited)
        self.addDockWidget(Qt.RightDockWidgetArea, self.property_dock)

    # ------------------------------------------------------------------ #
    # Selection handling
    # ------------------------------------------------------------------ #
    def _on_cv_selected(self, cv_id: str) -> None:
        self.property_dock.show_object("CV", cv_id)

    def _on_fl_selected(self, fl_id: str) -> None:
        self.property_dock.show_object("FL", fl_id)

    def _select_and_show(self, kind: str, obj_id: str) -> None:
        self.property_dock.show_object(kind, obj_id)
        if kind == "CV" and obj_id in self.scene.cv_items:
            self.view.centerOn(self.scene.cv_items[obj_id])
        elif kind == "FL" and obj_id in self.scene.fl_items:
            edge = self.scene.fl_items[obj_id]
            self.view.centerOn(edge.line().center())

    def _on_model_edited(self) -> None:
        self.scene.refresh_after_edit()
        self.object_dock.refresh()

    # ------------------------------------------------------------------ #
    # Object creation
    # ------------------------------------------------------------------ #
    def _on_new_cv(self) -> None:
        if not self.bridge:
            QMessageBox.information(self, "No model open", "Open a .inp file first.")
            return
        dialog = NewCVDialog(self)
        if dialog.exec():
            values = dialog.values()
            self.bridge.create_cv(**values)
            self._on_model_edited()
            self.status.showMessage(f"Created new CV: {values['name']}")

    def _on_new_fl(self) -> None:
        if not self.bridge:
            QMessageBox.information(self, "No model open", "Open a .inp file first.")
            return
        cv_ids = [cv.get_id() for cv in self.bridge.cv_list()]
        if len(cv_ids) < 2:
            QMessageBox.information(self, "Not enough CVs", "Create at least two Control Volumes first.")
            return
        dialog = NewFLDialog(cv_ids, self)
        if dialog.exec():
            values = dialog.values()
            self.bridge.create_fl(**values)
            self._on_model_edited()
            self.status.showMessage(f"Created new FL: {values['name']}")

    # ------------------------------------------------------------------ #
    # View
    # ------------------------------------------------------------------ #
    def _on_fit(self) -> None:
        if self.scene:
            self.view.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)
