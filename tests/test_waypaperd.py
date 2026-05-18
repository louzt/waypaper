import argparse
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch

from waypaper import waypaperd


class WaypaperdTests(unittest.TestCase):
    def test_parse_args_uses_default_interval(self):
        args = waypaperd.parse_args([])
        self.assertEqual(args.interval, waypaperd.DEFAULT_INTERVAL_SECONDS)

    def test_parse_args_accepts_custom_interval(self):
        args = waypaperd.parse_args(["600"])
        self.assertEqual(args.interval, 600)

    def test_positive_interval_rejects_non_positive_values(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            waypaperd.positive_interval("0")

    def test_build_waypaper_command_uses_current_python(self):
        self.assertEqual(
            waypaperd.build_waypaper_command(),
            [sys.executable, "-m", "waypaper", "--random"],
        )

    def test_trigger_random_wallpaper_returns_subprocess_code(self):
        with patch("waypaper.waypaperd.subprocess.run") as run_mock:
            run_mock.return_value.returncode = 7
            self.assertEqual(waypaperd.trigger_random_wallpaper(["waypaper"]), 7)
            run_mock.assert_called_once_with(["waypaper"], check=False)

    def test_trigger_random_wallpaper_passes_environment(self):
        environment = {"WAYLAND_DISPLAY": "wayland-1"}
        with patch("waypaper.waypaperd.subprocess.run") as run_mock:
            run_mock.return_value.returncode = 0

            self.assertEqual(waypaperd.trigger_random_wallpaper(["waypaper"], environment=environment), 0)

            run_mock.assert_called_once_with(["waypaper"], check=False, env=environment)

    def test_build_waypaper_environment_keeps_existing_display(self):
        with tempfile.TemporaryDirectory() as runtime_dir:
            environment = waypaperd.build_waypaper_environment(
                {"DISPLAY": ":0", "XDG_RUNTIME_DIR": runtime_dir},
                wait_seconds=0,
            )

        self.assertEqual(environment["DISPLAY"], ":0")
        self.assertNotIn("WAYLAND_DISPLAY", environment)

    def test_build_waypaper_environment_sets_wayland_display_from_socket(self):
        with tempfile.TemporaryDirectory() as runtime_dir:
            socket_path = f"{runtime_dir}/wayland-1"
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as wayland_socket:
                wayland_socket.bind(socket_path)

                environment = waypaperd.build_waypaper_environment(
                    {"XDG_RUNTIME_DIR": runtime_dir},
                    wait_seconds=0,
                )

        self.assertEqual(environment["WAYLAND_DISPLAY"], "wayland-1")

    def test_build_waypaper_environment_sets_wayland_display_when_display_exists(self):
        with tempfile.TemporaryDirectory() as runtime_dir:
            socket_path = f"{runtime_dir}/wayland-0"
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as wayland_socket:
                wayland_socket.bind(socket_path)

                environment = waypaperd.build_waypaper_environment(
                    {"DISPLAY": ":0", "XDG_RUNTIME_DIR": runtime_dir},
                    wait_seconds=0,
                )

        self.assertEqual(environment["DISPLAY"], ":0")
        self.assertEqual(environment["WAYLAND_DISPLAY"], "wayland-0")

    def test_build_waypaper_environment_adds_dbus_session_bus(self):
        with tempfile.TemporaryDirectory() as runtime_dir:
            bus_path = f"{runtime_dir}/bus"
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as bus_socket:
                bus_socket.bind(bus_path)

                environment = waypaperd.build_waypaper_environment(
                    {"DISPLAY": ":0", "XDG_RUNTIME_DIR": runtime_dir},
                    wait_seconds=0,
                )

        self.assertEqual(environment["DBUS_SESSION_BUS_ADDRESS"], f"unix:path={bus_path}")

    def test_build_waypaper_environment_times_out_without_socket(self):
        with tempfile.TemporaryDirectory() as runtime_dir:
            environment = waypaperd.build_waypaper_environment(
                {"XDG_RUNTIME_DIR": runtime_dir},
                wait_seconds=0,
            )

        self.assertNotIn("WAYLAND_DISPLAY", environment)

    def test_main_exits_cleanly_on_keyboard_interrupt(self):
        with patch("waypaper.waypaperd.build_waypaper_environment", return_value={"DISPLAY": ":0"}), patch(
            "waypaper.waypaperd.trigger_random_wallpaper", return_value=0
        ), patch(
            "waypaper.waypaperd.time.sleep", side_effect=KeyboardInterrupt
        ):
            self.assertEqual(waypaperd.main(["60"]), 0)


if __name__ == "__main__":
    unittest.main()