import streamlit as st
import json
import os
from anthropic import Anthropic

# Initialize Anthropic client
client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

# File to store the conversations
JSONL_FILE = "conversations.jsonl"

def get_claude_response(system_prompt, messages):
    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=4096,
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
        background-color: #0E1117;
        color: #FAFAFA;
    }
    .stTextArea textarea {
        background-color: #262730;
        color: #FAFAFA;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
    }
    .conversation-box {
        background-color: #1E1E1E;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .user-message {
        background-color: #2C3E50;
        color: #FAFAFA;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .assistant-message {
        background-color: #34495E;
        color: #FAFAFA;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .stExpander {
        background-color: #262730;
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

# Sidebar for system prompt and file operations
with st.sidebar:
    st.subheader("System Configuration")
    st.session_state.system_prompt = st.text_area("System Prompt", st.session_state.system_prompt, height=100)
    
    if os.path.exists(JSONL_FILE):
        st.subheader("File Statistics")
        file_size = os.path.getsize(JSONL_FILE)
        st.write(f"File Size: {file_size} bytes")
        with open(JSONL_FILE, "r") as f:
            num_conversations = sum(1 for line in f)
        st.write(f"Number of Conversations: {num_conversations}")
    
    if st.button("Export JSONL File"):
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
        claude_response = get_claude_response(st.session_state.system_prompt, st.session_state.conversation)
    st.session_state.conversation.append({"role": "assistant", "content": claude_response})
    st.session_state.editing = True
    st.experimental_rerun()

# Edit Assistant Message
if st.session_state.editing and st.session_state.conversation:
    last_assistant_message = next((m for m in reversed(st.session_state.conversation) if m['role'] == 'assistant'), None)
    if last_assistant_message:
        st.subheader("Edit Assistant's Last Response")
        edited_response = st.text_area("Edit response", last_assistant_message['content'], height=150)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Update Response"):
                last_assistant_message['content'] = edited_response
                st.session_state.editing = False
                st.experimental_rerun()
        with col2:
            if st.button("Continue Without Editing"):
                st.session_state.editing = False
                st.experimental_rerun()

# Accept and Save button
if st.button("Accept and Save Conversation"):
    if st.session_state.conversation:
        openai_format = {
            "messages": [{"role": "system", "content": st.session_state.system_prompt}] + st.session_state.conversation
        }
        safe_save_conversation(openai_format)
        st.success("Conversation saved successfully!")
        st.session_state.conversation = []
        st.session_state.editing = False
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