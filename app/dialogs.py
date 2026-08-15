"""
Simple modal dialogs for creating new Control Volumes and Flow Paths.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
)


class NewCVDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Control Volume")
        layout = QFormLayout(self)

        self.name_edit = QLineEdit("NEW-CV")
        self.pvol_spin = self._spin(101325.0, 0, 1e7)
        self.tatm_spin = self._spin(293.15, 0, 2000)
        self.rhum_spin = self._spin(0.5, 0, 1, step=0.05)
        self.altitude_spin = self._spin(0.0, -1000, 1000)
        self.height_spin = self._spin(3.0, 0.01, 1000)
        self.volume_spin = self._spin(100.0, 0.01, 1e7)

        layout.addRow("Name", self.name_edit)
        layout.addRow("Initial pressure (Pa)", self.pvol_spin)
        layout.addRow("Initial temperature (K)", self.tatm_spin)
        layout.addRow("Relative humidity", self.rhum_spin)
        layout.addRow("Base altitude (m)", self.altitude_spin)
        layout.addRow("Height (m)", self.height_spin)
        layout.addRow("Volume (m^3)", self.volume_spin)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    @staticmethod
    def _spin(value, minimum, maximum, step=1.0):
        spin = QDoubleSpinBox()
        spin.setRange(minimum, maximum)
        spin.setDecimals(4)
        spin.setSingleStep(step)
        spin.setValue(value)
        return spin

    def values(self) -> dict:
        return {
            "name": self.name_edit.text().strip() or "NEW-CV",
            "pvol": self.pvol_spin.value(),
            "tatm": self.tatm_spin.value(),
            "rhum": self.rhum_spin.value(),
            "base_altitude": self.altitude_spin.value(),
            "height": self.height_spin.value(),
            "volume": self.volume_spin.value(),
        }


class NewFLDialog(QDialog):
    def __init__(self, cv_ids: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Flow Path")
        layout = QFormLayout(self)

        self.name_edit = QLineEdit("NEW-FL")
        self.from_combo = QComboBox()
        self.to_combo = QComboBox()
        self.from_combo.addItems(cv_ids)
        self.to_combo.addItems(cv_ids)
        self.elev_from_spin = NewCVDialog._spin(0.0, -1000, 1000)
        self.elev_to_spin = NewCVDialog._spin(0.0, -1000, 1000)
        self.area_spin = NewCVDialog._spin(1.0, 0.0001, 1e5)
        self.length_spin = NewCVDialog._spin(1.0, 0.0001, 1e5)
        self.opening_spin = NewCVDialog._spin(1.0, 0.0, 1.0, step=0.1)

        layout.addRow("Name", self.name_edit)
        layout.addRow("From CV", self.from_combo)
        layout.addRow("To CV", self.to_combo)
        layout.addRow("From elevation (m)", self.elev_from_spin)
        layout.addRow("To elevation (m)", self.elev_to_spin)
        layout.addRow("Flow area (m^2)", self.area_spin)
        layout.addRow("Flow length (m)", self.length_spin)
        layout.addRow("Initial opening (0-1)", self.opening_spin)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def values(self) -> dict:
        return {
            "name": self.name_edit.text().strip() or "NEW-FL",
            "cv_from": self.from_combo.currentText()[2:],  # strip 'CV' prefix
            "cv_to": self.to_combo.currentText()[2:],
            "elev_from": self.elev_from_spin.value(),
            "elev_to": self.elev_to_spin.value(),
            "area": self.area_spin.value(),
            "length": self.length_spin.value(),
            "opening": self.opening_spin.value(),
        }
