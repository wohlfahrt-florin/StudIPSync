import unittest
from unittest.mock import patch

from studipsync.calendar_watch import diff_snapshots, event_fingerprint
from studipsync.studip_client import StudIPClient


class EventFingerprintTests(unittest.TestCase):
    def test_description_change_changes_fingerprint(self):
        original = {"title": "Seminar", "description": "Raum A"}
        changed = {"title": "Seminar", "description": "Raum B"}

        self.assertNotEqual(
            event_fingerprint(original),
            event_fingerprint(changed),
        )

    def test_irrelevant_fields_do_not_change_fingerprint(self):
        original = {"title": "Seminar", "id": "first"}
        same_event = {"title": "Seminar", "id": "second"}

        self.assertEqual(
            event_fingerprint(original),
            event_fingerprint(same_event),
        )


class DiffSnapshotsTests(unittest.TestCase):
    def test_reports_added_and_changed_events(self):
        previous = {"course:unchanged": "a", "course:changed": "old"}
        current = {
            "course:unchanged": "a",
            "course:changed": "new",
            "course:added": "b",
        }

        added, changed = diff_snapshots(previous, current)

        self.assertEqual(added, ["course:added"])
        self.assertEqual(changed, ["course:changed"])


class StudIPRetryTests(unittest.TestCase):
    def test_retries_server_errors_then_returns_success(self):
        class Response:
            def __init__(self, status_code):
                self.status_code = status_code

            def raise_for_status(self):
                if self.status_code >= 400:
                    raise RuntimeError(f"HTTP {self.status_code}")

        class Session:
            def __init__(self):
                self.responses = iter([Response(500), Response(502), Response(200)])
                self.calls = 0

            def get(self, url, params=None, timeout=30):
                self.calls += 1
                return next(self.responses)

        session = Session()
        with patch("studipsync.studip_client.time.sleep"):
            response = StudIPClient._get_response(session, "https://example.test")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(session.calls, 3)

    def test_does_not_retry_client_errors(self):
        class Response:
            status_code = 404

            def raise_for_status(self):
                raise RuntimeError("HTTP 404")

        class Session:
            calls = 0

            def get(self, url, params=None, timeout=30):
                self.calls += 1
                return Response()

        session = Session()
        with self.assertRaisesRegex(RuntimeError, "404"):
            StudIPClient._get_response(session, "https://example.test")

        self.assertEqual(session.calls, 1)


if __name__ == "__main__":
    unittest.main()
