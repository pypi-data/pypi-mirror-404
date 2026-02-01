"""
Dastavez - Document AI + Browser Agents API.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

if TYPE_CHECKING:
    from rotavision.client import Rotavision


class Dastavez:
    """
    Dastavez API client for document processing and browser automation.

    Usage:
        from rotavision import Rotavision

        client = Rotavision(api_key="rv_...")

        result = client.dastavez.extract(
            document=document_bytes,
            document_type="aadhaar",
            mask_pii=True
        )
    """

    def __init__(self, client: "Rotavision"):
        self._client = client

    def extract(
        self,
        document: Union[bytes, str],
        document_type: Optional[str] = None,
        extract_fields: Optional[List[str]] = None,
        language: str = "auto",
        mask_pii: bool = False,
    ) -> Dict[str, Any]:
        """
        Extract structured data from Indian documents.

        Args:
            document: Document as bytes or base64 string
            document_type: Document type (aadhaar, pan, driving_license, invoice, etc.)
            extract_fields: Specific fields to extract
            language: Expected language or "auto" for detection
            mask_pii: Whether to mask PII in response

        Returns:
            Extracted fields with confidence scores
        """
        raise NotImplementedError("Coming soon. Contact developers@rotavision.com")

    def ocr(
        self,
        image: Union[bytes, str],
        languages: Optional[List[str]] = None,
        output_format: str = "text",
    ) -> Dict[str, Any]:
        """
        Multi-script OCR supporting 22 Indian languages.

        Args:
            image: Image as bytes or base64 string
            languages: Expected languages (hi, ta, en, etc.)
            output_format: Output format (text, blocks, hocr)

        Returns:
            Extracted text with language and confidence info
        """
        raise NotImplementedError("Coming soon. Contact developers@rotavision.com")

    def agent(
        self,
        task: str,
        url: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        max_steps: int = 10,
    ) -> Dict[str, Any]:
        """
        Run a browser automation agent.

        Args:
            task: Natural language task description
            url: Starting URL (optional)
            context: Additional context for the agent
            max_steps: Maximum number of browser actions

        Returns:
            Agent execution result with actions taken
        """
        raise NotImplementedError("Coming soon. Contact developers@rotavision.com")
