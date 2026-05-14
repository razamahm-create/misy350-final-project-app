import unittest
from unittest.mock import MagicMock
from services import AuthService, ClinicService

class TestAuthService(unittest.TestCase):
    def setUp(self):
        # Create a mock database so we don't overwrite real JSON files
        self.mock_db = MagicMock()
        self.auth_service = AuthService(self.mock_db)
        
        # Fake user data
        self.mock_db.get_users.return_value = [
            {"user_id": "1", "email": "test@clinic.com", "password": "password123", "role": "Patient"}
        ]

    def test_successful_login(self):
        user = self.auth_service.login("test@clinic.com", "password123")
        self.assertIsNotNone(user)
        self.assertEqual(user["role"], "Patient")

    def test_failed_login_raises_error(self):
        with self.assertRaises(ValueError):
            self.auth_service.login("wrong@clinic.com", "badpassword")

    def test_duplicate_registration_raises_error(self):
        with self.assertRaises(ValueError):
            self.auth_service.register("John Doe", "test@clinic.com", "newpass", "Patient")

class TestClinicService(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.clinic_service = ClinicService(self.mock_db)
        
        self.mock_db.get_bookings.return_value = [
            {"booking_id": "b1", "slot_id": "s1", "patient_id": "p1", "status": "Scheduled"}
        ]

    def test_update_booking_status_success(self):
        # Update the status and verify it saved
        self.clinic_service.update_booking_status("b1", "Completed")
        
        # Verify save_bookings was called
        self.mock_db.save_bookings.assert_called_once()
        
        # Check that the modified booking list passed to save_bookings has the updated status
        saved_data = self.mock_db.save_bookings.call_args[0][0]
        self.assertEqual(saved_data[0]["status"], "Completed")

if __name__ == '__main__':
    unittest.main()