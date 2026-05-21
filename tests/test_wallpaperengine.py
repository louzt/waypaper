import json
import tempfile
import unittest
from pathlib import Path

from waypaper.wallpaperengine import (
    get_wallpaperengine_entry_path,
    get_wallpaperengine_project,
    get_wallpaperengine_project_dir,
    get_wallpaperengine_recommended_backend,
)


class WallpaperEngineHelpersTest(unittest.TestCase):
    def test_project_dir_accepts_project_directory_or_child_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            child_path = project_dir / "preview.jpg"

            self.assertEqual(get_wallpaperengine_project_dir(project_dir), project_dir)
            self.assertEqual(get_wallpaperengine_project_dir(child_path), project_dir)

    def test_project_metadata_normalizes_type_and_title(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            (project_dir / "project.json").write_text(json.dumps({"type": " Video "}))

            project = get_wallpaperengine_project(project_dir)

            self.assertEqual(project["type"], "video")
            self.assertEqual(project["title"], project_dir.name)

    def test_entry_path_returns_existing_project_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            entry_path = project_dir / "wallpaper.mp4"
            entry_path.touch()
            (project_dir / "project.json").write_text(json.dumps({"type": "video", "file": entry_path.name}))

            self.assertEqual(get_wallpaperengine_entry_path(project_dir / "preview.jpg"), entry_path)

    def test_recommended_backend_prefers_video_native_backends_for_video_projects(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            (project_dir / "project.json").write_text(json.dumps({"type": "video"}))

            self.assertEqual(get_wallpaperengine_recommended_backend(project_dir, ["mpvpaper"]), "mpvpaper")
            self.assertEqual(get_wallpaperengine_recommended_backend(project_dir, ["gslapper"]), "gslapper")
            self.assertEqual(get_wallpaperengine_recommended_backend(project_dir, []), "linux-wallpaperengine")

    def test_recommended_backend_keeps_scene_projects_on_linux_wallpaperengine(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            (project_dir / "project.json").write_text(json.dumps({"type": "scene"}))

            self.assertEqual(get_wallpaperengine_recommended_backend(project_dir, ["mpvpaper"]), "linux-wallpaperengine")


if __name__ == "__main__":
    unittest.main()