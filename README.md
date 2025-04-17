# WhatsApp Message Reader and Emailer

An automated system that reads WhatsApp Web messages and can email them to specified addresses. The system consists of a Chrome extension, a FastAPI server, and uses AI to process natural language queries.

## Components

### 1. WhatsApp Message Reader
- Automated WhatsApp Web interaction using Selenium
- Reads messages from both individual and group chats
- Maintains chat order and message formatting
- Can extract specified number of messages from each chat

### 2. FastAPI Server
- Processes natural language queries using Google's Gemini AI
- Integrates with Gmail for sending emails
- Provides REST API endpoints for the Chrome extension
- Handles WhatsApp message reading and email composition

### 3. Chrome Extension
- User-friendly interface for entering queries
- Communicates with the local FastAPI server
- Provides real-time status updates

## Requirements

- Python 3.x
- Chrome browser
- Required Python packages:
  ```
  fastapi
  uvicorn
  selenium
  undetected-chromedriver
  google-auth-oauthlib
  google-auth
  google-api-python-client
  google.generativeai
  python-dotenv
  ```

## Setup

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up Gmail API:
   - Create a Google Cloud project
   - Enable Gmail API
   - Create OAuth 2.0 credentials
   - Download credentials as `credentials.json`
   - Place in project root directory

3. Set up Gemini AI:
   - Get an API key from Google AI Studio
   - Create a `.env` file in the project root
   - Add your Gemini API key:
     ```
     GEMINI_API_KEY=your_api_key_here
     ```

4. Install Chrome Extension:
   - Open Chrome and go to `chrome://extensions/`
   - Enable Developer Mode
   - Click "Load unpacked"
   - Select the extension directory

## Usage

1. Start the FastAPI server:
   ```bash
   uvicorn whatsapp_server:app --reload
   ```

2. Open the Chrome extension:
   - Click the extension icon in Chrome
   - Enter your query in natural language
   - Examples:
     - "Read last 10 messages from 3 chats and email them to me"
     - "Get the top 4 longest messages from my recent chats"

3. First-time setup:
   - When first running, you'll need to:
     - Log into WhatsApp Web (scan QR code)
     - Authorize Gmail access
     - These authorizations will be saved for future use

## Features

- **Natural Language Processing**: Use everyday language to request actions
- **Flexible Message Reading**: Read any number of messages from any number of chats
- **Smart Message Processing**: Can identify and extract longest messages
- **Email Integration**: Automatically sends messages via Gmail
- **Secure Authentication**: Uses OAuth 2.0 for Gmail access
- **Error Handling**: Robust error handling and retry mechanisms
- **Status Updates**: Real-time feedback on operation progress

## Agent Behavior Examples

The system's AI agent adapts its behavior based on different natural language prompts. You can see examples of this in the following log files:

1. [agent_execution_read_and_mail.log](https://github.com/chbsaikiran/Assignment24-ERA-V3/blob/main/llm_log_messages_prompt1.log)
   - Shows how the agent handles the prompt: "Read last 10 messages from 3 chats and email them to me"
   - Demonstrates the complete flow:
     - Setting up Gmail service
     - Reading WhatsApp messages
     - Creating and sending email

2. [agent_execution_top_messages.log](https://github.com/chbsaikiran/Assignment24-ERA-V3/blob/main/llm_log_messages_prompt2.log)
   - Shows how the agent handles the prompt: "Get the top 4 longest messages from my recent chats"
   - Demonstrates a different execution path:
     - Reading WhatsApp messages
     - Processing to find longest messages
     - Formatting and emailing results

These logs showcase how the agent:
- Interprets different natural language queries
- Chooses appropriate functions to execute
- Adapts its workflow based on the user's request
- Provides detailed feedback during execution

## Notes

- The WhatsApp reader maintains the exact order of chats as they appear in WhatsApp Web
- Messages are processed in batches to handle large numbers efficiently
- The system includes extensive error handling and retry mechanisms
- Chat titles are truncated to 20 characters in output for readability
- The system handles both group and individual chats

## Troubleshooting

- If Chrome fails to start, ensure Chrome browser is installed and up to date
- If WhatsApp Web doesn't load, check your internet connection
- If Gmail authorization fails, ensure credentials.json is properly set up
- If messages aren't being read, ensure WhatsApp Web is properly logged in 