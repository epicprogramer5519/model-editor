"""
Dockable property editor: shows every record/field for the currently
selected object, editable in place, with Apply / Delete actions that go
through the ModelBridge (and therefore MELKIT's write_object/update_object).
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDockWidget,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from melkit.inputs import Object

from .melkit_bridge import ModelBridge


class PropertyPanel(QDockWidget):
    object_changed = Signal()  # emitted after a successful apply/delete

    def __init__(self, bridge: ModelBridge, parent=None):
        super().__init__("Properties", parent)
        self.bridge = bridge
        self._current_kind: Optional[str] = None
        self._current_id: Optional[str] = None
        self._field_edits: dict[str, QLineEdit] = {}

        container = QWidget()
        self._layout = QVBoxLayout(container)

        self.header = QLabel("No selection")
        self.header.setStyleSheet("font-weight: bold; font-size: 13px;")
        self._layout.addWidget(self.header)

        self.form_container = QWidget()
        self.form_layout = QFormLayout(self.form_container)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.form_container)
        self._layout.addWidget(scroll, stretch=1)

        button_row = QHBoxLayout()
        self.apply_btn = QPushButton("Apply Changes")
        self.apply_btn.clicked.connect(self._apply)
        self.delete_btn = QPushButton("Delete Object")
        self.delete_btn.setStyleSheet("color: #a83232;")
        self.delete_btn.clicked.connect(self._delete)
        button_row.addWidget(self.apply_btn)
        button_row.addWidget(self.delete_btn)
        self._layout.addLayout(button_row)

        self.setWidget(container)
        self._set_buttons_enabled(False)

    def _set_buttons_enabled(self, enabled: bool) -> None:
        self.apply_btn.setEnabled(enabled)
        self.delete_btn.setEnabled(enabled)

    def clear(self) -> None:
        while self.form_layout.rowCount():
            self.form_layout.removeRow(0)
        self._field_edits.clear()
        self.header.setText("No selection")
        self._current_kind = None
        self._current_id = None
        self._set_buttons_enabled(False)

    def show_object(self, kind: str, obj_id: str) -> None:
        """kind is 'CV', 'FL', or 'CF'."""
        obj = self._fetch(kind, obj_id)
        self._current_kind = kind
        self._current_id = obj_id

        while self.form_layout.rowCount():
            self.form_layout.removeRow(0)
        self._field_edits.clear()

        self.header.setText(f"{kind}  {obj_id}")

        for record_id, fields in obj.records.items():
            group_label = QLabel(f"— {record_id} —")
            group_label.setStyleSheet("color: #555; font-style: italic;")
            self.form_layout.addRow(group_label)
            for field_name, value in fields.items():
                edit = QLineEdit(str(value))
                key = f"{record_id}:{field_name}"
                self._field_edits[key] = edit
                self.form_layout.addRow(field_name, edit)

        self._set_buttons_enabled(True)

    def _fetch(self, kind: str, obj_id: str) -> Object:
        if kind == "CV":
            return self.bridge.get_cv(obj_id)
        if kind == "FL":
            return self.bridge.get_fl(obj_id)
        return self.bridge.get_cf(obj_id)

    def _apply(self) -> None:
        if not self._current_kind or not self._current_id:
            return
        obj = self._fetch(self._current_kind, self._current_id)
        for key, edit in self._field_edits.items():
            _, field_name = key.split(":", 1)
            new_val = edit.text()
            if obj.get_field(field_name) != new_val:
                self.bridge.update_field(obj, field_name, new_val)
                obj = self._fetch(self._current_kind, self._current_id)
        self.object_changed.emit()

    def _delete(self) -> None:
        if not self._current_kind or not self._current_id:
            return
        self.bridge.remove_object(self._current_id)
        self.clear()
        self.object_changed.emit()
