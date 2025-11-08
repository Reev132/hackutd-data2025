import os
from notion_client import Client
from typing import Optional

class NotionService:
    def __init__(self):
        self.client = Client(auth=os.getenv("NOTION_API_KEY"))

    def create_page(self, content: str, title: str, parent_page_id: Optional[str] = None) -> dict:
        """Create a new Notion page with the provided content."""

        # Parse markdown content into Notion blocks
        blocks = self._markdown_to_blocks(content)

        # Determine parent
        if parent_page_id:
            parent = {"page_id": parent_page_id}
        else:
            # Try to get default parent page ID from env
            default_parent = os.getenv("NOTION_PARENT_PAGE_ID")
            if not default_parent or default_parent.startswith("ntn_"):
                # No valid parent page ID, need to search for a page
                try:
                    # Search for user's pages
                    search_results = self.client.search(filter={"property": "object", "value": "page"})
                    if search_results.get("results"):
                        # Use the first available page as parent
                        parent = {"page_id": search_results["results"][0]["id"]}
                    else:
                        # If no pages found, we can't create a page - need database or page parent
                        return {
                            "success": False,
                            "error": "No parent page found. Please specify a parent_page_id or set NOTION_PARENT_PAGE_ID in your .env file with a valid page ID from your Notion workspace."
                        }
                except Exception as search_error:
                    return {
                        "success": False,
                        "error": f"Failed to find parent page: {str(search_error)}"
                    }
            else:
                parent = {"page_id": default_parent}

        try:
            page = self.client.pages.create(
                parent=parent,
                properties={
                    "title": {
                        "title": [
                            {
                                "text": {
                                    "content": title
                                }
                            }
                        ]
                    }
                },
                children=blocks
            )
            return {
                "success": True,
                "url": page["url"],
                "id": page["id"]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def add_to_database(self, content: str, title: str, database_id: str) -> dict:
        """Add a new entry to a Notion database."""

        blocks = self._markdown_to_blocks(content)

        try:
            page = self.client.pages.create(
                parent={"database_id": database_id},
                properties={
                    "Name": {
                        "title": [
                            {
                                "text": {
                                    "content": title
                                }
                            }
                        ]
                    }
                },
                children=blocks
            )
            return {
                "success": True,
                "url": page["url"],
                "id": page["id"]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _markdown_to_blocks(self, content: str) -> list:
        """Convert markdown content to Notion blocks."""
        blocks = []
        lines = content.split('\n')

        for line in lines:
            if not line.strip():
                continue

            # Handle headings
            if line.startswith('### '):
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{"type": "text", "text": {"content": line[4:]}}]
                    }
                })
            elif line.startswith('## '):
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": line[3:]}}]
                    }
                })
            elif line.startswith('# '):
                blocks.append({
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"type": "text", "text": {"content": line[2:]}}]
                    }
                })
            # Handle bullet points
            elif line.strip().startswith('- '):
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": line.strip()[2:]}}]
                    }
                })
            # Handle numbered lists
            elif line.strip()[0].isdigit() and line.strip()[1] == '.':
                blocks.append({
                    "object": "block",
                    "type": "numbered_list_item",
                    "numbered_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": line.strip()[3:]}}]
                    }
                })
            # Regular paragraph
            else:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": line}}]
                    }
                })

        return blocks
