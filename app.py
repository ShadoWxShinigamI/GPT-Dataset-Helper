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
        model="claude-3-5-sonnet-20240620", #claude-3-haiku-20240307, claude-3-sonnet-20240229, claude-3-opus-20240229
        max_tokens=max_tokens,
        system=system_prompt,
        messages=messages
    )
    return response.content[0].text

class SafeJSONEncoder(json.JSONEncoder):
    def encode(self, obj):
        return super(SafeJSONEncoder, self).encode(obj).replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")

def safe_save_conversation(conversation):
    with open(JSONL_FILE, "a") as f:
        json.dump(conversation, f, cls=SafeJSONEncoder)
        f.write("\n")

# Custom CSS for improved UI
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
    .stNumberInput>div>div>input {
        background-color: #2D2D2D;
        color: #D4D4D4;
        border: 1px solid #3E3E3E;
    }
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
    st.session_state.editing = -1
if 'max_tokens' not in st.session_state:
    st.session_state.max_tokens = 1000

# Sidebar
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
st.header("Current Conversation")

for i, message in enumerate(st.session_state.conversation):
    if message['role'] == 'user':
        st.markdown(f"<div class='user-message'>🧑 User: {message['content']}</div>", unsafe_allow_html=True)
    else:
        col1, col2, col3 = st.columns([0.8, 0.1, 0.1])
        with col1:
            st.markdown(f"<div class='assistant-message'>🤖 Assistant: {message['content']}</div>", unsafe_allow_html=True)
        with col2:
            if st.button("✏️", key=f"edit_{i}"):
                st.session_state.editing = i
        with col3:
            if i == len(st.session_state.conversation) - 1 and message['role'] == 'assistant':
                if st.button("🔄", key=f"retry_{i}"):
                    with st.spinner("Retrying..."):
                        st.session_state.conversation.pop()  # Remove the last assistant message
                        new_response = get_claude_response(st.session_state.system_prompt, st.session_state.conversation, st.session_state.max_tokens)
                        st.session_state.conversation.append({"role": "assistant", "content": new_response})
                    st.experimental_rerun()

    if st.session_state.editing == i:
        edited_response = st.text_area(f"Edit response", message['content'], key=f"edit_area_{i}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Update", key=f"update_{i}"):
                st.session_state.conversation[i]['content'] = edited_response
                st.session_state.editing = -1
                st.experimental_rerun()
        with col2:
            if st.button("Cancel", key=f"cancel_{i}"):
                st.session_state.editing = -1
                st.experimental_rerun()

# User input
user_message = st.text_area("Your message", key='user_message', height=100)
col1, col2, col3 = st.columns([1,1,2])
with col1:
    if st.button("Send", use_container_width=True):
        if user_message:
            st.session_state.conversation.append({"role": "user", "content": user_message})
            with st.spinner("Claude is thinking..."):
                claude_response = get_claude_response(st.session_state.system_prompt, st.session_state.conversation, st.session_state.max_tokens)
            st.session_state.conversation.append({"role": "assistant", "content": claude_response})
            st.experimental_rerun()
with col2:
    if st.button("Clear", use_container_width=True):
        st.session_state.conversation = []
        st.session_state.editing = -1
        st.success("Conversation cleared.")
        st.experimental_rerun()

# Save conversation
if st.button("Save Conversation", use_container_width=True):
    if st.session_state.conversation:
        openai_format = {
            "messages": [{"role": "system", "content": st.session_state.system_prompt}] + st.session_state.conversation
        }
        safe_save_conversation(openai_format)
        st.success("Conversation saved successfully!")
        st.session_state.conversation = []
        st.session_state.editing = -1
        st.experimental_rerun()

# Display saved conversations
if os.path.exists(JSONL_FILE):
    st.header("Recent Saved Conversations")
    with open(JSONL_FILE, "r") as f:
        conversations = [json.loads(line) for line in f]
        for i, conversation in enumerate(conversations[-3:], 1):
            with st.expander(f"Conversation {len(conversations)-3+i}"):
                for message in conversation['messages']:
                    st.write(f"{message['role'].capitalize()}: {message['content']}")