# GPT Fine-tuning Data Generator

This Streamlit application allows users to generate, edit, and save conversations for GPT fine-tuning. It uses the Anthropic Claude API to generate responses and saves the conversations in a format compatible with OpenAI's fine-tuning requirements.

## Features

- Interactive multi-turn conversation generation with Claude AI
- Ability to edit AI responses before saving
- Save conversations in OpenAI-compatible JSONL format
- View and export saved conversations

## Installation

1. Clone this repository:
`git clone https://github.com/ShadoWxShinigamI/GPT-Dataset-Helper.git`
2. Install Dependecies:
`pip install streamlit anthropic`
3. Create a `.streamlit/secrets.toml` file with your Anthropic API key:
```
[ANTHROPIC_API_KEY]
ANTHROPIC_API_KEY = "your-api-key"
```

## Usage
1. Run the App by running `streamlit run app.py`
2. Open your web browser and go to the URL provided by Streamlit (usually http://localhost:8501).
3. Use the interface to:
    - Set a system prompt
    - Generate conversations with Claude
    - Edit AI responses if needed
    - Save conversations for fine-tuning
    - View and export saved conversations

## Disclaimer
- This is a simple tool and should be used with caution. It is not recommended to use it to generate large datasets for fine-tuning.
- This is only for times when you need to verify and edit the synthetic data that you get from claude. If you want an automated solution, this is not the right tool for you.
