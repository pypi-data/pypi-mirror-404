"""
SharePoint MCP Server with Modern Azure AD Authentication
"""
import os
import logging
import asyncio
from functools import wraps
from typing import Optional
import base64
import mimetypes

from mcp.server import Server
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
from pydantic import AnyUrl
import mcp.server.stdio

from .graph_api import GraphAPIClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
app = Server("mcp-sharepoint")

# Global Graph API client and authenticator
graph_client: Optional[GraphAPIClient] = None
authenticator = None


def ensure_context(func):
    """Decorator to ensure Graph API client is available"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        global graph_client, authenticator
        if graph_client is None:
            try:
                logger.info("Initializing Graph API client...")
                from .auth import SharePointAuthenticator

                # Get credentials
                site_url = os.getenv("SHP_SITE_URL")
                client_id = os.getenv("SHP_ID_APP")
                client_secret = os.getenv("SHP_ID_APP_SECRET")
                tenant_id = os.getenv("SHP_TENANT_ID")
                cloud = "government" if ".sharepoint.us" in site_url else "commercial"

                logger.info(f"Site URL: {site_url}")
                logger.info(f"Tenant ID: {tenant_id}")
                logger.info(f"Client ID: {client_id}")
                logger.info(f"Cloud: {cloud}")

                # Create shared authenticator
                authenticator = SharePointAuthenticator(
                    site_url=site_url,
                    client_id=client_id,
                    client_secret=client_secret,
                    tenant_id=tenant_id,
                    cloud=cloud
                )
                logger.info("Authenticator created successfully")

                # Create Graph API client with direct token access
                def get_token():
                    """Get access token for Graph API"""
                    logger.debug("Token callback invoked")
                    token = authenticator.get_access_token()
                    logger.debug(f"Token acquired (length: {len(token)})")
                    return token

                graph_client = GraphAPIClient(
                    site_url=site_url,
                    token_callback=get_token
                )
                logger.info("Graph API client initialized successfully")

            except Exception as e:
                logger.error(f"Failed to initialize Graph API client: {e}", exc_info=True)
                raise RuntimeError(
                    f"Graph API authentication failed: {e}. "
                    "Please check your environment variables and ensure:\n"
                    "1. SHP_TENANT_ID is set correctly\n"
                    "2. Your Azure AD app has Microsoft Graph API permissions\n"
                    "3. The app registration has 'Sites.Read.All' and 'Files.ReadWrite.All' permissions"
                )
        return await func(*args, **kwargs)
    return wrapper


def get_document_library_path() -> str:
    """Get the document library path from environment"""
    return os.getenv("SHP_DOC_LIBRARY", "Shared Documents")


@app.list_resources()
async def list_resources() -> list[Resource]:
    """List available SharePoint resources"""
    return [
        Resource(
            uri=AnyUrl(f"sharepoint:///{get_document_library_path()}"),
            name=f"SharePoint Document Library: {get_document_library_path()}",
            mimeType="application/vnd.sharepoint.folder",
            description="Main SharePoint document library configured for this server"
        )
    ]


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available SharePoint tools"""
    return [
        Tool(
            name="List_SharePoint_Folders",
            description="List all folders in a specified directory or root of the document library",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_path": {
                        "type": "string",
                        "description": "Path to the folder (relative to document library root). Leave empty for root.",
                        "default": ""
                    }
                }
            }
        ),
        Tool(
            name="List_SharePoint_Documents",
            description="List all documents in a specified folder with metadata",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_path": {
                        "type": "string",
                        "description": "Path to the folder containing documents",
                        "default": ""
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="Get_Document_Content",
            description="Get the content of a document (supports text extraction from PDF, Word, Excel, and text files)",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file (relative to document library root)"
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="Upload_Document",
            description="Upload a new document to SharePoint",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_path": {
                        "type": "string",
                        "description": "Destination folder path"
                    },
                    "file_name": {
                        "type": "string",
                        "description": "Name of the file to create"
                    },
                    "content": {
                        "type": "string",
                        "description": "File content (text or base64 encoded for binary files)"
                    },
                    "is_binary": {
                        "type": "boolean",
                        "description": "Whether the content is base64 encoded binary",
                        "default": False
                    }
                },
                "required": ["folder_path", "file_name", "content"]
            }
        ),
        Tool(
            name="Update_Document",
            description="Update the content of an existing document",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to update"
                    },
                    "content": {
                        "type": "string",
                        "description": "New file content"
                    },
                    "is_binary": {
                        "type": "boolean",
                        "description": "Whether the content is base64 encoded binary",
                        "default": False
                    }
                },
                "required": ["file_path", "content"]
            }
        ),
        Tool(
            name="Delete_Document",
            description="Delete a document from SharePoint",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to delete"
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="Create_Folder",
            description="Create a new folder in SharePoint",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_path": {
                        "type": "string",
                        "description": "Path where to create the folder"
                    },
                    "folder_name": {
                        "type": "string",
                        "description": "Name of the new folder"
                    }
                },
                "required": ["folder_path", "folder_name"]
            }
        ),
        Tool(
            name="Delete_Folder",
            description="Delete an empty folder from SharePoint",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_path": {
                        "type": "string",
                        "description": "Path to the folder to delete"
                    }
                },
                "required": ["folder_path"]
            }
        ),
        Tool(
            name="Get_SharePoint_Tree",
            description="Get a recursive tree view of SharePoint folder structure",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_path": {
                        "type": "string",
                        "description": "Starting folder path (leave empty for root)",
                        "default": ""
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "Maximum depth to traverse",
                        "default": 5
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="Test_Connection",
            description="Test the SharePoint connection and authentication",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]


@app.call_tool()
@ensure_context
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool execution"""
    
    try:
        if name == "Test_Connection":
            return await test_connection()
        elif name == "List_SharePoint_Folders":
            return await list_folders(arguments.get("folder_path", ""))
        elif name == "List_SharePoint_Documents":
            return await list_documents(arguments.get("folder_path", ""))
        elif name == "Get_Document_Content":
            return await get_document_content(arguments["file_path"])
        elif name == "Upload_Document":
            return await upload_document(
                arguments["folder_path"],
                arguments["file_name"],
                arguments["content"],
                arguments.get("is_binary", False)
            )
        elif name == "Update_Document":
            return await update_document(
                arguments["file_path"],
                arguments["content"],
                arguments.get("is_binary", False)
            )
        elif name == "Delete_Document":
            return await delete_document(arguments["file_path"])
        elif name == "Create_Folder":
            return await create_folder(arguments["folder_path"], arguments["folder_name"])
        elif name == "Delete_Folder":
            return await delete_folder(arguments["folder_path"])
        elif name == "Get_SharePoint_Tree":
            return await get_tree(
                arguments.get("folder_path", ""),
                arguments.get("max_depth", 5)
            )
        else:
            raise ValueError(f"Unknown tool: {name}")
            
    except Exception as e:
        logger.exception(f"Tool '{name}' failed")  # <-- prints stack trace
        return [TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]



async def test_connection() -> list[TextContent]:
    """Test SharePoint connection using Microsoft Graph API"""
    try:
        logger.info("Testing Graph API connection...")

        # Try to get site ID and drive ID
        site_id = await asyncio.to_thread(graph_client._get_site_id)
        drive_id = await asyncio.to_thread(graph_client._get_drive_id)

        auth_method = "msal (Microsoft Graph API)"

        logger.info(f"✓ Connection test successful - Site ID: {site_id}, Drive ID: {drive_id}")

        return [TextContent(
            type="text",
            text=f"✓ Successfully connected to SharePoint via Microsoft Graph API!\n\n"
                 f"Site URL: {graph_client.site_url}\n"
                 f"Graph Endpoint: {graph_client.graph_endpoint}\n"
                 f"Site ID: {site_id}\n"
                 f"Drive ID: {drive_id}\n"
                 f"Authentication Method: {auth_method}\n"
                 f"Tenant ID: {os.getenv('SHP_TENANT_ID')}\n\n"
                 f"Connection is working correctly with Microsoft Graph API."
        )]
    except Exception as e:
        logger.error(f"✗ Connection test failed: {str(e)}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"✗ Connection failed: {str(e)}\n\n"
                 f"This usually means:\n"
                 f"1. Your credentials are incorrect\n"
                 f"2. Your app doesn't have proper Microsoft Graph permissions\n"
                 f"3. Network connectivity issues\n"
                 f"4. Azure AD app registration is missing required permissions:\n"
                 f"   - Sites.Read.All\n"
                 f"   - Files.ReadWrite.All\n\n"
                 f"Check the logs for more details."
        )]


async def list_folders(folder_path: str = "") -> list[TextContent]:
    """List folders in specified path using Microsoft Graph API"""
    doc_lib = get_document_library_path()
    full_path = f"{doc_lib}/{folder_path}" if folder_path else doc_lib

    try:
        # Use Graph API directly
        folders = await asyncio.to_thread(graph_client.list_folders, folder_path)
        folder_list = [f"📁 {f['name']}" for f in folders]

        result = f"Folders in '{full_path}':\n\n" + "\n".join(folder_list) if folder_list else f"No folders found in '{full_path}'"
        return [TextContent(type="text", text=result)]

    except Exception as e:
        return [TextContent(type="text", text=f"Error listing folders: {str(e)}")]


async def list_documents(folder_path: str = "") -> list[TextContent]:
    """List documents in specified folder using Microsoft Graph API"""
    doc_lib = get_document_library_path()
    full_path = f"{doc_lib}/{folder_path}" if folder_path else doc_lib

    try:
        # Use Graph API directly
        files = await asyncio.to_thread(graph_client.list_documents, folder_path)

        file_list = []
        for f in files:
            size_kb = f['size'] / 1024
            file_list.append(f"📄 {f['name']} ({size_kb:.2f} KB)")

        result = f"Documents in '{full_path}':\n\n" + "\n".join(file_list) if file_list else f"No documents found in '{full_path}'"
        return [TextContent(type="text", text=result)]

    except Exception as e:
        return [TextContent(type="text", text=f"Error listing documents: {str(e)}")]


async def get_document_content(file_path: str) -> list[TextContent]:
    """Get document content using Microsoft Graph API"""
    try:
        # Use Graph API to get file content
        content = await asyncio.to_thread(graph_client.get_file_content, file_path)

        ext = os.path.splitext(file_path)[1].lower()
        text_extensions = {'.txt', '.md', '.json', '.xml', '.html', '.csv', '.log'}

        if ext in text_extensions:
            text_content = content.decode("utf-8", errors="replace")
            return [TextContent(type="text", text=text_content)]

        b64_content = base64.b64encode(content).decode("utf-8")
        return [TextContent(
            type="text",
            text=(
                "Binary file (base64 encoded):\n\n"
                f"{b64_content[:200]}...\n\n"
                f"Full content length: {len(b64_content)} characters"
            )
        )]

    except Exception as e:
        logger.exception("Error reading document")
        return [TextContent(type="text", text=f"Error reading document: {str(e)}")]


async def upload_document(folder_path: str, file_name: str, content: str, is_binary: bool = False) -> list[TextContent]:
    """Upload a document using Microsoft Graph API"""
    try:
        if is_binary:
            file_content = base64.b64decode(content)
        else:
            file_content = content.encode('utf-8')

        # Use Graph API to upload file
        result = await asyncio.to_thread(
            graph_client.upload_file,
            folder_path,
            file_name,
            file_content
        )

        return [TextContent(
            type="text",
            text=f"✓ Successfully uploaded '{file_name}' to '{folder_path or 'root'}'"
        )]

    except Exception as e:
        return [TextContent(type="text", text=f"Error uploading document: {str(e)}")]


async def update_document(file_path: str, content: str, is_binary: bool = False) -> list[TextContent]:
    """Update a document using Microsoft Graph API"""
    try:
        if is_binary:
            file_content = base64.b64decode(content)
        else:
            file_content = content.encode('utf-8')

        # Split file_path into folder and filename
        folder_path = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)

        # Use Graph API to upload/update file (PUT overwrites)
        await asyncio.to_thread(
            graph_client.upload_file,
            folder_path,
            file_name,
            file_content
        )

        return [TextContent(
            type="text",
            text=f"✓ Successfully updated '{file_path}'"
        )]

    except Exception as e:
        return [TextContent(type="text", text=f"Error updating document: {str(e)}")]


async def delete_document(file_path: str) -> list[TextContent]:
    """Delete a document using Microsoft Graph API"""
    try:
        # Use Graph API to delete file
        await asyncio.to_thread(graph_client.delete_file, file_path)

        return [TextContent(
            type="text",
            text=f"✓ Successfully deleted '{file_path}'"
        )]

    except Exception as e:
        return [TextContent(type="text", text=f"Error deleting document: {str(e)}")]


async def create_folder(folder_path: str, folder_name: str) -> list[TextContent]:
    """Create a folder using Microsoft Graph API"""
    try:
        # Use Graph API to create folder
        await asyncio.to_thread(
            graph_client.create_folder,
            folder_path,
            folder_name
        )

        return [TextContent(
            type="text",
            text=f"✓ Successfully created folder '{folder_name}' in '{folder_path or 'root'}'"
        )]

    except Exception as e:
        return [TextContent(type="text", text=f"Error creating folder: {str(e)}")]


async def delete_folder(folder_path: str) -> list[TextContent]:
    """Delete a folder using Microsoft Graph API"""
    try:
        # Use Graph API to delete folder
        await asyncio.to_thread(graph_client.delete_folder, folder_path)

        return [TextContent(
            type="text",
            text=f"✓ Successfully deleted folder '{folder_path}'"
        )]

    except Exception as e:
        return [TextContent(type="text", text=f"Error deleting folder: {str(e)}")]


async def get_tree(folder_path: str = "", max_depth: int = 5, current_depth: int = 0) -> list[TextContent]:
    """Get folder tree structure using Microsoft Graph API"""
    if current_depth >= max_depth:
        return [TextContent(type="text", text="Max depth reached")]

    try:
        # Use Graph API to list folders
        folders = await asyncio.to_thread(graph_client.list_folders, folder_path)

        indent = "  " * current_depth
        tree_lines = [f"{indent}📁 {folder_path or 'Root'}"]

        for f in folders:
            sub_path = f"{folder_path}/{f['name']}" if folder_path else f['name']
            sub_tree = await get_tree(sub_path, max_depth, current_depth + 1)
            tree_lines.append(sub_tree[0].text)

        return [TextContent(type="text", text="\n".join(tree_lines))]

    except Exception as e:
        return [TextContent(type="text", text=f"Error getting tree: {str(e)}")]


async def main():
    """Main entry point"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())

def run():
    """Sync entry point for the package"""
    asyncio.run(main())