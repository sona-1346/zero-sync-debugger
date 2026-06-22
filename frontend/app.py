import os
import streamlit as nn  # Standard alias is st, but let's use st to avoid streamlit custom wrapper issues, wait we can just import streamlit as st
import streamlit as st
import requests
import datetime
import json
from typing import Dict, Any, List

# Get API URL from env or default
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Set Page Config
st.set_page_config(
    page_title="Zero-Sync Debugger | Remember Forever",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Dark Mode, Premium Glassmorphism & Neon Mint/Purple theme)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono:wght@400;600&display=swap');
    
    /* Global Overrides */
    * {
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Main Layout Styling */
    .stApp {
        background: radial-gradient(circle at top right, #1a103c 0%, #0d0b18 50%, #08060f 100%);
        color: #e2e8f0;
    }
    
    /* Header Gradient Text */
    .title-text {
        background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 3rem;
        margin-bottom: 5px;
        text-shadow: 0 4px 20px rgba(0, 242, 254, 0.15);
    }
    
    .tagline-text {
        font-size: 1.25rem;
        font-weight: 300;
        color: #94a3b8;
        margin-bottom: 25px;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #0c0a15 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Custom Card Design */
    .card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        transition: all 0.3s ease;
    }
    
    .card:hover {
        border-color: rgba(0, 242, 254, 0.3);
        box-shadow: 0 8px 32px 0 rgba(0, 242, 254, 0.1);
        transform: translateY(-2px);
    }
    
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding-bottom: 8px;
    }
    
    .project-badge {
        background: linear-gradient(90deg, #8b5cf6 0%, #6366f1 100%);
        color: #ffffff;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .timestamp-badge {
        color: #64748b;
        font-size: 0.75rem;
    }
    
    .card-title {
        color: #f1f5f9;
        font-size: 1.1rem;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
        margin-bottom: 10px;
        word-break: break-all;
    }
    
    .card-body {
        font-size: 0.95rem;
        line-height: 1.6;
        color: #cbd5e1;
    }
    
    /* Code and Preformatted Blocks */
    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
        background-color: #12101e !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 8px !important;
    }
    
    /* Status indicators */
    .match-banner {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.15) 100%);
        border: 1px solid #10b981;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 20px;
        color: #34d399;
    }
    
    .match-banner-title {
        font-weight: 600;
        font-size: 1.1rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .chat-bubble {
        padding: 14px 18px;
        border-radius: 16px;
        margin-bottom: 10px;
        max-width: 85%;
        line-height: 1.5;
    }
    
    .chat-user {
        background: #2563eb;
        color: white;
        margin-left: auto;
        border-bottom-right-radius: 4px;
    }
    
    .chat-assistant {
        background: rgba(255, 255, 255, 0.05);
        color: #cbd5e1;
        margin-right: auto;
        border-bottom-left-radius: 4px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Custom Timeline View */
    .timeline-container {
        border-left: 2px solid rgba(139, 92, 246, 0.3);
        margin-left: 20px;
        padding-left: 20px;
        position: relative;
    }
    
    .timeline-item {
        position: relative;
        margin-bottom: 30px;
    }
    
    .timeline-dot {
        position: absolute;
        left: -31px;
        top: 4px;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background: #8b5cf6;
        border: 4px solid #08060f;
        box-shadow: 0 0 10px rgba(139, 92, 246, 0.8);
    }
    
    .timeline-date {
        font-size: 0.85rem;
        color: #a78bfa;
        font-weight: 600;
        margin-bottom: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to query API
def api_request(method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Any:
    url = f"{BACKEND_URL}{endpoint}"
    try:
        if method.upper() == "POST":
            response = requests.post(url, json=data, timeout=15)
        else:
            response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Backend API returned status code {response.status_code}: {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("🔌 Cannot connect to backend server. Please verify the FastAPI server is running on port 8000.")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return None

# Check Backend Status
backend_online = False
try:
    health = requests.get(f"{BACKEND_URL}/", timeout=2)
    if health.status_code == 200:
        backend_online = True
except Exception:
    pass

# Sidebar Layout
with st.sidebar:
    st.image("https://img.icons8.com/nolan/128/artificial-intelligence.png", width=70)
    st.markdown("<h2 style='margin-top:0px; color:#f1f5f9;'>Zero-Sync</h2>", unsafe_allow_html=True)
    st.markdown("<p style='font-style:italic; color:#94a3b8;'>\"Debug once. Remember forever.\"</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    page = st.selectbox(
        "Navigate",
        ["Submit Error", "Similar Bugs", "Bug History", "AI Chat Assistant"]
    )
    
    st.markdown("---")
    # Project Settings / Status Panel
    st.subheader("System Status")
    if backend_online:
        st.success("Backend: ONLINE")
        # Check Parcle Service status
        # Since we don't have a direct health endpoint for parcle, we know if it operates or fallback.
        st.info("AI Service: OpenAI API Fallback (Mock) / Active (depending on .env configuration)")
    else:
        st.error("Backend: OFFLINE")
        st.warning("Run `uvicorn backend.main:app --reload` to start backend.")

# Top Header Layout
st.markdown("<div class='title-text'>⚡ Zero-Sync Debugger</div>", unsafe_allow_html=True)
st.markdown("<div class='tagline-text'>AI-powered long-term memory for developer bugs and solutions</div>", unsafe_allow_html=True)

# ----------------- PAGE 1: SUBMIT ERROR -----------------
if page == "Submit Error":
    st.subheader("Submit Error Signature")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("submit_error_form"):
            project_name = st.text_input("Project Name", value="My Awesome App", placeholder="e.g. sentinel-ai")
            error_message = st.text_area("Error Message *", height=120, placeholder="Paste the stack trace header or specific error message here...")
            description = st.text_area("Bug Description", height=80, placeholder="What were you doing when this happened? Add context...")
            
            uploaded_file = st.file_uploader("Upload Log File", type=["txt", "log", "out"])
            log_content = ""
            if uploaded_file is not None:
                try:
                    log_content = uploaded_file.read().decode("utf-8")
                    st.success(f"Successfully uploaded {uploaded_file.name} ({len(log_content)} bytes)")
                except Exception as e:
                    st.error(f"Error reading file: {e}")
            
            submit_btn = st.form_submit_button("Submit & Remember")
            
    with col2:
        st.markdown("""
        ### How it works
        1. **Semantic Comparison**: When you submit an error, Zero-Sync searches its SQLite / Parcle memory database.
        2. **Instant Recall**: If you've resolved a similar error before, it will retrieve your previous fix instantly, preventing redundant work.
        3. **AI Root Cause Analysis**: If this error is new, Zero-Sync will call the OpenAI API to analyze root causes, prevention guidelines, and code patches.
        4. **Memory Capture**: The new fix is committed to the long-term memory layer so it's remembered forever!
        """)

    if submit_btn:
        if not error_message.strip():
            st.warning("Please enter an error message.")
        else:
            with st.spinner("Searching memory layer for matches..."):
                payload = {
                    "error_message": error_message,
                    "description": description,
                    "project_name": project_name,
                    "log_content": log_content
                }
                
                result = api_request("POST", "/submit_error", data=payload)
                
                if result:
                    # Clear separation if matched vs generated
                    if result.get("similarity_matched"):
                        score = result.get("similarity_score", 0.0) * 100
                        st.markdown(f"""
                        <div class='match-banner'>
                            <div class='match-banner-title'>🎯 Memory Match Found (Similarity: {score:.1f}%)</div>
                            You or your team solved a highly similar bug in the past. Here is the recovered fix:
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.balloons()
                        st.markdown("""
                        <div style='background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(99, 102, 241, 0.15) 100%); border: 1px solid #8b5cf6; border-radius: 12px; padding: 16px; margin-bottom: 20px; color: #a78bfa;'>
                            <div style='font-weight: 600; font-size: 1.1rem;'>✨ New Bug Analyzed & Ingested</div>
                            This bug was not seen before. OpenAI has generated an analysis and recorded it in the memory layer.
                        </div>
                        """, unsafe_allow_html=True)

                    # Show Results in beautiful layout
                    st.markdown("### 📋 Debugging Guide")
                    
                    tab1, tab2, tab3 = st.tabs(["🔍 Root Cause & Solution", "💻 Suggested Code Fix", "🛠️ Commands & Dependencies"])
                    
                    with tab1:
                        st.markdown("#### **Root Cause Analysis**")
                        st.info(result.get("root_cause"))
                        
                        st.markdown("#### **Recommended Solution**")
                        st.success(result.get("solution"))
                        
                        st.markdown("#### **Prevention Tips**")
                        st.markdown(result.get("prevention_tips"))
                        
                    with tab2:
                        st.markdown("#### **Suggested Code Changes**")
                        code_snippet = result.get("suggested_code_changes", "")
                        if code_snippet:
                            st.code(code_snippet, language="python")
                        else:
                            st.write("No specific code modifications suggested.")
                            
                    with tab3:
                        st.markdown("#### **Execution Commands**")
                        cmds = result.get("suggested_commands", "")
                        if cmds:
                            st.code(cmds, language="bash")
                        else:
                            st.write("No execution commands required.")
                            
                        st.markdown("#### **Dependency Corrections**")
                        deps = result.get("suggested_dependency_fixes", "")
                        if deps:
                            st.code(deps, language="text")
                        else:
                            st.write("No dependency packages modified.")

# ----------------- PAGE 2: SIMILAR BUGS -----------------
elif page == "Similar Bugs":
    st.subheader("Semantic Similarity Search")
    st.write("Paste an error signature or type keyword descriptions to search similar historic entries in memory.")
    
    search_error = st.text_area("Error Message / Search Query", height=120, placeholder="Paste signature to compare against DB...")
    search_project = st.text_input("Filter by Project (Optional)", placeholder="e.g. sentinel-ai")
    search_limit = st.slider("Max Results", min_value=1, max_value=10, value=3)
    
    search_btn = st.button("Search Memory")
    
    if search_btn:
        if not search_error.strip():
            st.warning("Please provide an error message or query to search.")
        else:
            with st.spinner("Retrieving semantic matches..."):
                params = {
                    "error_message": search_error,
                    "limit": search_limit
                }
                if search_project:
                    params["project_name"] = search_project
                    
                results = api_request("GET", "/similar_bugs", params=params)
                
                if results:
                    st.success(f"Found {len(results)} matches in memory.")
                    for bug in results:
                        score = bug.get("similarity_score", 0.0)
                        
                        # Generate customized UI card
                        st.markdown(f"""
                        <div class='card'>
                            <div class='card-header'>
                                <span class='project-badge'>{bug.get('project_name')}</span>
                                <span class='timestamp-badge'>Matched with {(score*100):.1f}% confidence</span>
                            </div>
                            <div class='card-title'>ID #{bug.get('id')} - Error Message</div>
                            <pre style='padding: 10px; margin-bottom: 15px;'><code>{bug.get('error_message')}</code></pre>
                            <div class='card-body'>
                                <strong>Root Cause:</strong><br/>
                                {bug.get('root_cause')}<br/><br/>
                                <strong>Solution:</strong><br/>
                                {bug.get('solution')}<br/>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Expand details (Code / Commands) using streamlit components
                        with st.expander(f"Inspect code & dependency fixes for Bug #{bug.get('id')}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown("**Code Changes**")
                                if bug.get("suggested_code_changes"):
                                    st.code(bug.get("suggested_code_changes"), language="python")
                                else:
                                    st.caption("None suggested.")
                            with col2:
                                st.markdown("**Terminal Commands**")
                                if bug.get("suggested_commands"):
                                    st.code(bug.get("suggested_commands"), language="bash")
                                else:
                                    st.caption("None suggested.")
                else:
                    st.info("No matching historical bugs found.")

# ----------------- PAGE 3: BUG HISTORY -----------------
elif page == "Bug History":
    st.subheader("Historical Log Book")
    
    col1, col2 = st.columns(2)
    with col1:
        filter_project = st.text_input("Filter by Project", placeholder="e.g. My Awesome App")
    with col2:
        search_kw = st.text_input("Keyword Search", placeholder="e.g. division, database, IndexOutOfBounds")
        
    params = {}
    if filter_project:
        params["project_name"] = filter_project
    if search_kw:
        params["search"] = search_kw
        
    bugs = api_request("GET", "/bug_history", params=params)
    
    if bugs:
        st.write(f"Showing {len(bugs)} logged issues.")
        
        # Timeline view
        st.markdown("<div class='timeline-container'>", unsafe_allow_html=True)
        
        for bug in bugs:
            # Parse Date
            dt_str = bug.get("timestamp", "")
            try:
                # Format: 2026-06-21T17:04:40
                dt = datetime.datetime.fromisoformat(dt_str)
                display_date = dt.strftime("%B %d, %Y - %I:%M %p")
            except Exception:
                display_date = dt_str

            st.markdown(f"""
            <div class='timeline-item'>
                <div class='timeline-dot'></div>
                <div class='timeline-date'>{display_date}</div>
                <div class='card'>
                    <div class='card-header'>
                        <span class='project-badge'>{bug.get('project_name')}</span>
                        <span class='timestamp-badge'>Bug ID: #{bug.get('id')}</span>
                    </div>
                    <div class='card-title'>{bug.get('error_message')[:120]}...</div>
                    <div class='card-body'>
                        <strong>Root Cause:</strong> {bug.get('root_cause')[:250]}...
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Interactive expansion button for the full details
            with st.expander(f"🔍 Expand full resolution details for Bug #{bug.get('id')}"):
                st.markdown(f"**Full Error Message:**")
                st.code(bug.get("error_message"))
                
                st.markdown(f"**Root Cause:**")
                st.write(bug.get("root_cause"))
                
                st.markdown(f"**Solution:**")
                st.write(bug.get("solution"))
                
                st.markdown(f"**Prevention Tips:**")
                st.markdown(bug.get("prevention_tips", "No tips provided."))
                
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**Suggested Code Patch**")
                    if bug.get("suggested_code_changes"):
                        st.code(bug.get("suggested_code_changes"), language="python")
                    else:
                        st.caption("None.")
                with c2:
                    st.markdown("**Suggested Commands**")
                    if bug.get("suggested_commands"):
                        st.code(bug.get("suggested_commands"), language="bash")
                    else:
                        st.caption("None.")
                        
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No logs match the criteria or no bugs submitted yet.")

# ----------------- PAGE 4: AI CHAT ASSISTANT -----------------
elif page == "AI Chat Assistant":
    st.subheader("Memory Chat Room")
    st.caption("Ask questions about previously resolved bugs, common code fixes, or overall project diagnostic history.")

    project_ctx = st.text_input("Active Project Context", value="My Awesome App")
    
    # Session state for chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    # Clear history button
    if st.button("Clear Chat Logs"):
        st.session_state.messages = []
        st.success("Chat history cleared.")
        st.rerun()

    # Display historical chat logs
    for msg in st.session_state.messages:
        role_class = "chat-user" if msg["role"] == "user" else "chat-assistant"
        st.markdown(f"""
        <div class='chat-bubble {role_class}'>
            <strong>{'You' if msg['role'] == 'user' else 'Assistant'}:</strong><br/>
            {msg['content']}
        </div>
        """, unsafe_allow_html=True)

    # Input form for new message
    user_query = st.chat_input("Ask a question (e.g. 'Have we seen division by zero before?' or 'How did we fix the average calculator?')")
    
    if user_query:
        # Display user message instantly
        st.markdown(f"""
        <div class='chat-bubble chat-user'>
            <strong>You:</strong><br/>
            {user_query}
        </div>
        """, unsafe_allow_html=True)
        
        with st.spinner("Retrieving history & thinking..."):
            payload = {
                "message": user_query,
                "history": st.session_state.messages,
                "project_name": project_ctx
            }
            
            result = api_request("POST", "/chat", data=payload)
            
            if result:
                answer = result.get("response", "No response returned.")
                # Save to history
                st.session_state.messages.append({"role": "user", "content": user_query})
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
                # Rerun to render bubble correctly
                st.rerun()
