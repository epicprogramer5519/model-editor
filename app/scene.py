"""
ModelScene builds a QGraphicsScene diagram (CV nodes + FL edges) from a
ModelBridge, and re-syncs itself whenever the model changes.
"""
from __future__ import annotations

from PySide6.QtCore import QRectF
from PySide6.QtWidgets import QGraphicsScene

from .items import CVNodeItem, FLEdgeItem, SceneSignals
from .melkit_bridge import ModelBridge


class ModelScene(QGraphicsScene):
    def __init__(self, bridge: ModelBridge):
        super().__init__()
        self.bridge = bridge
        self.signals = SceneSignals()
        self.cv_items: dict[str, CVNodeItem] = {}
        self.fl_items: dict[str, FLEdgeItem] = {}
        self.rebuild()

    def rebuild(self) -> None:
        """Clear and redraw the whole diagram from the current model state."""
        self.clear()
        self.cv_items.clear()
        self.fl_items.clear()

        layout = self.bridge.compute_layout()

        for cv in self.bridge.cv_list():
            cv_id = cv.get_id()
            label = cv.get_field("NAME") or ""
            x, y = layout.get(cv_id, (0.0, 0.0))
            item = CVNodeItem(cv_id, label, self.signals)
            item.setPos(x, y)
            self.addItem(item)
            self.cv_items[cv_id] = item

        for fl in self.bridge.fl_list():
            fl_id = fl.get_id()
            frm, to = fl.get_field("KCVFM"), fl.get_field("KCVTO")
            if not frm or not to:
                continue
            src = self.cv_items.get("CV" + frm)
            tgt = self.cv_items.get("CV" + to)
            if src is None or tgt is None:
                continue
            label = fl.get_field("FLNAME") or ""
            edge = FLEdgeItem(fl_id, label, src, tgt, self.signals)
            self.addItem(edge)
            self.fl_items[fl_id] = edge

        self._fit_bounds()

    def _fit_bounds(self) -> None:
        rect = self.itemsBoundingRect()
        margin = 150
        self.setSceneRect(rect.adjusted(-margin, -margin, margin, margin) if not rect.isNull() else QRectF(-400, -400, 800, 800))

    def refresh_after_edit(self) -> None:
        """Model changed on disk (via bridge) — rebuild the diagram."""
        self.rebuild()
