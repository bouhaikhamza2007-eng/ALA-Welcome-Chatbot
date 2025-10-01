import flet as ft
from app import ChatbotApp

def main(page: ft.Page):
    """
    This is the entry point for the Flet application.
    It sets up the page and instantiates the main ChatbotApp control.
    """
    # Create an instance of your main app class
    app = ChatbotApp()

    # Configure the main page/window
    page.title = "ALA Language & Terms Assistant"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.DARK # Can be DARK, LIGHT, or SYSTEM
    
    # Add your main app control to the page
    page.add(app)
    
    # Update the page to display the content
    page.update()

# This is how you start a Flet app
if __name__ == "__main__":
    ft.app(target=main)