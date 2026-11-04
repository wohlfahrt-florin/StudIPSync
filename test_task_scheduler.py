import unittest

from task_scheduler import create_task_script


class CreateTaskScriptTests(unittest.TestCase):
    def test_creates_daily_command_for_packaged_app(self):
        script = create_task_script(
            "08:15",
            r"C:\Apps\StudIPSync.exe",
        )

        self.assertIn("-Daily -At '08:15'", script)
        self.assertIn("-Execute 'C:\\Apps\\StudIPSync.exe' -Argument '--sync'", script)
        self.assertIn("-LogonType Interactive", script)
        self.assertIn("-WakeToRun", script)

    def test_creates_daily_command_for_development_app(self):
        script = create_task_script(
            "18:30",
            r"C:\Python\python.exe",
            r"C:\Project\app.py",
        )

        self.assertIn(
            "-Execute 'C:\\Python\\python.exe' -Argument "
            "'\"C:\\Project\\app.py\" --sync'",
            script,
        )

    def test_rejects_invalid_time(self):
        with self.assertRaises(ValueError):
            create_task_script("25:61", "StudIPSync.exe")


if __name__ == "__main__":
    unittest.main()
