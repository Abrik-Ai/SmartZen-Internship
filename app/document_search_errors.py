class DocumentSearchError(Exception):
    """Base class for document search errors."""


class DocumentSearchConnectionError(DocumentSearchError):
    """Raised when the document-search database cannot be reached."""


class DocumentSearchQueryError(DocumentSearchError):
    """Raised when a document-search query fails."""