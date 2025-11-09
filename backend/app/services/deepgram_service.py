"""
Deepgram service for audio transcription.

This service handles both:
1. Live audio streaming transcription (WebSocket)
2. Pre-recorded file transcription (REST API)

Requires DEEPGRAM_API_KEY in environment variables.
"""

import os
from typing import Dict, Any
from deepgram import DeepgramClient


class DeepgramService:
    """Service for handling Deepgram transcription operations."""
    
    def __init__(self):
        """Initialize Deepgram service (client created lazily on first use)."""
        self._client = None  # Lazy initialization
        # Don't cache API key - read it fresh each time from environment

    @property
    def api_key(self):
        """Get API key from environment (fresh read each time)."""
        return os.getenv("DEEPGRAM_API_KEY")
    
    @property
    def client(self):
        """Lazy-load Deepgram client on first use."""
        # Always recreate client to get fresh API key from environment
        if not self.api_key:
            raise ValueError(
                "DEEPGRAM_API_KEY not found in environment variables. "
                "Please add it to your .env file."
            )
        print(f"[Deepgram] Initializing client with key: {self.api_key[:8] if self.api_key else 'None'}...")
        self._client = DeepgramClient(api_key=self.api_key)
        print("[Deepgram] Client initialized successfully")
        return self._client

    def _ensure_client(self):
        """Ensure client is initialized before use."""
        # Trigger lazy initialization by accessing the property
        _ = self.client
    
    def transcribe_file(
        self, 
        file_content: bytes, 
        mimetype: str = "audio/wav"
    ) -> Dict[str, Any]:
        """
        Transcribe a pre-recorded audio file.
        
        Args:
            file_content: Audio file bytes
            mimetype: MIME type of the audio file (e.g., 'audio/wav', 'audio/mp3')
        
        Returns:
            Dict containing transcript and metadata
        """
        self._ensure_client()
        
        try:
            print(f"Transcribing {len(file_content)} bytes of audio...")
            
            # Transcribe using Deepgram v5 API (synchronous call)
            # v5 API structure: client.listen.v1.media.transcribe_file()
            response = self.client.listen.v1.media.transcribe_file(
                request=file_content,
                model="nova-2",
                smart_format=True,
                diarize=True,
                punctuate=True,
                paragraphs=True,
                utterances=True,
                language="en"
            )
            
            print("Deepgram response received")
            print(f"Response type: {type(response)}")
            
            # Parse response - v5 uses object attributes, not dict
            if not response.results or not response.results.channels:
                return {
                    "success": False,
                    "error": "No transcription results returned"
                }
            
            channel = response.results.channels[0]
            if not channel.alternatives:
                return {
                    "success": False,
                    "error": "No transcript alternatives found"
                }
            
            alternative = channel.alternatives[0]
            transcript_text = alternative.transcript or ""
            
            print(f"Transcript length: {len(transcript_text)} characters")
            
            # Build simplified response with just the essentials
            transcript_data = {
                "transcript": transcript_text,
                "metadata": {
                    "duration": getattr(response.metadata, "duration", 0) if response.metadata else 0,
                    "channels": getattr(response.metadata, "channels", 1) if response.metadata else 1,
                },
            }
            
            return {
                "success": True,
                "data": transcript_data,
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    def get_client(self) -> DeepgramClient:
        """
        Get Deepgram client for live streaming.
        
        Returns:
            DeepgramClient instance
        """
        return self.client
    
    def get_api_key(self) -> str:
        """Get the API key for client-side usage (WebSocket)."""
        return self.api_key


# Singleton instance
deepgram_service = DeepgramService()

