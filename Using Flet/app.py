import flet as ft
import os
import time
import threading
from chat_manager import ChatManager
from api_client import GeminiApiClient
from translation import TRANSLATIONS
from Prompt import system_prompt

# --- IMPORTANT ---
# Place your Gemini API Key here.
API_KEY = "YOUR_API_KEY"

# --- A Self-Contained Animation Component ---
class ThinkingAnimation(ft.Row):
    def __init__(self):
        super().__init__(
            spacing=5,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            visible=False, 
            opacity=0,
            animate_opacity=300 
        )
        self.is_animating = False
        
        self.dots = [
            ft.Container(width=8, height=8, bgcolor="grey", shape=ft.BoxShape.CIRCLE, animate_scale=300, animate_opacity=300),
            ft.Container(width=8, height=8, bgcolor="grey", shape=ft.BoxShape.CIRCLE, animate_scale=300, animate_opacity=300),
            ft.Container(width=8, height=8, bgcolor="grey", shape=ft.BoxShape.CIRCLE, animate_scale=300, animate_opacity=300),
        ]
        self.controls = self.dots

    def start(self):
        self.visible = True
        self.opacity = 1
        self.is_animating = True
        self.animation_thread = threading.Thread(target=self._animation_loop, daemon=True)
        self.animation_thread.start()
        if self.page:
            self.update()

    def stop(self):
        self.is_animating = False
        time.sleep(0.4) 
        self.opacity = 0
        self.visible = False
        if self.page:
            self.update()

    def _animation_loop(self):
        base_scale = 1.0
        animated_scale = 1.3
        base_opacity = 0.5
        animated_opacity = 1.0
        
        dot_index = 0
        while self.is_animating:
            self.dots[dot_index].scale = animated_scale
            self.dots[dot_index].opacity = animated_opacity
            
            prev_dot_index = (dot_index - 1 + len(self.dots)) % len(self.dots)
            self.dots[prev_dot_index].scale = base_scale
            self.dots[prev_dot_index].opacity = base_opacity

            if self.page and self.is_animating:
                self.update()
            
            dot_index = (dot_index + 1) % len(self.dots)
            time.sleep(0.4)
        
        for dot in self.dots:
            dot.scale = base_scale
            dot.opacity = 1


class ChatbotApp(ft.Row):
    def __init__(self):
        super().__init__(expand=True)
        self.chat_manager = ChatManager()
        try:
            self.api_client = GeminiApiClient(API_KEY)
        except ValueError as e:
            self.controls = [ft.Text(f"CRITICAL ERROR: {e}", color="red")]
            return

        self.sidebar_expanded = True
        self.current_chat_file = None
        self.current_chat_title = ""
        self.conversation_history = []
        self.thinking_animation = ThinkingAnimation()
        
        self._define_controls()
        self._setup_layout()
        
    def did_mount(self):
        """Called when the app is first loaded."""
        self.load_chat_history_sidebar()
        self.start_new_chat(None) # This will now show the DB view
        self.language_changed(None) # This sets all text

    def _define_controls(self):
        # --- Main Chat View ---
        self.chat_messages = ft.ListView(expand=True, spacing=15, auto_scroll=True, visible=False)
        
        # --- Database/Glossary View (from Code 2) ---
        self.welcome_title = ft.Text(size=32, weight=ft.FontWeight.BOLD)
        self.welcome_subtitle = ft.Text(size=16, opacity=0.9)
        self.term_grid_view = ft.GridView(
            expand=1, runs_count=5, max_extent=200, 
            child_aspect_ratio=1.8, spacing=10, run_spacing=10
        )
        self.db_view = ft.Container(
            expand=True, padding=20,
            visible=True, # Start visible
            content=ft.Column(
                controls=[
                    self.welcome_title,
                    self.welcome_subtitle,
                    ft.Divider(height=20, color="transparent"),
                    self.term_grid_view
                ],
                expand=True, scroll=ft.ScrollMode.ADAPTIVE
            )
        )
        
        # --- Main Chat Stack (for switching views, from Code 2) ---
        self.main_chat_stack = ft.Stack(controls=[self.chat_messages, self.db_view], expand=True)

        self.input_entry = ft.TextField(
            expand=True, on_submit=self.send_message_click,
            border_radius=15, filled=True, shift_enter=True,
            min_lines=1, max_lines=5,
            on_focus=self.show_chat_view # Switch to chat on focus
        )
        self.send_button = ft.IconButton(icon="send_rounded", tooltip="Send", on_click=self.send_message_click, icon_size=24)
        self.show_db_button = ft.IconButton(icon="apps", on_click=self.show_db_view, tooltip="Show Terms") # Added from Code 2
        
        # --- Sidebar Controls (from Code 1) ---
        self.menu_button = ft.IconButton(icon="menu", on_click=self.toggle_sidebar, tooltip="Toggle sidebar")
        self.app_title = ft.Text("ALAI", size=20, weight=ft.FontWeight.BOLD, opacity=1, animate_opacity=200)
        
        self.new_chat_button_text = ft.Text("New Chat", animate_opacity=200, weight=ft.FontWeight.W_500)
        self.new_chat_button = ft.Container(
            content=ft.Row(
                controls=[ft.Icon("add"), self.new_chat_button_text],
                spacing=10, alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            on_click=self.start_new_chat,
            padding=ft.padding.symmetric(vertical=10, horizontal=12),
            border_radius=ft.border_radius.all(10),
            bgcolor="on_surface_variant",
            width=250,
            animate=ft.Animation(300, "easeOut"),
            ink=True,
            tooltip="New Chat"
        )
        
        self.language_label = ft.Text("Response Language:", weight=ft.FontWeight.BOLD)
        self.history_label = ft.Text("Chat History", weight=ft.FontWeight.BOLD)
        self.language_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option(lang) for lang in TRANSLATIONS.keys()],
            value="English", on_change=self.language_changed, border_radius=8
        )
        
        # --- THE KEY FIX ---
        # Using the ft.Column from Code 1, *not* the ft.ListView from Code 2
        self.history_view = ft.Column(scroll=ft.ScrollMode.ADAPTIVE, spacing=8, expand=True)
        
        self.sidebar_content_col = ft.Column(
            expand=True, spacing=10,
            controls=[
                self.language_label, self.language_dropdown,
                ft.Divider(height=10, color="transparent"),
                self.history_label, self.history_view
            ],
            opacity=1, animate_opacity=200
        )

    def _setup_layout(self):
        # --- Sidebar Layout (from Code 1) ---
        self.sidebar_main_col = ft.Column(
                controls=[
                    ft.Row(
                        controls=[self.menu_button, self.app_title],
                        alignment=ft.MainAxisAlignment.START,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    self.new_chat_button,
                    ft.Divider(height=15, color="transparent"),
                    self.sidebar_content_col
                ],
                expand=True, spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.START
            )
        
        self.sidebar_container = ft.Container(
            width=280, padding=ft.padding.symmetric(vertical=10, horizontal=15),
            bgcolor="surface_variant",
            border_radius=ft.border_radius.all(15),
            animate=ft.Animation(duration=300, curve="easeOut"),
            content=self.sidebar_main_col
        )

        # --- Main Content Layout (Updated to include Stack) ---
        self.controls = [
            self.sidebar_container,
            ft.VerticalDivider(width=1),
            ft.Container(
                expand=True, padding=ft.padding.symmetric(vertical=10, horizontal=20),
                content=ft.Column(
                    expand=True,
                    controls=[
                        # Added Row with show_db_button from Code 2
                        ft.Row([self.show_db_button], alignment=ft.MainAxisAlignment.END),
                        # Use the main_chat_stack from Code 2
                        self.main_chat_stack,
                        ft.Row(
                            controls=[self.input_entry, self.send_button],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER
                        )
                    ],
                    spacing=10
                )
            )
        ]

    # --- View Switching Functions (from Code 2) ---
    def show_chat_view(self, e):
        """Switches to the chat message list."""
        self.chat_messages.visible = True
        self.db_view.visible = False
        if self.page:
            self.page.update()

    def show_db_view(self, e):
        """Switches to the welcome/database view."""
        self.chat_messages.visible = False
        self.db_view.visible = True
        if self.page:
            self.page.update()

    def db_term_click(self, e):
        """Handles clicking a term in the welcome screen."""
        term = e.control.data
        user_message = f"What is {term} at ALA?"
        
        self.show_chat_view(None) # Switch to chat
        self.add_message("You", user_message)
        
        # Show thinking animation and get response
        self.chat_messages.controls.append(self.thinking_animation)
        self.page.update()
        self.thinking_animation.start()
        threading.Thread(target=self.process_bot_response, args=(user_message,), daemon=True).start()

    # --- Sidebar Toggle Function (from Code 1) ---
    def toggle_sidebar(self, e):
        self.sidebar_expanded = not self.sidebar_expanded
        self.sidebar_container.width = 280 if self.sidebar_expanded else 80
        
        self.sidebar_main_col.horizontal_alignment = ft.CrossAxisAlignment.START if self.sidebar_expanded else ft.CrossAxisAlignment.CENTER
        
        self.app_title.opacity = 1 if self.sidebar_expanded else 0
        self.app_title.visible = self.sidebar_expanded
        
        self.new_chat_button_text.opacity = 1 if self.sidebar_expanded else 0
        self.new_chat_button_text.visible = self.sidebar_expanded
        self.new_chat_button.width = 250 if self.sidebar_expanded else 48

        self.sidebar_content_col.opacity = 1 if self.sidebar_expanded else 0
        self.sidebar_content_col.visible = self.sidebar_expanded
        
        if self.page:
            self.page.update()
        
    # --- Chat Logic (Merged) ---
    def send_message_click(self, e):
        user_message = self.input_entry.value.strip()
        if not user_message: return

        # When user sends first message, switch to chat view
        if self.db_view.visible:
            self.show_chat_view(None)

        self.add_message("You", user_message)
        self.input_entry.value = ""
        self.input_entry.focus()
        
        self.chat_messages.controls.append(self.thinking_animation)
        self.page.update()
        self.thinking_animation.start()

        threading.Thread(target=self.process_bot_response, args=(user_message,), daemon=True).start()

    def process_bot_response(self, user_message):
        selected_language = self.language_dropdown.value
        is_new_chat = not self.conversation_history

        if is_new_chat:
            bot_response, title = self.api_client.get_initial_response_and_title(user_message, system_prompt, selected_language)
            self.current_chat_title = title
        else:
            bot_response = self.api_client.get_bot_response(
                user_message, system_prompt, selected_language, history=self.conversation_history
            )
        
        self.thinking_animation.stop()
        self.chat_messages.controls.remove(self.thinking_animation)
        self.add_message("System", bot_response)
        
        self.conversation_history.append({"user": user_message, "bot": bot_response})
        self.current_chat_file = self.chat_manager.save_chat(
            self.conversation_history, self.current_chat_file, title=self.current_chat_title
        )
        
        if is_new_chat: self.load_chat_history_sidebar()
        if self.page:
            self.page.update()

    def add_message(self, sender, message):
        self.chat_messages.controls.append(
            ft.Container(
                content=ft.Text(message, selectable=True),
                border_radius=15, padding=15,
                bgcolor="primary_container" if sender == "You" else "surface_variant",
                margin=ft.margin.only(right=40) if sender == "You" else ft.margin.only(left=40)
            )
        )
        if self.page:
            self.chat_messages.update()

    def start_new_chat(self, e):
        self.chat_messages.controls.clear()
        self.current_chat_file = None
        self.current_chat_title = ""
        self.conversation_history = []
        
        self.show_db_view(None) # Show welcome screen on new chat
        
        if self.page:
            # self.input_entry.focus() # Don't focus, so view stays on DB
            self.page.update()

    def load_chat(self, e):
        filepath = e.control.data
        self.conversation_history, self.current_chat_title = self.chat_manager.load_chat(filepath)
        self.current_chat_file = filepath
        
        self.chat_messages.controls.clear()
        for msg in self.conversation_history:
            self.add_message("You", msg.get("user", ""))
            self.add_message("System", msg.get("bot", ""))
        
        self.show_chat_view(None) # Show chat view when loading a chat
        if self.page:
            self.page.update()

    def load_chat_history_sidebar(self):
        self.history_view.controls.clear()
        chat_list = self.chat_manager.get_chat_list()
        
        # Using the simple TextButton from Code 1 (no delete button)
        for filepath, title in chat_list:
            self.history_view.controls.append(
                ft.TextButton(text=title, data=filepath, on_click=self.load_chat)
            )
        if self.page: self.history_view.update()

    def language_changed(self, e):
        lang = self.language_dropdown.value if e else "English"
        translations = TRANSLATIONS.get(lang, TRANSLATIONS["English"])
        
        if self.page:
            self.page.title = translations.get("page_title", "ALA Assistant")
        
        # Sidebar
        self.new_chat_button_text.value = translations.get("new_chat_button", "New Chat")
        self.language_label.value = translations.get("language_label", "Response Language:")
        self.history_label.value = translations.get("history_label", "Chat History")

        # Welcome/DB View (from Code 2)
        self.welcome_title.value = translations.get("welcome_title", "Welcome!")
        self.welcome_subtitle.value = translations.get("welcome_subtitle", "Click a term to learn.")
        
        # Rebuild the term grid (from Code 2)
        term_buttons = []
        translated_terms = translations.get("terms", {})
        for term, desc in translated_terms.items():
            term_buttons.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(term, weight=ft.FontWeight.BOLD, size=16),
                            ft.Text(desc, size=12, opacity=0.8),
                        ],
                        spacing=5
                    ),
                    on_click=self.db_term_click, data=term, padding=15,
                    border_radius=10, bgcolor="surface_variant", ink=True
                )
            )
        self.term_grid_view.controls = term_buttons

        # Main Chat Area
        self.input_entry.hint_text = translations.get("input_placeholder", "Ask something...")
        
        # Tooltips (Merged)
        self.menu_button.tooltip = translations.get("toggle_sidebar_tooltip", "Toggle sidebar")
        self.new_chat_button.tooltip = translations.get("new_chat_tooltip", "New Chat")
        self.show_db_button.tooltip = translations.get("show_terms_tooltip", "Show Terms")
        self.send_button.tooltip = translations.get("send_tooltip", "Send")
        
        if self.page: self.page.update()
# --- A Self-Contained Animation Component ---
class ThinkingAnimation(ft.Row):
    def __init__(self):
        super().__init__(
            spacing=5,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            visible=False, 
            opacity=0,
            animate_opacity=300 
        )
        self.is_animating = False
        
        self.dots = [
            ft.Container(width=8, height=8, bgcolor="grey", shape=ft.BoxShape.CIRCLE, animate_scale=300, animate_opacity=300),
            ft.Container(width=8, height=8, bgcolor="grey", shape=ft.BoxShape.CIRCLE, animate_scale=300, animate_opacity=300),
            ft.Container(width=8, height=8, bgcolor="grey", shape=ft.BoxShape.CIRCLE, animate_scale=300, animate_opacity=300),
        ]
        self.controls = self.dots

    def start(self):
        self.visible = True
        self.opacity = 1
        self.is_animating = True
        self.animation_thread = threading.Thread(target=self._animation_loop, daemon=True)
        self.animation_thread.start()
        if self.page:
            self.update()

    def stop(self):
        self.is_animating = False
        time.sleep(0.4) 
        self.opacity = 0
        self.visible = False
        if self.page:
            self.update()

    def _animation_loop(self):
        base_scale = 1.0
        animated_scale = 1.3
        base_opacity = 0.5
        animated_opacity = 1.0
        
        dot_index = 0
        while self.is_animating:
            self.dots[dot_index].scale = animated_scale
            self.dots[dot_index].opacity = animated_opacity
            
            prev_dot_index = (dot_index - 1 + len(self.dots)) % len(self.dots)
            self.dots[prev_dot_index].scale = base_scale
            self.dots[prev_dot_index].opacity = base_opacity

            if self.page and self.is_animating:
                self.update()
            
            dot_index = (dot_index + 1) % len(self.dots)
            time.sleep(0.4)
        
        for dot in self.dots:
            dot.scale = base_scale
            dot.opacity = 1


class ChatbotApp(ft.Row):
    def __init__(self):
        super().__init__(expand=True)
        self.chat_manager = ChatManager()
        try:
            self.api_client = GeminiApiClient(API_KEY)
        except ValueError as e:
            self.controls = [ft.Text(f"CRITICAL ERROR: {e}", color="red")]
            return

        self.sidebar_expanded = True
        self.current_chat_file = None
        self.current_chat_title = ""
        self.conversation_history = []
        self.thinking_animation = ThinkingAnimation()
        
        self._define_controls()
        self._setup_layout()
        
    def did_mount(self):
        self.load_chat_history_sidebar()
        self.start_new_chat(None)
        self.language_changed(None)

    def _define_controls(self):
        self.chat_messages = ft.ListView(expand=True, spacing=15, auto_scroll=True)
        self.input_entry = ft.TextField(
            expand=True, on_submit=self.send_message_click,
            border_radius=15, filled=True, shift_enter=True,
            min_lines=1, max_lines=5
        )
        self.send_button = ft.IconButton(icon="send_rounded", tooltip="Send", on_click=self.send_message_click, icon_size=24)
        
        self.menu_button = ft.IconButton(icon="menu", on_click=self.toggle_sidebar, tooltip="Toggle sidebar")
        self.app_title = ft.Text("ALAI", size=20, weight=ft.FontWeight.BOLD, opacity=1, animate_opacity=200)
        
        self.new_chat_button_text = ft.Text("New Chat", animate_opacity=200, weight=ft.FontWeight.W_500)
        self.new_chat_button = ft.Container(
            content=ft.Row(
                controls=[ft.Icon("add"), self.new_chat_button_text],
                spacing=10, alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            on_click=self.start_new_chat,
            padding=ft.padding.symmetric(vertical=10, horizontal=12),
            border_radius=ft.border_radius.all(10),
            bgcolor="on_surface_variant",
            width=250,
            animate=ft.Animation(300, "easeOut"),
            ink=True,
            tooltip="New Chat"
        )
        
        self.language_label = ft.Text("Response Language:", weight=ft.FontWeight.BOLD)
        self.history_label = ft.Text("Chat History", weight=ft.FontWeight.BOLD)
        self.language_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option(lang) for lang in TRANSLATIONS.keys()],
            value="English", on_change=self.language_changed, border_radius=8
        )
        self.history_view = ft.Column(scroll=ft.ScrollMode.ADAPTIVE, spacing=8, expand=True)
        
        self.sidebar_content_col = ft.Column(
            expand=True, spacing=10,
            controls=[
                self.language_label, self.language_dropdown,
                ft.Divider(height=10, color="transparent"),
                self.history_label, self.history_view
            ],
            opacity=1, animate_opacity=200
        )

    def _setup_layout(self):
        self.sidebar_main_col = ft.Column(
                controls=[
                    ft.Row(
                        controls=[self.menu_button, self.app_title],
                        alignment=ft.MainAxisAlignment.START,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    self.new_chat_button,
                    ft.Divider(height=15, color="transparent"),
                    self.sidebar_content_col
                ],
                expand=True, spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.START
            )
        
        self.sidebar_container = ft.Container(
            width=280, padding=ft.padding.symmetric(vertical=10, horizontal=15),
            bgcolor="surface_variant",
            border_radius=ft.border_radius.all(15),
            animate=ft.Animation(duration=300, curve="easeOut"),
            content=self.sidebar_main_col
        )

        self.controls = [
            self.sidebar_container,
            ft.VerticalDivider(width=1),
            ft.Container(
                expand=True, padding=ft.padding.symmetric(vertical=10, horizontal=20),
                content=ft.Column(
                    expand=True,
                    controls=[
                        self.chat_messages,
                        ft.Row(
                            controls=[self.input_entry, self.send_button],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER
                        )
                    ],
                    spacing=10
                )
            )
        ]

    def toggle_sidebar(self, e):
        self.sidebar_expanded = not self.sidebar_expanded
        self.sidebar_container.width = 280 if self.sidebar_expanded else 80
        
        self.sidebar_main_col.horizontal_alignment = ft.CrossAxisAlignment.START if self.sidebar_expanded else ft.CrossAxisAlignment.CENTER
        
        self.app_title.opacity = 1 if self.sidebar_expanded else 0
        self.app_title.visible = self.sidebar_expanded
        
        self.new_chat_button_text.opacity = 1 if self.sidebar_expanded else 0
        self.new_chat_button_text.visible = self.sidebar_expanded
        self.new_chat_button.width = 250 if self.sidebar_expanded else 48

        self.sidebar_content_col.opacity = 1 if self.sidebar_expanded else 0
        self.sidebar_content_col.visible = self.sidebar_expanded
        
        self.page.update()
        
    def send_message_click(self, e):
        user_message = self.input_entry.value.strip()
        if not user_message: return

        self.add_message("You", user_message)
        self.input_entry.value = ""
        self.input_entry.focus()
        
        self.chat_messages.controls.append(self.thinking_animation)
        self.page.update()
        self.thinking_animation.start()

        threading.Thread(target=self.process_bot_response, args=(user_message,), daemon=True).start()

    def process_bot_response(self, user_message):
        selected_language = self.language_dropdown.value
        is_new_chat = not self.conversation_history

        if is_new_chat:
            bot_response, title = self.api_client.get_initial_response_and_title(user_message, system_prompt, selected_language)
            self.current_chat_title = title
        else:
            # THE FIX: We now pass the conversation history to the API client.
            bot_response = self.api_client.get_bot_response(
                user_message, system_prompt, selected_language, history=self.conversation_history
            )
        
        self.thinking_animation.stop()
        self.chat_messages.controls.remove(self.thinking_animation)
        self.add_message("System", bot_response)
        
        self.conversation_history.append({"user": user_message, "bot": bot_response})
        self.current_chat_file = self.chat_manager.save_chat(
            self.conversation_history, self.current_chat_file, title=self.current_chat_title
        )
        
        if is_new_chat: self.load_chat_history_sidebar()
        self.page.update()

    def add_message(self, sender, message):
        self.chat_messages.controls.append(
            ft.Container(
                content=ft.Text(message, selectable=True),
                border_radius=15, padding=15,
                bgcolor="primary_container" if sender == "You" else "surface_variant",
                margin=ft.margin.only(right=40) if sender == "You" else ft.margin.only(left=40)
            )
        )
        self.chat_messages.update()

    def start_new_chat(self, e):
        self.chat_messages.controls.clear()
        self.current_chat_file = None
        self.current_chat_title = ""
        self.conversation_history = []
        if self.page:
            self.input_entry.focus()
            self.page.update()

    def load_chat(self, e):
        filepath = e.control.data
        self.conversation_history, self.current_chat_title = self.chat_manager.load_chat(filepath)
        self.current_chat_file = filepath
        
        self.chat_messages.controls.clear()
        for msg in self.conversation_history:
            self.add_message("You", msg.get("user", ""))
            self.add_message("System", msg.get("bot", ""))
        self.page.update()

    def load_chat_history_sidebar(self):
        self.history_view.controls.clear()
        chat_list = self.chat_manager.get_chat_list()
        for filepath, title in chat_list:
            self.history_view.controls.append(
                ft.TextButton(text=title, data=filepath, on_click=self.load_chat)
            )
        if self.page: self.history_view.update()

    def language_changed(self, e):
        lang = self.language_dropdown.value
        translations = TRANSLATIONS.get(lang, TRANSLATIONS["English"])
        
        self.page.title = translations.get("page_title", "Title Error")
        
        self.new_chat_button_text.value = translations.get("new_chat_button", "New Chat")

        self.language_label.value = translations.get("language_label", "Label Error")
        self.history_label.value = translations.get("history_label", "History Error")
        self.input_entry.hint_text = translations.get("input_placeholder", "Input Error")
        
        if self.page: self.page.update()


