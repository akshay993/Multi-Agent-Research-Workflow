import arxiv
import wikipedia
from tavily import TavilyClient

from config import settings

_tavily_client = (
    TavilyClient(settings.tavily_api_key) if settings.tavily_api_key else None
)


def tavily_search_tool(query: str, max_results: int = 3):
    """Search the web using Tavily and return top results with url, title, and content.

    Args:
        query (str): The search query to send to Tavily.
        max_results (int): Maximum number of results to return. Defaults to 3.

    Returns:
        list[dict]: Each dict contains 'url', 'title', and 'content'.
            On failure, returns [{'error': str}].
    """
    if _tavily_client is None:
        return [{"error": "Tavily API key not configured"}]
    try:
        response = _tavily_client.search(
            query=query, search_depth="basic", max_results=max_results
        )

        output = []

        for result in response.get("results", []):
            output.append(
                {
                    "url": result.get("url", ""),
                    "title": result.get("title", ""),
                    "content": result.get("content", ""),
                }
            )

        return output

    except Exception as exception:
        return [{"error": str(exception)}]  # For LLM-friendly agents


def arxiv_search_tool(query: str, max_results: int = 3):
    """Search arXiv for academic papers and return title, summary, url, and published date.

    Args:
        query (str): The search query to send to arXiv.
        max_results (int): Maximum number of papers to return. Defaults to 3.

    Returns:
        list[dict]: Each dict contains 'title', 'summary', 'url', and 'published'.
            On failure, returns [{'error': str}].
    """
    try:
        client = arxiv.Client()
        search = arxiv.Search(query=query, max_results=max_results)

        output = []
        for result in client.results(search):
            output.append(
                {
                    "title": result.title,
                    "summary": result.summary,
                    "url": result.entry_id,
                    "published": str(result.published.date()),
                }
            )

        return output

    except Exception as exception:
        return [{"error": str(exception)}]


def wikipedia_search_tool(query: str, max_results: int = 2, sentences: int = 2):
    """Search Wikipedia and return title, summary, and url for the top matching pages.

    Args:
        query (str): The search query to send to Wikipedia.
        max_results (int): Maximum number of pages to return. Defaults to 3.
        sentences (int): Number of sentences to include in each page summary. Defaults to 2.

    Returns:
        list[dict]: Each dict contains 'title', 'summary', and 'url'.
            On failure, returns [{'error': str}].
    """
    try:
        titles = wikipedia.search(query, results=max_results)

        output = []
        for title in titles:
            try:
                page = wikipedia.page(title)
                output.append(
                    {
                        "title": page.title,
                        "summary": page.summary,
                        "url": page.url,
                    }
                )
            except wikipedia.exceptions.DisambiguationError:
                continue
            except wikipedia.exceptions.PageError:
                continue

        return output

    except Exception as exception:
        return [{"error": str(exception)}]
