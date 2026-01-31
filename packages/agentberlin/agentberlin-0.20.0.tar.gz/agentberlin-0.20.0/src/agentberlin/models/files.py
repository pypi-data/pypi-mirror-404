"""Pydantic models for Files API responses."""

from pydantic import BaseModel


class FileMetadata(BaseModel):
    """Metadata about an uploaded file."""

    filename: str
    content_type: str
    size_bytes: int
    uploaded_at: str
    expires_at: str


class FileUploadResponse(BaseModel):
    """Response for file upload."""

    success: bool
    file_id: str
    url: str  # Full CloudFront URL to access the file
    metadata: FileMetadata
