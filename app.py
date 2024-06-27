import streamlit as st
import json
import os
from anthropic import Anthropic

# Initialize Anthropic client
client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

# File to store the conversations
JSONL_FILE = "conversations.jsonl"

def get_claude_response(system_prompt, messages, max_tokens):
    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=max_tokens,
        system=system_prompt,
        messages=messages
    )
    return response.content[0].text

# Custom JSON encoder to handle special characters
class SafeJSONEncoder(json.JSONEncoder):
    def encode(self, obj):
        return super(SafeJSONEncoder, self).encode(obj).replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")

# Function to safely save conversation
def safe_save_conversation(conversation):
    with open(JSONL_FILE, "a") as f:
        json.dump(conversation, f, cls=SafeJSONEncoder)
        f.write("\n")

# Custom CSS for dark mode
st.markdown("""
<style>
    .main {
        background-color: #1E1E1E;
        color: #D4D4D4;
    }
    .stTextArea textarea {
        background-color: #2D2D2D;
        color: #D4D4D4;
        border: 1px solid #3E3E3E;
    }
    .stButton>button {
        background-color: #2D2D2D;
        color: #D4D4D4;
        border: 1px solid #4A4A4A;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #3D3D3D;
        border-color: #5A5A5A;
    }
    .user-message {
        background-color: #264F78;
        color: #D4D4D4;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .assistant-message {
        background-color: #3E3E3E;
        color: #D4D4D4;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .stExpander {
        background-color: #2D2D2D;
        border: 1px solid #3E3E3E;
    }
    .sidebar .stButton>button {
        width: 100%;
    }
    .conversation-container {
        border: 1px solid #3E3E3E;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 20px;
    }
    .stSlider>div>div>div {
        background-color: transparent !important;
    }
    .stSlider>div>div>div>div {
        background-color: #0078D4 !important;
    }
    .stSlider>div>div>div>div>div {
        color: #D4D4D4 !important;
    }
    /* Custom styles for number input */
    .stNumberInput>div>div>input {
        background-color: #2D2D2D;
        color: #D4D4D4;
        border: 1px solid #3E3E3E;
    }
    /* Style for info boxes */
    .stAlert {
        background-color: #2D2D2D;
        color: #D4D4D4;
        border: 1px solid #3E3E3E;
    }
</style>
""", unsafe_allow_html=True)

st.title("🤖 GPT Fine-tuning Data Generator")

# Initialize session state
if 'conversation' not in st.session_state:
    st.session_state.conversation = []
if 'system_prompt' not in st.session_state:
    st.session_state.system_prompt = "You are a helpful assistant."
if 'editing' not in st.session_state:
    st.session_state.editing = False
if 'max_tokens' not in st.session_state:
    st.session_state.max_tokens = 1000

# Sidebar for system prompt and file operations
with st.sidebar:
    st.header("Configuration")
    st.session_state.system_prompt = st.text_area("System Prompt", st.session_state.system_prompt, height=100)
    
    st.subheader("Max Tokens")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.session_state.max_tokens = st.slider("", min_value=256, max_value=4096, value=st.session_state.max_tokens, step=8)
    with col2:
        max_tokens_input = st.number_input("", min_value=256, max_value=4096, value=st.session_state.max_tokens, step=1, label_visibility="collapsed")
        if max_tokens_input != st.session_state.max_tokens:
            st.session_state.max_tokens = max_tokens_input
    
    st.subheader("File Operations")
    if os.path.exists(JSONL_FILE):
        file_size = os.path.getsize(JSONL_FILE)
        with open(JSONL_FILE, "r") as f:
            num_conversations = sum(1 for line in f)
        st.info(f"File Size: {file_size} bytes\nConversations: {num_conversations}")
    
    if st.button("Export JSONL File", key="export"):
        with open(JSONL_FILE, "r") as f:
            st.download_button(
                label="Download JSONL",
                data=f,
                file_name="conversations.jsonl",
                mime="application/jsonl"
            )

# Main conversation area
st.subheader("Current Conversation")
conversation_placeholder = st.empty()

# Function to display conversation
def display_conversation():
    with conversation_placeholder.container():
        for message in st.session_state.conversation:
            if message['role'] == 'user':
                st.markdown(f"<div class='user-message'>🧑 User: {message['content']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='assistant-message'>🤖 Assistant: {message['content']}</div>", unsafe_allow_html=True)

display_conversation()

# User input and send button
with st.form(key='message_form'):
    user_message = st.text_area("Type your message here", key='user_message')
    send_button = st.form_submit_button("Send Message")

if send_button and user_message:
    st.session_state.conversation.append({"role": "user", "content": user_message})
    with st.spinner("Claude is thinking..."):
        claude_response = get_claude_response(st.session_state.system_prompt, st.session_state.conversation, st.session_state.max_tokens)
    st.session_state.conversation.append({"role": "assistant", "content": claude_response})
    st.session_state.editing = True
    st.experimental_rerun()

# Edit Assistant Message
if st.session_state.editing and st.session_state.conversation:
    last_assistant_message = next((m for m in reversed(st.session_state.conversation) if m['role'] == 'assistant'), None)
    if last_assistant_message:
        st.subheader("Edit Assistant's Last Response")
        edited_response = st.text_area("Edit response", last_assistant_message['content'], height=150)
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Update Response"):
                last_assistant_message['content'] = edited_response
                st.session_state.editing = False
                st.experimental_rerun()
        with col2:
            if st.button("Continue Without Editing"):
                st.session_state.editing = False
                st.experimental_rerun()
        with col3:
            if st.button("Retry Response", key="retry"):
                st.session_state.conversation.pop()  # Remove last assistant message
                with st.spinner("Claude is thinking..."):
                    new_response = get_claude_response(st.session_state.system_prompt, st.session_state.conversation, st.session_state.max_tokens)
                st.session_state.conversation.append({"role": "assistant", "content": new_response})
                st.experimental_rerun()

# Action buttons
col1, col2 = st.columns(2)
with col1:
    if st.button("Accept and Save Conversation", key="save"):
        if st.session_state.conversation:
            openai_format = {
                "messages": [{"role": "system", "content": st.session_state.system_prompt}] + st.session_state.conversation
            }
            safe_save_conversation(openai_format)
            st.success("Conversation saved successfully!")
            st.session_state.conversation = []
            st.session_state.editing = False
            st.experimental_rerun()

with col2:
    if st.button("Discard Conversation", key="discard", type="primary"):
        st.session_state.conversation = []
        st.session_state.editing = False
        st.success("Conversation discarded.")
        st.experimental_rerun()

# Display saved conversations
if os.path.exists(JSONL_FILE):
    st.subheader("Recent Saved Conversations")
    with open(JSONL_FILE, "r") as f:
        conversations = [json.loads(line) for line in f]
        for i, conversation in enumerate(conversations[-3:], 1):  # Show last 3 conversations
            with st.expander(f"Conversation {len(conversations)-3+i}"):
                for message in conversation['messages']:
                    st.write(f"{message['role'].capitalize()}: {message['content']}")