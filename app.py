import streamlit as st
from src.config import AppConfig
from src.services.mongo_service import MongoService
from src.services.llm_service import GeminiService
from src.utils.session import init_session_state, check_usage_limit, increment_message_count

# 1. Setup & Key Validation
st.set_page_config(page_title=AppConfig.PAGE_TITLE, page_icon=AppConfig.PAGE_ICON)
try:
    AppConfig.validate_keys()
except ValueError as e:
    st.error(f"🚨 {e}")
    st.stop()

init_session_state()

# --- SIDEBAR: USER INPUTS DATABASE INFO ---
with st.sidebar:
    st.header("🔌 Connect Your Database")
    st.caption("We use your data only to answer your questions.")
    
    # User provides THEIR data connection
    mongo_uri = st.text_input("MongoDB Connection String", type="password", placeholder="mongodb+srv://...")
    db_name = st.text_input("Database Name")
    col_name = st.text_input("Collection Name")
    
    if st.button("Link Database"):
        if not (mongo_uri and db_name and col_name):
            st.error("Please fill in all database fields.")
        else:
            try:
                # 1. Connect to User's DB
                mongo_svc = MongoService()
                mongo_svc.connect(mongo_uri, db_name, col_name)
                
                # 2. Fetch User's Data
                data_json = mongo_svc.fetch_documents(limit=AppConfig.DOC_FETCH_LIMIT)
                
                # 3. Store in Session
                st.session_state.mongo_data = data_json
                st.session_state.db_connected = True
                st.success("✅ Database Connected & Data Loaded!")
                
            except Exception as e:
                st.error(f"Connection Failed: {str(e)}")

    st.divider()
    
    # Usage Tracker (Your Business Logic)
    remaining = AppConfig.MAX_FREE_MESSAGES - st.session_state.message_count
    st.metric("Free Messages Left", max(0, remaining))
    
    if check_usage_limit():
        st.error("🚫 Free Limit Reached")
        st.info("Contact support to upgrade.")

# --- MAIN CHAT UI ---
st.title(f"{AppConfig.PAGE_ICON} Chat with your MongoDB")

# Display History
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input
if prompt := st.chat_input("Ask about the uploaded data..."):
    
    # 1. Check Constraints
    if check_usage_limit():
        st.error("🔒 You have used your 3 free messages.")
        st.stop()
        
    if not st.session_state.db_connected:
        st.warning("👈 Please connect your MongoDB in the sidebar first.")
        st.stop()

    # 2. Add User Message
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 3. Generate Response (Using YOUR Key + USER Data)
    with st.chat_message("assistant"):
        with st.spinner("Analyzing your data..."):
            try:
                # Assert the key is not None before passing it
                if not AppConfig.GEMINI_API_KEY:
                    st.error("Server Configuration Error: API Key missing.")
                    st.stop()

                # Initialize Service with YOUR key from config
                llm_svc = GeminiService(api_key=AppConfig.GEMINI_API_KEY)
                
                # Pass User's Data (context) + User's Question
                response_text = llm_svc.generate_response(
                    context_data=st.session_state.mongo_data,
                    user_question=prompt
                )
                
                st.markdown(response_text)
                
                # Update State
                st.session_state.chat_history.append({"role": "assistant", "content": response_text})
                increment_message_count()
                st.rerun()
                
            except Exception as e:
                st.error(f"Error generating response: {str(e)}")