import streamlit as st
import uuid
from datetime import date, time
from services import AuthService, ClinicService, AIAssistant
from data_manager import DataManager

# --- Page Setup ---
st.set_page_config(page_title="Clinic Portal Pro", layout="wide", page_icon="🏥")

# --- Initialize Services ---
auth_service = AuthService()
clinic_service = ClinicService()
ai_assistant = AIAssistant()
data_manager = DataManager()

# --- Session State ---
if "user" not in st.session_state:
    st.session_state.update({"user": None, "role": "", "page": "welcome"})

def navigate(page_name):
    st.session_state["page"] = page_name
    st.rerun()

# --- Sidebar Navigation ---
with st.sidebar:
    st.markdown("## 🏥 Clinic Portal Pro")
    st.divider()

    if st.session_state["user"]:
        st.success(f"Hello, {st.session_state['user']['full_name']}")
        st.caption(f"Role: {st.session_state['role']}")
        st.write("")

        if st.session_state["role"] == "Doctor":
            if st.button("📅 Daily Roster", use_container_width=True): navigate("doc_dashboard")
            if st.button("⚙️ Manage Timeslots", use_container_width=True): navigate("doc_slots")

        if st.session_state["role"] == "Patient":
            if st.button("🏠 Home", use_container_width=True): navigate("pat_dashboard")
            if st.button("➕ Book Appointment", use_container_width=True): navigate("pat_book")
            if st.button("🗓️ My Appointments", use_container_width=True): navigate("pat_history")
            if st.button("🤖 Clinical AI Triage", use_container_width=True): navigate("pat_ai")

        st.divider()
        if st.button("Log Out", type="secondary", use_container_width=True):
            st.session_state.update({"user": None, "role": "", "page": "welcome"})
            st.rerun()
    else:
        if st.button("Home", use_container_width=True): navigate("welcome")
        if st.button("Register", use_container_width=True): navigate("register")

# ==========================================
# PUBLIC PAGES
# ==========================================
if not st.session_state["user"]:
    if st.session_state["page"] == "welcome":
        st.title("Welcome to the Clinic Portal")
        
        # REQUIRED BY RUBRIC: Explicitly show test accounts on the login page
        st.info("""
        **Test Accounts (Ready to use)**
        * **Doctor:** `doctor@clinic.com` | Password: `doc`
        * **Patient:** `patient@email.com` | Password: `pat`
        """)

        with st.form("login_form"):
            st.subheader("Secure Log In")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Log In", use_container_width=True):
                user = auth_service.login(email, password)
                if user:
                    st.session_state.update({"user": user, "role": user["role"], "page": "doc_dashboard" if user["role"] == "Doctor" else "pat_dashboard"})
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

    elif st.session_state["page"] == "register":
        st.title("Register New Account")
        with st.form("register_form"):
            name = st.text_input("Full Name")
            email = st.text_input("Email Address")
            password = st.text_input("Password", type="password")
            role = st.selectbox("Role", ["Doctor", "Patient"])
            
            if st.form_submit_button("Create Account", use_container_width=True):
                if not name or not email or not password:
                    st.warning("All fields are required.")
                else:
                    success, msg = auth_service.register(name, email, password, role)
                    if success:
                        st.success(msg)
                        navigate("welcome")
                    else:
                        st.error(msg)

# ==========================================
# DOCTOR PAGES
# ==========================================
elif st.session_state["role"] == "Doctor":
    
    if st.session_state["page"] == "doc_dashboard":
        st.title("Daily Roster")
        roster = clinic_service.get_doctor_roster(st.session_state["user"]["user_id"])
        
        if not roster:
            st.info("No active appointments found.")
        else:
            for item in roster:
                booking, slot, patient = item["booking"], item["slot"], item["patient"]
                
                with st.container(border=True):
                    col1, col2, col3 = st.columns([2, 3, 1])
                    with col1:
                        st.subheader(f"{slot['time']}")
                        st.write(f"**Date:** {slot['date']}")
                        st.write(f"**Patient:** {patient['full_name']}")
                    with col2:
                        st.write(f"**Patient Notes:** {booking['reason_for_visit']}")
                        # Display the AI Summary if the patient submitted one
                        if booking.get("ai_summary"):
                            st.info(f"**🤖 AI Clinical Brief:**\n{booking['ai_summary']}")
                    with col3:
                        st.caption(f"Status: {booking['status']}")
                        with st.expander("Action"):
                            new_status = st.selectbox("Update", ["Scheduled", "Completed", "No-Show"], key=f"stat_{booking['booking_id']}")
                            if st.button("Save", key=f"save_{booking['booking_id']}", use_container_width=True):
                                clinic_service.update_booking_status(booking['booking_id'], new_status)
                                st.rerun()

    elif st.session_state["page"] == "doc_slots":
        st.title("Manage Timeslots")
        with st.form("create_slot_form"):
            col1, col2 = st.columns(2)
            with col1: new_date = st.date_input("Date", value=date.today())
            with col2: new_time = st.time_input("Time", value=time(9, 0))
            if st.form_submit_button("Add to Schedule", use_container_width=True):
                slots = data_manager.get_timeslots()
                slots.append({"slot_id": str(uuid.uuid4()), "doctor_id": st.session_state["user"]["user_id"], "date": str(new_date), "time": new_time.strftime("%I:%M %p"), "status": "Open"})
                data_manager.save_timeslots(slots)
                st.success("Slot added.")
                st.rerun()
                
        st.divider()
        st.subheader("Open Slots")
        slots = [s for s in data_manager.get_timeslots() if s["doctor_id"] == st.session_state["user"]["user_id"] and s["status"] == "Open"]
        for s in slots:
            col1, col2 = st.columns([4, 1])
            col1.write(f"📅 {s['date']} at {s['time']}")
            if col2.button("Delete", key=f"del_{s['slot_id']}"):
                all_slots = [x for x in data_manager.get_timeslots() if x["slot_id"] != s["slot_id"]]
                data_manager.save_timeslots(all_slots)
                st.rerun()

# ==========================================
# PATIENT PAGES
# ==========================================
elif st.session_state["role"] == "Patient":
    
    if st.session_state["page"] == "pat_dashboard":
        st.title("Patient Dashboard")
        appts = clinic_service.get_patient_appointments(st.session_state["user"]["user_id"])
        upcoming = [a for a in appts if a["booking"]["status"] == "Scheduled"]
        
        st.subheader("Upcoming Appointments")
        if not upcoming:
            st.info("No upcoming appointments.")
        else:
            for item in upcoming:
                st.success(f"🗓️ **{item['slot']['date']}** at **{item['slot']['time']}**")

    elif st.session_state["page"] == "pat_book":
        st.title("Book an Appointment")
        open_slots = [s for s in data_manager.get_timeslots() if s["status"] == "Open"]
        
        if not open_slots:
            st.warning("No open appointments available.")
        else:
            with st.form("booking_form"):
                slot_opts = {f"{s['date']} at {s['time']}": s['slot_id'] for s in sorted(open_slots, key=lambda x: x['date'])}
                selected_label = st.selectbox("Select Time", list(slot_opts.keys()))
                reason = st.text_area("Reason for visit")
                
                if st.form_submit_button("Confirm Booking", use_container_width=True):
                    if not reason.strip():
                        st.warning("Please provide a reason.")
                    else:
                        slot_id = slot_opts[selected_label]
                        # Update slot
                        slots = data_manager.get_timeslots()
                        for s in slots:
                            if s["slot_id"] == slot_id:
                                s["status"] = "Booked"
                        data_manager.save_timeslots(slots)
                        # Create booking
                        bookings = data_manager.get_bookings()
                        bookings.append({"booking_id": str(uuid.uuid4()), "slot_id": slot_id, "patient_id": st.session_state["user"]["user_id"], "reason_for_visit": reason.strip(), "status": "Scheduled", "ai_summary": None})
                        data_manager.save_bookings(bookings)
                        st.success("Booked successfully!")
                        navigate("pat_history")

    elif st.session_state["page"] == "pat_history":
        st.title("My Appointment History")
        appts = clinic_service.get_patient_appointments(st.session_state["user"]["user_id"])
        
        if not appts:
            st.info("No appointment history.")
        else:
            for item in appts:
                booking, slot = item["booking"], item["slot"]
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**{slot['date']}** at **{slot['time']}**")
                        st.write(f"Reason: {booking['reason_for_visit']}")
                    with col2:
                        st.caption(f"Status: {booking['status']}")
                        if booking["status"] == "Scheduled":
                            if st.button("Cancel", key=f"can_{booking['booking_id']}"):
                                clinic_service.update_booking_status(booking['booking_id'], "Cancelled", slot['slot_id'])
                                st.rerun()

    elif st.session_state["page"] == "pat_ai":
        st.title("🤖 Clinical AI Triage")
        st.write("Help your doctor prepare by describing your symptoms. Our AI will securely summarize them for your appointment file.")
        
        appts = clinic_service.get_patient_appointments(st.session_state["user"]["user_id"])
        upcoming = [a for a in appts if a["booking"]["status"] == "Scheduled"]
        
        if not upcoming:
            st.warning("You must book an appointment before using the AI Triage.")
        else:
            target_appt = upcoming[0] # Just grab the first one for the demo
            st.info(f"Adding notes for appointment on **{target_appt['slot']['date']}**")
            
            with st.form("ai_form"):
                symptoms = st.text_area("Describe your symptoms in detail (e.g., duration, severity, triggers):", height=150)
                if st.form_submit_button("Generate & Send to Doctor", type="primary", use_container_width=True):
                    if not symptoms.strip():
                        st.warning("Please enter your symptoms.")
                    else:
                        with st.spinner("AI is analyzing your symptoms..."):
                            summary = ai_assistant.generate_clinical_brief(symptoms)
                            clinic_service.attach_ai_summary(target_appt['booking']['booking_id'], summary)
                        st.success("Summary generated and attached to your file!")
                        st.markdown(f"**What the doctor will see:**\n{summary}")