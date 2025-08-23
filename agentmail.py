#!/usr/bin/env python3
"""
Simple AgentMail API Client
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()


def create_inbox():
    """Create a new inbox"""
    api_key = os.getenv('AGENTMAIL_API_KEY')
    if not api_key:
        print("Error: AGENTMAIL_API_KEY not found in environment variables")
        return None
    
    response = requests.post(
        "https://api.agentmail.to/v0/inboxes",
        headers={
            "Authorization": f"Bearer {api_key}"
        },
        json={},
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None


def get_inbox(inbox_id):
    """Get inbox details"""
    api_key = os.getenv('AGENTMAIL_API_KEY')
    if not api_key:
        print("Error: AGENTMAIL_API_KEY not found in environment variables")
        return None
    
    response = requests.get(
        f"https://api.agentmail.to/v0/inboxes/{inbox_id}",
        headers={
            "Authorization": f"Bearer {api_key}"
        }
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None


def send_message(inbox_id, to, subject, text=None, html=None):
    """Send a message from an inbox"""
    api_key = os.getenv('AGENTMAIL_API_KEY')
    if not api_key:
        print("Error: AGENTMAIL_API_KEY not found in environment variables")
        return None
    
    response = requests.post(
        f"https://api.agentmail.to/v0/inboxes/{inbox_id}/messages/send",
        headers={
            "Authorization": f"Bearer {api_key}"
        },
        json={
            "to": to,
            "subject": subject,
            "text": text,
            "html": html
        }
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None


if __name__ == "__main__":
    print("Creating new inbox...")
    result = create_inbox()
    if result:
        print("Success!")
        print(result)
        
        inbox_id = result['inbox_id']
        print(f"\nGetting inbox details for {inbox_id}...")
        
        inbox_details = get_inbox(inbox_id)
        if inbox_details:
            print("Inbox details:")
            print(inbox_details)
            
            print(f"\nSending test message from {inbox_id}...")
            message_result = send_message(
                inbox_id=inbox_id,
                to="s.ahmadmasood@gmail.com",
                subject="Test message from AgentMail",
                text="Hello! This is a test message from my AgentMail inbox."
            )
            
            if message_result:
                print("Message sent successfully!")
                print(f"Message ID: {message_result.get('message_id')}")
                print(f"Thread ID: {message_result.get('thread_id')}")
            else:
                print("Failed to send message")
        else:
            print("Failed to get inbox details")
    else:
        print("Failed to create inbox")