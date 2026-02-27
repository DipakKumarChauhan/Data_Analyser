"""
Streamlit Frontend for Tailor-Talk Agent CSV Data Analyzer
This app provides an interactive chat interface to analyze CSV datasets using natural language.
"""

import streamlit as st
import requests
import json
import plotly.io as pio


# ============================================================================
# CONFIGURATION
# ============================================================================

BACKEND_URL = "http://127.0.0.1:8000"


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Titanic AI Analyst",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def initialize_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "session_id" not in st.session_state:
        st.session_state.session_id = "titanic_default"
    
    if "dataset_uploaded" not in st.session_state:
        st.session_state.dataset_uploaded = False


initialize_session_state()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def upload_dataset(uploaded_file):
    """
    Upload a CSV file to the backend.
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        
    Returns:
        tuple: (success: bool, message: str, session_id: str or None)
    """
    try:
        response = requests.post(
            f"{BACKEND_URL}/upload-dataset",
            files={"file": uploaded_file}
        )
        
        if response.status_code == 200:
            data = response.json()
            return True, "Dataset uploaded successfully!", data["session_id"]
        else:
            return False, f"Upload failed: {response.text}", None
            
    except Exception as e:
        return False, f"Error: {str(e)}", None


def send_chat_query(query, session_id):
    """
    Send a chat query to the backend.
    
    Args:
        query: User query string
        session_id: Current session ID
        
    Returns:
        tuple: (success: bool, response_data: dict or None, error_msg: str or None)
    """
    try:
        response = requests.post(
            f"{BACKEND_URL}/chat",
            json={
                "query": query,
                "session_id": session_id
            }
        )
        
        if response.status_code == 200:
            return True, response.json(), None
        else:
            return False, None, f"Backend error: {response.text}"
            
    except Exception as e:
        return False, None, f"Connection error: {str(e)}"


def render_message(message, idx: int | None = None):
    """
    Render a single chat message.
    
    Args:
        message: Dict with 'role', 'content', and optional 'chart' keys
    """
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        if message.get("chart"):
            try:
                fig = pio.from_json(message["chart"])
                chart_kwargs = {"use_container_width": True}
                if idx is not None:
                    chart_kwargs["key"] = f"chart-{idx}"
                st.plotly_chart(fig, **chart_kwargs)
            except Exception as e:
                st.error(f"Error rendering chart: {str(e)}")


# ============================================================================
# MAIN UI COMPONENTS
# ============================================================================

def render_header():
    """Render the main header section."""
    st.title("🚢 Titanic Dataset AI Analyst")
    st.caption("Ask questions about passengers using natural language.")


def render_sidebar():
    """Render the sidebar with dataset selection and upload options."""
    st.sidebar.header("📊 Dataset Mode")
    
    mode = st.sidebar.radio(
        "Choose dataset:",
        ["Titanic Dataset", "Upload CSV"],
        help="Select a pre-loaded dataset or upload your own CSV file"
    )
    
    if mode == "Upload CSV":
        st.sidebar.markdown("---")
        uploaded_file = st.sidebar.file_uploader(
            "Upload CSV file",
            type=["csv"],
            help="Upload a CSV file to analyze"
        )
        
        if uploaded_file is not None:
            if not st.session_state.dataset_uploaded:
                with st.spinner("Uploading dataset..."):
                    success, message, session_id = upload_dataset(uploaded_file)
                
                if success:
                    st.session_state.session_id = session_id
                    st.session_state.dataset_uploaded = True
                    st.sidebar.success(message)
                    st.sidebar.info(f"Session ID: `{session_id}`")
                else:
                    st.sidebar.error(message)
    else:
        # Reset to default Titanic dataset
        if st.session_state.session_id != "titanic_default":
            st.session_state.session_id = "titanic_default"
            st.session_state.dataset_uploaded = False
    
    # Dataset info
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📌 Current Session")
    st.sidebar.code(st.session_state.session_id)
    
    # Clear chat button
    if st.sidebar.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


def render_chat_history():
    """Render the chat history."""
    for i, message in enumerate(st.session_state.messages):
        render_message(message, idx=i)


def handle_user_input():
    """Handle user input and process the query."""
    user_input = st.chat_input("Ask a question about the dataset...")
    
    if user_input:
        # Add user message to history
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Send query to backend
        with st.spinner("🤔 Analyzing dataset..."):
            success, data, error = send_chat_query(
                user_input, 
                st.session_state.session_id
            )
        
        if success:
            # Extract response components
            text = data.get("response", "")
            chart = data.get("chart")
            raw_data = data.get("data")
            
            # Add assistant response to history
            assistant_message = {
                "role": "assistant",
                "content": text,
                "chart": chart
            }
            st.session_state.messages.append(assistant_message)
            
            # Display assistant response
            render_message(assistant_message, idx=len(st.session_state.messages) - 1)
            
            # Optionally display raw data
            # Use JSON viewer only for dicts/lists; fall back to plain display for scalars
            if raw_data is not None:
                with st.expander("📊 View Raw Data"):
                    if isinstance(raw_data, (dict, list)):
                        st.json(raw_data)
                    else:
                        st.write(raw_data)
        else:
            # Display error
            error_message = {
                "role": "assistant",
                "content": f"❌ Error: {error}"
            }
            st.session_state.messages.append(error_message)
            
            with st.chat_message("assistant"):
                st.error(error)


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point."""
    render_header()
    render_sidebar()
    render_chat_history()
    handle_user_input()


if __name__ == "__main__":
    main()