"""Spec/Epic ID parsing and normalization.

nspec uses prefixed IDs:
  - Epics: E### (e.g. E001)
  - Specs: S### (e.g. S118)

Both may optionally include a single letter suffix (e.g. S100a) for splits.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

SPEC_REF_RE = re.compile(r"^(?P<prefix>[ES])(?P<number>\d{3})(?P<suffix>[a-z]?)$", re.IGNORECASE)


@dataclass(frozen=True)
class SpecRef:
    prefix: str  # "E" or "S"
    number: int  # 0-999 (stored as int, rendered as 3 digits)
    suffix: str = ""  # optional single letter, lowercase

    def __post_init__(self) -> None:
        prefix = self.prefix.upper()
        if prefix not in {"E", "S"}:
            raise ValueError(f"Invalid spec ref prefix: {self.prefix!r}")
        if not (0 <= self.number <= 999):
            raise ValueError(f"Invalid spec ref number: {self.number!r}")
        if self.suffix and (len(self.suffix) != 1 or not self.suffix.isalpha()):
            raise ValueError(f"Invalid spec ref suffix: {self.suffix!r}")
        object.__setattr__(self, "prefix", prefix)
        object.__setattr__(self, "suffix", self.suffix.lower())

    @property
    def text(self) -> str:
        return f"{self.prefix}{self.number:03d}{self.suffix}"

    @property
    def is_epic(self) -> bool:
        return self.prefix == "E"


def parse_spec_ref(raw: str) -> SpecRef:
    """Parse a prefixed ID like 'S004' or 'E001' (optionally with a suffix, e.g. 'S100a')."""
    value = (raw or "").strip()
    match = SPEC_REF_RE.match(value)
    if not match:
        raise ValueError(f"Invalid spec ref: {raw!r} (expected E### or S###, optional suffix)")
    prefix = match.group("prefix").upper()
    number = int(match.group("number"))
    suffix = match.group("suffix") or ""
    return SpecRef(prefix=prefix, number=number, suffix=suffix)


def normalize_spec_ref(raw: str) -> str:
    """Normalize to canonical 'E###'/'S###' (+ optional lowercase suffix)."""
    return parse_spec_ref(raw).text


def spec_ref_number(raw: str) -> int:
    """Extract numeric portion from a normalized ref."""
    return parse_spec_ref(raw).number
