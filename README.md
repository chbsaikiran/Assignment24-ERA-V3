# WhatsApp Message Reader

A Python script that automates reading WhatsApp Web messages using Selenium WebDriver. This script allows you to extract and save messages from both individual and group chats.

## Features

- Automatically processes the first 3 chats from WhatsApp Web
- Collects up to 20 messages from each chat
- Handles both group and individual chats
- Expands and captures full content of long messages
- Maintains message order and formatting
- Generates two output files:
  - `output.txt`: Contains all messages from processed chats
  - `top_messages.txt`: Contains the 4 lengthiest messages from each chat (while maintaining original message order)

## Requirements

- Python 3.x
- Chrome browser installed
- Required Python packages (install via pip):
  - selenium
  - undetected-chromedriver

## How It Works

1. **Setup and Login**:
   - Opens WhatsApp Web in Chrome
   - Waits for QR code scan (manual scan required)
   - Verifies successful login

2. **Chat Processing**:
   - Processes the first 3 chats in your WhatsApp
   - For each chat:
     - Identifies if it's a group or individual chat
     - Collects up to 20 recent messages
     - Expands and captures full content of long messages
     - Preserves sender information for group chats

3. **Output Format**:
   ```
   Group: [Group Name]
   Message0: [content]
   Message1: [content]
   ...

   [Individual Name]:
   Message0: [content]
   Message1: [content]
   ...
   ```

4. **Message Selection for top_messages.txt**:
   - Takes the 4 longest messages from each chat
   - Maintains the original order of messages
   - If a chat has 4 or fewer messages, includes all of them

## Usage

1. Install required packages:
   ```bash
   pip install selenium undetected-chromedriver
   ```

2. Run the script:
   ```bash
   python whatsapp_reader.py
   ```

3. When prompted:
   - Scan the QR code with your WhatsApp mobile app
   - Wait for the script to process messages

4. Check output files:
   - `output.txt`: Contains all collected messages
   - `top_messages.txt`: Contains the 4 lengthiest messages per chat

## Limitations

- Requires manual QR code scanning
- Processes only the first 3 chats
- Depends on WhatsApp Web's HTML structure
- Chrome browser must be installed
- Requires active internet connection

## Note

This script is for educational purposes only. Please ensure you have permission to access and store the messages you're collecting. 