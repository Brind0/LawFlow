import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add project root to python path
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import settings
from integrations.drive_client import DriveClient

load_dotenv()

def test_drive_integration():
    print("\n--- Testing Google Drive Integration ---")
    
    # Check credentials existence
    if not settings.GOOGLE_CREDENTIALS_PATH.exists():
        print(f"❌ Credentials not found at {settings.GOOGLE_CREDENTIALS_PATH}")
        print("Please download 'google_credentials.json' from Google Cloud Console")
        print("and place it in 'data/credentials/'.")
        return

    print(f"✅ Found credentials at {settings.GOOGLE_CREDENTIALS_PATH}")
    
    client = DriveClient(
        credentials_path=str(settings.GOOGLE_CREDENTIALS_PATH),
        token_path=str(settings.GOOGLE_TOKEN_PATH)
    )
    
    try:
        print("Authenticating (check your browser)...")
        client.authenticate()
        print("✅ Authentication successful!")
        
        # Test Folder Creation
        print("Creating/Finding 'LawFlow Test' folder...")
        folder_id = client.get_or_create_folder("LawFlow Test")
        print(f"✅ Folder ID: {folder_id}")
        
        # Test File Upload
        print("Uploading 'hello.txt'...")
        content = b"Hello from LawFlow Backtest!"
        result = client.upload_file(
            file_content=content,
            file_name="hello.txt",
            folder_id=folder_id,
            mime_type="text/plain"
        )
        print(f"✅ File uploaded! ID: {result['id']}")
        print(f"URL: {result['url']}")
        
        # Cleanup (Optional)
        # print("Deleting test file...")
        # client.delete_file(result['id'])
        # print("✅ File deleted.")
        
    except Exception as e:
        print(f"❌ Drive operation failed: {e}")

if __name__ == "__main__":
    test_drive_integration()
