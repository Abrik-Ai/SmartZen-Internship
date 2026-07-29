from app.rag.search import search_docs


def documentation_search(query: str) -> list[dict]:
    """
    Search the university's documentation and help guides.

    Call this when the user asks:
    - how to do something
    - what a feature means
    - how the system works
    - where a documented feature is explained

    Do NOT call this for:
    - schedules
    - room occupancy
    - active sessions
    - user-specific information

    Those should be answered by dedicated tools.
    """

    return search_docs(query)