"""
Dockable object browser: a tree of Control Volumes / Flow Paths /
Control Functions the user can click to select in the diagram.
"""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDockWidget, QTreeWidget, QTreeWidgetItem

from .melkit_bridge import ModelBridge


class ObjectListDock(QDockWidget):
    cv_activated = Signal(str)
    fl_activated = Signal(str)
    cf_activated = Signal(str)

    def __init__(self, bridge: ModelBridge, parent=None):
        super().__init__("Model Objects", parent)
        self.bridge = bridge

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["ID", "Name"])
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.setWidget(self.tree)

        self.cv_root: QTreeWidgetItem | None = None
        self.fl_root: QTreeWidgetItem | None = None
        self.cf_root: QTreeWidgetItem | None = None

        self.refresh()

    def refresh(self) -> None:
        self.tree.clear()

        self.cv_root = QTreeWidgetItem(["Control Volumes", ""])
        self.fl_root = QTreeWidgetItem(["Flow Paths", ""])
        self.cf_root = QTreeWidgetItem(["Control Functions", ""])
        for root in (self.cv_root, self.fl_root, self.cf_root):
            self.tree.addTopLevelItem(root)
            root.setExpanded(True)

        for cv in self.bridge.cv_list():
            item = QTreeWidgetItem([cv.get_id(), cv.get_field("NAME") or ""])
            item.setData(0, 32, ("CV", cv.get_id()))
            self.cv_root.addChild(item)

        for fl in self.bridge.fl_list():
            item = QTreeWidgetItem([fl.get_id(), fl.get_field("FLNAME") or ""])
            item.setData(0, 32, ("FL", fl.get_id()))
            self.fl_root.addChild(item)

        for cf in self.bridge.cf_list():
            item = QTreeWidgetItem([cf.get_id(), cf.get_field("CFNAME") or ""])
            item.setData(0, 32, ("CF", cf.get_id()))
            self.cf_root.addChild(item)

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        data = item.data(0, 32)
        if not data:
            return
        kind, obj_id = data
        if kind == "CV":
            self.cv_activated.emit(obj_id)
        elif kind == "FL":
            self.fl_activated.emit(obj_id)
        elif kind == "CF":
            self.cf_activated.emit(obj_id)
