"""
Graphics items for the model diagram: CV nodes (rounded rects) and FL
edges (arrowed lines between CVs).
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt, Signal, QObject
from PySide6.QtGui import QBrush, QColor, QFont, QPainterPath, QPen, QPolygonF
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsSimpleTextItem,
    QStyleOptionGraphicsItem,
    QWidget,
)

CV_WIDTH = 120
CV_HEIGHT = 56
CV_FILL = QColor("#dbe9ff")
CV_FILL_SELECTED = QColor("#ffe6a7")
CV_BORDER = QColor("#2b5fa8")
FL_COLOR = QColor("#7a7a7a")
FL_COLOR_SELECTED = QColor("#c0392b")


class SceneSignals(QObject):
    """Qt signals can't be emitted from QGraphicsItem directly, so items
    report through this shared emitter that the scene owns."""

    cv_selected = Signal(str)
    fl_selected = Signal(str)


class CVNodeItem(QGraphicsItem):
    """A single Control Volume, drawn as a labelled rounded rectangle."""

    def __init__(self, cv_id: str, label: str, signals: SceneSignals):
        super().__init__()
        self.cv_id = cv_id
        self.label = label
        self.signals = signals
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.edges: list["FLEdgeItem"] = []
        self.setZValue(1)

    def boundingRect(self) -> QRectF:
        return QRectF(-CV_WIDTH / 2, -CV_HEIGHT / 2, CV_WIDTH, CV_HEIGHT)

    def paint(self, painter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        rect = self.boundingRect()
        fill = CV_FILL_SELECTED if self.isSelected() else CV_FILL
        painter.setBrush(QBrush(fill))
        painter.setPen(QPen(CV_BORDER, 2))
        painter.drawRoundedRect(rect, 10, 10)

        painter.setPen(QPen(QColor("#1c1c1c")))
        font = QFont()
        font.setBold(True)
        font.setPointSize(9)
        painter.setFont(font)
        painter.drawText(rect.adjusted(4, 4, -4, -20), Qt.AlignHCenter | Qt.AlignTop, self.cv_id)

        font.setBold(False)
        font.setPointSize(8)
        painter.setFont(font)
        painter.drawText(rect.adjusted(4, 22, -4, -4), Qt.AlignHCenter | Qt.AlignTop, self.label)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            for edge in self.edges:
                edge.update_position()
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.signals.cv_selected.emit(self.cv_id)


class FLEdgeItem(QGraphicsLineItem):
    """A Flow Path drawn as an arrowed line connecting two CV nodes."""

    def __init__(self, fl_id: str, label: str, source: CVNodeItem, target: CVNodeItem, signals: SceneSignals):
        super().__init__()
        self.fl_id = fl_id
        self.label = label
        self.source = source
        self.target = target
        self.signals = signals
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setZValue(0)
        pen = QPen(FL_COLOR, 2)
        self.setPen(pen)
        self.setAcceptedMouseButtons(Qt.LeftButton)

        self._label_item = QGraphicsSimpleTextItem(label, self)
        self._label_item.setBrush(QBrush(QColor("#333333")))
        font = QFont()
        font.setPointSize(7)
        self._label_item.setFont(font)

        source.edges.append(self)
        target.edges.append(self)
        self.update_position()

    def update_position(self):
        p1, p2 = self.source.pos(), self.target.pos()
        self.setLine(p1.x(), p1.y(), p2.x(), p2.y())
        mid = (p1 + p2) / 2
        self._label_item.setPos(mid.x() + 4, mid.y() - 12)

    def shape(self) -> QPainterPath:
        path = QPainterPath()
        line = self.line()
        # widen the hit area so thin lines are easy to click
        path.moveTo(line.p1())
        path.lineTo(line.p2())
        stroker = self._stroker()
        return stroker.createStroke(path)

    def _stroker(self):
        from PySide6.QtGui import QPainterPathStroker

        stroker = QPainterPathStroker()
        stroker.setWidth(10)
        return stroker

    def paint(self, painter, option, widget=None):
        pen = QPen(FL_COLOR_SELECTED if self.isSelected() else FL_COLOR, 2)
        painter.setPen(pen)
        line = self.line()
        painter.drawLine(line)

        # arrowhead at the target end
        angle = math.atan2(line.dy(), line.dx())
        arrow_size = 9
        p1 = line.p2()
        back = QPointF(
            p1.x() - arrow_size * math.cos(angle - math.pi / 7),
            p1.y() - arrow_size * math.sin(angle - math.pi / 7),
        )
        back2 = QPointF(
            p1.x() - arrow_size * math.cos(angle + math.pi / 7),
            p1.y() - arrow_size * math.sin(angle + math.pi / 7),
        )
        painter.setBrush(QBrush(pen.color()))
        painter.drawPolygon(QPolygonF([p1, back, back2]))

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.signals.fl_selected.emit(self.fl_id)
