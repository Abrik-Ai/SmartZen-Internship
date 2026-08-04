from unittest.mock import MagicMock, patch

import psycopg
import pytest

from app.document_search_errors import (
    DocumentSearchConnectionError,
    DocumentSearchQueryError,
)
from app.rag.search import search_docs


@patch("app.rag.search.embed_text", return_value=[0.1, 0.2, 0.3])
def test_connection_error_is_translated(mock_embed: MagicMock) -> None:
    with patch(
        "app.rag.search.get_connection",
        side_effect=psycopg.OperationalError("connection failed"),
    ):
        with pytest.raises(DocumentSearchConnectionError):
            search_docs("test query")


@patch("app.rag.search.embed_text", return_value=[0.1, 0.2, 0.3])
def test_query_error_is_translated(mock_embed: MagicMock) -> None:
    mock_connection = MagicMock()
    mock_cursor = MagicMock()

    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = psycopg.DatabaseError("query failed")

    with patch(
        "app.rag.search.get_connection",
        return_value=mock_connection,
    ):
        with pytest.raises(DocumentSearchQueryError):
            search_docs("test query")