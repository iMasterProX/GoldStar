from pathlib import Path
from typing import List

from .models import PackMetadata


def scan_pack(pack_path: Path) -> PackMetadata:
    default_files = sorted(
        [p for p in pack_path.rglob("default_*") if p.is_file()]
    )
    item_texture = pack_path / "textures" / "item_texture.json"
    if not item_texture.is_file():
        item_texture = None
    icon_dir = pack_path / "textures" / "items"
    default_icons: List[Path] = []
    if icon_dir.is_dir():
        default_icons = sorted(
            [p for p in icon_dir.glob("default_*.png") if p.is_file()]
        )
    return PackMetadata(
        name=pack_path.name,
        path=pack_path,
        default_files=default_files,
        item_texture=item_texture,
        default_icons=default_icons,
    )


def scan_packs(root_path: Path) -> List[PackMetadata]:
    pack_dirs = sorted(
        [p for p in root_path.iterdir() if p.is_dir() and p.name.startswith("BLF_")]
    )
    return [scan_pack(p) for p in pack_dirs]