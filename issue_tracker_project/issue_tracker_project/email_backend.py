import msal
import requests
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail import EmailMessage

# Azure AD Credentials
# CLIENT_ID = 'a6d16065-c072-460b-a441-feabd3988bf8'
# CLIENT_SECRET = 'XvL8Q~gcS8c4tPUbUlvHcgmBWqnZqTrOHaeo6bR6'
# TENANT_ID = 'faba5712-ad3b-4d88-aeaa-a2903faaa8e7'
# USER_EMAIL = 'no-reply@keelis.com'  # The sender's email
GRAPH_API_ENDPOINT = 'https://graph.microsoft.com/v1.0'




CLIENT_ID = 'f56a9bc8-6062-4868-9a15-d0175a4a69d7'
CLIENT_SECRET = '8eV8Q~MhiaverN8TLFSpqofVWhDyxmQJBPXuVa.O'
TENANT_ID = 'faba5712-ad3b-4d88-aeaa-a2903faaa8e7'
USER_EMAIL = 'no-reply@keelis.com'
 
class MicrosoftGraphEmailBackend(BaseEmailBackend):
    def get_access_token(self):
        """Get an access token from Microsoft Identity Platform"""
        authority = f'https://login.microsoftonline.com/{TENANT_ID}'
        app = msal.ConfidentialClientApplication(
            CLIENT_ID,
            authority=authority,
            client_credential=CLIENT_SECRET
        )
        scopes = ['https://graph.microsoft.com/.default']
        result = app.acquire_token_for_client(scopes=scopes)

        if 'access_token' in result:
            return result['access_token']
        else:
            print("Error acquiring token:", result.get('error_description'))
            return None

    def send_messages(self, email_messages):
        """Send emails using Microsoft Graph API"""
        token = self.get_access_token()
        if not token:
            print("Failed to get access token")
            return False

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        for email_message in email_messages:
            email_data = {
                "message": {
                    "subject": email_message.subject,
                    "body": {
                        "contentType": "HTML",
                        "content": email_message.body
                    },
                    "toRecipients": [
                        {"emailAddress": {"address": addr}} for addr in email_message.to
                    ],
                    "ccRecipients": [
                        {"emailAddress": {"address": addr}} for addr in email_message.cc
                    ] if email_message.cc else []
                }
            }

            response = requests.post(
                f'{GRAPH_API_ENDPOINT}/users/{USER_EMAIL}/sendMail',
                headers=headers,
                json=email_data
            )

            if response.status_code == 202:
                print(f"Email sent successfully to {email_message.to}")
            else:
                print(f"Failed to send email: {response.status_code}")
                print(response.json())

        return True
