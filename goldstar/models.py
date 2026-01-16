from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class PackMetadata:
    name: str
    path: Path
    default_files: List[Path] = field(default_factory=list)
    item_texture: Optional[Path] = None
    default_icons: List[Path] = field(default_factory=list)

    def summary_line(self) -> str:
        item_texture_flag = "yes" if self.item_texture else "no"
        return (
            f"{self.name} | defaults: {len(self.default_files)} | "
            f"item_texture: {item_texture_flag} | icons: {len(self.default_icons)}"
        )