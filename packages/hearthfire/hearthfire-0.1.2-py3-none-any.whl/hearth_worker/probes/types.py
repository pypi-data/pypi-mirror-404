"""
Probe Result Types
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProbeResult:
    probe: str
    found: bool
    version: str | None = None
    path: str | None = None
    error: str | None = None
    raw: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result = {
            "probe": self.probe,
            "found": self.found,
        }
        if self.version:
            result["version"] = self.version
        if self.path:
            result["path"] = self.path
        if self.error:
            result["error"] = self.error
        if self.extra:
            result.update(self.extra)
        return result
