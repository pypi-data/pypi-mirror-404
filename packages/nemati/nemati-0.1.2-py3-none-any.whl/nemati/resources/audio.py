"""
Audio resource for Nemati AI SDK.
"""

from typing import BinaryIO, Optional

from ..models.audio import SpeechResponse, TranscriptionResponse


class Audio:
    """
    Audio resource for text-to-speech and speech-to-text.
    
    Usage:
        # Text to speech
        audio = client.audio.speech.create(text="Hello world!")
        audio.save("hello.mp3")
        
        # Speech to text
        transcription = client.audio.transcribe(
            file=open("audio.mp3", "rb")
        )
        print(transcription.text)
    """
    
    def __init__(self, http_client):
        self._http = http_client
        self.speech = Speech(http_client)
    
    def transcribe(
        self,
        file: BinaryIO,
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        response_format: str = "json",
        temperature: float = 0.0,
        **kwargs,
    ) -> TranscriptionResponse:
        """
        Transcribe audio to text (speech-to-text).
        
        Args:
            file: Audio file object to transcribe.
                  Supported formats: mp3, mp4, mpeg, mpga, m4a, wav, webm.
            language: Language code (e.g., 'en', 'es'). If None, auto-detected.
            prompt: Optional prompt to guide transcription style.
            response_format: Output format ('json', 'text', 'srt', 'vtt').
            temperature: Sampling temperature (0-1).
            **kwargs: Additional parameters.
        
        Returns:
            TranscriptionResponse with transcribed text.
        
        Example:
            transcription = client.audio.transcribe(
                file=open("meeting.mp3", "rb"),
                language="en"
            )
            print(transcription.text)
        """
        files = {"file": file}
        data = {
            "response_format": response_format,
            "temperature": temperature,
            **kwargs,
        }
        
        if language:
            data["language"] = language
        if prompt:
            data["prompt"] = prompt
        
        response = self._http.request(
            "POST",
            "/audio/transcribe/",
            files=files,
            data=data,
        )
        return TranscriptionResponse.from_dict(response.get("data", response))
    
    def translate(
        self,
        file: BinaryIO,
        prompt: Optional[str] = None,
        response_format: str = "json",
        **kwargs,
    ) -> TranscriptionResponse:
        """
        Translate audio to English text.
        
        Args:
            file: Audio file object to translate.
            prompt: Optional prompt to guide translation style.
            response_format: Output format ('json', 'text', 'srt', 'vtt').
            **kwargs: Additional parameters.
        
        Returns:
            TranscriptionResponse with translated text.
        """
        files = {"file": file}
        data = {
            "response_format": response_format,
            **kwargs,
        }
        
        if prompt:
            data["prompt"] = prompt
        
        response = self._http.request(
            "POST",
            "/audio/translate/",
            files=files,
            data=data,
        )
        return TranscriptionResponse.from_dict(response.get("data", response))


class Speech:
    """Text-to-speech functionality."""
    
    def __init__(self, http_client):
        self._http = http_client
    
    def create(
        self,
        text: str,
        voice: str = "alloy",
        model: str = "tts-1",
        speed: float = 1.0,
        response_format: str = "mp3",
        **kwargs,
    ) -> SpeechResponse:
        """
        Convert text to speech.
        
        Args:
            text: The text to convert to speech.
            voice: Voice to use. Options vary by model:
                   - 'alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer'
            model: TTS model ('tts-1' or 'tts-1-hd').
            speed: Speaking speed (0.25-4.0). Default is 1.0.
            response_format: Output format ('mp3', 'opus', 'aac', 'flac').
            **kwargs: Additional parameters.
        
        Returns:
            SpeechResponse with audio data.
        
        Example:
            audio = client.audio.speech.create(
                text="Welcome to Nemati AI!",
                voice="nova",
                speed=1.1
            )
            audio.save("welcome.mp3")
        """
        payload = {
            "text": text,
            "voice": voice,
            "model": model,
            "speed": speed,
            "response_format": response_format,
            **kwargs,
        }
        
        response = self._http.request("POST", "/audio/speech/", json=payload)
        return SpeechResponse.from_dict(response.get("data", response))
