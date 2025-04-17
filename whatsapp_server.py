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
from whatsapp_reader import read_whatsapp_messages, write_top_messages_to_string
import os
from dotenv import load_dotenv
import google.generativeai as genai
from pydantic import BaseModel

# Add Pydantic model for request
class QueryRequest(BaseModel):
    query: str

app = FastAPI()

# Scopes for Gmail API - just sending email
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def function_caller(params):
    """Simple function caller that maps function names to actual functions"""
    function_map = {
        "read_whatsapp_messages_wrapper": read_whatsapp_messages_wrapper,
        "create_message_wrapper": create_message_wrapper,
        "send_email_wrapper": send_email_wrapper,
        "write_top_messages_to_string_wrapper":write_top_messages_to_string_wrapper,
    }
    
    if params[0] in function_map:
        if(params == None):
            return function_map[params[0]]()
        else:
            return function_map[params[0]](params[1:])
    else:
        return f"Function {params[0]} not found"

def create_message_wrapper(params):
    return create_message(params[0],params[1],params[2],params[3])

def send_email_wrapper(params):
    return send_email(params[0],params[1],params[2])

def read_whatsapp_messages_wrapper(params):
    return read_whatsapp_messages(params[0],params[1])

def write_top_messages_to_string_wrapper(params):
    return write_top_messages_to_string(params[0],params[1])

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
    allow_origins=["chrome-extension://*"],  # Allow all Chrome extensions
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/process_query")
async def process_query(request: QueryRequest):
    try:
        if not request.query:
            raise HTTPException(
                status_code=400, 
                detail="Query cannot be empty"
            )
        
        # Load environment variables from .env file
        load_dotenv()
        # Access your API key
        api_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=api_key)

        model = genai.GenerativeModel("gemini-2.0-flash")
        
        service = get_gmail_service()
        
        system_prompt = """You are a agent which reads whatsapp messages and then if asked finds top 4 lengthy whatsapp messages from them and then either mail the read whatsapp messages or top 4 lengthy whatsapp messages based on the prompt. Respond with EXACTLY ONE of these formats:
        1. FUNCTION_CALL:python_function_name|input1|input2|...|inputN
        2. FINAL_ANSWER:Message sent!
        
        where python_function_name is one of the followin:
        1. read_whatsapp_messages_wrapper(int, int) It takes two inputs the number of messages to read from each chat and how many chats to read.
        2. write_top_messages_to_string_wrapper(string,int) It called only when the top N lengthy messages from messages returned from read_whatsapp_messages_wrapper is asked for, else this function is not called.
        3. create_message_wrapper(string, string, string, string) This creates the message which need to send to the gmail, the first parameter to function is sender email which is sai.406@gmail.com, second parameter receiver email which is sai.406@gmail.com, third parameter subject of mail you can return just string "Whatsapp Messages" and fourth body of mail you can give returned string of iteration 1(whatever is returned by read_whatsapp_messages_wrapper and when you didn't ask for top N lengthy messages) or iteration 2(whatever is returned by write_top_messages_to_string_wrapper if top N lengthy messages are asked for) for this. After this there is no more task.
        DO NOT include multiple responses. Give ONE response at a time."""

        print("\n\n")
        print(request.query)
        print("\n\n")
        max_iterations = 4
        query = request.query
        last_response = None
        iteration_result = None
        iteration = 0
        iteration_response = []
        
        while iteration < max_iterations:
            print(f"\n--- Iteration {iteration + 1} ---")
            if last_response == None:
                current_query = query
            else:
                current_query = current_query + "\n\n" + " ".join(iteration_response)
                current_query = current_query + "  What should I do next?"
            
            # Get model's response
            prompt = f"{system_prompt}\n\nQuery: {current_query}"
            response = model.generate_content(prompt)
            
            response_text = response.text.strip()
            print(f"LLM Response: {response_text}")
            
            
            if response_text.startswith("FUNCTION_CALL:"):
                response_text = response.text.strip()
                _, function_info = response_text.split(":", 1)
                params = []
                for x in function_info.split("|"):
                    params.append(x)
                print(params)
                iteration_result = function_caller(params)
            
            # Check if it's the final answer
            elif response_text.startswith("FINAL_ANSWER:"):
                print("\n=== Agent Execution Complete ===")
                break
                
            
            print(f"  Result: {iteration_result}")
            last_response = iteration_result
            iteration_response.append(f"In the {iteration + 1} iteration you called {params[0]} with {params[1:]} parameters, and the function returned {iteration_result}.")
            
            iteration += 1
        #prompt = f"{system_prompt}\n\nQuery: {request.query}"
        #response = model.generate_content(prompt)
        #print(response.text)
        #response_text = response.text.strip()
        #_, function_info = response_text.split(":", 1)
        #params = []
        #for x in function_info.split("|"):
        #    params.append(x)
        #print(params)
        #body = function_caller(params)
        #params.append(body)
        #
        #iteration_1 = f"In the first iteration you called {params[0]} with {params[1:]} parameters, and the function returned {params[-1]}. What should I do next?"
        #prompt = f"{system_prompt}\n\nQuery: {request.query}\n\n{iteration_1}"
        #response = model.generate_content(prompt)
        ##print(response.text)
        #response_text = response.text.strip()
        #_, function_info = response_text.split(":", 1)
        #params = []
        #for x in function_info.split("|"):
        #    params.append(x)
        #message = function_caller(params)
        
        #iteration_2 = f"In the second iteration you called {params[0]} with {params[1:]} parameters, and the function returned {message}. What should I do next?"
        #prompt = f"{system_prompt}\n\nQuery: {request.query}\n\n{iteration_1}\n\n{iteration_2}"
        #response = model.generate_content(prompt)
        ##print(response.text)
        #response_text = response.text.strip()
        #_, function_info = response_text.split(":", 1)
        #params = []
        #for x in function_info.split("|"):
        #    params.append(x)
        #params[1] = service
        #params[2] = 'me'
        #params[3] = message
        #function_caller(params)
        
        send_email(service,'me',iteration_result)

        return {"success": True, "message": "Query processed successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000) 