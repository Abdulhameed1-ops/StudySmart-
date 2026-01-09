import streamlit as st
import requests
import json
import base64
from PIL import Image
import io
import PyPDF2
import docx

# Page config
st.set_page_config(
    page_title="StudySmart",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to match Meta AI style
st.markdown("""
<style>
    /* Main container */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Header styling */
    .main-header {
        background: white;
        padding: 20px;
        border-radius: 16px;
        margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    .main-header h1 {
        color: #1c1e21;
        font-size: 32px;
        font-weight: 600;
        margin: 0;
    }
    
    /* Chat container */
    .chat-container {
        background: white;
        border-radius: 16px;
        padding: 24px;
        margin: 20px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    /* Greeting message */
    .greeting {
        text-align: center;
        font-size: 28px;
        font-weight: 500;
        color: #1c1e21;
        margin: 60px 0 40px 0;
    }
    
    /* Suggestion cards */
    .suggestion-card {
        background: #f5f5f5;
        border-radius: 12px;
        padding: 16px 20px;
        margin: 12px 0;
        cursor: pointer;
        transition: all 0.2s;
        border: 1px solid transparent;
    }
    
    .suggestion-card:hover {
        background: #e9ecef;
        border-color: #0866ff;
    }
    
    .suggestion-card-text {
        color: #1c1e21;
        font-size: 15px;
        font-weight: 400;
    }
    
    /* Message bubbles */
    .user-message {
        background: #0866ff;
        color: white;
        padding: 12px 16px;
        border-radius: 18px;
        margin: 8px 0;
        max-width: 70%;
        float: right;
        clear: both;
    }
    
    .ai-message {
        background: #f0f2f5;
        color: #1c1e21;
        padding: 12px 16px;
        border-radius: 18px;
        margin: 8px 0;
        max-width: 70%;
        float: left;
        clear: both;
    }
    
    /* Input area */
    .stTextInput > div > div > input {
        border-radius: 24px;
        border: 1px solid #dfe1e5;
        padding: 12px 20px;
        font-size: 15px;
    }
    
    /* Buttons */
    .stButton > button {
        background: #0866ff;
        color: white;
        border: none;
        border-radius: 24px;
        padding: 10px 24px;
        font-weight: 500;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        background: #0952cc;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: white;
    }
    
    /* File uploader */
    .uploadedFile {
        background: #f0f2f5;
        border-radius: 12px;
        padding: 12px;
        margin: 8px 0;
    }
    
    /* Hide default streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'uploaded_content' not in st.session_state:
    st.session_state.uploaded_content = ""
if 'cohere_api_key' not in st.session_state:
    st.session_state.cohere_api_key = ""

# Cohere API function
def chat_with_cohere(message, context=""):
    """Send message to Cohere API using requests"""
    api_key = st.session_state.cohere_api_key
    
    if not api_key:
        return "Please enter your Cohere API key in the sidebar."
    
    url = "https://api.cohere.ai/v1/chat"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Build the message with context
    full_message = message
    if context:
        full_message = f"Context from uploaded files:\n{context}\n\nUser question: {message}"
    
    data = {
        "model": "command-r-plus",
        "message": full_message,
        "chat_history": [
            {"role": msg["role"], "message": msg["content"]} 
            for msg in st.session_state.messages[-5:]  # Last 5 messages for context
        ] if st.session_state.messages else [],
        "temperature": 0.7
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result.get("text", "Sorry, I couldn't generate a response.")
    except Exception as e:
        return f"Error: {str(e)}"

# Extract text from different file types
def extract_text_from_file(uploaded_file):
    """Extract text from PDF, DOCX, or TXT files"""
    try:
        if uploaded_file.type == "application/pdf":
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
        
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(io.BytesIO(uploaded_file.read()))
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        
        elif uploaded_file.type == "text/plain":
            return uploaded_file.read().decode("utf-8")
        
        else:
            return "Unsupported file type"
    except Exception as e:
        return f"Error extracting text: {str(e)}"

def generate_quiz(content, num_questions=5):
    """Generate quiz questions from content"""
    prompt = f"""Based on the following content, generate {num_questions} multiple-choice quiz questions. 
    Format each question as:
    Q[number]: [question]
    A) [option]
    B) [option]
    C) [option]
    D) [option]
    Correct Answer: [letter]
    Explanation: [brief explanation]
    
    Content:
    {content[:3000]}"""  # Limit content length
    
    return chat_with_cohere(prompt)

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    # API Key input
    api_key = st.text_input(
        "Cohere API Key",
        type="password",
        value=st.session_state.cohere_api_key,
        help="Get your API key from https://cohere.ai"
    )
    if api_key:
        st.session_state.cohere_api_key = api_key
    
    st.markdown("---")
    
    # File upload
    st.markdown("### 📁 Upload Files")
    uploaded_files = st.file_uploader(
        "Upload study materials",
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
        help="Upload PDFs, Word docs, text files, or images"
    )
    
    if uploaded_files:
        st.session_state.uploaded_content = ""
        for file in uploaded_files:
            if file.type.startswith("image"):
                st.image(file, caption=file.name, use_column_width=True)
                st.session_state.uploaded_content += f"\n[Image: {file.name}]\n"
            else:
                text = extract_text_from_file(file)
                st.session_state.uploaded_content += f"\n{text}\n"
                st.success(f"✅ {file.name} loaded")
    
    st.markdown("---")
    
    # Quick actions
    st.markdown("### 🎯 Quick Actions")
    
    if st.button("🎲 Generate Quiz"):
        if st.session_state.uploaded_content:
            with st.spinner("Generating quiz..."):
                quiz = generate_quiz(st.session_state.uploaded_content)
                st.session_state.messages.append({"role": "user", "content": "Generate a quiz from my uploaded files"})
                st.session_state.messages.append({"role": "assistant", "content": quiz})
                st.rerun()
        else:
            st.warning("Please upload files first")
    
    if st.button("📝 Summarize Content"):
        if st.session_state.uploaded_content:
            with st.spinner("Summarizing..."):
                summary = chat_with_cohere("Provide a comprehensive summary of this content", st.session_state.uploaded_content)
                st.session_state.messages.append({"role": "user", "content": "Summarize my uploaded content"})
                st.session_state.messages.append({"role": "assistant", "content": summary})
                st.rerun()
        else:
            st.warning("Please upload files first")
    
    if st.button("🔑 Extract Key Points"):
        if st.session_state.uploaded_content:
            with st.spinner("Extracting key points..."):
                points = chat_with_cohere("Extract the main key points and concepts from this content in bullet points", st.session_state.uploaded_content)
                st.session_state.messages.append({"role": "user", "content": "Extract key points from my content"})
                st.session_state.messages.append({"role": "assistant", "content": points})
                st.rerun()
        else:
            st.warning("Please upload files first")
    
    st.markdown("---")
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# Main content
st.markdown('<div class="main-header"><h1>📚 StudySmart</h1></div>', unsafe_allow_html=True)

# Show greeting if no messages
if not st.session_state.messages:
    st.markdown('<div class="greeting">Hey, how can I help you study today?</div>', unsafe_allow_html=True)
    
    # Suggestion cards
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📚 Explain a concept from my notes", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "Explain the main concept from my uploaded notes"})
            if st.session_state.uploaded_content:
                response = chat_with_cohere("Explain the main concept from this content in simple terms", st.session_state.uploaded_content)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()
        
        if st.button("🎯 Create practice questions", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "Create practice questions"})
            if st.session_state.uploaded_content:
                response = generate_quiz(st.session_state.uploaded_content, 3)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()
    
    with col2:
        if st.button("💡 Help me understand a topic", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "Help me understand the main topics"})
            if st.session_state.uploaded_content:
                response = chat_with_cohere("Break down and explain the main topics in this content", st.session_state.uploaded_content)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()
        
        if st.button("🔍 Find specific information", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "What information is available in my files?"})
            if st.session_state.uploaded_content:
                response = chat_with_cohere("List the main topics and information available in this content", st.session_state.uploaded_content)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()

# Display chat messages
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f'<div class="user-message">{message["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="ai-message">{message["content"]}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Chat input
st.markdown("<br>", unsafe_allow_html=True)
col1, col2 = st.columns([6, 1])

with col1:
    user_input = st.text_input(
        "Message",
        placeholder="Ask anything...",
        label_visibility="collapsed",
        key="user_input"
    )

with col2:
    send_button = st.button("Send ⬆️", use_container_width=True)

# Handle message sending
if send_button and user_input:
    if not st.session_state.cohere_api_key:
        st.error("Please enter your Cohere API key in the sidebar")
    else:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Get AI response
        with st.spinner("Thinking..."):
            response = chat_with_cohere(user_input, st.session_state.uploaded_content)
            st.session_state.messages.append({"role": "assistant", "content": response})
        
        st.rerun()

# Footer
st.markdown("""
<div style='text-align: center; color: #65676b; font-size: 13px; margin-top: 40px;'>
    StudySmart • Powered by Cohere AI
</div>
""", unsafe_allow_html=True)