import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from studipsync.app_paths import clear_user_data, data_dir


class PackagedDataDirectoryTests(unittest.TestCase):
    def test_imports_existing_project_configuration_and_sync_state(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = root / "project"
            executable_dir = project / "dist"
            local_app_data = root / "local"
            executable_dir.mkdir(parents=True)
            (project / "studipsync.py").write_text("", encoding="utf-8")
            executable = executable_dir / "StudIPSync.exe"
            executable.write_text("", encoding="utf-8")
            for name in (".env", "credentials.json", "token.json", "sync_state.json"):
                (project / name).write_text(name, encoding="utf-8")

            with (
                patch.dict(os.environ, {"LOCALAPPDATA": str(local_app_data)}),
                patch("studipsync.app_paths.sys.executable", str(executable)),
                patch("studipsync.app_paths.sys.frozen", True, create=True),
            ):
                result = data_dir()

            for name in (".env", "credentials.json", "token.json", "sync_state.json"):
                self.assertEqual((result / name).read_text(encoding="utf-8"), name)


class ClearUserDataTests(unittest.TestCase):
    def test_removes_account_and_sync_data_but_keeps_app_oauth_config(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for name in (
                ".env",
                "token.json",
                "sync_state.json",
                "sync.log",
                "credentials.json",
            ):
                (root / name).write_text(name, encoding="utf-8")
            temp_files = root / "temp" / "course"
            temp_files.mkdir(parents=True)
            (temp_files / "lecture.pdf").write_text("download", encoding="utf-8")

            clear_user_data(root)

            for name in (".env", "token.json", "sync_state.json", "sync.log"):
                self.assertFalse((root / name).exists())
            self.assertTrue((root / "credentials.json").is_file())
            self.assertFalse((root / "temp").exists())


if __name__ == "__main__":
    unittest.main()
