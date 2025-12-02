import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Add project root to python path
sys.path.append(str(Path(__file__).parent.parent))

from integrations.markdown_converter import markdown_to_notion_blocks, validate_blocks
from integrations.notion_client import NotionClient

load_dotenv()

def test_markdown_conversion():
    print("\n--- Testing Markdown Conversion ---")
    md = """
# Heading 1
## Heading 2
### Heading 3

This is a paragraph with **bold** and *italic* text.

- Bullet 1
- Bullet 2

1. Numbered 1
2. Numbered 2

> This is a quote.

```python
print("Hello World")
```
    """
    
    try:
        blocks = markdown_to_notion_blocks(md)
        valid_blocks = validate_blocks(blocks)
        print(f"✅ Successfully converted to {len(valid_blocks)} blocks.")
        
        # Print first few blocks to verify structure
        print("Sample block structure:")
        print(json.dumps(valid_blocks[:2], indent=2))
        return valid_blocks
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        return []

def test_notion_api(blocks):
    print("\n--- Testing Notion API ---")
    
    token = os.getenv("NOTION_TOKEN")
    if not token or token.startswith("secret_xxx"):
        print("⚠️ NOTION_TOKEN not set or invalid in .env. Skipping API test.")
        return

    client = NotionClient(token)
    
    # Verify Auth first
    try:
        print("Verifying authentication...")
        users = client.client.users.list()
        print(f"✅ Authentication successful! Found {len(users.get('results', []))} users.")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return

    # We need a database ID to test page creation
    # Try to find one in env or ask user to provide one
    # For backtest, we might just check auth by listing users or something simple if possible,
    # but Notion API is strict.
    # Let's try to list databases or just skip if no DB ID.
    
    # We'll look for any env var starting with NOTION_DB_
    db_id = None
    for key, val in os.environ.items():
        if key.startswith("NOTION_DB_") and val and not val.startswith("xxxx"):
            db_id = val
            break
            
    if not db_id:
        print("⚠️ No valid NOTION_DB_xxx found in .env. Skipping Page Creation test.")
        print("ℹ️ To test page creation, add NOTION_DB_TEST=your_db_id to .env")
        return

    print(f"Using Database ID: {db_id}")

    try:
        print("Creating test page...")
        result = client.create_page(
            database_id=db_id,
            title="LawFlow Backtest - Delete Me",
            properties={
                "Stage": "MK1",
                "Version": 1
            },
            content_blocks=blocks
        )
        print(f"✅ Page created successfully!")
        print(f"URL: {result['url']}")
        
        # Optional: Update status
        # print("Updating status...")
        # client.update_page_status(result['id'], "Superseded")
        # print("✅ Status updated.")
        
    except Exception as e:
        print(f"❌ API call failed: {e}")

if __name__ == "__main__":
    blocks = test_markdown_conversion()
    if blocks:
        test_notion_api(blocks)
