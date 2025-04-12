# WhatsApp Message Reader

This script allows you to read WhatsApp Web messages between specified start and end times, organizing them by groups and individual chats.

## Prerequisites

1. Python 3.6 or higher
2. Chrome browser installed
3. Chrome WebDriver installed and in your system PATH

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Import the function in your Python code:
```python
from whatsapp_reader import read_whatsapp_messages
from datetime import datetime

# Define your time range
start_time = datetime(2024, 3, 1, 0, 0, 0)  # Year, Month, Day, Hour, Minute, Second
end_time = datetime(2024, 3, 2, 0, 0, 0)

# Call the function
messages = read_whatsapp_messages(start_time, end_time)
print(messages)
```

2. When you run the script:
   - It will open Chrome browser and navigate to WhatsApp Web
   - Scan the QR code when prompted
   - The script will automatically collect messages within the specified time range
   - Messages will be returned as a string with group messages followed by individual chat messages

## Notes

- The script requires you to scan the WhatsApp Web QR code to access your messages
- Only text messages are collected (attachments and links are ignored)
- Messages are organized by chat type (groups first, then individual chats)
- Each message includes the sender's name and timestamp
- The browser will automatically close after collecting messages 