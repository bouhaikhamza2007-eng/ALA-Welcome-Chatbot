import customtkinter as ctk
import requests
import json
import threading

from translation import TRANSLATIONS

# --- Main Application Class ---
class ChatbotApp(ctk.CTk):
    API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
    API_KEY = "AIzaSyBcomw0whVNEF1PpNFIbn0o4AK6cRET8O8"
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title("ALA Language & Terms Assistant")
        self.geometry("600x700")
        self.language_var = ctk.StringVar(value="English")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("ala_theme.json")
        self._setup_widgets()
        self._change_language("English")

    def _setup_widgets(self):

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
    # --- Language Selection ---
        language_frame = ctk.CTkFrame(self, fg_color="transparent")
        language_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        language_frame.grid_columnconfigure(1, weight=1)
        
        self.language_label = ctk.CTkLabel(language_frame)
        self.language_label.grid(row=0, column=0, padx=(0,10), sticky="w")
        
        self.language_menu = ctk.CTkOptionMenu(
            language_frame,
            values=list(TRANSLATIONS.keys()),
            variable=self.language_var,
            command=self._change_language
        )
        self.language_menu.grid(row=0, column=1, sticky="ew")

    # --- Chat History Display ---
        self.chat_history = ctk.CTkTextbox(
            self,
            wrap='word',
            state='disabled',
            font=("Helvetica", 14),
            corner_radius=10
        )
        self.chat_history.grid(row=1, column=0, padx=20, pady=(10, 20), sticky="nsew")

    # --- Bottom frame for user input and send button ---
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
        bottom_frame.grid_columnconfigure(0, weight=1)
        self.user_input = ctk.CTkEntry(
            bottom_frame,
            font=("Helvetica", 14),
            height=40,
            corner_radius=10
        )
        
        self.user_input.grid(row=0, column=0, sticky="ew")
        self.user_input.bind("<Return>", self.send_message_event)

        self.send_button = ctk.CTkButton(
            bottom_frame,
            command = self.send_message_event,
            font=("Helvetica", 14, "bold"),
            width=80,
            height=40,
            corner_radius=10
        )
        self.send_button.grid(row=0, column=1, padx=(10, 0))
    
    def _change_language(self, selected_language):
        # The function now uses the imported TRANSLATIONS dictionary directly
        translations = TRANSLATIONS[selected_language]
        
        self.title(translations["window_title"])
        self.language_label.configure(text=translations["language_label"])
        self.user_input.configure(placeholder_text=translations["placeholder_text"])
        self.send_button.configure(text=translations["send_button"])

        self.focus()
    
    def send_message_event(self, event=None):
        user_message = self.user_input.get().strip()
        
        if not user_message:
            return
        
        if self.API_KEY == "GEMINI_API_KEY":
            self._display_message("System: Please replace the 'GEMINI_API_KEY' placeholder in the code with your actual API key.\n\n")
            return

        self._display_message(f"You: {user_message}\n\n")
        self.user_input.delete(0, 'end')
        self.send_button.configure(state="disabled")
        self._display_message("Assistant: Thinking...\n\n")

    # API Call
        thread = threading.Thread(target=self.get_bot_response, args=(user_message,))
        thread.daemon = True
        thread.start()

    def get_bot_response(self, user_message):
        selected_language = self.language_var.get()
    # System Prompt/Database
        system_prompt = (
            "You are a friendly and helpful assistant for students at the African Leadership Academy (ALA). "
            "Your main purpose is to explain complex English terms, acronyms, and concepts in a simple, clear, and easy-to-understand way. "
            "You must be aware of ALA-specific terminology. For example, 'SE' means Student Enterprise, 'BUILD' is a problem-solving framework that stands for ... . "
            "You must be aware of African Leadership Academy Values"
            "When you explain a term, provide a simple definition and a brief example of how it's used at ALA. "
            f"You MUST provide your entire response in {selected_language}. Do not use any other language."
        )

        payload = {
            "contents": [{
                "parts": [{"text": user_message}]
            }],
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            }
        }
        
        headers = {
            'Content-Type': 'application/json',
            'X-goog-api-key': self.API_KEY
        }

        try:
            response = requests.post(self.API_URL, headers=headers, data=json.dumps(payload), timeout=60)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            
            data = response.json()
            bot_response = data['candidates'][0]['content']['parts'][0]['text']
            
        except requests.exceptions.RequestException as e:
            bot_response = f"Network Error: Could not connect to the API. Please check your connection. Details: {e}"
        except KeyError:
            bot_response = "Error: Received an unexpected response from the API. The API key might be invalid or the model may have changed."
        except Exception as e:
            bot_response = f"An unexpected error occurred: {e}"

        # Schedule the UI update to run on the main thread
        self.after(0, self._update_chat_with_response, bot_response)

    def _update_chat_with_response(self, bot_response):
        """
        Updates the chat history with the bot's final response on the main thread.
        """
        self._remove_last_message()
        self._display_message(f"Assistant: {bot_response}\n\n")
        self.send_button.configure(state="normal")

    def _display_message(self, message):
        """
        Inserts a message into the chat history text area.
        """
        self.chat_history.configure(state='normal')
        self.chat_history.insert('end', message)
        self.chat_history.configure(state='disabled')
        self.chat_history.see('end')
        
    def _remove_last_message(self):
        """Removes the last entry (e.g., "Thinking...") from the chat history."""
        self.chat_history.configure(state='normal')
        
        text_content = self.chat_history.get("1.0", "end-1c")
        lines = text_content.split('\n\n')
        
        # Remove the last non-empty entry
        if lines and lines[-1] == '':
            lines.pop(-1)
        if lines:
            lines.pop(-1)
        
        new_content = '\n\n'.join(lines)
        if new_content: # Add trailing newlines back if content exists
             new_content += '\n\n'

        self.chat_history.delete("1.0", "end")
        self.chat_history.insert("1.0", new_content)
        self.chat_history.configure(state='disabled')


# --- Main Execution ---
if __name__ == "__main__":
    app = ChatbotApp()
    app.mainloop()