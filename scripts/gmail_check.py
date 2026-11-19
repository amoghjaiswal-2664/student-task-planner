from googleapiclient.discovery import build

from planner.sources.google_auth import get_credentials

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

creds = get_credentials(SCOPES, "token_gmail.json")
service = build("gmail", "v1", credentials=creds)

profile = service.users().getProfile(userId="me").execute()
listing = service.users().messages().list(userId="me", maxResults=5).execute()

print("login ok")
print("messages in mailbox:", profile["messagesTotal"])
print("sample fetch returned:", len(listing.get("messages", [])), "message ids")