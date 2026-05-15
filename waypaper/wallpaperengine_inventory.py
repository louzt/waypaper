"""Export Wallpaper Engine metadata and compatibility recommendations."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from waypaper.common import get_wallpaperengine_runtime_metadata
from waypaper.config import Config


def iter_wallpaperengine_project_dirs(workshop_dir: Path) -> list[Path]:
    return sorted(project_file.parent for project_file in workshop_dir.glob("*/project.json"))


def build_wallpaperengine_inventory(cf: Config) -> list[dict]:
    project_dirs = iter_wallpaperengine_project_dirs(cf.wallpaperengine_folder)
    return [get_wallpaperengine_runtime_metadata(project_dir, cf.installed_backends) for project_dir in project_dirs]


def export_wallpaperengine_inventory(cf: Config) -> tuple[Path, Path]:
    records = build_wallpaperengine_inventory(cf)
    by_type = Counter(record["type"] for record in records)
    by_backend = Counter(record["recommended_backend"] for record in records)

    json_path = cf.cache_dir / "wallpaperengine-index.json"
    jsonl_path = cf.cache_dir / "wallpaperengine-index.jsonl"

    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "workshop_dir": str(cf.wallpaperengine_folder),
                "count": len(records),
                "by_type": dict(by_type),
                "by_backend": dict(by_backend),
                "records": records,
            },
            handle,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )

    with jsonl_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=True, sort_keys=True))
            handle.write("\n")

    return json_path, jsonl_path


def main() -> int:
    cf = Config()
    cf.read()
    json_path, jsonl_path = export_wallpaperengine_inventory(cf)
    print(json_path)
    print(jsonl_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
