"""
DeepAI Chat API Documentation & Client Library
================================================

This module provides a Python client for interacting with DeepAI's Chat API.
It includes documentation and ready-to-use functions for all available endpoints.

Base URL: https://api.deepai.org

Authentication:
- Some endpoints require session cookies (csrftoken, sessionid)
- Chat endpoint requires an api-key header

Available Endpoints:
1. /save_chat_session - Save or update a chat session
2. /hacking_is_a_serious_crime - Main chat completion endpoint
3. /get_my_chat_sessions_and_convert_anonymous_sessions - Retrieve user's chat sessions
"""

import requests
import json
import uuid
from typing import List, Dict, Optional, Any
from dataclasses import dataclass



BASE_URL = "https://api.deepai.org"

DEFAULT_HEADERS = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache",
    "origin": "https://deepai.org",
    "pragma": "no-cache",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
}

# Supported AI models (default: gpt-5-nano)
SUPPORTED_MODELS = [
    "gpt-5-nano",           # Default - lightweight, supports function calling
    "gpt-4.1-nano",         # GPT-4.1 nano version
    "deepseek-v3.2",        # DeepSeek v3.2
    "gemini-2.5-flash-lite", # Google Gemini Flash Lite
    "llama-4-scout",        # Meta Llama 4 Scout
    "gemma2-9b-it",         # Google Gemma 2 9B Instruct
]

DEFAULT_MODEL = "gpt-5-nano"



def get_user_login_type(email: str) -> Dict[str, Any]:
    """
    Check user login type by email.
    
    Endpoint: POST /get_user_login_type
    
    Args:
        email: User's email address
    
    Returns:
        dict: Login type information
    """
    url = f"{BASE_URL}/get_user_login_type"
    data = {"email": email}
    
    response = requests.post(url, data=data, headers=DEFAULT_HEADERS)
    response.raise_for_status()
    
    return response.json()


def login_with_password(email: str, password: str) -> Dict[str, Any]:
    """
    Login with email and password.
    
    Endpoint: POST /login_user
    
    Args:
        email: User's email address
        password: User's password
    
    Returns:
        dict: {
            "success": True/False,
            "session_id": "...",
            "csrf_token": "...",
            "api_key": "...",
            "error": "..." (if failed)
        }
    """
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    
    result = {
        "success": False,
        "session_id": None,
        "csrf_token": None,
        "api_key": None,
        "error": None
    }
    
    try:
        # Login endpoint
        url_login = f"{BASE_URL}/daily-time-sync/login/"
        data = {
            "username": email,  # Uses 'username' field
            "password": password
        }
        
        response = session.post(url_login, data=data)
        
        # Extract cookies
        cookies = session.cookies.get_dict()
        session_id = cookies.get("sessionid")
        csrf_token = cookies.get("csrftoken")
        
        # Check response status
        if response.status_code == 200:
            try:
                json_response = response.json()
                api_key = json_response.get("key")
                
                if api_key:
                    result["success"] = True
                    result["session_id"] = session_id
                    result["csrf_token"] = csrf_token
                    result["api_key"] = api_key
                    result["user_info"] = json_response
                else:
                    result["error"] = "No API key returned"
            except Exception as e:
                result["error"] = f"Invalid response: {str(e)}"
        else:
            # Login failed
            try:
                json_response = response.json()
                # Handle django auth error format
                errors = json_response.get("non_field_errors", [])
                if errors:
                    result["error"] = errors[0]
                else:
                    result["error"] = json_response.get("detail", "Login failed")
            except:
                result["error"] = f"Login failed - status {response.status_code}"
                
    except Exception as e:
        result["error"] = str(e)
    
    return result



@dataclass
class Message:
    """Represents a chat message."""
    role: str  # "user" or "assistant"
    content: str
    attachment_uuids: Optional[List[str]] = None  # For messages with attachments
    
    def to_dict(self) -> Dict[str, Any]:
        result = {"role": self.role, "content": self.content}
        if self.attachment_uuids:
            result["attachment_uuids"] = self.attachment_uuids
        return result


@dataclass
class ChatSession:
    """Represents a chat session."""
    uuid: str
    title: str
    updated_at: str
    chat_style: str


@dataclass
class LoginResult:
    """Represents login result."""
    success: bool
    session_id: Optional[str]
    csrf_token: Optional[str]
    api_key: Optional[str]
    error: Optional[str]



class DeepAIClient:
    """
    DeepAI Chat API Client
    
    Example Usage:
    --------------
    ```python
    # Method 1: Login with email/password (auto-login)
    client = DeepAIClient.login(email="your@email.com", password="yourpass")
    
    # Method 2: Use existing credentials
    client = DeepAIClient(
        api_key="your-api-key",
        session_id="your-session-id",
        csrf_token="your-csrf-token"
    )
    
    # Send a chat message
    response = client.chat("Hello, how are you?")
    print(response)
    
    # Get chat history
    sessions = client.get_chat_sessions()
    for session in sessions:
        print(session.title)
    ```
    """
    
    def __init__(
        self, 
        api_key: str,
        session_id: Optional[str] = None,
        csrf_token: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None
    ):
        """
        Initialize the DeepAI client.
        
        Args:
            api_key: API key for authentication (required for chat endpoint)
            session_id: Session ID cookie (optional, for session management)
            csrf_token: CSRF token cookie (optional, for session management)
            email: Email for auto-login (optional)
            password: Password for auto-login (optional, requires email)
        """
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        
        # Auto-login if email and password provided
        if email and password:
            login_result = login_with_password(email, password)
            if login_result["success"]:
                self.api_key = login_result.get("api_key") or api_key
                self.session_id = login_result.get("session_id")
                self.csrf_token = login_result.get("csrf_token")
                self.user_info = login_result.get("user_info")
                self.logged_in = True
            else:
                raise Exception(f"Login failed: {login_result.get('error')}")
        else:
            self.api_key = api_key
            self.session_id = session_id
            self.csrf_token = csrf_token
            self.user_info = None
            self.logged_in = False
        
        # Set cookies if available (use .deepai.org for cross-domain)
        if self.session_id:
            self.session.cookies.set("sessionid", self.session_id, domain=".deepai.org")
        if self.csrf_token:
            self.session.cookies.set("csrftoken", self.csrf_token, domain=".deepai.org")
    
    @classmethod
    def login(cls, email: str, password: str) -> "DeepAIClient":
        """
        Create a client by logging in with email and password.
        
        Args:
            email: User's email address
            password: User's password
        
        Returns:
            DeepAIClient: Authenticated client instance
        
        Example:
            >>> client = DeepAIClient.login("user@example.com", "password123")
            >>> print(f"Logged in! API Key: {client.api_key}")
        """
        login_result = login_with_password(email, password)
        
        if not login_result["success"]:
            raise Exception(f"Login failed: {login_result.get('error')}")
        
        client = cls(
            api_key=login_result.get("api_key", ""),
            session_id=login_result.get("session_id"),
            csrf_token=login_result.get("csrf_token")
        )
        client.user_info = login_result.get("user_info")
        client.logged_in = True
        
        return client
    
    @classmethod
    def guest(cls) -> "DeepAIClient":
        """
        Create a guest client for anonymous chat (no login required).
        
        Guest mode supports:
        - ✅ Chat with AI
        - ✅ Upload attachments
        - ✅ Chat with attachments
        - ❌ Save history (no session)
        - ❌ Load saved sessions
        
        Returns:
            DeepAIClient: Anonymous client instance
        
        Example:
            >>> client = DeepAIClient.guest()
            >>> response = client.chat("Hello!")
            >>> attachment = client.upload_attachment("file.txt")
            >>> response = client.chat("Explain this", attachment_uuids=[...])
        """
        import uuid
        
        # Generate simple guest API key
        guest_key = f"guest-{uuid.uuid4()}"
        
        client = cls(api_key=guest_key)
        client.logged_in = False
        
        return client
    
    # ENDPOINT 1: CHAT COMPLETION
    
    def chat(
        self,
        message: str,
        chat_history: Optional[List[Message]] = None,
        chat_style: str = "chat",
        model: str = "standard",
        enabled_tools: Optional[List[str]] = None,
        attachment_uuids: Optional[List[str]] = None
    ) -> str:
        """
        Send a chat message and get AI response.
        
        Endpoint: POST /hacking_is_a_serious_crime
        
        Args:
            message: The user's message to send
            chat_history: Previous messages in the conversation (optional)
            chat_style: Style of chat - "chat" (default)
            model: AI model to use - "standard", "gemini-2.5-flash-lite", etc.
            enabled_tools: List of enabled tools, e.g. ["image_generator", "image_editor"]
            attachment_uuids: List of uploaded attachment UUIDs to include
        
        Returns:
            str: The AI's response text
        
        Example:
            >>> client = DeepAIClient(api_key="your-key")
            >>> response = client.chat("What is Python?")
            >>> print(response)
            
            # With attachment
            >>> attachment = client.upload_attachment("image.png")
            >>> response = client.chat("Explain this image", 
            ...     attachment_uuids=[attachment["uuid"]])
        """
        url = f"{BASE_URL}/hacking_is_a_serious_crime"
        
        # Build chat history
        if chat_history is None:
            chat_history = []
        
        # Add current message to history
        all_messages = [msg.to_dict() for msg in chat_history]
        
        # Build user message with optional attachments
        user_message = {"role": "user", "content": message}
        if attachment_uuids:
            user_message["attachment_uuids"] = attachment_uuids
        all_messages.append(user_message)
        
        # Default tools
        if enabled_tools is None:
            enabled_tools = ["image_generator", "image_editor"]
        
        # Prepare form data
        data = {
            "chat_style": chat_style,
            "chatHistory": json.dumps(all_messages),
            "model": model,
            "hacker_is_stinky": "very_stinky",  # Required field
            "enabled_tools": json.dumps(enabled_tools)
        }
        
        # Add attachment UUIDs if provided
        if attachment_uuids:
            data["attachment_uuids"] = json.dumps(attachment_uuids)
        
        headers = {"api-key": self.api_key}
        
        try:
            response = self.session.post(url, data=data, headers=headers)
            response.raise_for_status()
            return response.text
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise Exception("Invalid API key or session expired")
            elif e.response.status_code == 429:
                raise Exception("Rate limited - too many requests")
            raise Exception(f"Chat failed: {e.response.status_code}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {str(e)}")
    
    # ENDPOINT: UPLOAD ATTACHMENT
    
    def upload_attachment(
        self,
        file_path: str,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload a file/image attachment for use in chat.
        
        Endpoint: POST /chat_attachments/upload
        
        Args:
            file_path: Path to the file to upload
            filename: Optional custom filename (uses original if not provided)
        
        Returns:
            dict: {
                "success": True,
                "attachment": {
                    "uuid": "6af3eb8e-54e0-4197-b542-18641ca95646",
                    "original_filename": "image.png",
                    "content_type": "image/png",
                    "file_size": 73332,
                    "extraction_status": "skipped",
                    "created_at": "2026-02-01T04:31:30.088631+00:00",
                    "download_url": "https://..."
                }
            }
        
        Example:
            >>> result = client.upload_attachment("./my_image.png")
            >>> print(f"Uploaded: {result['attachment']['uuid']}")
            >>> 
            >>> # Use in chat
            >>> response = client.chat("What's in this image?",
            ...     attachment_uuids=[result['attachment']['uuid']])
        """
        import os
        import mimetypes
        
        url = f"{BASE_URL}/chat_attachments/upload"
        
        # Determine filename
        if filename is None:
            filename = os.path.basename(file_path)
        
        # Determine content type
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type is None:
            content_type = "application/octet-stream"
        
        # Check file exists
        import os
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Read file and upload
        try:
            with open(file_path, "rb") as f:
                files = {
                    "file": (filename, f, content_type)
                }
                response = self.session.post(url, files=files)
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            raise Exception(f"Upload failed: {e.response.status_code} - {e.response.text[:200]}")
    
    def upload_attachment_bytes(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str = "application/octet-stream"
    ) -> Dict[str, Any]:
        """
        Upload file bytes as an attachment.
        
        Args:
            file_bytes: Raw bytes of the file
            filename: Filename to use
            content_type: MIME type (e.g., "image/png")
        
        Returns:
            dict: Attachment info with uuid, download_url, etc.
        """
        url = f"{BASE_URL}/chat_attachments/upload"
        
        files = {
            "file": (filename, file_bytes, content_type)
        }
        
        response = self.session.post(url, files=files)
        response.raise_for_status()
        return response.json()
    
    # ENDPOINT: GET ATTACHMENT
    
    def get_attachment(self, attachment_uuid: str) -> Dict[str, Any]:
        """
        Get attachment info by UUID.
        
        Endpoint: GET /chat_attachments/get?uuid=...
        
        Args:
            attachment_uuid: UUID of the attachment
        
        Returns:
            dict: {
                "success": True,
                "attachment": {
                    "uuid": "...",
                    "original_filename": "image.png",
                    "content_type": "image/png",
                    "file_size": 73332,
                    "download_url": "https://..."
                }
            }
        """
        url = f"{BASE_URL}/chat_attachments/get"
        params = {"uuid": attachment_uuid}
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    # ENDPOINT: IMAGE GENERATION (text2img)
    
    def generate_image(
        self,
        prompt: str,
        width: int = 832,
        height: int = 448,
        aspect_ratio: str = "16:9",
        quality: bool = True,
        version: str = "hd"
    ) -> Dict[str, Any]:
        """
        Generate an image from text prompt.
        
        Endpoint: POST /api/text2img
        
        Args:
            prompt: Text description of the image to generate
            width: Image width in pixels (default: 832)
            height: Image height in pixels (default: 448)
            aspect_ratio: Aspect ratio - "16:9", "1:1", "9:16", etc.
            quality: High quality mode (default: True)
            version: Generator version - "hd" (default)
        
        Returns:
            dict: {
                "id": "e263bd68-2d0b-4d5e-af21-41f6eca6a017",
                "output_url": "https://api.deepai.org/job-view-file/.../output.jpg",
                "share_url": "https://images.deepai.org/art-image/..."
            }
        
        Example:
            >>> result = client.generate_image("A cute cat sleeping")
            >>> print(result["share_url"])  # Direct image URL
            >>> print(result["output_url"]) # API job URL
        
        Aspect Ratios & Dimensions:
            - "16:9" (landscape): 832x448
            - "1:1" (square): 640x640
            - "9:16" (portrait): 448x832
            - "4:3": 768x576
            - "3:4": 576x768
        """
        url = f"{BASE_URL}/api/text2img"
        
        # Adjust dimensions based on aspect ratio
        dimensions = {
            "16:9": (832, 448),
            "1:1": (640, 640),
            "9:16": (448, 832),
            "4:3": (768, 576),
            "3:4": (576, 768),
            "3:2": (768, 512),
            "2:3": (512, 768)
        }
        
        if aspect_ratio in dimensions:
            width, height = dimensions[aspect_ratio]
        
        data = {
            "text": prompt,
            "width": str(width),
            "height": str(height),
            "image_generator_version": version,
            "quality": str(quality).lower()
        }
        
        # Image generation requires "tryit" key format, not login API key
        # Generate a tryit key if the current api_key is not in tryit format
        import random
        import time
        if not self.api_key.startswith("tryit-"):
            random_id = int(time.time() * 1000) % 100000000000
            random_hash = ''.join(random.choices('0123456789abcdef', k=32))
            tryit_key = f"tryit-{random_id}-{random_hash}"
        else:
            tryit_key = self.api_key
        
        headers = {"api-key": tryit_key}
        
        try:
            response = self.session.post(url, data=data, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise Exception("Image generation requires Pro account or valid tryit key")
            raise Exception(f"Image generation failed: {e.response.status_code}")
    
    def chat_with_image_generation(
        self,
        message: str,
        chat_history: Optional[List[Message]] = None,
        model: str = "gpt-5-nano",
        auto_generate: bool = True
    ) -> Dict[str, Any]:
        """
        Chat with automatic image generation support.
        
        If the AI decides to generate an image, this method will
        automatically call text2img and return the generated image.
        
        Args:
            message: User's message (e.g., "Create a cat image")
            chat_history: Previous messages
            model: AI model to use (default: gpt-5-nano)
            auto_generate: Auto-call text2img if AI requests it
        
        Returns:
            dict: {
                "response_type": "text" | "image",
                "content": "text response" | image_result,
                "function_call": {...} (if image was requested)
            }
        
        Example:
            >>> result = client.chat_with_image_generation("Tạo ảnh mèo")
            >>> if result["response_type"] == "image":
            ...     print(f"Image URL: {result['content']['share_url']}")
        """
        # Call chat API
        response_text = self.chat(
            message=message,
            chat_history=chat_history,
            model=model,
            enabled_tools=["image_generator", "image_editor"]
        )
        
        result = {
            "response_type": "text",
            "content": response_text,
            "function_call": None
        }
        
        # Check if response is a function call for image generation
        try:
            if response_text.startswith('{"function_call"'):
                import json
                func_data = json.loads(response_text)
                
                if func_data.get("function_call", {}).get("name") == "generate_image":
                    result["function_call"] = func_data["function_call"]
                    
                    if auto_generate:
                        # Parse arguments and generate image
                        args = json.loads(func_data["function_call"]["arguments"])
                        prompt = args.get("prompt", "")
                        aspect_ratio = args.get("aspect_ratio", "16:9")
                        
                        image_result = self.generate_image(
                            prompt=prompt,
                            aspect_ratio=aspect_ratio
                        )
                        
                        result["response_type"] = "image"
                        result["content"] = image_result
                        result["prompt"] = prompt
        except Exception:
            pass  # Not a function call, return as text
        
        return result
    
    # ENDPOINT 2: SAVE CHAT SESSION
    
    def save_chat_session(
        self,
        messages: List[Message],
        session_uuid: Optional[str] = None,
        title: str = "",
        chat_style: str = "chat"
    ) -> Dict[str, Any]:
        """
        Save or update a chat session.
        
        Endpoint: POST /save_chat_session
        
        Args:
            messages: List of Message objects in the conversation
            session_uuid: UUID of existing session (generates new if not provided)
            title: Optional title for the session
            chat_style: Style of chat - "chat" (default)
        
        Returns:
            dict: Response containing success status and session UUID
                  {"success": true, "uuid": "..."}
        
        Example:
            >>> messages = [
            ...     Message(role="user", content="Hello"),
            ...     Message(role="assistant", content="Hi there!")
            ... ]
            >>> result = client.save_chat_session(messages)
            >>> print(result["uuid"])
        
        Request Format (multipart/form-data):
            - uuid: string (UUID v4)
            - title: string (optional)
            - chat_style: string (e.g., "chat")
            - messages: JSON array of message objects
        
        Response JSON:
            {
                "success": true,
                "uuid": "ebcdac6a-13e0-4da4-ae5b-cb53b4b1dad5"
            }
        """
        url = f"{BASE_URL}/save_chat_session"
        
        # Generate UUID if not provided
        if session_uuid is None:
            session_uuid = str(uuid.uuid4())
        
        # Convert messages to dict format
        messages_data = [msg.to_dict() for msg in messages]
        
        data = {
            "uuid": session_uuid,
            "title": title,
            "chat_style": chat_style,
            "messages": json.dumps(messages_data)
        }
        
        response = self.session.post(url, data=data)
        response.raise_for_status()
        
        return response.json()
    
    # ENDPOINT 3: GET CHAT SESSIONS
    
    def get_chat_sessions(
        self,
        known_uuids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Retrieve user's chat sessions and convert anonymous sessions.
        
        Endpoint: POST /get_my_chat_sessions_and_convert_anonymous_sessions
        
        Args:
            known_uuids: List of session UUIDs already known to the client
        
        Returns:
            dict: Response containing sessions list and UUIDs to forget
                  {
                      "sessions": [...],
                      "session_uuids_to_forget": [...]
                  }
        
        Example:
            >>> sessions = client.get_chat_sessions()
            >>> for session in sessions["sessions"]:
            ...     print(f"{session['title']} - {session['updated_at']}")
        
        Request Format (multipart/form-data):
            - my_known_uuids: JSON array of UUID strings
        
        Response JSON:
            {
                "sessions": [
                    {
                        "uuid": "ebcdac6a-13e0-4da4-ae5b-cb53b4b1dad5",
                        "title": "Brief Message Clarification and Assistance",
                        "updated_at": "2026-02-01T04:14:58.181Z",
                        "chat_style": "chat"
                    }
                ],
                "session_uuids_to_forget": [
                    "ebcdac6a-13e0-4da4-ae5b-cb53b4b1dad5"
                ]
            }
        """
        url = f"{BASE_URL}/get_my_chat_sessions_and_convert_anonymous_sessions"
        
        if known_uuids is None:
            known_uuids = []
        
        data = {
            "my_known_uuids": json.dumps(known_uuids)
        }
        
        response = self.session.post(url, data=data)
        response.raise_for_status()
        
        return response.json()
    
    def get_chat_session(self, session_uuid: str) -> Dict[str, Any]:
        """
        Load a chat session's full history from server.
        
        Endpoint: GET /get_chat_session?uuid={uuid}
        
        Args:
            session_uuid: UUID of the session to load
        
        Returns:
            dict: {
                "uuid": "a0e3917d-8f07-4efb-8c99-a0ce9be393bb",
                "title": "...",
                "messages": [
                    {
                        "content": "...",
                        "role": "user",
                        "attachment_uuids": [...],
                        "attachments": [...]
                    },
                    {
                        "content": "...",
                        "role": "assistant"
                    }
                ]
            }
        
        Example:
            >>> session = client.get_chat_session("a0e3917d-8f07-...")
            >>> for msg in session["messages"]:
            ...     print(f"[{msg['role']}]: {msg['content'][:50]}")
        """
        url = f"{BASE_URL}/get_chat_session"
        params = {"uuid": session_uuid}
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise Exception(f"Session not found: {session_uuid}")
            elif e.response.status_code == 403:
                raise Exception(f"Access denied to session: {session_uuid}")
            raise
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {str(e)}")
    
    # COMBINED: CHAT AND AUTO-SAVE
    
    def chat_and_save(
        self,
        message: str,
        session_uuid: Optional[str] = None,
        chat_history: Optional[List[Message]] = None,
        title: str = "",
        chat_style: str = "chat",
        model: str = "standard",
        enabled_tools: Optional[List[str]] = None,
        auto_generate_title: bool = True
    ) -> Dict[str, Any]:
        """
        Send a chat message and automatically save the session.
        
        This method combines chat() and save_chat_session() into one call.
        It sends the message, gets the response, and saves everything.
        
        Args:
            message: The user's message to send
            session_uuid: UUID of existing session (generates new if not provided)
            chat_history: Previous messages in the conversation (optional)
            title: Optional title for the session
            chat_style: Style of chat - "chat" (default)
            model: AI model to use - "standard" (default)
            enabled_tools: List of enabled tools
            auto_generate_title: Generate title from first message if empty
        
        Returns:
            dict: {
                "response": "AI response text",
                "session_uuid": "uuid of saved session",
                "messages": [list of all messages including new ones],
                "save_result": {save API response}
            }
        
        Example:
            >>> result = client.chat_and_save("Hello!")
            >>> print(result["response"])
            >>> print(f"Session saved: {result['session_uuid']}")
        """
        # Generate UUID if not provided
        if session_uuid is None:
            session_uuid = str(uuid.uuid4())
        
        # Build chat history
        if chat_history is None:
            chat_history = []
        
        # Add user message
        all_messages = chat_history.copy()
        all_messages.append(Message(role="user", content=message))
        
        # Auto generate title from first user message
        if auto_generate_title and not title and len(chat_history) == 0:
            title = message[:50] + "..." if len(message) > 50 else message
        
        # FIRST SAVE: Save session with user message only
        self.save_chat_session(
            messages=all_messages,
            session_uuid=session_uuid,
            title=title,
            chat_style=chat_style
        )
        
        # Get AI response
        ai_response = self.chat(
            message=message,
            chat_history=chat_history,
            chat_style=chat_style,
            model=model,
            enabled_tools=enabled_tools
        )
        
        # Add AI response
        all_messages.append(Message(role="assistant", content=ai_response))
        
        # SECOND SAVE: Save session with user + AI messages
        save_result = self.save_chat_session(
            messages=all_messages,
            session_uuid=session_uuid,
            title=title,
            chat_style=chat_style
        )
        
        return {
            "response": ai_response,
            "session_uuid": session_uuid,
            "messages": all_messages,
            "save_result": save_result
        }


# CONVERSATION MANAGER - Auto Chat & Save

class ConversationManager:
    """
    Manages a continuous conversation with auto-save functionality.
    
    This class maintains conversation state and automatically saves
    after each message exchange.
    
    Example Usage:
    --------------
    ```python
    manager = ConversationManager(api_key="your-api-key")
    
    # Start chatting - auto saves after each message
    response1 = manager.send("Hello!")
    print(response1)
    
    response2 = manager.send("Tell me about Python")
    print(response2)
    
    # Get current session info
    print(f"Session UUID: {manager.session_uuid}")
    print(f"Total messages: {len(manager.messages)}")
    
    # Start a new conversation
    manager.new_conversation()
    response3 = manager.send("New topic!")
    ```
    """
    
    def __init__(
        self,
        api_key: str,
        session_id: Optional[str] = None,
        csrf_token: Optional[str] = None,
        model: str = "standard",
        enabled_tools: Optional[List[str]] = None
    ):
        """
        Initialize the conversation manager.
        
        Args:
            api_key: API key for authentication
            session_id: Session ID cookie (optional)
            csrf_token: CSRF token cookie (optional)
            model: Default AI model to use
            enabled_tools: Default tools to enable
        """
        self.client = DeepAIClient(
            api_key=api_key,
            session_id=session_id,
            csrf_token=csrf_token
        )
        self.model = model
        self.enabled_tools = enabled_tools or ["image_generator", "image_editor"]
        
        # Conversation state
        self.session_uuid: Optional[str] = None
        self.messages: List[Message] = []
        self.title: str = ""
    
    def send(
        self, 
        message: str, 
        title: Optional[str] = None,
        model: Optional[str] = None,
        attachment_uuids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send a message and automatically save the conversation.
        Automatically detects and handles image generation requests.
        
        Flow (matches DeepAI website behavior):
        1. User sends message -> Save session (user only)
        2. Get AI response -> If image request, generate image
        3. Save session (user + AI)
        
        Args:
            message: The message to send
            title: Optional title (only used for first message)
            model: AI model to use (overrides default). Options:
                   - "gpt-5-nano" (default, supports function calling)
                   - "gemini-2.5-flash-lite"
                   - "standard"
                   - etc.
            attachment_uuids: List of uploaded attachment UUIDs
        
        Returns:
            dict: {
                "type": "text" | "image",
                "content": "response text" | image_info,
                "image_url": "..." (if image generated)
            }
        """
        # Generate session UUID if this is a new conversation
        if self.session_uuid is None:
            self.session_uuid = str(uuid.uuid4())
        
        # Set title from first message if not provided
        if not self.title and title:
            self.title = title
        elif not self.title and len(self.messages) == 0:
            self.title = message[:50] + "..." if len(message) > 50 else message
        
        # Use provided model or default
        use_model = model or self.model
        
        # Add user message to history (with attachments if any)
        user_msg = Message(role="user", content=message, attachment_uuids=attachment_uuids)
        self.messages.append(user_msg)
        
        # FIRST SAVE: Save session with user message only
        self.client.save_chat_session(
            messages=self.messages,
            session_uuid=self.session_uuid,
            title=self.title
        )
        
        # Get AI response (pass history without the last user message we just added)
        ai_response = self.client.chat(
            message=message,
            chat_history=self.messages[:-1],  # Exclude last message (already in API call)
            model=use_model,
            enabled_tools=self.enabled_tools,
            attachment_uuids=attachment_uuids
        )
        
        result = {
            "type": "text",
            "content": ai_response,
            "image_url": None
        }
        
        # Check if AI wants to generate an image
        try:
            if '{"function_call"' in ai_response:
                func_data = json.loads(ai_response)
                
                if func_data.get("function_call", {}).get("name") == "generate_image":
                    # Parse image generation arguments
                    args = json.loads(func_data["function_call"]["arguments"])
                    prompt = args.get("prompt", message)
                    aspect_ratio = args.get("aspect_ratio", "16:9")
                    
                    # Generate the image
                    image_result = self.client.generate_image(
                        prompt=prompt,
                        aspect_ratio=aspect_ratio
                    )
                    
                    # Format response like DeepAI website does
                    image_response = json.dumps({
                        "type": "generated_image",
                        "prompt": prompt,
                        "url": image_result.get("share_url", image_result.get("output_url"))
                    })
                    
                    # Add special character prefix like DeepAI does
                    ai_response = "\x1c" + image_response
                    
                    result = {
                        "type": "image",
                        "content": ai_response,
                        "image_url": image_result.get("share_url", image_result.get("output_url")),
                        "prompt": prompt,
                        "image_result": image_result
                    }
        except json.JSONDecodeError:
            pass  # Not a function call, keep as text
        except Exception:
            pass  # Error handling, keep original response
        
        # Add AI response to history
        self.messages.append(Message(role="assistant", content=ai_response))
        
        # SECOND SAVE: Save session with user + AI messages
        self.client.save_chat_session(
            messages=self.messages,
            session_uuid=self.session_uuid,
            title=self.title
        )
        
        return result
    
    def new_conversation(self, title: str = "") -> str:
        """
        Start a new conversation and reset state.
        
        Args:
            title: Optional title for the new conversation
        
        Returns:
            str: New session UUID
        """
        self.session_uuid = str(uuid.uuid4())
        self.messages = []
        self.title = title
        return self.session_uuid
    
    def get_history(self) -> List[Dict[str, str]]:
        """Get current conversation history as list of dicts."""
        return [msg.to_dict() for msg in self.messages]
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get current session information."""
        return {
            "session_uuid": self.session_uuid,
            "title": self.title,
            "message_count": len(self.messages),
            "messages": self.get_history()
        }
    
    def load_session(self, session_uuid: str) -> Dict[str, Any]:
        """
        Load an existing session from server and resume conversation.
        
        Args:
            session_uuid: UUID of the session to load
        
        Returns:
            dict: Session info with messages
        
        Example:
            >>> manager.load_session("a0e3917d-8f07-4efb-...")
            >>> # Now AI will remember previous conversation
            >>> result = manager.send("Bạn còn nhớ tôi không?")
        """
        session_data = self.client.get_chat_session(session_uuid)
        
        # Check if session exists and belongs to current user
        if "uuid" not in session_data:
            raise Exception(f"Session not found or access denied: {session_uuid}")
        
        self.session_uuid = session_data["uuid"]
        self.title = session_data.get("title", "")
        
        # Load messages from server
        self.messages = []
        for msg in session_data.get("messages", []):
            if msg.get("content"):  # Skip empty messages
                self.messages.append(Message(
                    role=msg["role"],
                    content=msg["content"],
                    attachment_uuids=msg.get("attachment_uuids")
                ))
        
        return {
            "session_uuid": self.session_uuid,
            "title": self.title,
            "message_count": len(self.messages)
        }


# STANDALONE FUNCTIONS (Alternative to class-based approach)

def send_chat_message(
    api_key: str,
    message: str,
    chat_history: Optional[List[Dict[str, str]]] = None,
    model: str = "standard",
    enabled_tools: Optional[List[str]] = None
) -> str:
    """
    Send a chat message to DeepAI (standalone function).
    
    Args:
        api_key: Your DeepAI API key
        message: The message to send
        chat_history: Previous messages [{"role": "user/assistant", "content": "..."}]
        model: AI model ("standard")
        enabled_tools: List of tools to enable
    
    Returns:
        AI response text
    """
    url = f"{BASE_URL}/hacking_is_a_serious_crime"
    
    if chat_history is None:
        chat_history = []
    
    chat_history.append({"role": "user", "content": message})
    
    if enabled_tools is None:
        enabled_tools = ["image_generator", "image_editor"]
    
    data = {
        "chat_style": "chat",
        "chatHistory": json.dumps(chat_history),
        "model": model,
        "hacker_is_stinky": "very_stinky",
        "enabled_tools": json.dumps(enabled_tools)
    }
    
    headers = {**DEFAULT_HEADERS, "api-key": api_key}
    
    response = requests.post(url, data=data, headers=headers)
    response.raise_for_status()
    
    return response.text


def save_session(
    messages: List[Dict[str, str]],
    session_uuid: Optional[str] = None,
    title: str = "",
    cookies: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Save a chat session (standalone function).
    
    Args:
        messages: List of message dicts [{"role": "...", "content": "..."}]
        session_uuid: Existing session UUID or None for new
        title: Session title
        cookies: Dict with "sessionid" and "csrftoken"
    
    Returns:
        Response dict with success and uuid
    """
    url = f"{BASE_URL}/save_chat_session"
    
    if session_uuid is None:
        session_uuid = str(uuid.uuid4())
    
    data = {
        "uuid": session_uuid,
        "title": title,
        "chat_style": "chat",
        "messages": json.dumps(messages)
    }
    
    response = requests.post(url, data=data, headers=DEFAULT_HEADERS, cookies=cookies)
    response.raise_for_status()
    
    return response.json()


def get_sessions(
    known_uuids: Optional[List[str]] = None,
    cookies: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Get user's chat sessions (standalone function).
    
    Args:
        known_uuids: List of known session UUIDs
        cookies: Dict with "sessionid" and "csrftoken"
    
    Returns:
        Response dict with sessions and session_uuids_to_forget
    """
    url = f"{BASE_URL}/get_my_chat_sessions_and_convert_anonymous_sessions"
    
    if known_uuids is None:
        known_uuids = []
    
    data = {
        "my_known_uuids": json.dumps(known_uuids)
    }
    
    response = requests.post(url, data=data, headers=DEFAULT_HEADERS, cookies=cookies)
    response.raise_for_status()
    
    return response.json()



if __name__ == "__main__":
    print("=" * 60)
    print("DeepAI Chat API Client")
    print("=" * 60)
    
    print("\n--- Các cách sử dụng ---\n")
    
    print("1. Login với email/password:")
    print("""
    client = DeepAIClient.login(
        email="your@email.com",
        password="yourpassword"
    )
    print(f"Đăng nhập thành công! API Key: {client.api_key}")
    """)
    
    print("2. Sử dụng API key có sẵn:")
    print("""
    client = DeepAIClient(api_key="your-api-key")
    """)
    
    print("3. Chat và tự động lưu:")
    print("""
    manager = ConversationManager(api_key=client.api_key)
    response = manager.send("Hello!")
    print(response)
    """)
    
    print("=" * 60)
    print("\nBạn có muốn đăng nhập và chat thử? (y/n): ", end="")
    
    try:
        choice = input().strip().lower()
        
        if choice == 'y':
            print("\n--- ĐĂNG NHẬP ---")
            email = input("Email: ").strip()
            password = input("Password: ").strip()
            
            print("\nĐang đăng nhập...")
            
            try:
                client = DeepAIClient.login(email=email, password=password)
                print(f"✓ Đăng nhập thành công!")
                print(f"  - Session ID: {client.session_id[:20]}..." if client.session_id else "  - No session")
                print(f"  - CSRF Token: {client.csrf_token[:20]}..." if client.csrf_token else "  - No CSRF")
                print(f"  - API Key: {client.api_key[:30]}..." if client.api_key else "  - No API key")
                
                # Tạo conversation manager
                manager = ConversationManager(
                    api_key=client.api_key,
                    session_id=client.session_id,
                    csrf_token=client.csrf_token
                )
                
                print("\n" + "=" * 60)
                print("CHAT VỚI DEEPAI")
                print("Gõ 'quit' để thoát, 'new' để bắt đầu cuộc trò chuyện mới")
                print("=" * 60)
                
                while True:
                    try:
                        user_input = input("\nYou: ").strip()
                        
                        if not user_input:
                            continue
                        
                        if user_input.lower() == 'quit':
                            print("Goodbye!")
                            break
                        
                        if user_input.lower() == 'new':
                            manager.new_conversation()
                            print("=== Bắt đầu cuộc trò chuyện mới ===")
                            continue
                        
                        print("Đang xử lý...")
                        response = manager.send(user_input)
                        print(f"\nAI: {response}")
                        print(f"\n[Đã lưu - Session: {manager.session_uuid}]")
                        
                    except KeyboardInterrupt:
                        print("\nGoodbye!")
                        break
                    except Exception as e:
                        print(f"Lỗi: {e}")
                        
            except Exception as e:
                print(f"✗ Đăng nhập thất bại: {e}")
        else:
            print("\nSử dụng các hàm trong module để bắt đầu:")
            print("  from deepai_api import DeepAIClient, ConversationManager")
            print("  client = DeepAIClient.login('email', 'password')")
            
    except EOFError:
        print("\n\nChạy script trực tiếp để sử dụng interactive mode.")
        print("Hoặc import module: from deepai_api import DeepAIClient")
