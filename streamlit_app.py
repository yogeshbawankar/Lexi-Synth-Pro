# src/streamlit_app.py
import streamlit as st
import requests
import pandas as pd
import re
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="Lexi-Synth Pro",
    page_icon="⚖️",
    layout="wide"
)

# --- Backend API URL ---
API_URL = "https://yogeshbawankar03-lexiscribe-backend.hf.space"

# --- Initialize Session State ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'page' not in st.session_state:
    st.session_state.page = "Login"
if 'history' not in st.session_state:
    st.session_state.history = {}
if 'current_analysis_id' not in st.session_state:
    st.session_state.current_analysis_id = None
if 'highlight_entity' not in st.session_state:
    st.session_state.highlight_entity = None

# --- Authentication Pages ---
def show_login_page():
    st.header("Login to Lexi-Synth Pro")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            try:
                response = requests.post(f"{API_URL}/login/", json={"username": username, "password": password})
                if response.status_code == 200:
                    st.session_state.logged_in = True
                    st.session_state.user = response.json().get("user")
                    st.session_state.page = "App"
                    st.rerun()
                else:
                    st.error("Incorrect username or password.")
            except requests.exceptions.RequestException:
                st.error("Could not connect to the server. Please ensure the backend is running.")
    
    if st.button("Don't have an account? Register"):
        st.session_state.page = "Register"
        st.rerun()

def show_register_page():
    st.header("Register for an Account")
    with st.form("register_form"):
        name = st.text_input("Name")
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Register")
        if submitted:
            payload = {"name": name, "username": username, "email": email, "password": password}
            try:
                response = requests.post(f"{API_URL}/register/", json=payload)
                if response.status_code == 200:
                    st.success("Registration successful! Please log in.")
                    st.session_state.page = "Login"
                    st.rerun()
                else:
                    st.error(f"Registration failed: {response.json().get('detail')}")
            except requests.exceptions.RequestException:
                st.error("Could not connect to the server.")

    if st.button("Already have an account? Login"):
        st.session_state.page = "Login"
        st.rerun()

# --- Main Application Page ---
def show_app_page():
    # Helper function for report download
    def create_downloadable_report(results):
        report = f"# Lexi-Synth Analysis Report for: {results.get('filename', 'N/A')}\n\n"
        report += f"## 📝 Summary\n{results.get('summary', 'N/A')}\n\n"
        report += f"## 📌 Key Entities\n"
        for entity in results.get('entities', []):
            report += f"- {entity['word']} ({entity['entity_group']})\n"
        report += f"\n## 🔗 Legal Citations\n"
        for item in results.get('citations', []):
            report += f"- {item.get('citation')}\n"
        report += f"\n## 📄 Full Text / Transcription\n"
        report += results.get('original_text', 'N/A')
        return report

    # --- Sidebar UI ---
    with st.sidebar:
        st.header("User Account")
        if st.session_state.user:
            st.info(f"👤 {st.session_state.user.get('name', 'User')}")
        
        if st.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        st.header("Analyze New Document")
        
        # --- NEW: Choose input method ---
        input_method = st.radio("Select input method:", ("Upload File", "Paste Text"), key="input_method_selector")

        uploaded_file = None
        pasted_text = None
        analysis_type = "Text" # Default to text

        if input_method == "Upload File":
            analysis_type = st.radio("Select document type:", ("Text", "Audio"), key="analysis_type_selector")
            file_types = ['txt'] if analysis_type == 'Text' else ['mp3', 'wav', 'm4a']
            uploaded_file = st.file_uploader("Upload a file", type=file_types)
        
        elif input_method == "Paste Text":
            pasted_text = st.text_area("Paste your text here:", height=200)

        # Determine if the analyze button should be enabled
        is_ready_to_analyze = (uploaded_file is not None) or (pasted_text and pasted_text.strip())

        if st.button("Analyze Document", disabled=(not is_ready_to_analyze)):
            with st.spinner("Analysis in progress... This may take a moment."):
                response = None
                try:
                    if input_method == "Upload File" and uploaded_file:
                        if analysis_type == "Text":
                            file_content = uploaded_file.getvalue().decode("utf-8")
                            payload = {"filename": uploaded_file.name, "text": file_content}
                            response = requests.post(f"{API_URL}/analyze-text/", json=payload)
                        else:  # Audio
                            files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                            response = requests.post(f"{API_URL}/analyze-audio/", files=files)
                    
                    elif input_method == "Paste Text" and pasted_text:
                        # Use a timestamp for the filename of pasted text
                        filename = f"Pasted Text - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.txt"
                        payload = {"filename": filename, "text": pasted_text}
                        response = requests.post(f"{API_URL}/analyze-text/", json=payload)
                
                except requests.exceptions.RequestException:
                    st.error("Connection to backend failed. Please check the API URL and server status.")
                
                if response and response.status_code == 200:
                    results = response.json()
                    analysis_id = results.get('analysis_id')
                    st.session_state.history[analysis_id] = results
                    st.session_state.current_analysis_id = analysis_id
                    st.success("Analysis complete!")
                    st.rerun()
                elif response is not None:
                    st.error(f"Analysis failed with status code {response.status_code}: {response.text}")
        
        # --- History Section ---
        st.header("Analysis History")
        if not st.session_state.history:
            st.write("No analyses yet.")
        else:
            for analysis_id, data in reversed(list(st.session_state.history.items())):
                if st.button(f"📄 {data.get('filename')}", key=analysis_id, use_container_width=True):
                    st.session_state.current_analysis_id = analysis_id
                    st.session_state.highlight_entity = None
                    st.rerun()

    # --- Main Page Display ---
    st.title("⚖️ Lexi-Synth Pro: AI Legal Analysis Suite")
    
    current_id = st.session_state.current_analysis_id
    if current_id and current_id in st.session_state.history:
        results = st.session_state.history[current_id]
        st.header(f"Analysis for: *{results.get('filename')}*")
        
        st.subheader("❓ Ask a Question")
        question = st.text_input("Ask anything about the document:", key=f"qa_input_{current_id}")
        if question:
            with st.spinner("Finding answer..."):
                context_text = results.get('original_text')
                qa_payload = {"question": question, "context": context_text}
                try:
                    qa_response = requests.post(f"{API_URL}/answer-question/", json=qa_payload)
                    if qa_response.status_code == 200:
                        answer_data = qa_response.json()
                        st.success(f"**Answer:** {answer_data.get('answer')} (Confidence: {answer_data.get('score'):.2f})")
                    else:
                        st.error("Could not get an answer from the backend.")
                except requests.exceptions.RequestException:
                    st.error("Connection to backend failed.")

        with st.expander("📊 Visual Dashboard", expanded=True):
            entity_groups = [entity['entity_group'] for entity in results.get('entities', [])]
            if entity_groups:
                df = pd.DataFrame(entity_groups, columns=["Entity Type"])
                chart_data = df['Entity Type'].value_counts()
                st.bar_chart(chart_data)
            else:
                st.write("No entities to visualize.")

        col1, col2 = st.columns([2, 1])

        with col1:
            with st.expander("📝 Summary", expanded=True):
                st.write(results.get("summary", "No summary available."))
            
            search_term = st.text_input("Search in Full Text", key=f"search_{current_id}")
            with st.expander("📄 Full Text / Transcription", expanded=True):
                full_text = results.get('original_text', "No text available.")
                display_text = full_text
                
                highlight_term = st.session_state.highlight_entity or search_term
                if highlight_term:
                    display_text = re.sub(f"({re.escape(highlight_term)})", r"**\1**", full_text, flags=re.IGNORECASE)
                
                html_text = display_text.replace('\n', '<br>').replace('**', '<b>').replace('</b>', '</b>')
                st.markdown(f"<div style='height: 300px; overflow-y: scroll; border: 1px solid #ddd; padding: 10px; border-radius: 5px;'>{html_text}</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("#### 📌 Key Entities")
            all_entities = results.get('entities', [])
            entity_types = sorted(list(set(e['entity_group'] for e in all_entities)))
            selected_types = st.multiselect("Filter entities by type:", options=entity_types, default=entity_types, key=f"filter_{current_id}")
            
            filtered_entities = [e for e in all_entities if e['entity_group'] in selected_types]
            for entity in filtered_entities:
                if st.button(f"{entity['word']} (`{entity['entity_group']}`)", key=f"entity_{entity['word']}_{entity['score']}_{current_id}"):
                    st.session_state.highlight_entity = entity['word']
                    st.rerun()
            
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown("#### 🔗 Legal Citations")
            citations = results.get("citations", [])
            if citations:
                for item in citations:
                    with st.expander(f"⚖️ {item.get('citation')}"):
                        st.write(item.get('text', 'Full text not available.'))
            else:
                st.write("No legal citations found.")

            st.markdown("<hr>", unsafe_allow_html=True)
            report_data = create_downloadable_report(results)
            st.download_button(
                label="📥 Download Full Report",
                data=report_data,
                file_name=f"lexisynth_report_{results.get('filename', 'file')}.md",
                mime="text/markdown"
            )
    else:
        st.info("Upload a document or select a past analysis from the history to begin.")

# --- Page Router ---
if not st.session_state.logged_in:
    if st.session_state.page == "Register":
        show_register_page()
    else:
        show_login_page()
else:
    show_app_page()