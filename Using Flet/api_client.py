import requests
import json
import re

class GeminiApiClient:
    """Handles all communication with the Google Gemini API."""
    def __init__(self, api_key):
        if api_key == "GEMINI_API_KEY" or not api_key:
             raise ValueError("API key is not set. Please replace 'GEMINI_API_KEY' in your app.py file.")
        self.api_key = api_key
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

    def _make_api_request(self, history, new_prompt):
        """
        A helper method to handle the core API request logic.
        THE FIX: It now accepts the full conversation history.
        """
        headers = {
            'Content-Type': 'application/json',
            'x-goog-api-key': self.api_key
        }
        
        # Construct the full conversation payload for the API
        contents = []
        for item in history:
            contents.append({"role": "user", "parts": [{"text": item["user"]}]})
            contents.append({"role": "model", "parts": [{"text": item["bot"]}]})
        
        # Add the new user prompt
        contents.append({"role": "user", "parts": [{"text": new_prompt}]})

        payload = {"contents": contents}

        try:
            response = requests.post(self.api_url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            response_json = response.json()
            
            return response_json['candidates'][0]['content']['parts'][0]['text']
        except requests.exceptions.RequestException as e:
            return f"API Connection Error: {e}"
        except (KeyError, IndexError, TypeError, json.JSONDecodeError):
            return f"Error: Invalid response format from API. Response: {response.text if 'response' in locals() else 'No response'}"

    def _generate_title_for_conversation(self, first_question, first_answer):
        """Makes a second, specific API call to generate a title."""
        title_prompt = (
            f"The following is the start of a conversation:\n\n"
            f"User: \"{first_question}\"\n"
            f"Assistant: \"{first_answer}\"\n\n"
            "Based on this, generate a short, descriptive title for the conversation (3-5 words max). "
            "Do not add any extra text, formatting, or quotation marks. Just the title."
        )
        
        # Titling doesn't need history, it's a one-off task.
        return self._make_api_request(history=[], new_prompt=title_prompt)

    def get_initial_response_and_title(self, user_prompt, system_prompt, language):
        """Gets the initial response and then generates a title for the conversation."""
        answer = self.get_bot_response(user_prompt, system_prompt, language, history=[])

        if "API Connection Error" in answer or "Error:" in answer:
            return answer, "Error"
            
        title = self._generate_title_for_conversation(user_prompt, answer)
        
        if "API Connection Error" in title or "Error:" in title:
            title = "Untitled Chat"

        return answer, title

    def get_bot_response(self, user_prompt, system_prompt, language, history):
        """Gets a standard response for an ongoing conversation."""
        # The system prompt is now part of the history construction
        full_prompt = (
            f"{system_prompt}\n\n"
            f"Translate your final answer to {language}.\n\n"
            f"Current Question: \"{user_prompt}\""
        )
        
        return self._make_api_request(history=history, new_prompt=full_prompt)

