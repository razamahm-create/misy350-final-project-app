import uuid
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

logger = logging.getLogger(__name__)
load_dotenv()

class AuthService:
    """Handles user login and registration."""
    def __init__(self, db_manager):
        self.db = db_manager

    def login(self, email, password):
        users = self.db.get_users()
        for user in users:
            if user["email"] == email.lower().strip() and user["password"] == password:
                logger.info(f"User {email} logged in successfully.")
                return user
        logger.warning(f"Failed login attempt for {email}.")
        raise ValueError("Invalid email or password.")

    def register(self, full_name, email, password, role):
        users = self.db.get_users()
        clean_email = email.lower().strip()
        
        if any(u["email"] == clean_email for u in users):
            logger.warning(f"Registration failed: {clean_email} already exists.")
            raise ValueError("Email already registered.")

        new_user = {
            "user_id": str(uuid.uuid4()),
            "full_name": full_name.strip(),
            "email": clean_email,
            "password": password,
            "role": role,
            "registered_at": str(datetime.now())
        }
        users.append(new_user)
        self.db.save_users(users)
        logger.info(f"New user registered: {clean_email}")
        return new_user


class ClinicService:
    """Handles the core CRUD logic for appointments."""
    def __init__(self, db_manager):
        self.db = db_manager

    def get_doctor_roster(self, doctor_id):
        bookings = self.db.get_bookings()
        timeslots = self.db.get_timeslots()
        users = self.db.get_users()
        
        roster = []
        for b in bookings:
            if b["status"] in ["Scheduled", "Completed", "No-Show"]:
                slot = next((s for s in timeslots if s["slot_id"] == b["slot_id"] and s["doctor_id"] == doctor_id), None)
                if slot:
                    patient = next((u for u in users if u["user_id"] == b["patient_id"]), None)
                    roster.append({"booking": b, "slot": slot, "patient": patient})
        return roster

    def get_patient_appointments(self, patient_id):
        bookings = self.db.get_bookings()
        timeslots = self.db.get_timeslots()
        
        my_appts = []
        for b in bookings:
            if b["patient_id"] == patient_id:
                slot = next((s for s in timeslots if s["slot_id"] == b["slot_id"]), None)
                if slot:
                    my_appts.append({"booking": b, "slot": slot})
        return my_appts

    def update_booking_status(self, booking_id, new_status, slot_id=None):
        bookings = self.db.get_bookings()
        booking_found = False
        
        for b in bookings:
            if b["booking_id"] == booking_id:
                b["status"] = new_status
                booking_found = True
                break
                
        if not booking_found:
            raise KeyError(f"Booking ID {booking_id} not found.")
            
        self.db.save_bookings(bookings)
        logger.info(f"Booking {booking_id} updated to {new_status}.")
        
        if new_status == "Cancelled" and slot_id:
            timeslots = self.db.get_timeslots()
            for s in timeslots:
                if s["slot_id"] == slot_id:
                    s["status"] = "Open"
                    break
            self.db.save_timeslots(timeslots)

    def attach_ai_summary(self, booking_id, summary_text):
        bookings = self.db.get_bookings()
        for b in bookings:
            if b["booking_id"] == booking_id:
                b["ai_summary"] = summary_text
                break
        self.db.save_bookings(bookings)


class AIAssistant:
    """Handles the OpenAI API connection."""
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.error("OpenAI API Key is missing from environment.")
            
    def generate_clinical_brief(self, patient_notes):
        if not self.api_key:
            raise EnvironmentError("OpenAI API Key not found. Please check your .env file.")
        
        client = OpenAI(api_key=self.api_key)
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a clinical assistant. Summarize the patient's symptoms into a brief, professional bulleted list for the doctor. Keep it under 3 bullet points."},
                    {"role": "user", "content": patient_notes}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API Error: {e}")
            raise RuntimeError("Failed to generate AI summary. Please try again later.")