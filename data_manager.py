import json
import logging
from pathlib import Path
from datetime import datetime, date

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataManager:
    """Handles all JSON database operations with safe file I/O."""
    
    def __init__(self):
        self.users_path = Path("users.json")
        self.timeslots_path = Path("timeslots.json")
        self.bookings_path = Path("bookings.json")
        self.initialize_defaults()

    def initialize_defaults(self):
        """Creates files with sample data if they don't exist."""
        try:
            if not self.users_path.exists():
                self._save_json(self.users_path, [
                    {"user_id": "doc-1", "full_name": "Dr. Smith", "email": "doctor@clinic.com", "password": "doc", "role": "Doctor", "registered_at": str(datetime.now())},
                    {"user_id": "pat-1", "full_name": "Demo Patient", "email": "patient@email.com", "password": "pat", "role": "Patient", "registered_at": str(datetime.now())}
                ])
                logger.info("Initialized default users.json")

            if not self.timeslots_path.exists():
                self._save_json(self.timeslots_path, [
                    {"slot_id": "slot-1", "doctor_id": "doc-1", "date": str(date.today()), "time": "10:00 AM", "status": "Booked"},
                    {"slot_id": "slot-2", "doctor_id": "doc-1", "date": str(date.today()), "time": "02:00 PM", "status": "Open"}
                ])
                logger.info("Initialized default timeslots.json")

            if not self.bookings_path.exists():
                self._save_json(self.bookings_path, [
                    {
                        "booking_id": "book-1", 
                        "slot_id": "slot-1", 
                        "patient_id": "pat-1", 
                        "reason_for_visit": "Persistent headaches.", 
                        "status": "Scheduled",
                        "ai_summary": None 
                    }
                ])
                logger.info("Initialized default bookings.json")
        except Exception as e:
            logger.error(f"Failed to initialize default databases: {e}")
            raise IOError(f"Database initialization error: {e}")

    def _load_json(self, path):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            logger.warning(f"File not found: {path}. Returning empty list.")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Corrupted JSON in {path}: {e}")
            raise ValueError(f"Data corruption in {path.name}.")

    def _save_json(self, path, data):
        try:
            path.write_text(json.dumps(data, indent=4), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to save data to {path}: {e}")
            raise IOError(f"Could not write to {path.name}.")

    def get_users(self): return self._load_json(self.users_path)
    def save_users(self, users): self._save_json(self.users_path, users)

    def get_timeslots(self): return self._load_json(self.timeslots_path)
    def save_timeslots(self, timeslots): self._save_json(self.timeslots_path, timeslots)

    def get_bookings(self): return self._load_json(self.bookings_path)
    def save_bookings(self, bookings): self._save_json(self.bookings_path, bookings)