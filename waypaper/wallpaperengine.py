"""Wallpaper Engine project helpers."""

import json
from pathlib import Path


def get_wallpaperengine_project_dir(full_path: Path | str) -> Path:
    full_path = Path(full_path)
    return full_path if full_path.is_dir() else full_path.parent


def get_wallpaperengine_project(full_path: Path | str) -> dict:
    image_dir = get_wallpaperengine_project_dir(full_path)
    with open(image_dir / "project.json", "r") as file:
        project = json.load(file)
    wallpaper_type = str(project.get("type", "unknown")).strip().lower() or "unknown"
    project["type"] = wallpaper_type
    project["title"] = str(project.get("title") or image_dir.name)
    return project


def get_wallpaperengine_entry_path(full_path: Path | str) -> Path | None:
    image_dir = get_wallpaperengine_project_dir(full_path)
    project = get_wallpaperengine_project(image_dir)
    entry_name = project.get("file")
    if not entry_name:
        return None

    entry_path = image_dir / entry_name
    if entry_path.exists():
        return entry_path
    return None


def get_wallpaperengine_recommended_backend(
        full_path: Path | str,
        installed_backends: list[str] | None = None) -> str:
    project = get_wallpaperengine_project(full_path)
    installed_backends = installed_backends or []

    if project["type"] == "video":
        if "mpvpaper" in installed_backends:
            return "mpvpaper"
        if "gslapper" in installed_backends:
            return "gslapper"
    return "linux-wallpaperengine"