from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
import os
import pickle
from typing import Optional
from io import BytesIO

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive.file']

class DriveClient:
    """
    Google Drive API client for LawFlow.
    """
    
    def __init__(self, credentials_path: str, token_path: str):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        # We don't authenticate in __init__ to allow instantiation without immediate interaction
        # But for simplicity in this app, we might want to.
        # Let's add an authenticate method that can be called explicitly or lazily.
    
    def authenticate(self):
        """
        Handles OAuth 2.0 flow with proper token persistence.
        """
        if self.service:
            return

        creds = None
        
        # Load existing token if available
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
        
        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"Google credentials not found at {self.credentials_path}. "
                        "Please download them from Google Cloud Console."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                # Run local server for auth
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('drive', 'v3', credentials=creds)
    
    def get_or_create_folder(self, name: str, parent_id: str = None) -> str:
        """
        Gets existing folder or creates new one.
        Returns folder ID.
        """
        self.authenticate()
        
        # Search for existing folder
        query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        
        results = self.service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        files = results.get('files', [])
        
        if files:
            return files[0]['id']
        
        # Create new folder
        file_metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            file_metadata['parents'] = [parent_id]
        
        folder = self.service.files().create(
            body=file_metadata,
            fields='id'
        ).execute()
        
        return folder['id']
    
    def upload_file(
        self,
        file_content: bytes,
        file_name: str,
        folder_id: str,
        mime_type: str = 'application/pdf'
    ) -> dict:
        """
        Uploads file to specified folder.
        Returns dict with id and webViewLink.
        """
        self.authenticate()
        
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        
        media = MediaIoBaseUpload(
            BytesIO(file_content),
            mimetype=mime_type,
            resumable=True
        )
        
        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        return {
            'id': file['id'],
            'url': file['webViewLink']
        }
    
    def delete_file(self, file_id: str) -> bool:
        """
        Moves file to trash.
        """
        self.authenticate()
        try:
            self.service.files().update(
                fileId=file_id,
                body={'trashed': True}
            ).execute()
            return True
        except Exception:
            return False
