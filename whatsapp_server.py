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
import os
from dotenv import load_dotenv
import google.generativeai as genai

app = FastAPI()

# Scopes for Gmail API - just sending email
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def function_caller(func_name, params):
    """Simple function caller that maps function names to actual functions"""
    function_map = {
        "read_whatsapp_messages": read_whatsapp_messages,
        "create_message_wrapper": create_message_wrapper,
        "send_email_wrapper": send_email_wrapper,
        "get_gmail_service":get_gmail_service
    }
    
    if func_name in function_map:
        if(params == None):
            return function_map[func_name]()
        else:
            return function_map[func_name](params)
    else:
        return f"Function {func_name} not found"

def create_message_wrapper(params):
    return create_message(params[0],params[1],params[2],params[3])

def send_email_wrapper(params):
    return send_email(params[0],params[1],params[2])

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
        
        #service = get_gmail_service()

        sender_email = 'sai.406@gmail.com'
        receiver_email = 'sai.406@gmail.com'
        subject = 'Test Subject from Python'
        print(f"Getting last {message_count} messages from each chat")

        # Load environment variables from .env file
        load_dotenv()
        # Access your API key
        api_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=api_key)

        model = genai.GenerativeModel("gemini-2.0-flash")
        
        system_prompt = """You are a agent which reads whatsapp messages and then if asked finds top 4 lengthy whatsapp messages from them and then either mail the read whatsapp messages or top 4 lengthy whatsapp messages based on the prompt. Respond with EXACTLY ONE of these formats:
        1. FUNCTION_CALL: python_function_name|input
        2. FINAL_ANSWER: Message sent! Message ID: [ID_number]
        
        where python_function_name is one of the followin:
        1. get_gmail_service(): It doesn't take any arguments it used to set the gmail service after this is first function which needs to be called to set gmail.
        2. read_whatsapp_messages(int) It takes the number of messages to read from each chat and opens chrome browser and allows the user to login to whatsapp account and then reads the set number of messages from each chat.
        3. create_message_wrapper(string, string, string, string) This creates the message which need to send to the gmail, the first parameter to function is sender email which is sai.406@gmail.com, second parameter receiver email which is sai.406@gmail.com, third parameter subject of mail you can return just string "subject" and fourth body of mail you can give returned string of iteration 2 for this.
        4. send_email_wrapper(string, string, string) This send the created message to gmail ID. First parameter to function is service which is returned in first iteration, second parameter just string 'me' and third parameter is message you can use returned string of iteration 3 for this.
        DO NOT include multiple responses. Give ONE response at a time."""
        
        
        current_query= """Set the gmail service and get 10 whatsapp messages from each chat and mail them to my gmail ID"""
        #query= """Get 10 whatsapp messages from each chat and mail them to my gmail ID"""
        
        #while iteration < max_iterations:
        #    print(f"\n--- Iteration {iteration + 1} ---")
        #    if last_response == None:
        #        current_query = query
        #    else:
        #        current_query = current_query + "\n\n" + " ".join(iteration_response)
        #        current_query = current_query + "  What should I do next?"
        #    
        #    # Get model's response
        #    prompt = f"{system_prompt}\n\nQuery: {current_query}"
        #    response = model.generate_content(prompt)
        #    
        #    response_text = response.text.strip()
        #    print(f"LLM Response: {response_text}")
        #    
        #    
        #    if response_text.startswith("FUNCTION_CALL:"):
        #        response_text = response.text.strip()
        #        _, function_info = response_text.split(":", 1)
        #        func_name, params = [x.strip() for x in function_info.split("|", 1)]
        #        iteration_result = function_caller(func_name, params)
        #    
        #    # Check if it's the final answer
        #    elif response_text.startswith("FINAL_ANSWER:"):
        #        print("\n=== Agent Execution Complete ===")
        #        break
        #        
        #    
        #    print(f"  Result: {iteration_result}")
        #    last_response = iteration_result
        #    iteration_response.append(f"In the {iteration + 1} iteration you called {func_name} with {params} parameters, and the function returned {iteration_result}.")
        #    
        #    iteration += 1
        
        prompt = f"{system_prompt}\n\nQuery: {current_query}"
        response = model.generate_content(prompt)
        print(response.text)
        response_text = response.text.strip()
        response_text
        _, function_info = response_text.split(":", 1)
        _, function_info
        func_name, params = [x.strip() for x in function_info.split("|", 1)]
        service = function_caller(func_name, None)
        #service = get_gmail_service()
        
        iteration_1 = f"In the first iteration you called {func_name} with {params} parameters, and the function returned {service}. What should I do next?"
        prompt = f"{system_prompt}\n\nQuery: {current_query}\n\n{iteration_1}"
        response = model.generate_content(prompt)
        print(response.text)
        response_text = response.text.strip()
        _, function_info = response_text.split(":", 1)
        func_name, params = [x.strip() for x in function_info.split("|",1)]
        body = function_caller(func_name, params)
        #body = read_whatsapp_messages(10)

        iteration_2 = f"In the second iteration you called {func_name} with {params} parameters, and the function returned {body}. What should I do next?"
        prompt = f"{system_prompt}\n\nQuery: {current_query}\n\n{iteration_1}\n\n{iteration_2}"
        response = model.generate_content(prompt)
        print(response.text)
        response_text = response.text.strip()
        _, function_info = response_text.split(":", 1)
        func_name, param1,param2,param3,param4 = [x.strip() for x in function_info.split("|")]
        params = []
        params.append(param1)
        params.append(param2)
        params.append(param3)
        params.append(param4)
        message = function_caller(func_name, params)
        #message = create_message_wrapper(sender_email, receiver_email, subject, body)
        
        iteration_3 = f"In the second iteration you called {func_name} with {params} parameters, and the function returned {message}. What should I do next?"
        prompt = f"{system_prompt}\n\nQuery: {current_query}\n\n{iteration_1}\n\n{iteration_2}\n\n{iteration_3}"
        response = model.generate_content(prompt)
        print(response.text)
        response_text = response.text.strip()
        _, function_info = response_text.split(":", 1)
        func_name, param1,param2,param3 = [x.strip() for x in function_info.split("|")]
        params = []
        params.append(service)
        params.append('me')
        params.append(message)
        function_caller(func_name, params)
        #send_email(service, 'me', message)

        return {"success": True, "message": f"Started reading {message_count} messages"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000) 