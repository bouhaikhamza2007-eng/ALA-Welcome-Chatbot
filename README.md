ALAI: The ALA Language & Terms Assistant
Project Overview

Welcome to ALAI, a desktop chatbot application designed to assist students at the African Leadership Academy (ALA). Built with Python and the Flet framework, this tool provides a modern, intuitive interface for students to ask questions about ALA-specific terminology, acronyms, and concepts. The assistant leverages Google's Gemini API to provide clear, simple explanations in multiple languages, making it an invaluable resource for a diverse student body.

This project was developed with a focus on clean, modular architecture and a polished, user-centric design inspired by leading applications like Google's Gemini.
Features

    Conversational AI: Get intelligent, context-aware answers to your questions.

    Multi-Language Support: Select from a range of languages, including several African languages, for the AI's responses.

    Persistent Chat History: Conversations are automatically saved and can be revisited at any time.

    Intelligent Titling: New conversations are automatically given a descriptive title by the AI for easy navigation.

    Modern, Responsive UI: Features a sleek, collapsible sidebar and smooth animations for a professional user experience.

Setup and Installation

Follow these steps to get the application running on your local machine.
Step 1: Prerequisites

    Python 3.8 or newer: This project requires a modern version of Python. You can download it from python.org.

Step 2: Download the Project Files

Download and unzip the project folder to a location on your computer (e.g., your Desktop). The folder should contain the following files:

    main.py

    app.py

    api_client.py

    chat_manager.py

    translation.py

    Prompt.py

    requirements.txt

Step 3: Install Required Libraries

    Open your terminal or command prompt.

    Navigate into the project folder using the cd command. For example:

    cd "C:\Users\YourName\Desktop\ALAI Project"

    Install the necessary libraries by running the following command:

    pip install -r requirements.txt

Step 4: Configure the API Key (Crucial Step)

The application requires a Google Gemini API key to function.

    Open the app.py file in a text editor.

    Navigate to line 12.

    Replace the placeholder text "API_KEY" with your own valid Gemini API key.

    # In app.py on line 12
    API_KEY = "YOUR_ACTUAL_API_KEY_HERE"

    Save and close the file.

How to Run the Application

Once the setup is complete, run the application from your terminal with the following command:

flet run main.py

The application window should appear on your screen, ready to use.
How to Use the Application

    Start a New Chat: Click the + New Chat button in the sidebar.

    Ask a Question: Type a question into the input box at the bottom and press Enter.

    Change Language: Use the dropdown menu in the sidebar to change the language of the AI's response.

    Navigate History: Previously saved chats will appear in the "Chat History" section. Click on a title to load that conversation.

    Toggle Sidebar: Click the "hamburger" menu icon (≡) to collapse or expand the sidebar for a more focused view.
