import os.path
import base64
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from whatsapp_reader import read_whatsapp_messages, write_top_messages

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

# ======= USAGE =======
if __name__ == '__main__':
    service = get_gmail_service()

    sender_email = 'sai.406@gmail.com'
    receiver_email = 'sai.406@gmail.com'
    subject = 'Test Subject from Python'
    num_messages = 20
    print(f"Getting last {num_messages} messages from each chat")
    messages = read_whatsapp_messages(num_messages)
    #with open("output.txt", "w", encoding="utf-8") as file:
    #    file.write(messages)
    #write_top_messages(messages)
    body = messages

    message = create_message(sender_email, receiver_email, subject, body)
    send_email(service, 'me', message)
