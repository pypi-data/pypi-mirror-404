"""
Documents resource for Nemati AI SDK.
"""

from typing import BinaryIO, List, Optional

from ..models.documents import Document, DocumentChatResponse


class Documents:
    """
    Documents resource for upload, conversion, and chat.
    
    Upload documents, convert between formats, and chat with your documents.
    
    Usage:
        # Upload document
        doc = client.documents.upload(file=open("report.pdf", "rb"))
        
        # Chat with document
        response = client.documents.chat(
            document_id=doc.id,
            message="What are the key findings?"
        )
    """
    
    def __init__(self, http_client):
        self._http = http_client
    
    def upload(
        self,
        file: BinaryIO,
        name: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs,
    ) -> Document:
        """
        Upload a document.
        
        Args:
            file: File object to upload.
            name: Optional name for the document.
            description: Optional description.
            **kwargs: Additional metadata.
        
        Returns:
            Document object with ID.
        
        Supported formats:
            PDF, DOCX, DOC, TXT, MD, HTML, CSV, XLSX, XLS
        
        Example:
            doc = client.documents.upload(
                file=open("report.pdf", "rb"),
                name="Q4 Report"
            )
            print(f"Uploaded: {doc.id}")
        """
        files = {"file": file}
        data = {**kwargs}
        
        if name:
            data["name"] = name
        if description:
            data["description"] = description
        
        response = self._http.request(
            "POST",
            "/documents/upload/",
            files=files,
            data=data,
        )
        return Document.from_dict(response.get("data", response))
    
    def list(
        self,
        limit: int = 20,
        offset: int = 0,
        **kwargs,
    ) -> List[Document]:
        """
        List uploaded documents.
        
        Args:
            limit: Maximum documents to return.
            offset: Number to skip.
            **kwargs: Additional filters.
        
        Returns:
            List of Document objects.
        """
        response = self._http.request(
            "GET",
            "/documents",
            params={"limit": limit, "offset": offset, **kwargs},
        )
        return [
            Document.from_dict(d)
            for d in response.get("data", response.get("documents", []))
        ]
    
    def get(self, document_id: str) -> Document:
        """
        Get a specific document.
        
        Args:
            document_id: The document ID.
        
        Returns:
            Document object.
        """
        response = self._http.request("GET", f"/documents/{document_id}")
        return Document.from_dict(response.get("data", response))
    
    def delete(self, document_id: str) -> bool:
        """
        Delete a document.
        
        Args:
            document_id: The document ID.
        
        Returns:
            True if deleted successfully.
        """
        self._http.request("DELETE", f"/documents/{document_id}")
        return True
    
    def chat(
        self,
        document_id: str,
        message: str,
        conversation_id: Optional[str] = None,
        **kwargs,
    ) -> DocumentChatResponse:
        """
        Chat with a document.
        
        Args:
            document_id: The document ID to chat with.
            message: Your question or message.
            conversation_id: Optional conversation ID to continue chat.
            **kwargs: Additional parameters.
        
        Returns:
            DocumentChatResponse with answer and sources.
        
        Example:
            response = client.documents.chat(
                document_id="doc_123",
                message="What are the main conclusions?"
            )
            print(response.answer)
            for source in response.sources:
                print(f"Page {source.page}: {source.text}")
        """
        payload = {
            "document_id": document_id,
            "message": message,
            **kwargs,
        }
        
        if conversation_id:
            payload["conversation_id"] = conversation_id
        
        response = self._http.request("POST", "/documents/chat/", json=payload)
        return DocumentChatResponse.from_dict(response.get("data", response))
    
    def convert(
        self,
        file: BinaryIO,
        output_format: str,
        **kwargs,
    ) -> "ConvertedDocument":
        """
        Convert a document to another format.
        
        Args:
            file: Source file to convert.
            output_format: Target format ('pdf', 'docx', 'txt', 'html', 'md').
            **kwargs: Additional options.
        
        Returns:
            ConvertedDocument with download URL.
        
        Example:
            converted = client.documents.convert(
                file=open("document.docx", "rb"),
                output_format="pdf"
            )
            converted.save("document.pdf")
        """
        files = {"file": file}
        data = {"output_format": output_format, **kwargs}
        
        response = self._http.request(
            "POST",
            "/documents/convert/",
            files=files,
            data=data,
        )
        return ConvertedDocument.from_dict(response.get("data", response))
    
    def extract_text(
        self,
        file: BinaryIO,
        **kwargs,
    ) -> str:
        """
        Extract text from a document.
        
        Args:
            file: File to extract text from.
            **kwargs: Additional options.
        
        Returns:
            Extracted text content.
        """
        files = {"file": file}
        
        response = self._http.request(
            "POST",
            "/documents/extract/",
            files=files,
            data=kwargs,
        )
        return response.get("data", response).get("text", "")


class ConvertedDocument:
    """Converted document result."""
    
    def __init__(
        self,
        url: str,
        format: str,
        size: int,
        content: Optional[bytes] = None,
    ):
        self.url = url
        self.format = format
        self.size = size
        self._content = content
    
    @classmethod
    def from_dict(cls, data: dict) -> "ConvertedDocument":
        return cls(
            url=data.get("url", ""),
            format=data.get("format", ""),
            size=data.get("size", 0),
            content=data.get("content"),
        )
    
    def save(self, path: str) -> None:
        """
        Save the converted document to a file.
        
        Args:
            path: File path to save to.
        """
        if self._content:
            with open(path, "wb") as f:
                f.write(self._content)
        else:
            import httpx
            response = httpx.get(self.url)
            with open(path, "wb") as f:
                f.write(response.content)
