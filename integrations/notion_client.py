from notion_client import Client
from typing import List, Dict, Any, Optional
import os
import time

class NotionClient:
    """
    Notion API client for LawFlow.
    """
    
    def __init__(self, token: str):
        self.client = Client(auth=token)
    
    def create_page(
        self,
        database_id: str,
        title: str,
        properties: Dict[str, Any],
        content_blocks: List[Dict]
    ) -> dict:
        """
        Creates a new page in the specified database.
        """
        # Build properties payload
        notion_properties = {
            "Name": {"title": [{"text": {"content": title}}]}
        }
        
        # Add other properties
        for key, value in properties.items():
            if key in ["Topic", "Stage", "Status"]:
                notion_properties[key] = {"select": {"name": value}}
            elif key == "Version":
                notion_properties[key] = {"number": value}
            elif key == "Generated":
                notion_properties[key] = {"date": {"start": value}}
            elif key == "Source Files":
                notion_properties[key] = {
                    "multi_select": [{"name": f} for f in value]
                }
        
        # Create page with properties
        # Note: We can pass children (blocks) directly in create, 
        # but limited to 100. If more, we need to append later.
        
        initial_blocks = content_blocks[:100]
        remaining_blocks = content_blocks[100:]
        
        page = self.client.pages.create(
            parent={"database_id": database_id},
            properties=notion_properties,
            children=initial_blocks
        )
        
        page_id = page["id"]
        
        # Append remaining blocks in chunks
        if remaining_blocks:
            self._append_children(page_id, remaining_blocks)
        
        return {
            "id": page_id,
            "url": page["url"]
        }
    
    def _append_children(self, page_id: str, blocks: List[Dict]):
        """Helper to append blocks in chunks of 100."""
        for i in range(0, len(blocks), 100):
            chunk = blocks[i:i+100]
            try:
                self.client.blocks.children.append(
                    block_id=page_id,
                    children=chunk
                )
                time.sleep(0.3) # Rate limit protection
            except Exception as e:
                print(f"Error appending blocks: {e}")
                # Continue trying other chunks? Or fail?
                # For now, log and re-raise
                raise e

    def update_page_status(self, page_id: str, status: str):
        """
        Updates the Status property of a page.
        """
        self.client.pages.update(
            page_id=page_id,
            properties={
                "Status": {"select": {"name": status}}
            }
        )
