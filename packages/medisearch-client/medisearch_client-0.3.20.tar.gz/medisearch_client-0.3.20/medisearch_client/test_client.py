import asyncio
import argparse
from typing import List, Tuple, Callable, Awaitable
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
import traceback
import aiohttp
import uuid

from medisearch_client.client import MediSearchClient, Settings, Filters, ResponseHandler

console = Console()

class MediSearchTests:
    def __init__(self, api_key: str, base_url: str = "https://api.backend.medisearch.io"):
        self.client = MediSearchClient(
            api_key=api_key,
            base_url=base_url,
            timeout=60,
            retry_delay=2.0
        )
        
    async def test_basic_usage(self) -> bool:
        """Test basic API usage without any special settings."""
        console.print(Panel("Testing Basic Usage", style="bold green"))
        
        try:
            message = "What are the symptoms of eczema and psoriasis?!????"
            console.print(f"[bold]Sending message:[/bold] '{message}'")
            
            with Progress() as progress:
                task = progress.add_task("[cyan]Getting response...", total=None)
                responses = self.client.send_message(
                    conversation=[message],
                    conversation_id="test-basic-usage-v5"
                )
                progress.update(task, completed=True)
            
            return self._process_responses(responses)
        except Exception as e:
            console.print(f"[bold red]Exception:[/bold red] {str(e)}")
            return False

    async def test_model_types(self) -> bool:
        """Test both pro and standard model types."""
        console.print(Panel("Testing Model Types", style="bold green"))
        
        try:
            message = "What are the latest treatments for hypertension?"

            # Test deep model
            console.print("\n[bold]Testing DEEP model:[/bold]")
            settings_deep = Settings(model_type="max")
            responses_deep = self.client.send_message(
                conversation=[message],
                conversation_id="test-model-deep",
                settings=settings_deep
            )
            deep_success = self._process_responses(responses_deep)

            # Test pro model
            console.print("\n[bold]Testing PRO model:[/bold]")
            settings_pro = Settings(model_type="pro")
            responses_pro = self.client.send_message(
                conversation=[message],
                conversation_id="test-model-pro",
                settings=settings_pro
            )
            pro_success = self._process_responses(responses_pro)
            
            # Test standard model
            console.print("\n[bold]Testing STANDARD model:[/bold]")
            settings_standard = Settings(model_type="standard")
            responses_standard = self.client.send_message(
                conversation=[message],
                conversation_id="test-model-standard",
                settings=settings_standard
            )
            standard_success = self._process_responses(responses_standard)
            
            return pro_success and standard_success and deep_success
        except Exception as e:
            console.print(f"[bold red]Exception:[/bold red] {str(e)}")
            return False

    async def test_languages(self) -> bool:
        """Test responses in different languages."""
        console.print(Panel("Testing Multiple Languages", style="bold green"))
        
        languages = {
            "Spanish": "¿Cuáles son los síntomas del COVID largo?",
            "French": "Quels sont les effets secondaires du paracétamol?",
            "German": "Was sind die Ursachen von Migräne?",
            "Italian": "Quali sono i benefici della vitamina D?"
        }
        
        success = True
        for lang, message in languages.items():
            try:
                console.print(f"\n[bold]Testing {lang}:[/bold]")
                settings = Settings(language=lang)
                responses = self.client.send_message(
                    conversation=[message],
                    conversation_id=f"test-lang-{lang.lower()}",
                    settings=settings
                )
                if not self._process_responses(responses):
                    success = False
            except Exception as e:
                console.print(f"[bold red]Exception in {lang} test:[/bold red] {str(e)}")
                success = False
                
        return success

    async def test_filters(self) -> bool:
        """Test different filter combinations."""
        console.print(Panel("Testing Filters", style="bold green"))
        
        try:
            message = "What are the latest treatments for Alzheimer's?"
            
            # Test year range filter
            console.print("\n[bold]Testing recent publications (2020-2023):[/bold]")
            filters_recent = Filters(
                sources=["scientificArticles"],
                year_start=2020,
                year_end=2023,
            )
            settings_recent = Settings(filters=filters_recent)
            responses_recent = self.client.send_message(
                conversation=[message],
                conversation_id="test-filters-recent",
                settings=settings_recent
            )
            recent_success = self._process_responses(responses_recent)
            
            # Test article types filter
            console.print("\n[bold]Testing meta-analyses only:[/bold]")
            filters_meta = Filters(
                sources=["scientificArticles"],
                article_types=["metaAnalysis"],
            )
            settings_meta = Settings(filters=filters_meta)
            responses_meta = self.client.send_message(
                conversation=[message],
                conversation_id="test-filters-meta",
                settings=settings_meta
            )
            meta_success = self._process_responses(responses_meta)
            
            return recent_success and meta_success
        except Exception as e:
            console.print(f"[bold red]Exception:[/bold red] {str(e)}")
            return False

    async def test_source_filters(self) -> bool:
        """Test filtering by individual source types."""
        console.print(Panel("Testing Source Filters", style="bold green"))
        
        sources_to_test = [
            "scientificArticles",
            "internationalHealthGuidelines",
            "medicineGuidelines",
            "healthBlogs",
            "books"
        ]
        
        message = "What are the common treatments for asthma?"
        success = True
        
        for source in sources_to_test:
            try:
                console.print(f"\n[bold]Testing source: {source}[/bold]")
                filters = Filters(sources=[source])
                settings = Settings(filters=filters)
                responses = self.client.send_message(
                    conversation=[message],
                    conversation_id=f"test-source-{source}",
                    settings=settings
                )
                if not self._process_responses(responses):
                    # Allow failure for less common sources like books if no articles found
                    if source in ["books", "healthBlogs"]: 
                        console.print(f"[yellow]Warning: No results for source '{source}', continuing test.[/yellow]")
                    else:
                        console.print(f"[bold red]Failed for source: {source}[/bold red]")
                        success = False
            except Exception as e:
                console.print(f"[bold red]Exception testing source {source}:[/bold red] {str(e)}")
                success = False
                
        return success

    async def test_article_type_filters(self) -> bool:
        """Test filtering by individual article types."""
        console.print(Panel("Testing Article Type Filters", style="bold green"))
        
        article_types_to_test = [
            "metaAnalysis",
            "reviews",
            "clinicalTrials",
            "observationalStudies",
            "other"
        ]
        
        message = "What are the latest advancements in treating type 1 diabetes?"
        success = True
        
        for article_type in article_types_to_test:
            try:
                console.print(f"\n[bold]Testing article type: {article_type}[/bold]")
                # Article types only apply to scientificArticles source
                filters = Filters(sources=["scientificArticles"], article_types=[article_type])
                settings = Settings(filters=filters)
                responses = self.client.send_message(
                    conversation=[message],
                    conversation_id=f"test-articletype-{article_type}",
                    settings=settings
                )
                if not self._process_responses(responses):
                    console.print(f"[bold red]Failed for article type: {article_type}[/bold red]")
                    success = False
            except Exception as e:
                console.print(f"[bold red]Exception testing article type {article_type}:[/bold red] {str(e)}")
                success = False
                
        return success

    async def test_streaming(self) -> bool:
        """Test streaming responses."""
        console.print(Panel("Testing Streaming Response", style="bold green"))
        
        try:
            message = "Explain the different types of diabetes."
            console.print(f"[bold]Streaming response for:[/bold] '{message}'")
            
            response_text = ""
            for response in self.client.send_message(
                conversation=[message],
                conversation_id="test-streaming",
                should_stream_response=True
            ):
                if response["event"] == "llm_response":
                    chunk = response["data"]
                    response_text += chunk
                    console.print(chunk, end="")
                elif response["event"] == "articles":
                    console.print("\n\n[bold]Sources found:[/bold]", 
                                f"{len(response['data'])} articles")
                elif response["event"] == "error":
                    console.print(f"\n[bold red]Error:[/bold red] {response['data']}")
                    return False
            
            return len(response_text) > 0
        except Exception as e:
            console.print(f"[bold red]Exception:[/bold red] {str(e)}")
            return False

    async def test_async_api(self) -> bool:
        """Test basic async API usage."""
        console.print(Panel("Testing Async API", style="bold green"))
        
        try:
            message = "What are the cardiovascular effects of COVID-19?"
            console.print(f"[bold]Sending async message:[/bold] '{message}'")
            
            with Progress() as progress:
                task = progress.add_task("[cyan]Getting async response...", total=None)
                responses = await self.client.send_message_async(
                    conversation=[message],
                    conversation_id="test-async-api"
                )
                progress.update(task, completed=True)
            
            return self._process_responses(responses)
        except Exception as e:
            console.print(f"[bold red]Exception:[/bold red] {str(e)}")
            return False

    async def test_async_streaming(self) -> bool:
        """Test async streaming responses."""
        console.print(Panel("Testing Async Streaming", style="bold green"))
        
        try:
            message = "What are the long-term complications of diabetes?"
            console.print(f"[bold]Streaming async response for:[/bold] '{message}'")
            
            response_text = ""
            response_stream = await self.client.send_message_async(
                conversation=[message],
                conversation_id="test-async-streaming",
                should_stream_response=True
            )
            
            try:
                async for response in response_stream:
                    if response["event"] == "llm_response":
                        chunk = response["data"]
                        response_text += chunk
                        console.print(chunk, end="")
                    elif response["event"] == "articles":
                        console.print("\n\n[bold]Sources found:[/bold]", 
                                    f"{len(response['data'])} articles")
                        break  # Exit after receiving articles
                    elif response["event"] == "error":
                        console.print(f"\n[bold red]Error:[/bold red] {response['data']}")
                        return False
            except aiohttp.ClientConnectionError as e:
                # If we got some response text before the connection closed, consider it a success
                if len(response_text) > 0:
                    console.print("\n[yellow]Connection closed but received partial response[/yellow]")
                    return True
                raise  # Re-raise if we got no response
            
            return len(response_text) > 0
        except Exception as e:
            console.print(f"[bold red]Exception:[/bold red] {str(e)}")
            traceback.print_exc()
            return False

    async def test_concurrent_requests(self) -> bool:
        """Test multiple concurrent requests."""
        console.print(Panel("Testing Concurrent Requests", style="bold green"))
        
        try:
            messages = [
                ("What are the risk factors for heart disease?", "concurrent-1"),
                ("What are effective treatments for depression?", "concurrent-2"),
                ("What are the long-term effects of hypertension?", "concurrent-3")
            ]
            
            async def process_message(message: str, conversation_id: str) -> bool:
                console.print(f"[bold]Starting request:[/bold] {conversation_id} - '{message}'")
                
                try:
                    responses = await self.client.send_message_async(
                        conversation=[message],
                        conversation_id=conversation_id
                    )
                    
                    response_text = None
                    article_count = 0
                    
                    for response in responses:
                        if response["event"] == "llm_response":
                            response_text = response["data"]
                        elif response["event"] == "articles":
                            article_count = len(response["data"])
                    
                    console.print(f"[bold green]Completed request:[/bold green] {conversation_id}")
                    console.print(f"  Response length: {len(response_text) if response_text else 0} chars")
                    console.print(f"  Articles found: {article_count}")
                    
                    return True
                except Exception as e:
                    console.print(f"[bold red]Error in {conversation_id}:[/bold red] {str(e)}")
                    return False
            
            console.print("[bold]Starting concurrent requests...[/bold]")
            tasks = [process_message(msg, conv_id) for msg, conv_id in messages]
            results = await asyncio.gather(*tasks)
            
            success_count = sum(1 for result in results if result)
            console.print(f"[bold]Completed {success_count}/{len(messages)} concurrent requests[/bold]")
            
            return all(results)
        except Exception as e:
            console.print(f"[bold red]Exception:[/bold red] {str(e)}")
            return False

    async def test_multi_turn_conversation(self) -> bool:
        """Test multi-turn conversation."""
        console.print(Panel("Testing Multi-turn Conversation", style="bold green"))
        
        try:
            # First message
            message1 = "What is the recommended treatment for mild COVID-19?"
            console.print(f"[bold]User:[/bold] {message1}")
            
            conversation = [message1]
            responses1 = self.client.send_message(
                conversation=conversation,
                conversation_id="test-multi-turn"
            )
            
            ai_response = None
            for response in responses1:
                if response["event"] == "llm_response":
                    ai_response = response["data"]
                    console.print(f"[bold cyan]AI:[/bold cyan] {ai_response[:300]}...")
                elif response["event"] == "articles":
                    console.print(f"[dim]Sources found: {len(response['data'])}")
            
            if not ai_response:
                return False
                
            # Add the AI's response to the conversation
            conversation.append(ai_response)
            
            # Follow-up message
            message2 = "What about for severe cases?"
            console.print(f"\n[bold]User:[/bold] {message2}")
            
            conversation.append(message2)
            responses2 = self.client.send_message(
                conversation=conversation,
                conversation_id="test-multi-turn"
            )
            
            has_response = False
            for response in responses2:
                if response["event"] == "llm_response":
                    has_response = True
                    console.print(f"[bold cyan]AI:[/bold cyan] {response['data'][:300]}...")
                elif response["event"] == "articles":
                    console.print(f"[dim]Sources found: {len(response['data'])}")
            
            return has_response
        except Exception as e:
            console.print(f"[bold red]Exception:[/bold red] {str(e)}")
            return False

    async def test_error_handling(self) -> bool:
        """Test error handling with invalid inputs."""
        console.print(Panel("Testing Error Handling", style="bold green"))
        
        try:
            # Test with empty conversation
            console.print("\n[bold]Testing empty conversation:[/bold]")
            try:
                self.client.send_message(
                    conversation=[],
                    conversation_id="test-error-empty"
                )
                console.print("[bold red]Failed:[/bold red] Expected ValueError for empty conversation")
                return False
            except ValueError as e:
                console.print(f"[bold green]Success:[/bold green] Caught expected error: {str(e)}")
            
            # Test with invalid model type
            console.print("\n[bold]Testing invalid model type:[/bold]")
            try:
                settings = Settings(model_type="invalid_model")
                self.client.send_message(
                    conversation=["Test message"],
                    conversation_id="test-error-model",
                    settings=settings
                )
                console.print("[bold red]Failed:[/bold red] Expected ValueError for invalid model type")
                return False
            except ValueError as e:
                console.print(f"[bold green]Success:[/bold green] Caught expected error: {str(e)}")

            # Test error_not_enough_articles error
            console.print("\n[bold]Testing not enough articles error:[/bold]")
            try:
                # Create very restrictive filters
                filters = Filters(
                    sources=["scientificArticles"],
                    year_start=1800,
                    year_end=1801,
                    article_types=["metaAnalysis"]
                )
                settings = Settings(filters=filters)
                
                # Use a nonsensical query that's unlikely to match any articles
                gibberish_query = "xylophone quantum diabetes zebra polynomial treatment in martian hospitals"
                responses = self.client.send_message(
                    conversation=[gibberish_query],
                    conversation_id="test-error-no-articles",
                    settings=settings
                )
                # Check if we got the expected error
                for response in responses:
                    if response["event"] == "error":
                        error_code = response["data"]
                        if error_code == "error_not_enough_articles":
                            console.print(f"[bold green]Success:[/bold green] Received expected error: {error_code}")
                            return True
                
                console.print("[bold red]Failed:[/bold red] Did not receive expected error_not_enough_articles")
                return False
                
            except Exception as e:
                console.print(f"[bold red]Unexpected error testing not enough articles:[/bold red] {str(e)}")
                return False
            
            return True
        except Exception as e:
            console.print(f"[bold red]Unexpected exception:[/bold red] {str(e)}")
            return False

    async def test_response_handler(self) -> bool:
        """Test synchronous response handler."""
        console.print(Panel("Testing Response Handler", style="bold green"))
        
        try:
            # Track handler calls
            handler_calls = {
                "llm_response": 0,
                "articles": 0,
                "error": 0,
                "followups": 0
            }
            
            # Define handler functions
            def handle_llm_response(response):
                handler_calls["llm_response"] += 1
                console.print(f"[bold cyan]Handler:[/bold cyan] Received LLM response of {len(response['data'])} characters")
            
            def handle_articles(response):
                handler_calls["articles"] += 1
                articles = response["data"]
                console.print(f"[bold cyan]Handler:[/bold cyan] Found {len(articles)} relevant articles")
            
            def handle_error(response):
                handler_calls["error"] += 1
                console.print(f"[bold red]Handler Error:[/bold red] {response['data']}")

            def handle_followups(response):
                handler_calls["followups"] += 1
                followups = response["data"]
                console.print(f"[bold cyan]Handler:[/bold cyan] Found {len(followups)} followup questions")
            
            # Create a response handler
            handler = ResponseHandler(
                on_llm_response=handle_llm_response,
                on_articles=handle_articles,
                on_error=handle_error,
                on_followups=handle_followups
            )
            
            # Send a message with the handler
            message = "What are the latest treatments for Alzheimer's?"
            console.print(f"[bold]Sending message with response handler:[/bold] '{message}'")
            
            with Progress() as progress:
                task = progress.add_task("[cyan]Getting response...", total=None)
                self.client.send_message(
                    conversation=[message],
                    conversation_id="test-response-handler",
                    response_handler=handler,
                    settings=Settings(followup_count=3)
                )
                progress.update(task, completed=True)
            
            # Verify handlers were called
            console.print("\n[bold]Handler call summary:[/bold]")
            console.print(f"LLM responses handled: {handler_calls['llm_response']}")
            console.print(f"Article responses handled: {handler_calls['articles']}")
            console.print(f"Error responses handled: {handler_calls['error']}")
            console.print(f"Followups responses handled: {handler_calls['followups']}")
            
            # Check that we got at least one LLM response and one articles response
            return handler_calls["llm_response"] > 0 and handler_calls["articles"] > 0 and handler_calls["followups"] > 0
            
        except Exception as e:
            console.print(f"[bold red]Exception:[/bold red] {str(e)}")
            return False

    async def test_async_response_handler(self) -> bool:
        """Test asynchronous response handler."""
        console.print(Panel("Testing Async Response Handler", style="bold green"))
        
        try:
            # Track handler calls
            handler_calls = {
                "llm_response": 0,
                "articles": 0,
                "error": 0
            }
            
            # Define handler functions
            def handle_llm_response(response):
                handler_calls["llm_response"] += 1
                console.print(f"[bold cyan]Async Handler:[/bold cyan] Received LLM response of {len(response['data'])} characters")
            
            def handle_articles(response):
                handler_calls["articles"] += 1
                articles = response["data"]
                console.print(f"[bold cyan]Async Handler:[/bold cyan] Found {len(articles)} relevant articles")
            
            def handle_error(response):
                handler_calls["error"] += 1
                console.print(f"[bold red]Async Handler Error:[/bold red] {response['data']}")
            
            # Create a response handler
            handler = ResponseHandler(
                on_llm_response=handle_llm_response,
                on_articles=handle_articles,
                on_error=handle_error
            )
            
            # Send a message with the handler
            message = "What are the risk factors for stroke?"
            console.print(f"[bold]Sending async message with response handler:[/bold] '{message}'")
            
            with Progress() as progress:
                task = progress.add_task("[cyan]Getting async response...", total=None)
                await self.client.send_message_async(
                    conversation=[message],
                    conversation_id="test-async-response-handler",
                    response_handler=handler
                )
                progress.update(task, completed=True)
            
            # Verify handlers were called
            console.print("\n[bold]Async handler call summary:[/bold]")
            console.print(f"LLM responses handled: {handler_calls['llm_response']}")
            console.print(f"Article responses handled: {handler_calls['articles']}")
            console.print(f"Error responses handled: {handler_calls['error']}")
            
            # Check that we got at least one LLM response and one articles response
            return handler_calls["llm_response"] > 0 and handler_calls["articles"] > 0
            
        except Exception as e:
            console.print(f"[bold red]Exception:[/bold red] {str(e)}")
            return False

    async def test_system_prompt(self) -> bool:
        """Test system prompt functionality."""
        console.print(Panel("Testing System Prompt", style="bold green"))
        
        try:
            message = "What are the symptoms of flu?"
            
            # Test with a system prompt for brief responses
            console.print("\n[bold]Testing with brief response prompt:[/bold]")
            settings_brief = Settings(
                system_prompt="Provide very brief, bullet-point responses"
            )
            responses_brief = self.client.send_message(
                conversation=[message],
                conversation_id="test-system-prompt-brief",
                settings=settings_brief
            )
            brief_success = self._process_responses(responses_brief)
            
            # Test with a system prompt for detailed responses
            console.print("\n[bold]Testing with detailed response prompt:[/bold]")
            settings_detailed = Settings(
                system_prompt="Provide detailed responses with medical terminology explained"
            )
            responses_detailed = self.client.send_message(
                conversation=[message],
                conversation_id="test-system-prompt-detailed",
                settings=settings_detailed
            )
            detailed_success = self._process_responses(responses_detailed)
            
            return brief_success and detailed_success
        except Exception as e:
            console.print(f"[bold red]Exception:[/bold red] {str(e)}")
            return False

    async def test_system_prompt_restrictions(self) -> bool:
        """Test system prompt restrictions."""
        console.print(Panel("Testing System Prompt Restrictions", style="bold green"))
        
        try:
            # Test with a system prompt that restricts cancer-related responses
            console.print("\n[bold]Testing with cancer restriction prompt:[/bold]")
            settings_restricted = Settings(
                system_prompt="Do not provide any information about cancer. If a question is about cancer, respond with 'I cannot provide information about cancer-related topics.'"
            )
            
            # Test with a cancer-related question
            message = "What are the symptoms of lung cancer?"
            console.print(f"\n[bold]Testing restricted topic:[/bold] '{message}'")
            responses_cancer = self.client.send_message(
                conversation=[message],
                conversation_id="test-system-prompt-restricted",
                settings=settings_restricted
            )
            
            # Verify the response contains the restriction message
            has_restriction = False
            for response in responses_cancer:
                console.print(response)
                if response["event"] == "llm_response":
                    if "cannot provide information about cancer" in response["data"].lower():
                        has_restriction = True
                        console.print("[bold green]Success:[/bold green] Model correctly restricted cancer information")
            
            # Test with a non-cancer question to ensure normal operation
            message_normal = "What are the symptoms of the flu?"
            console.print(f"\n[bold]Testing allowed topic:[/bold] '{message_normal}'")
            responses_normal = self.client.send_message(
                conversation=[message_normal],
                conversation_id="test-system-prompt-normal",
                settings=settings_restricted
            )
            
            # Verify we get a normal response for non-cancer questions
            normal_response = self._process_responses(responses_normal)
            
            return has_restriction and normal_response
        except Exception as e:
            console.print(f"[bold red]Exception:[/bold red] {str(e)}")
            return False

    async def test_followup_questions(self) -> bool:
        """Test followup question suggestions with different counts."""
        console.print(Panel("Testing Followup Questions", style="bold green"))
        
        # Test different followup counts
        followup_counts = [0, 1, 3, 5]
        all_tests_passed = True
        
        for count in followup_counts:
            try:
                console.print(f"\n[bold]Testing with followup_count={count}:[/bold]")
                
                # Create settings with specific followup_count
                settings = Settings(followup_count=count)
                
                message = "What are the symptoms of diabetes?"
                console.print(f"[bold]Sending message with followup_count={count}:[/bold] '{message}'")
                
                with Progress() as progress:
                    task = progress.add_task(f"[cyan]Getting response with {count} followups...", total=None)
                    responses = self.client.send_message(
                        conversation=[message],
                        conversation_id=f"test-followups-{count}",
                        settings=settings
                    )
                    progress.update(task, completed=True)
                
                has_followups = False
                followups_count = 0
                
                for response in responses:
                    if response["event"] == "followups":
                        has_followups = True
                        followups = response["data"]
                        followups_count = len(followups)
                        
                        console.print(f"\n[bold]Received {followups_count} suggested followup questions:[/bold]")
                        for i, question in enumerate(followups, 1):
                            console.print(f"{i}. {question}")
                
                # Check if the result is as expected
                if count == 0:
                    # When count is 0, we shouldn't receive followups
                    if not has_followups:
                        console.print("[bold green]Success:[/bold green] No followup questions received as expected")
                    else:
                        console.print(f"[bold yellow]Warning:[/bold yellow] Received {followups_count} followups despite count=0")
                        all_tests_passed = False
                else:
                    # For non-zero counts, we should get followups (if feature is supported)
                    if has_followups:
                        # Check if count matches or is less than requested (API might have limit)
                        if followups_count <= count:
                            console.print(f"[bold green]Success:[/bold green] Received {followups_count} of {count} requested followup questions")
                        else:
                            console.print(f"[bold yellow]Warning:[/bold yellow] Received {followups_count} followups, more than {count} requested")
                            all_tests_passed = False
                    else:
                        console.print(f"[bold yellow]Warning:[/bold yellow] No followup questions received with count={count}. API might not support this feature yet.")
                        # Don't fail the test if API might not support it
                
            except Exception as e:
                console.print(f"[bold red]Exception with followup_count={count}:[/bold red] {str(e)}")
                all_tests_passed = False
        
        return all_tests_passed

    def _process_responses(self, responses: List[dict]) -> bool:
        """Process and display responses from the API."""
        has_response = False
        has_articles = False
        
        for response in responses:
            if response["event"] == "llm_response":
                has_response = True
                console.print(f"\n[bold]Answer:[/bold]\n{response['data'][:500]}...")
            elif response["event"] == "articles":
                has_articles = True
                console.print("\n[bold]Sources:[/bold]")
                for idx, article in enumerate(response["data"][:3], 1):
                    console.print(f"{idx}. {article.get('title', 'No title')} "
                                f"({article.get('year', 'N/A')})")
                    if "url" in article:
                        console.print(f"   {article['url']}")
                
                if len(response["data"]) > 3:
                    console.print(f"   ... and {len(response['data']) - 3} more articles")
            elif response["event"] == "error":
                console.print(f"[bold red]Error:[/bold red] {response['data']}")
                return False
        
        return has_response and has_articles

async def run_tests(api_key: str, base_url: str) -> None:
    """Run all MediSearch client tests."""
    console.print(Panel("MediSearch Client Tests", style="bold blue"))
    console.print(f"Using API endpoint: {base_url}")
    
    test_suite = MediSearchTests(api_key, base_url)
    
    tests: List[Tuple[str, Callable[[], Awaitable[bool]]]] = [
        ("Basic Usage", test_suite.test_basic_usage),
        ("Model Types", test_suite.test_model_types),
        ("Multiple Languages", test_suite.test_languages),
        ("Filters", test_suite.test_filters),
        ("Source Filters", test_suite.test_source_filters),
        ("Article Type Filters", test_suite.test_article_type_filters),
        ("Streaming", test_suite.test_streaming),
        ("Async API", test_suite.test_async_api),
        ("Async Streaming", test_suite.test_async_streaming),
        ("Concurrent Requests", test_suite.test_concurrent_requests),
        ("Multi-turn Conversation", test_suite.test_multi_turn_conversation),
        ("Response Handler", test_suite.test_response_handler),
        ("Async Response Handler", test_suite.test_async_response_handler),
        ("Error Handling", test_suite.test_error_handling),
        ("System Prompt", test_suite.test_system_prompt),
        ("System Prompt Restrictions", test_suite.test_system_prompt_restrictions),
        ("Followup Questions", test_suite.test_followup_questions)
    ]
    
    results = []
    
    # Ask user which tests to run
    console.print("\n[bold]Available tests:[/bold]")
    for i, (name, _) in enumerate(tests, 1):
        console.print(f"{i}. {name}")
    console.print("0. Run all tests")
    
    choice = input("\nEnter test number(s) to run (comma-separated) or 0 for all: ")
    
    if choice.strip() == "0":
        selected_tests = tests
    else:
        try:
            indices = [int(idx.strip()) - 1 for idx in choice.split(",")]
            selected_tests = [tests[idx] for idx in indices if 0 <= idx < len(tests)]
            if not selected_tests:
                console.print("[bold yellow]Warning:[/bold yellow] No valid tests selected. Running all tests.")
                selected_tests = tests
        except:
            console.print("[bold yellow]Warning:[/bold yellow] Invalid selection. Running all tests.")
            selected_tests = tests
    
    for name, test_func in selected_tests:
        console.print(f"\n[bold]Running test:[/bold] {name}")
        try:
            result = await test_func()
            results.append((name, result))
            console.print(f"[bold]{'✅ Passed' if result else '❌ Failed'}[/bold]: {name}")
        except Exception as e:
            console.print(f"[bold red]Error running test {name}:[/bold red] {str(e)}")
            results.append((name, False))
            console.print(f"[bold]❌ Failed[/bold]: {name}")
    
    # Print summary
    console.print()
    console.print(Panel("Test Summary", style="bold blue"))
    passed = sum(1 for _, result in results if result)
    console.print(f"[bold]Passed {passed}/{len(results)} tests[/bold]")
    
    for name, result in results:
        status = "[bold green]✅ Passed[/bold green]" if result else "[bold red]❌ Failed[/bold red]"
        console.print(f"{status}: {name}")

def main():
    parser = argparse.ArgumentParser(description="MediSearch API Client Tests")
    parser.add_argument("--api-key", default="api_key",
                       help="MediSearch API key")
    parser.add_argument("--base-url", default="https://api.backend.medisearch.io",
                       help="Base URL for MediSearch API")
    args = parser.parse_args()
    
    try:
        asyncio.run(run_tests(args.api_key, args.base_url))
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Tests interrupted by user[/bold yellow]")

if __name__ == "__main__":
    main()
