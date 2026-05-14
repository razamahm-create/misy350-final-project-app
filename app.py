import streamlit as st
import uuid
from datetime import date, time
from services import AuthService, ClinicService, AIAssistant
from data_manager import DataManager

# --- Page Setup ---
st.set_page_config(page_title="Clinic Portal Pro", layout="wide", page_icon="🏥")

# --- Centralized Database Instance (Fixes Race Conditions) ---
@st.cache_resource
def get_database():
    return DataManager()

db = get_database()

# --- Initialize Services ---
auth_service = AuthService(db)
clinic_service = ClinicService(db)
ai_assistant = AIAssistant()

# --- Session State ---
if "user" not in st.session_state:
    st.session_state.update({"user": None, "role": ""})

# ==========================================
# UI COMPONENTS (Functions)
# ==========================================

def render_auth_page():
    st.title("Clinic Portal")
    st.info("**Test Accounts:**\n* **Doctor:** `doctor@clinic.com` / `doc`\n* **Patient:** `patient@email.com` / `pat`")
    
    tab1, tab2 = st.tabs(["Log In", "Register"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Log In", type="primary", use_container_width=True):
                try:
                    user = auth_service.login(email, password)
                    st.session_state.update({"user": user, "role": user["role"]})
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error("A system error occurred. Please try again.")

    with tab2:
        with st.form("register_form"):
            name = st.text_input("Full Name")
            reg_email = st.text_input("Email Address")
            reg_password = st.text_input("Password", type="password")
            role = st.selectbox("Role", ["Doctor", "Patient"])
            
            if st.form_submit_button("Create Account", use_container_width=True):
                if not name or not reg_email or not reg_password:
                    st.warning("All fields are required.")
                else:
                    try:
                        auth_service.register(name, reg_email, reg_password, role)
                        st.success("Account created successfully! Please Log In via the other tab.")
                    except ValueError as e:
                        st.error(str(e))

def render_doctor_dashboard():
    st.title(f"Doctor Dashboard: {st.session_state['user']['full_name']}")
    
    tab1, tab2 = st.tabs(["📋 Daily Roster", "⚙️ Manage Timeslots"])
    
    with tab1:
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
                        st.write(f"**Date:** {slot['date']} | **Patient:** {patient['full_name']}")
                    with col2:
                        st.write(f"**Patient Notes:** {booking['reason_for_visit']}")
                        if booking.get("ai_summary"):
                            st.info(f"**🤖 AI Clinical Brief:**\n{booking['ai_summary']}")
                    with col3:
                        st.caption(f"Status: {booking['status']}")
                        with st.popover("Update Status"):
                            new_status = st.selectbox("Status", ["Scheduled", "Completed", "No-Show", "Cancelled"], key=f"stat_{booking['booking_id']}")
                            if st.button("Save", key=f"save_{booking['booking_id']}", use_container_width=True):
                                try:
                                    clinic_service.update_booking_status(booking['booking_id'], new_status, slot['slot_id'])
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed to update: {e}")

    with tab2:
        with st.form("create_slot_form"):
            c1, c2 = st.columns(2)
            with c1: new_date = st.date_input("Date", value=date.today())
            with c2: new_time = st.time_input("Time", value=time(9, 0))
            if st.form_submit_button("Add to Schedule", type="primary", use_container_width=True):
                try:
                    slots = db.get_timeslots()
                    slots.append({"slot_id": str(uuid.uuid4()), "doctor_id": st.session_state["user"]["user_id"], "date": str(new_date), "time": new_time.strftime("%I:%M %p"), "status": "Open"})
                    db.save_timeslots(slots)
                    st.success("Slot added.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving timeslot: {e}")
                    
        st.subheader("Open Slots")
        slots = [s for s in db.get_timeslots() if s["doctor_id"] == st.session_state["user"]["user_id"] and s["status"] == "Open"]
        for s in slots:
            c1, c2 = st.columns([4, 1])
            c1.write(f"📅 {s['date']} at {s['time']}")
            if c2.button("Delete", key=f"del_{s['slot_id']}"):
                all_slots = [x for x in db.get_timeslots() if x["slot_id"] != s["slot_id"]]
                db.save_timeslots(all_slots)
                st.rerun()

def render_patient_dashboard():
    st.title(f"Patient Portal: {st.session_state['user']['full_name']}")
    
    tab1, tab2, tab3 = st.tabs(["🏠 My Schedule", "➕ Book Appointment", "🤖 AI Triage"])
    
    with tab1:
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
                                try:
                                    clinic_service.update_booking_status(booking['booking_id'], "Cancelled", slot['slot_id'])
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error cancelling: {e}")

    with tab2:
        open_slots = [s for s in db.get_timeslots() if s["status"] == "Open"]
        if not open_slots:
            st.warning("No open appointments available.")
        else:
            with st.form("booking_form"):
                slot_opts = {f"{s['date']} at {s['time']}": s['slot_id'] for s in sorted(open_slots, key=lambda x: x['date'])}
                selected_label = st.selectbox("Select Time", list(slot_opts.keys()))
                reason = st.text_area("Reason for visit")
                
                if st.form_submit_button("Confirm Booking", type="primary", use_container_width=True):
                    if not reason.strip():
                        st.warning("Please provide a reason.")
                    else:
                        try:
                            slot_id = slot_opts[selected_label]
                            slots = db.get_timeslots()
                            for s in slots:
                                if s["slot_id"] == slot_id: s["status"] = "Booked"
                            db.save_timeslots(slots)
                            
                            bookings = db.get_bookings()
                            bookings.append({"booking_id": str(uuid.uuid4()), "slot_id": slot_id, "patient_id": st.session_state["user"]["user_id"], "reason_for_visit": reason.strip(), "status": "Scheduled", "ai_summary": None})
                            db.save_bookings(bookings)
                            
                            st.success("Booked successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Booking failed: {e}")

    with tab3:
        st.write("Help your doctor prepare by describing your symptoms.")
        appts = clinic_service.get_patient_appointments(st.session_state["user"]["user_id"])
        upcoming = [a for a in appts if a["booking"]["status"] == "Scheduled"]
        
        if not upcoming:
            st.warning("You must book an appointment before using the AI Triage.")
        else:
            target_appt = upcoming[0]
            st.info(f"Adding notes for appointment on **{target_appt['slot']['date']}**")
            
            with st.form("ai_form"):
                symptoms = st.text_area("Describe your symptoms in detail:", height=150)
                if st.form_submit_button("Generate & Send to Doctor", type="primary", use_container_width=True):
                    if not symptoms.strip():
                        st.warning("Please enter your symptoms.")
                    else:
                        try:
                            with st.spinner("AI is analyzing your symptoms..."):
                                summary = ai_assistant.generate_clinical_brief(symptoms)
                                clinic_service.attach_ai_summary(target_appt['booking']['booking_id'], summary)
                            st.success("Summary generated and attached to your file!")
                            st.markdown(f"**What the doctor will see:**\n{summary}")
                        except Exception as e:
                            st.error(str(e))

# ==========================================
# MAIN APP ROUTING
# ==========================================

with st.sidebar:
    if st.session_state["user"]:
        st.write(f"Logged in as **{st.session_state['user']['full_name']}**")
        if st.button("Log Out", use_container_width=True):
            st.session_state.update({"user": None, "role": ""})
            st.rerun()

if not st.session_state["user"]:
    render_auth_page()
elif st.session_state["role"] == "Doctor":
    render_doctor_dashboard()
elif st.session_state["role"] == "Patient":
    render_patient_dashboard()