import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dotenv import dotenv_values

from studipsync.app import save_configuration
from studipsync.drive_client import parse_picker_callback


class PickerCallbackTests(unittest.TestCase):
    def test_returns_code_and_single_folder_id(self):
        result = parse_picker_callback(
            "http://localhost/?code=auth-code&state=state-1&picked_file_ids=folder-1",
            "state-1",
        )

        self.assertEqual(result, ("auth-code", "folder-1"))

    def test_rejects_mismatched_state(self):
        with self.assertRaisesRegex(ValueError, "nicht sicher zugeordnet"):
            parse_picker_callback(
                "http://localhost/?code=auth-code&state=wrong&picked_file_ids=folder-1",
                "state-1",
            )

    def test_rejects_cancelled_selection(self):
        with self.assertRaisesRegex(ValueError, "abgebrochen"):
            parse_picker_callback(
                "http://localhost/?error=access_denied&state=state-1",
                "state-1",
            )

    def test_requires_exactly_one_folder(self):
        with self.assertRaisesRegex(ValueError, "genau einen"):
            parse_picker_callback(
                "http://localhost/?code=auth-code&state=state-1&picked_file_ids=a,b",
                "state-1",
            )


class SaveConfigurationTests(unittest.TestCase):
    def test_saves_settings_using_bundled_google_credentials(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            data_directory = root / "data"
            data_directory.mkdir()
            credentials = root / "credentials.json"
            credentials.write_text('{"installed": {}}', encoding="utf-8")

            with patch("studipsync.app.data_dir", return_value=data_directory):
                with patch("studipsync.app.bundled_credentials_path", return_value=credentials):
                    save_configuration("student", "secret", "")

            values = dotenv_values(data_directory / ".env")
            self.assertEqual(values["STUDIP_USER"], "student")
            self.assertEqual(values["STUDIP_PASSWORD"], "secret")
            self.assertEqual(values["DRIVE_ROOT_FOLDER_ID"], "")
            self.assertEqual(values["DRIVE_ROOT_FOLDER_NAME"], "")
            self.assertTrue((data_directory / "credentials.json").is_file())
            self.assertEqual(
                (data_directory / "credentials.json").read_text(encoding="utf-8"),
                '{"installed": {}}',
            )


if __name__ == "__main__":
    unittest.main()
