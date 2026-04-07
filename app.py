import streamlit as st
import json
from pathlib import Path
from datetime import datetime, date, time
import uuid

# making the page look a bit nicer and adding an icon
st.set_page_config(page_title="Clinic Portal", layout="centered", page_icon="🏥")

# setting up session state variables so the app stops forgetting who is logged in when it refreshes
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


# pointing to where my JSON files live
users_path = Path("users.json")
timeslots_path = Path("timeslots.json")
bookings_path = Path("bookings.json")

# creating some default demo data if the files don't exist yet (wrapped in try/except just in case)
try:
    if not users_path.exists():
        users_path.write_text(json.dumps([
            {"user_id": "doc-1", "full_name": "Dr. Smith", "email": "doctor@clinic.com", "password": "doc", "role": "Doctor", "registered_at": str(datetime.now())},
            {"user_id": "pat-1", "full_name": "Demo Patient", "email": "patient@email.com", "password": "pat", "role": "Patient", "registered_at": str(datetime.now())}
        ], indent=4), encoding="utf-8")

    if not timeslots_path.exists():
        timeslots_path.write_text(json.dumps([
            {"slot_id": "slot-1", "doctor_id": "doc-1", "date": str(date.today()), "time": "10:00 AM", "status": "Open"}
        ], indent=4), encoding="utf-8")

    if not bookings_path.exists():
        bookings_path.write_text(json.dumps([], indent=4), encoding="utf-8")
except Exception as e:
    st.error(f"Critical System Error initializing databases: {e}")

# loading the data safely (using try/except because it kept crashing my app earlier when the files were empty)
try:
    users = json.loads(users_path.read_text(encoding="utf-8"))
except Exception:
    users = []

try:
    timeslots = json.loads(timeslots_path.read_text(encoding="utf-8"))
except Exception:
    timeslots = []

try:
    bookings = json.loads(bookings_path.read_text(encoding="utf-8"))
except Exception:
    bookings = []


# setting up the sidebar navigation (finally got the routing to work!)
with st.sidebar:
    st.markdown("## 🏥 Clinic Portal")
    st.divider()

    # what to show when they are actually logged in
    if st.session_state["logged_in"]:
        st.success(f"Welcome, {st.session_state['user']['full_name']}")
        st.caption(f"Role: {st.session_state['role']}")
        st.write("") # just adding a little spacing

        # doctor specific menu
        if st.session_state["role"] == "Doctor":
            if st.button("📅 Daily Roster", use_container_width=True, key="nav_doc_dash"):
                st.session_state["page"] = "doctor_dashboard"
                st.session_state["selected_booking_id"] = None
                st.rerun()
            if st.button("⚙️ Manage Timeslots", use_container_width=True, key="nav_create_slot"):
                st.session_state["page"] = "create_timeslot"
                st.rerun()

        # patient specific menu
        if st.session_state["role"] == "Patient":
            if st.button("🏠 Home", use_container_width=True, key="nav_pat_dash"):
                st.session_state["page"] = "patient_dashboard"
                st.session_state["selected_booking_id"] = None
                st.rerun()
            if st.button("➕ Book Appointment", use_container_width=True, key="nav_browse"):
                st.session_state["page"] = "browse_availability"
                st.rerun()
            if st.button("🗓️ My Appointments", use_container_width=True, key="nav_my_appts"):
                st.session_state["page"] = "my_appointments"
                st.session_state["selected_booking_id"] = None
                st.rerun()
            if st.button("💬 Clinic Assistant", use_container_width=True, key="nav_assistant"):
                st.session_state["page"] = "clinic_assistant"
                st.rerun()

        st.divider()
        # logout button resets all the session state variables
        if st.button("Log Out", type="secondary", use_container_width=True, key="nav_logout"):
            st.session_state["logged_in"] = False
            st.session_state["user"] = None
            st.session_state["role"] = ""
            st.session_state["page"] = "welcome"
            st.rerun()

    # what to show when they aren't logged in yet
    else:
        if st.button("Home", use_container_width=True, key="nav_welcome"):
            st.session_state["page"] = "welcome"
            st.rerun()
        if st.button("Register", use_container_width=True, key="nav_register"):
            st.session_state["page"] = "register"
            st.rerun()
        if st.button("Log In", type="primary", use_container_width=True, key="nav_login"):
            st.session_state["page"] = "login"
            st.rerun()


# --- public pages (welcome, register, login) ---

if not st.session_state["logged_in"] and st.session_state["page"] == "welcome":
    st.title("Welcome to the Clinic Portal")
    st.write("A streamlined scheduling portal for our specialized medical clinic.")
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown("#### Patient Access")
            st.write("Book appointments, manage your schedule, and check clinic policies.")
    with col2:
        with st.container(border=True):
            st.markdown("#### Doctor Access")
            st.write("Manage your availability and view your daily patient roster.")
            
    st.info("**Demo Logins:** \n* **Doctor:** doctor@clinic.com / doc\n* **Patient:** patient@email.com / pat")

elif not st.session_state["logged_in"] and st.session_state["page"] == "register":
    st.title("Register New Account")
    with st.container(border=True):
        reg_name = st.text_input("Full Name", key="reg_name_input")
        reg_email = st.text_input("Email Address", key="reg_email_input")
        reg_password = st.text_input("Password", type="password", key="reg_password_input")
        reg_role = st.selectbox("I am a...", ["Select a role", "Doctor", "Patient"], key="reg_role_select")

        if st.button("Create Account", type="primary", use_container_width=True, key="reg_submit_btn"):
            clean_email = reg_email.strip().lower()
            
            # making sure they didn't leave anything blank
            if reg_name.strip() == "" or clean_email == "" or reg_password.strip() == "" or reg_role == "Select a role":
                st.warning("Please fill out all required fields.")
            else:
                # checking to make sure no one registers with the exact same email
                email_exists = any(u["email"] == clean_email for u in users)
                if email_exists:
                    st.error("This email address is already registered. Please log in.")
                else:
                    try:
                        # saving the new user details
                        users.append({
                            "user_id": str(uuid.uuid4()),
                            "full_name": reg_name.strip(),
                            "email": clean_email,
                            "password": reg_password,
                            "role": reg_role,
                            "registered_at": str(datetime.now())
                        })
                        users_path.write_text(json.dumps(users, indent=4), encoding="utf-8")
                        st.success("Account created successfully! Please log in.")
                    except Exception as e:
                        st.error("System error saving account. Please try again later.")

elif not st.session_state["logged_in"] and st.session_state["page"] == "login":
    st.title("Log In")
    with st.container(border=True):
        login_email = st.text_input("Email", key="login_email_input")
        login_password = st.text_input("Password", type="password", key="login_password_input")

        if st.button("Secure Log In", type="primary", use_container_width=True, key="login_submit_btn"):
            # look through the users list to see if the email and password match
            found_user = next((u for u in users if u["email"] == login_email.strip().lower() and u["password"] == login_password), None)

            if not found_user:
                st.error("Invalid email or password.")
            else:
                # log them in and save their details to session state
                st.session_state["logged_in"] = True
                st.session_state["user"] = found_user
                st.session_state["role"] = found_user["role"]
                # send them to the right dashboard based on their role
                st.session_state["page"] = "doctor_dashboard" if found_user["role"] == "Doctor" else "patient_dashboard"
                st.rerun()


# --- doctor views ---

elif st.session_state["logged_in"] and st.session_state["role"] == "Doctor" and st.session_state["page"] == "doctor_dashboard":
    st.title("Daily Roster")
    st.write("Manage your scheduled and completed appointments.")
    st.divider()
    
    # filter out cancelled bookings so the doctor only sees active ones
    active_bookings = [b for b in bookings if b["status"] in ["Scheduled", "Completed", "No-Show"]]
    
    if not active_bookings:
        st.info("You have no patient bookings currently.")
    else:
        # using columns here so it looks much better than just dumping a table on the screen
        for b in active_bookings:
            slot = next((s for s in timeslots if s["slot_id"] == b["slot_id"]), None)
            pat = next((u for u in users if u["user_id"] == b["patient_id"]), None)
            
            if slot and pat:
                with st.container(border=True):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    with col1:
                        st.markdown(f"**{slot['date']}** at **{slot['time']}**")
                        st.write(f"Patient: {pat['full_name']}")
                    with col2:
                        st.write(f"**Reason:** {b['reason_for_visit']}")
                    with col3:
                        # color coding the status indicators
                        if b["status"] == "Scheduled":
                            st.info("Scheduled")
                        elif b["status"] == "Completed":
                            st.success("Completed")
                        else:
                            st.error("No-Show")
                            
                    # hiding the update controls in an expander to keep things tidy
                    with st.expander("Update Appointment Status"):
                        new_status = st.selectbox(
                            "Mark as:", 
                            ["Scheduled", "Completed", "No-Show"], 
                            index=["Scheduled", "Completed", "No-Show"].index(b["status"]), 
                            key=f"status_update_{b['booking_id']}"
                        )
                        
                        btn_col1, btn_col2 = st.columns(2)
                        with btn_col1:
                            if st.button("Save New Status", type="primary", use_container_width=True, key=f"save_stat_{b['booking_id']}"):
                                b["status"] = new_status
                                try:
                                    bookings_path.write_text(json.dumps(bookings, indent=4), encoding="utf-8")
                                    st.success("Status updated.")
                                    # refreshing the screen so the update shows immediately
                                    st.rerun() 
                                except Exception:
                                    st.error("Error saving status.")
                        with btn_col2:
                            # lets the doctor delete a mistake and open the time back up
                            if st.button("Cancel & Reopen Slot", use_container_width=True, key=f"del_book_{b['booking_id']}"):
                                if slot: slot["status"] = "Open"
                                bookings.remove(b)
                                try:
                                    timeslots_path.write_text(json.dumps(timeslots, indent=4), encoding="utf-8")
                                    bookings_path.write_text(json.dumps(bookings, indent=4), encoding="utf-8")
                                    st.success("Appointment removed and slot reopened.")
                                    st.rerun()
                                except Exception:
                                    st.error("Error cancelling appointment.")

elif st.session_state["logged_in"] and st.session_state["role"] == "Doctor" and st.session_state["page"] == "create_timeslot":
    st.title("Manage Timeslots")
    
    st.subheader("Create New Availability")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            new_date = st.date_input("Select Date", value=date.today(), key="slot_date_input")
        with col2:
            new_time = st.time_input("Select Time", value=time(9, 0), key="slot_time_input")
        
        if st.button("Add to Schedule", type="primary", use_container_width=True, key="create_slot_btn"):
            try:
                timeslots.append({
                    "slot_id": str(uuid.uuid4()),
                    "doctor_id": st.session_state["user"]["user_id"],
                    "date": str(new_date),
                    "time": new_time.strftime("%I:%M %p"),
                    "status": "Open"
                })
                timeslots_path.write_text(json.dumps(timeslots, indent=4), encoding="utf-8")
                st.success("Timeslot added successfully.")
            except Exception:
                st.error("Error saving timeslot.")
            
    st.divider()
    st.subheader("Current Open Slots")
    # only show slots that haven't been booked yet
    open_slots = [s for s in timeslots if s["status"] == "Open"]
    if not open_slots:
        st.info("You have no unbooked timeslots.")
    else:
        for slot in open_slots:
            with st.container(border=True):
                col_info, col_del = st.columns([3, 1])
                with col_info:
                    st.write(f"📅 **{slot['date']}** at **{slot['time']}**")
                with col_del:
                    # need a unique key for the button since it's inside a loop
                    if st.button("Remove Slot", key=f"del_slot_{slot['slot_id']}", use_container_width=True):
                        timeslots.remove(slot)
                        try:
                            timeslots_path.write_text(json.dumps(timeslots, indent=4), encoding="utf-8")
                            st.rerun()
                        except Exception:
                            st.error("Error deleting slot.")


# --- patient views ---

elif st.session_state["logged_in"] and st.session_state["role"] == "Patient" and st.session_state["page"] == "patient_dashboard":
    st.title("Patient Dashboard")
    st.write(f"Welcome back, {st.session_state['user']['full_name']}.")
    st.divider()
    
    # grab only their own scheduled appointments
    my_bookings = [b for b in bookings if b["patient_id"] == st.session_state["user"]["user_id"] and b["status"] == "Scheduled"]
    
    st.subheader("Upcoming Appointments")
    if not my_bookings:
        st.info("You currently have no upcoming appointments.")
    else:
        for booking in my_bookings:
            slot = next((s for s in timeslots if s["slot_id"] == booking["slot_id"]), None)
            if slot:
                with st.container(border=True):
                    st.success(f"🗓️ **{slot['date']}** at **{slot['time']}**")
                    st.caption(f"Reason: {booking['reason_for_visit']}")

elif st.session_state["logged_in"] and st.session_state["role"] == "Patient" and st.session_state["page"] == "browse_availability":
    st.title("Book an Appointment")
    st.write("Select an open time from our clinic's schedule.")
    
    open_slots = [s for s in timeslots if s["status"] == "Open"]
    
    if not open_slots:
        st.warning("There are currently no open appointments available. Please check back later.")
    else:
        with st.container(border=True):
            # sort the slots cleanly for the dropdown
            open_slots_sorted = sorted(open_slots, key=lambda x: (x['date'], x['time']))
            slot_options = {f"{s['date']} at {s['time']}": s['slot_id'] for s in open_slots_sorted}
            
            selected_slot_label = st.selectbox("Available Timeslots", list(slot_options.keys()), key="pat_slot_select")
            selected_id = slot_options[selected_slot_label]
            
            reason = st.text_area("Reason for visit (Required)", placeholder="E.g., Annual checkup, knee pain, etc.", key="pat_reason_input")
            
            if st.button("Confirm Booking", type="primary", use_container_width=True, key="pat_book_btn"):
                # validate the reason text area
                if reason.strip() == "":
                    st.warning("Please provide a brief reason for your visit so the doctor can prepare.")
                else:
                    try:
                        # 1. mark the slot as booked
                        for slot in timeslots:
                            if slot["slot_id"] == selected_id:
                                slot["status"] = "Booked"
                                break
                                
                        # 2. save the new booking details
                        bookings.append({
                            "booking_id": str(uuid.uuid4()),
                            "slot_id": selected_id,
                            "patient_id": st.session_state["user"]["user_id"],
                            "reason_for_visit": reason.strip(),
                            "status": "Scheduled"
                        })
                        
                        # 3. write everything back to the json files
                        timeslots_path.write_text(json.dumps(timeslots, indent=4), encoding="utf-8")
                        bookings_path.write_text(json.dumps(bookings, indent=4), encoding="utf-8")
                        
                        st.success("Appointment successfully booked!")
                        st.session_state["page"] = "my_appointments"
                        st.rerun()
                    except Exception as e:
                        st.error("There was an error securing your booking. Please try again.")

elif st.session_state["logged_in"] and st.session_state["role"] == "Patient" and st.session_state["page"] == "my_appointments":
    st.title("My Appointment History")
    st.divider()
    
    my_bookings = [b for b in bookings if b["patient_id"] == st.session_state["user"]["user_id"]]
    
    if not my_bookings:
        st.info("You do not have any appointment history.")
    else:
        # formatting the appointment history nicely with columns instead of a dataframe dump
        for b in my_bookings:
            slot = next((s for s in timeslots if s["slot_id"] == b["slot_id"]), None)
            if slot:
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**{slot['date']}** at **{slot['time']}**")
                        st.write(f"**Reason:** {b['reason_for_visit']}")
                    with col2:
                        if b["status"] == "Scheduled":
                            st.info("Scheduled")
                        elif b["status"] == "Completed":
                            st.success("Completed")
                        else:
                            st.caption(b["status"])
                            
                    # only let them cancel if the appointment is still scheduled in the future
                    if b["status"] == "Scheduled":
                        with st.expander("Manage"):
                            if st.button("Cancel this Appointment", use_container_width=True, key=f"pat_cancel_{b['booking_id']}"):
                                try:
                                    b["status"] = "Cancelled"
                                    # open the timeslot back up for other patients
                                    if slot: slot["status"] = "Open" 
                                    
                                    timeslots_path.write_text(json.dumps(timeslots, indent=4), encoding="utf-8")
                                    bookings_path.write_text(json.dumps(bookings, indent=4), encoding="utf-8")
                                    
                                    st.success("Your appointment has been cancelled.")
                                    st.rerun()
                                except Exception:
                                    st.error("Error cancelling appointment.")

elif st.session_state["logged_in"] and st.session_state["role"] == "Patient" and st.session_state["page"] == "clinic_assistant":
    st.title("💬 Clinic Assistant")
    st.write("Ask me a basic question about your appointments or the clinic!")
    st.caption("E.g., 'When is my next appointment?', 'What are the hours?', 'Where are you located?', 'How do I cancel?'")
    
    user_query = st.text_input("Your question:", key="chat_input")
    
    if st.button("Ask Assistant", type="primary", key="chat_submit_btn"):
        query = user_query.lower()
        
        with st.container(border=True):
            st.markdown("**Assistant Response:**")
            
            # really basic keyword matching for the phase 1 chatbot MVP
            if "when" in query and "appointment" in query:
                my_active_bookings = [b for b in bookings if b["patient_id"] == st.session_state["user"]["user_id"] and b["status"] == "Scheduled"]
                if not my_active_bookings:
                    st.write("You don't currently have any scheduled appointments.")
                else:
                    first_booking = my_active_bookings[0]
                    slot = next((s for s in timeslots if s["slot_id"] == first_booking["slot_id"]), None)
                    if slot:
                        st.write(f"Your next scheduled appointment is on **{slot['date']}** at **{slot['time']}**.")
            elif "where" in query or "located" in query or "location" in query:
                st.write("We are located at 123 Health Way, in the Medical District.")
            elif "hours" in query or "open" in query:
                st.write("Our clinic is open Monday through Friday, from 8:00 AM to 5:00 PM.")
            elif "cancel" in query or "reschedule" in query:
                st.write("To cancel, navigate to the 'My Appointments' tab on your sidebar. Click 'Manage' on any scheduled appointment to cancel it.")
            elif "who" in query and "doctor" in query:
                st.write("Our primary physician is Dr. Smith.")
            else:
                st.write("I am a simple Phase 1 Assistant. I can answer questions about your next appointment, our hours, location, cancellation policies, and our doctors.")