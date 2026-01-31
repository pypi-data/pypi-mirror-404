"""Files resource for Agent Berlin SDK."""

import mimetypes
import os
from typing import Optional

from .._http import HTTPClient
from ..models.files import FileUploadResponse


class FilesResource:
    """Resource for file upload operations.

    Files are stored in cloud storage with automatic deletion after 30 days.
    Useful for workflow outputs like CSV exports, reports, or generated content.

    Example:
        # Upload from file path
        result = client.files.upload(file_path="output.csv")
        print(f"File ID: {result.file_id}")

        # Upload from bytes
        result = client.files.upload(
            file_data=b"Hello, World!",
            filename="hello.txt",
            content_type="text/plain"
        )
    """

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def upload(
        self,
        *,
        file_path: Optional[str] = None,
        file_data: Optional[bytes] = None,
        filename: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> FileUploadResponse:
        """Upload a file to cloud storage.

        Files are automatically deleted after 30 days.

        Args:
            file_path: Path to the file to upload. If provided, filename and
                content_type are auto-detected from the path.
            file_data: Raw bytes to upload. Requires filename to be specified.
            filename: Filename for the uploaded file. Required if using file_data,
                optional if using file_path (defaults to basename of path).
            content_type: MIME type of the file. Auto-detected if not provided.
                Allowed types: text/plain, text/csv, text/markdown, text/html,
                text/css, text/javascript, application/json, application/xml

        Returns:
            FileUploadResponse with file_id and metadata.

        Raises:
            ValueError: If neither file_path nor file_data is provided,
                or if file_data is provided without filename.
            AgentBerlinAPIError: On API errors.
        """
        if file_path is None and file_data is None:
            raise ValueError("Either file_path or file_data must be provided")

        if file_data is not None and filename is None:
            raise ValueError("filename is required when using file_data")

        # Read file data if path provided
        if file_path is not None:
            with open(file_path, "rb") as f:
                file_data = f.read()
            if filename is None:
                filename = os.path.basename(file_path)

        # Auto-detect content type
        if content_type is None and filename is not None:
            content_type, _ = mimetypes.guess_type(filename)
            if content_type is None:
                content_type = "application/octet-stream"

        # Upload via HTTP client
        data = self._http.upload_file(
            "/files/upload",
            file_data=file_data,
            filename=filename,
            content_type=content_type,
        )
        return FileUploadResponse.model_validate(data)
