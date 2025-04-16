from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import os
import uvicorn
import os.path
import base64
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from whatsapp_reader import read_whatsapp_messages, write_top_messages

app = FastAPI()

# Scopes for Gmail API - just sending email
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def get_gmail_service():
    creds = None
    # Token file stores user's access/refresh tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If no token or it's invalid, login again
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)

def create_message(sender, to, subject, message_text):
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw}

def send_email(service, user_id, message):
    try:
        sent_msg = service.users().messages().send(userId=user_id, body=message).execute()
        print(f"Message sent! Message ID: {sent_msg['id']}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Enable CORS for Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["chrome-extension://becihgkfjbkhknkjibgdmdcgogddgdfh"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/read_messages/{message_count}")
async def read_messages(message_count: int):
    try:
        if not 1 <= message_count <= 50:
            raise HTTPException(
                status_code=400, 
                detail="Message count must be between 1 and 50"
            )
        
        service = get_gmail_service()

        sender_email = 'sai.406@gmail.com'
        receiver_email = 'sai.406@gmail.com'
        subject = 'Test Subject from Python'
        print(f"Getting last {message_count} messages from each chat")
        messages = read_whatsapp_messages(message_count)
        #with open("output.txt", "w", encoding="utf-8") as file:
        #    file.write(messages)
        #write_top_messages(messages)
        body = messages
        
        message = create_message(sender_email, receiver_email, subject, body)
        send_email(service, 'me', message)
        
        return {"success": True, "message": f"Started reading {message_count} messages"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000) 