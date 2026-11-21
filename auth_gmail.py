from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
SCOPES=["https://www.googleapis.com/auth/gmail.readonly","https://www.googleapis.com/auth/gmail.send"]
p=Path("credentials.json")
if not p.exists(): raise SystemExit("Download Google OAuth Desktop credentials and save as credentials.json.")
flow=InstalledAppFlow.from_client_secrets_file(str(p),SCOPES)
creds=flow.run_local_server(port=0)
Path("token.json").write_text(creds.to_json(),encoding="utf-8")
print("token.json created. Keep it private.")
