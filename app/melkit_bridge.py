"""
ModelBridge wraps MELKIT's Toolkit class with everything the GUI needs:
graph layout (MELCOR files store no x/y coordinates, so we derive one),
field-level CRUD, and simple templates for creating new CVs/FLs.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import networkx as nx

from melkit.toolkit import Toolkit
from melkit.inputs import CV, FL, CF, Object


class ModelBridge:
    """Editor-facing wrapper around a MELKIT Toolkit instance."""

    def __init__(self, filename: str):
        self.filename = filename
        self.toolkit = Toolkit(filename)
        self._layout_cache: Dict[str, Tuple[float, float]] = {}

    # ------------------------------------------------------------------ #
    # Loading / reload
    # ------------------------------------------------------------------ #
    def reload(self) -> None:
        """Re-parse the input file (call after any write)."""
        self.toolkit = Toolkit(self.filename)
        self._layout_cache.clear()

    def cv_list(self) -> List[CV]:
        return self.toolkit.get_cv_list()

    def fl_list(self) -> List[FL]:
        return self.toolkit.get_fl_list()

    def cf_list(self) -> List[CF]:
        return self.toolkit.get_cf_list()

    def get_cv(self, cv_id: str) -> CV:
        return self.toolkit.get_cv(cv_id)

    def get_fl(self, fl_id: str) -> FL:
        return self.toolkit.get_fl(fl_id)

    def get_cf(self, cf_id: str) -> CF:
        return self.toolkit.get_cf(cf_id)

    # ------------------------------------------------------------------ #
    # Layout — MELCOR .inp files carry no visual coordinates, so we lay
    # the CV/FL graph out with a spring layout, cached until reload().
    # ------------------------------------------------------------------ #
    def compute_layout(self, scale: float = 260.0) -> Dict[str, Tuple[float, float]]:
        if self._layout_cache:
            return self._layout_cache

        graph = nx.Graph()
        for cv in self.cv_list():
            graph.add_node(cv.get_id())

        for fl in self.fl_list():
            frm, to = fl.get_field("KCVFM"), fl.get_field("KCVTO")
            if frm and to:
                frm_id, to_id = "CV" + frm, "CV" + to
                if frm_id in graph and to_id in graph:
                    graph.add_edge(frm_id, to_id, fl_id=fl.get_id())

        if len(graph) == 0:
            return {}

        pos = nx.spring_layout(graph, seed=42, k=1.8 / max(len(graph) ** 0.5, 1))
        self._layout_cache = {
            node: (float(xy[0]) * scale, float(xy[1]) * scale)
            for node, xy in pos.items()
        }
        return self._layout_cache

    def connections_for_cv(self, cv_id: str) -> List[FL]:
        return self.toolkit.get_fl_connections(cv_id)

    # ------------------------------------------------------------------ #
    # Field-level editing
    # ------------------------------------------------------------------ #
    def update_field(self, obj: Object, field: str, value: str) -> None:
        obj.update_field(field, value)
        self.toolkit.update_object(obj, overwrite=True)
        self.reload()

    def remove_object(self, obj_id: str) -> None:
        self.toolkit.remove_object(obj_id, overwrite=True)
        self.reload()

    # ------------------------------------------------------------------ #
    # ID allocation
    # ------------------------------------------------------------------ #
    def next_available_id(self, kind: str) -> str:
        """kind is 'CV' or 'FL'. Returns e.g. 'CV042'."""
        existing = self.cv_list() if kind == "CV" else self.fl_list()
        used = {obj.get_id()[2:] for obj in existing}
        for i in range(1, 1000):
            candidate = f"{i:03}"
            if candidate not in used:
                return kind + candidate
        raise RuntimeError(f"No available {kind} IDs left")

    # ------------------------------------------------------------------ #
    # Templates for new objects. These are deliberately minimal — enough
    # records for MELKIT to parse them back, with sensible defaults the
    # user edits afterward in the property panel.
    # ------------------------------------------------------------------ #
    def create_cv(
        self,
        name: str,
        pvol: float = 101325.0,
        tatm: float = 293.15,
        rhum: float = 0.5,
        base_altitude: float = 0.0,
        height: float = 3.0,
        volume: float = 100.0,
    ) -> CV:
        cv_id = self.next_available_id("CV")
        records = {
            f"{cv_id}00": {"NAME": name, "ICVTHR": "2", "ICVFF": "0", "ICVTYP": "1"},
            f"{cv_id}01": {"IPFSW": "0", "ICVACT": "0"},
            f"{cv_id}A0": {"ITYPTH": "3"},
            f"{cv_id}A1": {"PVOL": str(pvol)},
            f"{cv_id}A3": {"TATM": str(tatm), "RHUM": str(rhum)},
            f"{cv_id}A5": {"MLFR.4": "0.78"},
            f"{cv_id}A6": {"MLFR.5": "0.21"},
            f"{cv_id}A8": {"MLFR.8": "0.01"},
            f"{cv_id}B1": {"ALTITUDE": str(base_altitude), "VOLUME": "0.0"},
            f"{cv_id}B2": {
                "ALTITUDE": str(base_altitude + height),
                "VOLUME": str(volume),
            },
        }
        cv = CV(records)
        self.toolkit.write_object(cv, overwrite=True)
        self.reload()
        return cv

    def create_fl(
        self,
        name: str,
        cv_from: str,
        cv_to: str,
        elev_from: float = 0.0,
        elev_to: float = 0.0,
        area: float = 1.0,
        length: float = 1.0,
        opening: float = 1.0,
    ) -> FL:
        """cv_from / cv_to are 3-digit numeric CV ids, e.g. '015'."""
        fl_id = self.next_available_id("FL")
        records = {
            f"{fl_id}00": {
                "FLNAME": name,
                "KCVFM": cv_from,
                "KCVTO": cv_to,
                "ZFM": str(elev_from),
                "ZTO": str(elev_to),
            },
            f"{fl_id}01": {
                "FLARA": str(area),
                "FLLEN": str(length),
                "FLOPO": str(opening),
            },
            f"{fl_id}02": {"KFLGFL": "0"},
        }
        fl = FL(records)
        self.toolkit.write_object(fl, overwrite=True)
        self.reload()
        return fl
