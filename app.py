import streamlit as st
import json
from pathlib import Path
from datetime import datetime, date, time
import uuid

# set the layout
st.set_page_config(page_title="Clinic Portal MVP", layout="centered")

# keep track of login status, user details, and which page we are on so it doesn't reset
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user" not in st.session_state:
    st.session_state["user"] = None
if "role" not in st.session_state:
    st.session_state["role"] = ""
if "page" not in st.session_state:
    st.session_state["page"] = "welcome"
if "selected_booking_id" not in st.session_state:
    st.session_state["selected_booking_id"] = None
if "selected_slot_id" not in st.session_state:
    st.session_state["selected_slot_id"] = None

# setup file paths for our data storage
users_path = Path("users.json")
timeslots_path = Path("timeslots.json")
bookings_path = Path("bookings.json")

# create some default demo accounts if the file doesn't exist yet
if not users_path.exists():
    users_path.write_text(json.dumps([
        {
            "user_id": "doc-1",
            "full_name": "Dr. Smith",
            "email": "doctor@clinic.com",
            "password": "doc",
            "role": "Doctor",
            "registered_at": str(datetime.now())
        },
        {
            "user_id": "pat-1",
            "full_name": "Demo Patient",
            "email": "patient@email.com",
            "password": "pat",
            "role": "Patient",
            "registered_at": str(datetime.now())
        }
    ], indent=4), encoding="utf-8")

# add a default timeslot just to have something in the system
if not timeslots_path.exists():
    timeslots_path.write_text(json.dumps([
        {
            "slot_id": "slot-1",
            "doctor_id": "doc-1",
            "date": str(date.today()),
            "time": "10:00 AM",
            "status": "Open"
        }
    ], indent=4), encoding="utf-8")

if not bookings_path.exists():
    bookings_path.write_text(json.dumps([], indent=4), encoding="utf-8")

# try to load data, if it fails just make an empty list so the app doesn't crash
try: users = json.loads(users_path.read_text(encoding="utf-8"))
except: users = []

try: timeslots = json.loads(timeslots_path.read_text(encoding="utf-8"))
except: timeslots = []

try: bookings = json.loads(bookings_path.read_text(encoding="utf-8"))
except: bookings = []

# build the sidebar menu
with st.sidebar:
    st.markdown("## 🏥 Clinic Portal")

    # what to show when someone is actually logged in
    if st.session_state["logged_in"]:
        st.success(f"Welcome, {st.session_state['user']['full_name']}")
        st.caption(f"Role: {st.session_state['role']}")

        # doctor specific menu
        if st.session_state["role"] == "Doctor":
            if st.button("Doctor Dashboard", use_container_width=True, key="nav_doc_dash"):
                st.session_state["page"] = "doctor_dashboard"
                st.session_state["selected_booking_id"] = None
                st.rerun()
            if st.button("Create Timeslots", use_container_width=True, key="nav_create_slot"):
                st.session_state["page"] = "create_timeslot"
                st.rerun()

        # patient specific menu
        if st.session_state["role"] == "Patient":
            if st.button("Patient Dashboard", use_container_width=True, key="nav_pat_dash"):
                st.session_state["page"] = "patient_dashboard"
                st.session_state["selected_booking_id"] = None
                st.rerun()
            if st.button("Browse Availability", use_container_width=True, key="nav_browse"):
                st.session_state["page"] = "browse_availability"
                st.session_state["selected_slot_id"] = None
                st.rerun()
            if st.button("My Appointments", use_container_width=True, key="nav_my_appts"):
                st.session_state["page"] = "my_appointments"
                st.session_state["selected_booking_id"] = None
                st.rerun()
            if st.button("💬 Clinic Assistant", use_container_width=True, key="nav_assistant"):
                st.session_state["page"] = "clinic_assistant"
                st.rerun()

        st.divider()
        if st.button("Log Out", type="primary", use_container_width=True, key="nav_logout"):
            st.session_state["logged_in"] = False
            st.session_state["user"] = None
            st.session_state["role"] = ""
            st.session_state["page"] = "welcome"
            st.rerun()

    # what to show when they aren't logged in yet
    else:
        if st.button("Welcome", use_container_width=True, key="nav_welcome"):
            st.session_state["page"] = "welcome"
            st.rerun()
        if st.button("Register", use_container_width=True, key="nav_register"):
            st.session_state["page"] = "register"
            st.rerun()
        if st.button("Log In", use_container_width=True, key="nav_login"):
            st.session_state["page"] = "login"
            st.rerun()


# --- public pages ---

if not st.session_state["logged_in"] and st.session_state["page"] == "welcome":
    st.title("Welcome to the Clinic Portal")
    st.write("A streamlined scheduling portal for our specialized medical clinic.")
    with st.container(border=True):
        st.markdown("### Demo Credentials")
        st.write("**Doctor:** doctor@clinic.com / doc")
        st.write("**Patient:** patient@email.com / pat")

elif not st.session_state["logged_in"] and st.session_state["page"] == "register":
    st.title("Register New Account")
    with st.container(border=True):
        # inputs for new account
        reg_name = st.text_input("Full Name", key="reg_name_input")
        reg_email = st.text_input("Email", key="reg_email_input")
        reg_password = st.text_input("Password", type="password", key="reg_password_input")
        reg_role = st.selectbox("Role", ["Select a role", "Doctor", "Patient"], key="reg_role_select")

        if st.button("Create Account", type="primary", use_container_width=True, key="reg_submit_btn"):
            # check if they left anything blank
            if reg_name.strip() == "" or reg_email.strip() == "" or reg_password.strip() == "" or reg_role == "Select a role":
                st.warning("All fields are required.")
            else:
                users.append({
                    "user_id": str(uuid.uuid4()),
                    "full_name": reg_name.strip(),
                    "email": reg_email.strip().lower(),
                    "password": reg_password,
                    "role": reg_role,
                    "registered_at": str(datetime.now())
                })
                # save to json immediately
                users_path.write_text(json.dumps(users, indent=4), encoding="utf-8")
                st.success("Account created! Please log in.")
                st.session_state["page"] = "login"
                st.rerun()

elif not st.session_state["logged_in"] and st.session_state["page"] == "login":
    st.title("Log In")
    with st.container(border=True):
        login_email = st.text_input("Email", key="login_email_input")
        login_password = st.text_input("Password", type="password", key="login_password_input")

        if st.button("Log In", type="primary", use_container_width=True, key="login_submit_btn"):
            found_user = None
            # look through users file to find a match
            for user in users:
                if user["email"] == login_email.strip().lower() and user["password"] == login_password:
                    found_user = user
                    break

            if found_user is None:
                st.error("Invalid credentials.")
            else:
                # set up the session state so they stay logged in
                st.session_state["logged_in"] = True
                st.session_state["user"] = found_user
                st.session_state["role"] = found_user["role"]
                
                # send them to the right dashboard based on their role
                if found_user["role"] == "Doctor":
                    st.session_state["page"] = "doctor_dashboard"
                else:
                    st.session_state["page"] = "patient_dashboard"
                st.rerun()


# --- doctor pages ---

elif st.session_state["logged_in"] and st.session_state["role"] == "Doctor" and st.session_state["page"] == "doctor_dashboard":
    st.title("Doctor Dashboard: Daily Roster")
    
    # filter out cancelled bookings so they only see active ones
    active_bookings = [b for b in bookings if b["status"] in ["Scheduled", "Completed", "No-Show"]]
    
    if not active_bookings:
        st.info("There are no patient bookings currently.")
    else:
        # build a list of dictionaries to display cleanly in a dataframe
        df_display = []
        for b in active_bookings:
            slot = next((s for s in timeslots if s["slot_id"] == b["slot_id"]), None)
            pat = next((u for u in users if u["user_id"] == b["patient_id"]), None)
            if slot and pat:
                df_display.append({
                    "Date": slot["date"],
                    "Time": slot["time"],
                    "Patient": pat["full_name"],
                    "Status": b["status"],
                    "Booking ID": b["booking_id"]
                })
        
        st.dataframe(df_display, use_container_width=True)
        
        # dropdown to select a specific record to view or edit
        st.subheader("Manage Appointment")
        booking_options = [f"{row['Date']} at {row['Time']} - {row['Patient']} | {row['Booking ID']}" for row in df_display]
        selected_label = st.selectbox("Select a booking to manage", booking_options, key="doc_booking_select")
        
        if selected_label:
            st.session_state["selected_booking_id"] = selected_label.split(" | ")[-1]
            
            selected_booking = next((b for b in bookings if b["booking_id"] == st.session_state["selected_booking_id"]), None)
            
            if selected_booking:
                with st.container(border=True):
                    st.write(f"**Reason for visit:** {selected_booking['reason_for_visit']}")
                    
                    new_status = st.selectbox(
                        "Update Status", 
                        ["Scheduled", "Completed", "No-Show"], 
                        index=["Scheduled", "Completed", "No-Show"].index(selected_booking["status"]), 
                        key="doc_status_update"
                    )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Save Status", use_container_width=True, type="primary", key="doc_save_status_btn"):
                            selected_booking["status"] = new_status
                            bookings_path.write_text(json.dumps(bookings, indent=4), encoding="utf-8")
                            st.success("Status updated.")
                            st.rerun()
                    with col2:
                        # lets the doctor delete a mistake and open the time back up
                        if st.button("Delete Booking", use_container_width=True, key="doc_del_booking_btn"):
                            slot_info = next((s for s in timeslots if s["slot_id"] == selected_booking["slot_id"]), None)
                            if slot_info:
                                slot_info["status"] = "Open"
                            bookings.remove(selected_booking)
                            
                            timeslots_path.write_text(json.dumps(timeslots, indent=4), encoding="utf-8")
                            bookings_path.write_text(json.dumps(bookings, indent=4), encoding="utf-8")
                            st.success("Booking deleted and slot reopened.")
                            st.session_state["selected_booking_id"] = None
                            st.rerun()

elif st.session_state["logged_in"] and st.session_state["role"] == "Doctor" and st.session_state["page"] == "create_timeslot":
    st.title("Manage Timeslots")
    with st.container(border=True):
        new_date = st.date_input("Select Date", value=date.today(), key="slot_date_input")
        new_time = st.time_input("Select Time", value=time(9, 0), key="slot_time_input")
        
        if st.button("Create Slot", type="primary", use_container_width=True, key="create_slot_btn"):
            timeslots.append({
                "slot_id": str(uuid.uuid4()),
                "doctor_id": st.session_state["user"]["user_id"],
                "date": str(new_date),
                "time": new_time.strftime("%I:%M %p"),
                "status": "Open"
            })
            timeslots_path.write_text(json.dumps(timeslots, indent=4), encoding="utf-8")
            st.success("Timeslot created.")
            st.rerun()
            
    st.subheader("Open Slots")
    # only show slots that haven't been booked yet
    open_slots = [s for s in timeslots if s["status"] == "Open"]
    if not open_slots:
        st.info("No open timeslots available.")
    else:
        for slot in open_slots:
            with st.container(border=True):
                st.write(f"**{slot['date']}** at **{slot['time']}**")
                # need a unique key for the button since it's inside a loop
                if st.button("Delete Slot", key=f"del_slot_{slot['slot_id']}"):
                    timeslots.remove(slot)
                    timeslots_path.write_text(json.dumps(timeslots, indent=4), encoding="utf-8")
                    st.success("Timeslot deleted.")
                    st.rerun()


# --- patient pages ---

elif st.session_state["logged_in"] and st.session_state["role"] == "Patient" and st.session_state["page"] == "patient_dashboard":
    st.title("Patient Dashboard")
    st.write("Welcome to your patient portal.")
    
    # grab only their own scheduled appointments
    my_bookings = [b for b in bookings if b["patient_id"] == st.session_state["user"]["user_id"] and b["status"] == "Scheduled"]
    
    st.subheader("Upcoming Appointments Overview")
    if not my_bookings:
        st.info("You have no upcoming appointments.")
    else:
        for booking in my_bookings:
            slot_info = next((s for s in timeslots if s["slot_id"] == booking["slot_id"]), None)
            if slot_info:
                st.success(f"📅 **{slot_info['date']}** at **{slot_info['time']}**")

elif st.session_state["logged_in"] and st.session_state["role"] == "Patient" and st.session_state["page"] == "browse_availability":
    st.title("Book an Appointment")
    
    open_slots = [s for s in timeslots if s["status"] == "Open"]
    
    if not open_slots:
        st.warning("No open appointments available.")
    else:
        with st.container(border=True):
            slot_options = [f"{s['date']} at {s['time']} | {s['slot_id']}" for s in open_slots]
            selected_slot_label = st.selectbox("Select Timeslot", slot_options, key="pat_slot_select")
            
            st.session_state["selected_slot_id"] = selected_slot_label.split(" | ")[-1]
            reason = st.text_area("Reason for visit (Required)", key="pat_reason_input")
            
            if st.button("Book Appointment", type="primary", use_container_width=True, key="pat_book_btn"):
                # validate the reason text area
                if reason.strip() == "":
                    st.warning("Please provide a brief reason for your visit.")
                else:
                    # mark the slot as booked
                    for slot in timeslots:
                        if slot["slot_id"] == st.session_state["selected_slot_id"]:
                            slot["status"] = "Booked"
                            break
                            
                    # save the booking details
                    bookings.append({
                        "booking_id": str(uuid.uuid4()),
                        "slot_id": st.session_state["selected_slot_id"],
                        "patient_id": st.session_state["user"]["user_id"],
                        "reason_for_visit": reason.strip(),
                        "status": "Scheduled"
                    })
                    
                    timeslots_path.write_text(json.dumps(timeslots, indent=4), encoding="utf-8")
                    bookings_path.write_text(json.dumps(bookings, indent=4), encoding="utf-8")
                    
                    st.success("Appointment booked!")
                    st.session_state["page"] = "my_appointments"
                    st.rerun()

elif st.session_state["logged_in"] and st.session_state["role"] == "Patient" and st.session_state["page"] == "my_appointments":
    st.title("My Appointments")
    
    my_bookings = [b for b in bookings if b["patient_id"] == st.session_state["user"]["user_id"]]
    
    if not my_bookings:
        st.info("You do not have any appointment history.")
    else:
        # put their history in a dataframe
        df_my_appts = []
        for b in my_bookings:
            slot = next((s for s in timeslots if s["slot_id"] == b["slot_id"]), None)
            if slot:
                df_my_appts.append({
                    "Date": slot["date"],
                    "Time": slot["time"],
                    "Status": b["status"],
                    "ID": b["booking_id"]
                })
        
        st.dataframe(df_my_appts, use_container_width=True)
        
        st.subheader("Manage Appointment")
        appt_options = [f"{row['Date']} at {row['Time']} ({row['Status']}) | {row['ID']}" for row in df_my_appts]
        selected_appt_label = st.selectbox("Select Appointment", appt_options, key="pat_manage_select")
        
        if selected_appt_label:
            st.session_state["selected_booking_id"] = selected_appt_label.split(" | ")[-1]
            selected_booking = next((b for b in bookings if b["booking_id"] == st.session_state["selected_booking_id"]), None)
            
            # only let them cancel if it's currently scheduled
            if selected_booking and selected_booking["status"] == "Scheduled":
                with st.container(border=True):
                    st.write(f"**Reason:** {selected_booking['reason_for_visit']}")
                    if st.button("Cancel Appointment", use_container_width=True, key="pat_cancel_btn"):
                        selected_booking["status"] = "Cancelled"
                        
                        # open the timeslot back up for other patients
                        slot_info = next((s for s in timeslots if s["slot_id"] == selected_booking["slot_id"]), None)
                        if slot_info:
                            slot_info["status"] = "Open" 
                            
                        timeslots_path.write_text(json.dumps(timeslots, indent=4), encoding="utf-8")
                        bookings_path.write_text(json.dumps(bookings, indent=4), encoding="utf-8")
                        
                        st.success("Appointment cancelled.")
                        st.session_state["selected_booking_id"] = None
                        st.rerun()

elif st.session_state["logged_in"] and st.session_state["role"] == "Patient" and st.session_state["page"] == "clinic_assistant":
    st.title("💬 Clinic Assistant")
    st.write("Ask me a basic question about your appointments or the clinic!")
    
    user_query = st.text_input("Your question:", key="chat_input")
    
    if st.button("Ask Assistant", type="primary", key="chat_submit_btn"):
        query = user_query.lower()
        
        with st.container(border=True):
            st.markdown("**Assistant Response:**")
            
            # basic keyword matching for the chatbot MVP
            if "when" in query and "appointment" in query:
                my_active_bookings = [b for b in bookings if b["patient_id"] == st.session_state["user"]["user_id"] and b["status"] == "Scheduled"]
                if not my_active_bookings:
                    st.write("You don't currently have any scheduled appointments.")
                else:
                    first_booking = my_active_bookings[0]
                    slot_info = next((s for s in timeslots if s["slot_id"] == first_booking["slot_id"]), None)
                    if slot_info:
                        st.write(f"Your next scheduled appointment is on **{slot_info['date']}** at **{slot_info['time']}**.")
            elif "where" in query or "located" in query or "location" in query:
                st.write("We are located at 123 Health Way, in the Medical District.")
            elif "hours" in query or "open" in query:
                st.write("Our clinic is open Monday through Friday, from 8:00 AM to 5:00 PM.")
            elif "cancel" in query or "reschedule" in query:
                st.write("To cancel, navigate to the 'My Appointments' tab on your sidebar.")
            elif "who" in query and "doctor" in query:
                st.write("Our primary physician is Dr. Smith.")
            else:
                st.write("I am a simple Phase 1 Assistant. I can answer questions about your next appointment, our hours, location, and doctors.")