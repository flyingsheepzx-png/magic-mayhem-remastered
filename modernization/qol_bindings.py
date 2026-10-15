"""Versioned, save-independent spell-key layout for the single-player QoL trial.

This module owns the on-disk contract and deterministic binding rules. Native
input must supply an already-validated equipped (tray, slot) identity.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile

KEYS = "QWERASDFZXCV"
TRAY_COUNT = 3
SLOTS_PER_TRAY = 21
DEFAULT_PATH = Path(__file__).resolve().parent / "config" / "qol-hotkeys.json"


def _slot(tray: int, slot: int) -> tuple[int, int]:
    if type(tray) is not int or type(slot) is not int:
        raise ValueError("Tray and slot must be integer indexes")
    if not (0 <= tray < TRAY_COUNT and 0 <= slot < SLOTS_PER_TRAY):
        raise ValueError("Unknown tray or slot")
    return tray, slot


def _key(key: str) -> str:
    if type(key) is not str or len(key) != 1 or key.upper() not in KEYS:
        raise ValueError("Unsupported spell key")
    return key.upper()


class Layout:
    def __init__(self, bindings: dict[str, tuple[int, int]] | None = None):
        self.bindings = dict(bindings or {})
        if any(_key(key) != key or _slot(*value) != value
               for key, value in self.bindings.items()):
            raise ValueError("Invalid layout")
        if len(set(self.bindings.values())) != len(self.bindings):
            raise ValueError("Multiple keys assigned to one slot")

    def bind(self, key: str, tray: int, slot: int) -> bool:
        key, target = _key(key), _slot(tray, slot)
        if self.bindings.get(key) == target:
            return False
        # The key moves directly. A previous key on the new slot is displaced.
        for old_key, old_slot in tuple(self.bindings.items()):
            if old_slot == target or old_key == key:
                del self.bindings[old_key]
        self.bindings[key] = target
        return True

    def clear(self, tray: int, slot: int) -> bool:
        target = _slot(tray, slot)
        for key, old_slot in tuple(self.bindings.items()):
            if old_slot == target:
                del self.bindings[key]
                return True
        return False

    def key_for(self, tray: int, slot: int) -> str | None:
        target = _slot(tray, slot)
        return next((key for key, value in self.bindings.items() if value == target), None)

    def active_slot(self, key: str, equipped: set[tuple[int, int]]) -> tuple[int, int] | None:
        slot = self.bindings.get(_key(key))
        return slot if slot in equipped else None

    def to_json(self) -> dict:
        return {"version": 1, "bindings": {key: {"tray": value[0], "slot": value[1]}
                                         for key, value in sorted(self.bindings.items())}}

    @classmethod
    def from_json(cls, value: object) -> "Layout":
        if type(value) is not dict or set(value) != {"version", "bindings"} or value["version"] != 1:
            raise ValueError("Unsupported layout version")
        records = value["bindings"]
        if type(records) is not dict or len(records) > len(KEYS):
            raise ValueError("Invalid bindings")
        bindings = {}
        for key, record in records.items():
            if type(record) is not dict or set(record) != {"tray", "slot"}:
                raise ValueError("Invalid binding record")
            bindings[key] = _slot(record["tray"], record["slot"])
        return cls(bindings)

    @classmethod
    def load(cls, path: Path = DEFAULT_PATH) -> "Layout":
        if not path.exists():
            return cls()
        return cls.from_json(json.loads(path.read_text(encoding="utf-8")))

    def save(self, path: Path = DEFAULT_PATH) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        serialized = json.dumps(self.to_json(), indent=2, ensure_ascii=False) + "\n"
        temp = None
        try:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n",
                                             dir=path.parent, prefix="qol-hotkeys-",
                                             suffix=".tmp", delete=False) as file:
                temp = Path(file.name)
                file.write(serialized)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temp, path)
        finally:
            if temp is not None and temp.exists():
                temp.unlink()
