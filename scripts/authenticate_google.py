import os
import sys
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/spreadsheets.readonly"
]

def main():
    creds_path = "credentials.json"
    token_path = "token.json"
    
    if not os.path.exists(creds_path):
        print(f"Error: {creds_path} not found.")
        sys.exit(1)
        
    print("========================================================", flush=True)
    print("GoogleGuard AI: Live Google Drive & Sheets Authentication", flush=True)
    print("========================================================", flush=True)
    
    flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
    try:
        creds = flow.run_local_server(
            port=0,
            open_browser=True,
            authorization_prompt_message=(
                "\n" + "="*65 + "\n"
                "1. If your browser does not open automatically, copy & paste this URL:\n\n"
                "{url}\n\n"
                "2. In your browser:\n"
                "   - Sign in with: aziz.whibi9@gmail.com\n"
                "   - Click 'Parametres avances' ('Advanced') -> 'Acceder a blo9 (non securise)'\n"
                "   - Click 'Continuer' ('Allow')\n"
                "\nWaiting for authorization callback from Google... (keep this open)\n"
                + "="*65 + "\n"
            ),
            success_message="Authentication successful! You can close this browser window and return to your terminal."
        )
    except KeyboardInterrupt:
        print("\n[CANCELLED] Authentication interrupted by user.")
        sys.exit(1)
    
    with open(token_path, "w", encoding="utf-8") as f:
        f.write(creds.to_json())
        
    print("\n[SUCCESS] Authentication complete! Saved token.json.", flush=True)
    print("Google Drive and Sheets live connections are now ACTIVE.")

if __name__ == "__main__":
    main()
