"""Configuration utilities for TerminalAI."""
import os
import json

CONFIG_PATH = os.path.expanduser("~/.terminalai_config.json")

DEFAULT_SYSTEM_PROMPT = (
    "You are TerminalAI, an assistant that provides terminal commands for the user's specific operating system.\n\n"
    "CRITICAL RULES:\n"
    "1. ONLY provide commands for the user's CURRENT operating system (provided in the context).\n"
    "2. NEVER provide alternative commands for other operating systems unless specifically asked.\n"
    "3. Be extremely concise. Do not explain standard commands unless they are complex.\n"
    "4. For questions like 'how many...', suggest a command that counts the result.\n"
    "5. Format commands in ```bash code blocks.\n"
    "6. Preserve the exact casing of file and folder names provided by the user.\n"
    "7. Always use '~' for the user's home directory."
)

DEFAULT_CONFIG = {
    "providers": {
        "openrouter": {"api_key": ""},
        "gemini": {"api_key": ""},
        "mistral": {"api_key": ""},
        "ollama": {"host": "http://localhost:11434"}
    },
    "default_provider": "openrouter",
    "system_prompt": DEFAULT_SYSTEM_PROMPT
}

def load_config():
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT_CONFIG)
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)

def get_system_prompt():
    config = load_config()
    return config.get("system_prompt", DEFAULT_SYSTEM_PROMPT)

def set_system_prompt(prompt):
    config = load_config()
    config["system_prompt"] = prompt
    save_config(config)

def reset_system_prompt():
    config = load_config()
    config["system_prompt"] = DEFAULT_SYSTEM_PROMPT
    save_config(config)
