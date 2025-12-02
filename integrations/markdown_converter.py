from markdown_it import MarkdownIt
from typing import List, Dict, Any

def markdown_to_notion_blocks(markdown_text: str) -> List[Dict[str, Any]]:
    """
    Converts markdown text to Notion block objects using markdown-it-py.
    """
    md = MarkdownIt()
    tokens = md.parse(markdown_text)
    
    blocks = []
    
    i = 0
    while i < len(tokens):
        token = tokens[i]
        
        if token.type == 'heading_open':
            # Handle headings
            level = int(token.tag[1])
            # Notion only supports h1, h2, h3
            if level > 3: level = 3
            block_type = f"heading_{level}"
            
            # Get content from next inline token
            content = tokens[i+1].content
            
            blocks.append({
                "object": "block",
                "type": block_type,
                block_type: {
                    "rich_text": [{"type": "text", "text": {"content": content}}]
                }
            })
            i += 2 # Skip inline and close
            
        elif token.type == 'paragraph_open':
            # Handle paragraphs
            # Check if it's inside a list item, handled separately usually?
            # markdown-it flattens structure somewhat or nests it.
            # For top level paragraphs:
            if not token.hidden:
                content = tokens[i+1].content
                if content.strip(): # Skip empty paragraphs
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": content}}]
                        }
                    })
            i += 2
            
        elif token.type == 'bullet_list_open':
            # Handle bullet lists
            # We need to iterate until bullet_list_close
            i += 1
            while i < len(tokens) and tokens[i].type != 'bullet_list_close':
                if tokens[i].type == 'list_item_open':
                    # Get content from paragraph inside list item
                    # Structure: list_item_open -> paragraph_open -> inline -> paragraph_close -> list_item_close
                    # We need to find the inline token
                    j = i + 1
                    while j < len(tokens) and tokens[j].type != 'inline':
                        j += 1
                    
                    if j < len(tokens) and tokens[j].type == 'inline':
                        content = tokens[j].content
                        blocks.append({
                            "object": "block",
                            "type": "bulleted_list_item",
                            "bulleted_list_item": {
                                "rich_text": [{"type": "text", "text": {"content": content}}]
                            }
                        })
                    
                    # Skip to list_item_close
                    while i < len(tokens) and tokens[i].type != 'list_item_close':
                        i += 1
                i += 1
            # i is now at bullet_list_close
            
        elif token.type == 'ordered_list_open':
            # Handle ordered lists
            i += 1
            while i < len(tokens) and tokens[i].type != 'ordered_list_close':
                if tokens[i].type == 'list_item_open':
                    j = i + 1
                    while j < len(tokens) and tokens[j].type != 'inline':
                        j += 1
                    
                    if j < len(tokens) and tokens[j].type == 'inline':
                        content = tokens[j].content
                        blocks.append({
                            "object": "block",
                            "type": "numbered_list_item",
                            "numbered_list_item": {
                                "rich_text": [{"type": "text", "text": {"content": content}}]
                            }
                        })
                    
                    while i < len(tokens) and tokens[i].type != 'list_item_close':
                        i += 1
                i += 1
                
        elif token.type == 'fence':
            # Handle code blocks
            lang = token.info.strip() or "plain text"
            content = token.content
            
            blocks.append({
                "object": "block",
                "type": "code",
                "code": {
                    "language": lang.split()[0] if lang else "plain text", # Notion needs valid language or plain text
                    "rich_text": [{"type": "text", "text": {"content": content}}]
                }
            })
            
        elif token.type == 'blockquote_open':
             # Handle quotes
             # Structure: blockquote_open -> paragraph_open -> inline -> paragraph_close -> blockquote_close
             j = i + 1
             while j < len(tokens) and tokens[j].type != 'inline':
                 j += 1
             
             if j < len(tokens) and tokens[j].type == 'inline':
                 content = tokens[j].content
                 blocks.append({
                     "object": "block",
                     "type": "quote",
                     "quote": {
                         "rich_text": [{"type": "text", "text": {"content": content}}]
                     }
                 })
             
             while i < len(tokens) and tokens[i].type != 'blockquote_close':
                 i += 1
        
        i += 1
        
    return blocks

def validate_blocks(blocks: List[Dict]) -> List[Dict]:
    """
    Validates and sanitizes blocks before sending to Notion.
    - Ensures text content doesn't exceed 2000 chars per block
    """
    valid_blocks = []
    
    for block in blocks:
        # Check for 2000 char limit in rich_text
        block_type = block.get('type')
        if block_type and block_type in block:
            content_obj = block[block_type]
            if 'rich_text' in content_obj:
                text_content = content_obj['rich_text'][0]['text']['content']
                if len(text_content) > 2000:
                    # Truncate for now, or split (splitting is harder)
                    content_obj['rich_text'][0]['text']['content'] = text_content[:2000] + "..."
        
        valid_blocks.append(block)
    
    return valid_blocks
