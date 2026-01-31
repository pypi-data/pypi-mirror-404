"""MediSearch API client code.

This module provides a client for the MediSearch API, which allows users to search
for medical information using natural language queries. The client supports both
synchronous and asynchronous communication with the API, as well as streaming and
non-streaming responses.

Examples:
    Basic usage:
        ```python
        client = MediSearchClient(api_key="your_api_key")
        response = client.send_message(
            conversation=["What are the symptoms of diabetes?"],
            conversation_id="unique-id"
        )
        
        for item in response:
            if item["event"] == "llm_response":
                print(f"Answer: {item['data']}")
            elif item["event"] == "articles":
                print(f"Sources: {item['data']}")
            elif item["event"] == "followups":
                print(f"Suggested follow-up questions: {item['data']}")
        ```
    
    Streaming response:
        ```python
        filters = Filters(
            sources=["scientificArticles", "healthBlogs"],
            year_start=2020,
            article_types=["metaAnalysis", "reviews"]
        )
        settings = Settings(language="Spanish", filters=filters)
        
        for response in client.send_message(
            conversation=["¿Cuáles son los tratamientos para la hipertensión?"],
            settings=settings,
            should_stream_response=True
        ):
            if response["event"] == "llm_response":
                print(f"Streaming answer: {response['data']}")
            elif response["event"] == "articles":
                print(f"Sources: {response['data']}")
            elif response["event"] == "followups":
                print(f"You might also want to ask: {response['data']}")
        ```
        
    With response handler:
        ```python
        def handle_llm_response(response):
            print(f"AI response: {response['data']}")
        
        def handle_articles(response):
            print(f"Found {len(response['data'])} relevant articles")
            for article in response['data']:
                print(f"- {article['title']}")
        
        def handle_followups(response):
            print("Suggested follow-up questions:")
            for i, question in enumerate(response['data'], 1):
                print(f"{i}. {question}")
        
        def handle_error(response):
            print(f"Error: {response['data']}")
        
        handler = ResponseHandler(
            on_llm_response=handle_llm_response,
            on_articles=handle_articles,
            on_followups=handle_followups,
            on_error=handle_error
        )
        
        client.send_message(
            conversation=["What are the latest treatments for Alzheimer's?"],
            response_handler=handler
        )
        ```
"""

from collections.abc import AsyncGenerator, Callable, Generator
import json
import time
from typing import Any

import aiohttp
import requests


class Filters:
    """Filters for controlling the MediSearch API search behavior."""

    VALID_SOURCES = [
        "scientificArticles",
        "internationalHealthGuidelines",
        "medicineGuidelines",
        "healthBlogs",
        "books"
    ]

    VALID_ARTICLE_TYPES = [
        "metaAnalysis",
        "reviews",
        "clinicalTrials",
        "observationalStudies",
        "other"
    ]

    def __init__(
        self,
        sources: list[str] | None = None,
        year_start: int | None = None,
        year_end: int | None = None,
        article_types: list[str] | None = None,
    ):
        """Initialize Filters with the given parameters.
        
        Args:
            sources: List of source types to search
            year_start: Start year for filtering articles
            year_end: End year for filtering articles
            article_types: Types of articles to include in search results
        """
        self.sources = sources or [
            "scientificArticles",
            "internationalHealthGuidelines",
            "medicineGuidelines",
            "healthBlogs",
            "books",
        ]
        self.article_types = article_types or [
            "metaAnalysis",
            "reviews",
            "clinicalTrials",
            "observationalStudies",
            "other",
        ]

        self._validate_article_types(self.article_types, self.sources)

        self.year_start = year_start
        self.year_end = year_end

    def _validate_sources(self, sources: list[str]) -> None:
        """Validate the sources list."""
        if not sources:
            raise ValueError("At least one source must be specified")

        invalid_sources = [s for s in sources if s not in self.VALID_SOURCES]
        if invalid_sources:
            raise ValueError(
                f"Invalid sources: {invalid_sources}. Valid sources are: {self.VALID_SOURCES}")

    def _validate_article_types(self, article_types: list[str], sources: list[str]) -> None:
        """Validate the article types list."""
        if "scientificArticles" in sources and not article_types:
            raise ValueError(
                "At least one article type must be specified when scientificArticles is selected")

        invalid_types = [t for t in article_types if t not in self.VALID_ARTICLE_TYPES]
        if invalid_types:
            raise ValueError(
                f"Invalid article types: {invalid_types}. Valid types are: {self.VALID_ARTICLE_TYPES}")

    def to_dict(self) -> dict[str, Any]:
        """Convert the filters to a dictionary for API requests."""
        return {
            "sources": self.sources,
            "year_start": self.year_start,
            "year_end": self.year_end,
            "article_types": self.article_types,
        }


class Settings:
    """Settings for the MediSearch API."""

    VALID_MODEL_TYPES = ["pro", "standard", "max_lightning", "max_deep", "max", "lightning"]

    def __init__(
        self,
        language: str = "English",
        filters: Filters | None = None,
        model_type: str = "pro",
        system_prompt: str | None = None,
        followup_count: int | None = None,
    ):
        """Initialize Settings with the given parameters.
        
        Args:
            language: Expected language of the response
            filters: Filters to apply to the search
            model_type: Type of model to use ("pro" or "standard")
            system_prompt: Optional system prompt to adjust response style
            followup_count: Number of follow-up questions to generate (if supported)
        """
        self._validate_model_type(model_type)

        self.language = language
        self.filters = filters or Filters()
        self.model_type = model_type
        self.system_prompt = system_prompt
        self.followup_count = followup_count

    def _validate_model_type(self, model_type: str) -> None:
        """Validate the model type."""
        if model_type not in self.VALID_MODEL_TYPES:
            raise ValueError(
                f"Invalid model type: {model_type}. Must be one of: {self.VALID_MODEL_TYPES}")

    def to_dict(self) -> dict[str, Any]:
        """Convert the settings to a dictionary for API requests."""
        settings_dict: dict[str, Any] = {
            "language": self.language,
            "model_type": self.model_type,
            "filters": self.filters.to_dict(),
        }
        if self.system_prompt is not None:
            settings_dict["system_prompt"] = self.system_prompt
        if self.followup_count is not None:
            settings_dict["followup_count"] = self.followup_count
        return settings_dict


class ResponseHandler:
    """Handler for processing MediSearch API responses."""

    def __init__(
        self,
        on_llm_response: Callable[[dict[str, Any]], None] | None = None,
        on_articles: Callable[[dict[str, Any]], None] | None = None,
        on_followups: Callable[[dict[str, Any]], None] | None = None,
        on_error: Callable[[dict[str, Any]], None] | None = None,
    ):
        """Initialize the response handler.
        
        Args:
            on_llm_response: Callback for handling llm_response events
            on_articles: Callback for handling articles events
            on_followups: Callback for handling followups events
            on_error: Callback for handling error events
        """
        self.on_llm_response = on_llm_response
        self.on_articles = on_articles
        self.on_followups = on_followups
        self.on_error = on_error

    def handle_response(self, response: dict[str, Any]) -> None:
        """Handle a response from the MediSearch API."""
        event = response.get("event")
        handlers = {
            "llm_response": self.on_llm_response,
            "articles": self.on_articles,
            "followups": self.on_followups,
            "error": self.on_error,
        }

        if handler := handlers.get(event):
            handler(response)


class MediSearchClient:
    """Client for the MediSearch API."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.backend.medisearch.io",
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: int = 300
    ):
        """Initialize the MediSearch client.
        
        Args:
            api_key: API key for authentication
            base_url: Base URL of the MediSearch API
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retry attempts in seconds
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.sse_endpoint = f"{self.base_url}/sse/medichat"
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout

    def send_message(
        self,
        conversation: list[str],
        conversation_id: str,
        settings: Settings | None = None,
        should_stream_response: bool = False,
        response_handler: ResponseHandler | None = None,
    ) -> Generator[dict[str, Any], None, None] | list[dict[str, Any]]:
        """Send a message to the MediSearch API.
        
        Args:
            conversation: The conversation history as a list of strings where user and AI messages alternate.
                          The last message must be from the user.
            conversation_id: Unique ID for the conversation
            settings: Settings for the conversation. If not provided, default settings will be used.
            should_stream_response: Whether to stream the response
            response_handler: Handler for processing responses
            
        Returns:
            If should_stream_response is True, a generator of responses. 
            Otherwise, a list of responses.
        """
        if not conversation:
            raise ValueError("Conversation cannot be empty.")

        if settings is None:
            settings = Settings()

        payload = self._create_payload(conversation, conversation_id, settings)
        sse_client = self._create_sse_connection(payload)
        response_iter = self._response_iterator(sse_client)

        # Apply response handler if set
        if response_handler:
            def handled_response_iter():
                for response in response_iter:
                    response_handler.handle_response(response)
                    yield response

            if should_stream_response:
                return handled_response_iter()
            else:
                responses = list(handled_response_iter())
        else:
            if should_stream_response:
                return response_iter
            else:
                responses = list(response_iter)

        # For non-streaming responses, filter all but the last llm_response
        return self._filter_llm_responses(responses)


    async def send_message_async(
        self,
        conversation: list[str],
        conversation_id: str,
        settings: Settings | None = None,
        should_stream_response: bool = False,
        response_handler: ResponseHandler | None = None,
    ) -> AsyncGenerator[dict[str, Any], None] | list[dict[str, Any]]:
        """Send a message to the MediSearch API asynchronously.
        
        Args:
            conversation: The conversation history as a list of strings
            conversation_id: Unique ID for the conversation
            settings: Settings for the conversation
            should_stream_response: Whether to stream the response
            response_handler: Handler for processing responses
            
        Returns:
            If should_stream_response is True, an async generator of responses. 
            Otherwise, a list of responses.
        """
        if not conversation:
            raise ValueError("Conversation cannot be empty.")

        if settings is None:
            settings = Settings()

        payload = self._create_payload(conversation, conversation_id, settings)
        
        timeout = aiohttp.ClientTimeout(
            total=self.timeout * 3,
            sock_read=self.timeout * 5,
            sock_connect=self.timeout
        )
        
        session = aiohttp.ClientSession()
        
        try:
            response = await session.post(
                self.sse_endpoint,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream",
                    "Connection": "keep-alive"
                },
                json=payload,
                timeout=timeout
            )
            
            if response.status != 200:
                error_text = await response.text()
                await session.close()
                raise RuntimeError(f"Failed to connect to MediSearch API: {response.status} - {error_text}")

            async def process_event(event: str) -> dict[str, Any] | None:
                """Process a single SSE event and return the parsed result."""
                if not event or not event.startswith("data: "):
                    return None
                    
                try:
                    content = event[6:]  # Remove 'data: ' prefix
                    data = json.loads(content)
                    
                    event_type = data.get("event")
                    if event_type == "llm_response":
                        return {"event": "llm_response", "data": data.get("data", "")}
                    elif event_type == "articles":
                        return {"event": "articles", "data": data.get("data", [])}
                    elif event_type == "followups":
                        return {"event": "followups", "data": data.get("data", [])}
                    elif event_type == "error":
                        return {"event": "error", "data": data.get("data", "unknown_error")}
                except json.JSONDecodeError:
                    return None
                
                return None

            async def stream_generator():
                buffer = ""
                try:
                    async for chunk in response.content:
                        chunk_text = chunk.decode("utf-8", errors="ignore")
                        buffer += chunk_text
                        
                        events = buffer.split("\n")
                        if len(events) <= 1:
                            continue
                            
                        complete_events = events[:-1]
                        buffer = events[-1]
                        
                        for event in complete_events:
                            result = await process_event(event.strip())
                            if result:
                                if response_handler:
                                    response_handler.handle_response(result)
                                yield result
                                
                                if result["event"] in ["error"]:
                                    return
                finally:
                    await response.release()
                    await session.close()

            if should_stream_response:
                return stream_generator()
            
            # For non-streaming mode, collect all responses
            all_responses = []
            async for result in stream_generator():
                all_responses.append(result)
            return self._filter_llm_responses(all_responses)
                
        except Exception as e:
            await session.close()
            raise RuntimeError(f"Error in async request: {str(e)}")

    def _create_payload(
        self,
        conversation: list[str],
        conversation_id: str,
        settings: Settings,
    ) -> dict[str, Any]:
        """Create a payload for the MediSearch API.
        
        Args:
            conversation: The conversation history
            conversation_id: Unique ID for the conversation
            settings: Settings for the conversation
            
        Returns:
            Dictionary payload for the API request
        """
        return {
            "event": "user_message",
            "conversation": conversation,
            "key": self.api_key,
            "id": conversation_id,
            "settings": settings.to_dict()
        }

    def _create_sse_connection(
        self,
        payload: dict[str, Any],
        retries: int = 0,
    ) -> requests.Response:
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "Connection": "keep-alive"
        }

        try:
            response = requests.post(
                self.sse_endpoint,
                headers=headers,
                json=payload,
                stream=True,
                timeout=(self.timeout, 14400),  # (connect timeout, read timeout) matching K8s config
                verify=True  # Ensure SSL verification is enabled
            )
            
            if response.status_code != 200:
                error_message = f"Failed to connect to MediSearch API: {response.status_code}"
                try:
                    error_details = response.json()
                    error_message += f" - {json.dumps(error_details)}"
                except Exception:
                    error_message += f" - {response.text}"
                    
                # Log the full URL that was attempted
                error_message += f"\nAttempted URL: {self.sse_endpoint}"
                # Log request headers
                error_message += f"\nRequest headers: {headers}"
                
                raise RuntimeError(error_message)
                
            return response

        except requests.exceptions.SSLError as e:
            raise RuntimeError(f"SSL Error connecting to MediSearch API: {str(e)}")
        except requests.exceptions.ConnectionError as e:
            raise RuntimeError(f"Connection Error: {str(e)}")
        except Exception as e:
            if retries < self.max_retries:
                time.sleep(self.retry_delay)
                return self._create_sse_connection(payload, retries + 1)
            raise RuntimeError(
                f"Failed to connect to MediSearch API after {self.max_retries} attempts: {str(e)}")
    
    def _response_iterator(
        self,
        response: requests.Response,
    ) -> Generator[dict[str, Any], None, None]:
        """Parse SSE response and yield complete events.
        
        Args:
            response: Streaming response from the MediSearch API
            
        Yields:
            Parsed JSON data from the SSE events
        """
        try:
            buffer = ""  # Buffer to accumulate incomplete events
            
            # Process the streaming response with explicit chunk encoding error handling
            while True:
                try:
                    # Read chunks with explicit error handling
                    for chunk in response.iter_content(chunk_size=1024):
                      
                        if not chunk:
                            continue
                            
                        # Decode the chunk
                        try:
                            chunk_text = chunk.decode('utf-8')
                        except UnicodeDecodeError:
                            # Skip chunks that can't be decoded
                            continue
                            
                        buffer += chunk_text
                        
                        # Process complete events (those containing newlines)
                        events = buffer.split('\n')
                        
                        # If we only have one event (or none), continue accumulating
                        if len(events) <= 1:
                            continue
                            
                        # Process all events except potentially the last one
                        complete_events = events[:-1]
                        buffer = events[-1]  # Keep the last part in buffer
                        
                        for event in complete_events:
                            event = event.strip()
                            if not event:
                                continue

                            if event.startswith('data: '):
                                try:
                                    content = event[6:]  # Remove 'data: ' prefix
                                    data = json.loads(content)
                                    
                                    # Map the response structure to match our expected format
                                    event_type = data.get('event')
                                    if event_type == 'llm_response':
                                        yield {"event": "llm_response", "data": data.get("data", '')}
                                    elif event_type == 'articles':
                                        yield {"event": "articles", "data": data.get("data", [])}
                                    elif event_type == 'followups':
                                        yield {"event": "followups", "data": data.get("data", [])}
                                    elif event_type == 'error':
                                        yield {"event": "error", "data": data.get("data", 'unknown_error')}
                                    
                                    # Stop processing after terminal events
                                    if event_type in ["error"]:
                                        return
                                        
                                except json.JSONDecodeError:
                                    # Skip malformed JSON
                                    continue
                    break  # Exit the while loop if no ChunkedEncodingError occurs
                    
                except requests.exceptions.ChunkedEncodingError as e:
                    # If we get an invalid chunk, try to continue processing
                    continue
                except requests.exceptions.RequestException as e:
                    # Handle other request-related errors
                    raise RuntimeError(f"Request error: {str(e)}")
        
        except Exception as e:
            raise RuntimeError(f"Error processing SSE stream: {str(e)}")
        finally:
            # Ensure proper cleanup
            response.close()


    def _filter_llm_responses(
        self,
        responses: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Remove all but the last llm_response event from the responses.
        
        Args:
            responses: List of responses from the MediSearch API
            
        Returns:
            Filtered list of responses
        """
        seen_llm_response = False
        filtered_responses = []

        for resp in reversed(responses):
            if resp["event"] == "llm_response" and not seen_llm_response:
                seen_llm_response = True
                filtered_responses.append(resp)
            elif resp["event"] != "llm_response":
                filtered_responses.append(resp)

        return list(reversed(filtered_responses))
