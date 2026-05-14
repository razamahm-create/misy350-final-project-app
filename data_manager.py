import json
from pathlib import Path
from datetime import datetime, date

class DataManager:
    """Handles all JSON database operations."""
    
    def __init__(self):
        self.users_path = Path("users.json")
        self.timeslots_path = Path("timeslots.json")
        self.bookings_path = Path("bookings.json")
        self.initialize_defaults()

    def initialize_defaults(self):
        """Creates files with sample data if they don't exist so the demo works immediately."""
        if not self.users_path.exists():
            self._save_json(self.users_path, [
                {"user_id": "doc-1", "full_name": "Dr. Smith", "email": "doctor@clinic.com", "password": "doc", "role": "Doctor", "registered_at": str(datetime.now())},
                {"user_id": "pat-1", "full_name": "Demo Patient", "email": "patient@email.com", "password": "pat", "role": "Patient", "registered_at": str(datetime.now())}
            ])

        if not self.timeslots_path.exists():
            # One open slot, one booked slot
            self._save_json(self.timeslots_path, [
                {"slot_id": "slot-1", "doctor_id": "doc-1", "date": str(date.today()), "time": "10:00 AM", "status": "Booked"},
                {"slot_id": "slot-2", "doctor_id": "doc-1", "date": str(date.today()), "time": "02:00 PM", "status": "Open"}
            ])

        if not self.bookings_path.exists():
            # Link the booked slot to our demo patient
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

    # --- Generic Load/Save Methods ---
    def _load_json(self, path):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _save_json(self, path, data):
        path.write_text(json.dumps(data, indent=4), encoding="utf-8")

    # --- Specific Entity Methods ---
    def get_users(self): return self._load_json(self.users_path)
    def save_users(self, users): self._save_json(self.users_path, users)

    def get_timeslots(self): return self._load_json(self.timeslots_path)
    def save_timeslots(self, timeslots): self._save_json(self.timeslots_path, timeslots)

    def get_bookings(self): return self._load_json(self.bookings_path)
    def save_bookings(self, bookings): self._save_json(self.bookings_path, bookings)