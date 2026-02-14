import streamlit as st
import time
from src.config import AppConfig
from src.services.user_service import UserService
from src.services.auth_handler import AuthHandler
from src.services.mongo_service import MongoService
from src.services.llm_service import GeminiService
from src.utils.session import init_session_state, increment_message_count, check_usage_limit

# --- CONFIG & INIT ---
st.set_page_config(page_title="MongoChat Platform", page_icon="🍃")
init_session_state()

# Additional Session States for Auth
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "username" not in st.session_state:
    st.session_state.username = None

# --- AUTH VIEW ---
def login_view():
    st.title("🔐 MongoChat Login")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    user_svc = UserService()

    with tab1: # Login Tab
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            user = user_svc.verify_user(email, password)
            if user:
                # Create Token
                token = AuthHandler.create_access_token({"sub": email, "name": user["username"]})
                
                # Update Session
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.session_state.username = user["username"]
                st.session_state.token = token
                st.success(f"Welcome back, {user['username']}!")
                st.rerun()
            else:
                st.error("Invalid email or password")

    with tab2: # Signup Tab
        new_email = st.text_input("New Email")
        new_user = st.text_input("Choose Username")
        new_pass = st.text_input("Choose Password", type="password")
        
        if st.button("Create Account"):
            try:
                user_svc.create_user(new_email, new_user, new_pass)
                st.success("Account created! Please log in.")
            except ValueError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"Error: {e}")

# --- APP VIEW (Chat) ---
def main_app_view():
    user_svc = UserService()
    
    # --- FETCH USAGE STATS ---
    # We fetch this fresh every rerun to ensure accuracy
    usage_count, usage_limit, hours_left = user_svc.get_usage_stats(st.session_state.user_email)
    
    with st.sidebar:
        # ... (Keep User Profile & Logout) ...
        st.write(f"👤 **{st.session_state.username}**")

        # ✅ RESTORE LOGOUT BUTTON HERE
        if st.button("Log out", type="secondary"):
            st.session_state.clear() # Wipes session (auth, token, db connection)
            st.rerun() # Refreshes to show Login View
        
        # --- NEW: USAGE DISPLAY ---
        st.divider()
        st.subheader("📊 Usage")
        
        # Calculate percentage for progress bar
        pct = min(usage_count / usage_limit, 1.0)
        st.progress(pct, text=f"{usage_count} / {usage_limit} Messages")
        
        if usage_count >= usage_limit:
            st.error(f"Limit Reached! Resets in {int(hours_left)}h {int((hours_left%1)*60)}m")
        else:
            st.caption(f"Resets in {int(hours_left)}h")
        
        st.divider()
        st.header("🔌 Database Connection")
        
        user_svc = UserService()
        
        # 1. IF CONNECTED: Show Disconnect Option
        if st.session_state.db_connected:
            st.success("✅ Linked to Database")
            st.caption(f"Using saved connection for: {st.session_state.user_email}")
            
            if st.button("❌ Disconnect / Switch Database"):
                # Clear session state for DB
                st.session_state.db_connected = False
                st.session_state.mongo_data = None
                # Optional: You could also delete the saved config from DB if you wanted
                # user_svc.delete_user_config(st.session_state.user_email) 
                st.rerun()
                
        # 2. IF NOT CONNECTED: Show Connect Form
        else:
            # Check if we have saved credentials in the Master DB
            saved_config = user_svc.get_user_config(st.session_state.user_email)
            
            # If saved config exists, Auto-Connect logic could go here, 
            # OR we pre-fill the fields so they just hit "Connect"
            def_uri = saved_config["mongo_uri"] if saved_config else ""
            def_db = saved_config["db_name"] if saved_config else ""
            def_col = saved_config["collection"] if saved_config else ""
            
            st.caption("Enter your MongoDB Atlas details:")
            mongo_uri = st.text_input("Connection String", value=def_uri, type="password")
            db_name = st.text_input("Database Name", value=def_db)
            col_name = st.text_input("Collection Name", value=def_col)
            
            if st.button("Connect & Save"):
                if not (mongo_uri and db_name and col_name):
                    st.error("Please fill in all fields.")
                else:
                    try:
                        with st.spinner("Connecting..."):
                            # A. Test Connection
                            mongo_svc = MongoService()
                            mongo_svc.connect(mongo_uri, db_name, col_name)
                            data = mongo_svc.fetch_documents(limit=AppConfig.DOC_FETCH_LIMIT)
                            
                            # B. Save Config to Master DB (So they don't type it next time)
                            user_svc.save_user_config(st.session_state.user_email, mongo_uri, db_name, col_name)
                            
                            # C. Update Session
                            st.session_state.mongo_data = data
                            st.session_state.db_connected = True
                            st.rerun()
                            
                    except Exception as e:
                        st.error(f"Connection Failed: {e}")

    # Chat Interface
    st.subheader("💬 Chat with your Data")
    
    if not st.session_state.db_connected:
        st.info("👈 Please connect your database in the sidebar to start.")
        return

    # ... (Insert your existing Chat UI Logic here) ...
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask about your data..."):
        # --- 1. BLOCK IF LIMIT REACHED ---
        if usage_count >= usage_limit:
            st.error(f"🚫 Daily limit of {usage_limit} messages reached. Please wait {int(hours_left)} hours.")
            return # Stop execution here

        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # (Keep your existing LLM logic)
                    llm_svc = GeminiService(api_key=AppConfig.GEMINI_API_KEY)
                    response_text = llm_svc.generate_response(
                        context_data=st.session_state.mongo_data,
                        user_question=prompt
                    )
                    
                    st.markdown(response_text)
                    st.session_state.chat_history.append({"role": "assistant", "content": response_text})
                    
                    # --- 2. INCREMENT DB COUNTER ---
                    # Only increment if successful
                    user_svc.increment_usage(st.session_state.user_email)
                    
                    st.rerun() # Refresh to update the sidebar bar immediately
                except Exception as e:
                    st.error(str(e))

# --- ROUTER ---
if not st.session_state.authenticated:
    login_view()
else:
    main_app_view()