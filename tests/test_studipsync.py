import os
import tempfile
import unittest

from studipsync.sync_paths import absolute_studip_url, sanitize_filename, temp_path_for


class SanitizeFilenameTests(unittest.TestCase):
    def test_replaces_windows_forbidden_characters(self):
        self.assertEqual(sanitize_filename('Skript: Woche 1?.pdf'), "Skript_ Woche 1_.pdf")

    def test_empty_name_becomes_unnamed(self):
        self.assertEqual(sanitize_filename("   "), "unnamed")


class TempPathForTests(unittest.TestCase):
    def test_same_filename_in_two_courses_does_not_collide(self):
        with tempfile.TemporaryDirectory() as temp_root:
            path_a = temp_path_for("Mathe I", "Skript.pdf", temp_root=temp_root)
            path_b = temp_path_for("Physik I", "Skript.pdf", temp_root=temp_root)

            self.assertNotEqual(path_a, path_b)

            os.makedirs(os.path.dirname(path_a), exist_ok=True)
            with open(path_a, "wb") as fh:
                fh.write(b"mathe")

            self.assertTrue(os.path.exists(path_a))
            self.assertFalse(os.path.exists(path_b))

    def test_nested_course_folder_uses_sanitized_names(self):
        path = temp_path_for("WiSe 25/26", "Folien: Intro.pdf", temp_root="temp")
        self.assertEqual(path, os.path.join("temp", "WiSe 25_26", "Folien_ Intro.pdf"))


class AbsoluteStudipUrlTests(unittest.TestCase):
    def test_root_relative_href(self):
        self.assertEqual(
            absolute_studip_url("/sendfile.php?file_id=1", "https://studip.uni-halle.de"),
            "https://studip.uni-halle.de/sendfile.php?file_id=1",
        )

    def test_already_absolute_href_is_not_prefixed_again(self):
        href = "https://studip.uni-halle.de/sendfile.php?file_id=1"
        self.assertEqual(absolute_studip_url(href, "https://studip.uni-halle.de"), href)


if __name__ == "__main__":
    unittest.main()
