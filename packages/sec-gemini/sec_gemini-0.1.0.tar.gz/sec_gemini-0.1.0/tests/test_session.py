import unittest
from unittest.mock import MagicMock
from sec_gemini import Session
from sec_gemini import constants


class TestSession(unittest.TestCase):
    def setUp(self):
        self.session = Session(id="test-session")

    def test_status_update(self):
        self.assertEqual(self.session.status, "PENDING")

        # Test updating from event
        self.session.update_from_event({constants.SESSION_EVENT_STATUS: "RUNNING"})
        self.assertEqual(self.session.status, "RUNNING")

        # Test invalid status (should be ignored)
        self.session.update_from_event({constants.SESSION_EVENT_STATUS: "INVALID"})
        self.assertEqual(self.session.status, "RUNNING")

    def test_status_callback(self):
        callback = MagicMock()
        self.session.add_status_callback(callback)

        self.session.update_from_event({constants.SESSION_EVENT_STATUS: "COMPLETED"})

        callback.assert_called_with("test-session", "COMPLETED")

    def test_name(self):
        self.assertEqual(self.session.name, "New Session")
        self.session.name = "My Session"
        self.assertEqual(self.session.name, "My Session")


if __name__ == "__main__":
    unittest.main()
