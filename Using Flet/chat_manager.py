import os
import json
import glob
from datetime import datetime

class ChatManager:
    """Handles saving, loading, and managing chat history files."""
    def __init__(self, chats_dir="chats"):
        self.chats_dir = chats_dir
        if not os.path.exists(self.chats_dir):
            os.makedirs(self.chats_dir)

    def save_chat(self, conversation_history, filepath=None, title=None):
        """Saves a conversation to a JSON file, including its title."""
        if not conversation_history:
            return None

        if filepath is None:
            # This is a new chat, create a new file
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filepath = os.path.join(self.chats_dir, f"{timestamp}.json")
            data = {"title": title or "Untitled Chat", "history": conversation_history}
        else:
            # This is an existing chat, update the history
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Ensure data is a dict for backward compatibility
                    if isinstance(data, list):
                        data = {"title": title or "Untitled Chat", "history": data}
            except (FileNotFoundError, json.JSONDecodeError):
                data = {"title": title or "Untitled Chat"}
            data["history"] = conversation_history
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        
        return filepath

    def load_chat(self, filepath):
        """Loads a chat history and title from a file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Handle both old (list) and new (dict) formats
                if isinstance(data, dict):
                    return data.get("history", []), data.get("title", "Untitled")
                elif isinstance(data, list):
                    return data, "Untitled Chat" # Old format
        except (FileNotFoundError, json.JSONDecodeError):
            return [], "Error Loading Chat"
        return [], "Invalid Format"


    def get_chat_list(self):
        """
        THE FIX: This function now handles both old and new chat file formats.
        Returns a sorted list of (filepath, title) tuples for all saved chats.
        """
        chat_files = sorted(glob.glob(os.path.join(self.chats_dir, "*.json")), reverse=True)
        chat_list = []
        for filepath in chat_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    title = "Untitled Chat"
                    # Check if the loaded data is a dictionary (new format)
                    if isinstance(data, dict):
                        title = data.get("title", os.path.basename(filepath))
                    # If it's a list (old format), we'll just use the default title
                    # which we can derive from the filename later if needed.
                    
                    chat_list.append((filepath, title))
            except (FileNotFoundError, json.JSONDecodeError):
                continue # Skip corrupted files
        return chat_list

