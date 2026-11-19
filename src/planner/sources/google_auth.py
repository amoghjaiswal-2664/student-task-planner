from pathlib import Path

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


def get_credentials(scopes: list[str], token_path: str, credentials_path: str = "credentials.json") -> Credentials:
    creds = None
    token_file = Path(token_path)
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), scopes)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except RefreshError:
            creds = None  # login expired (Testing mode: ~7 days), so ask again

    if not creds or not creds.valid:
        if not Path(credentials_path).is_file():
            raise FileNotFoundError(f"{credentials_path} not found. See the Google Cloud setup steps.")
        flow = InstalledAppFlow.from_client_secrets_file(credentials_path, scopes)
        creds = flow.run_local_server(port=0)

    token_file.write_text(creds.to_json())
    return creds