from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class EthernetCommand:
    action: str = ""
    data: Dict = field(default_factory=dict)

    def as_str(self) -> str:
        return f"{self.__class__.__name__}({self.action})[{self.data}]"

    def to_dict(self) -> Dict:
        return {"action": self.action, "data": self.data}

    @staticmethod
    def from_dict(d: Dict) -> "EthernetCommand":
        return EthernetCommand(
            action=str(d.get("action", "")),
            data=dict(d.get("data", {}) or {}),
        )
