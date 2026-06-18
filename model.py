from google import genai
from google.genai import types
from duckduckgo_search import DDGS
from google.genai.errors import APIError
import json
import re
from datetime import datetime
import time

class FactCheckerRAG:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        # Using gemini-2.5-flash for faster real-time generation
        self.model_name = 'gemini-2.5-flash'
        self.ddgs = DDGS()

    def _generate_with_retry(self, prompt, model_name, config=None, max_retries=3):
        """Internal method to handle API retries with exponential backoff."""
        delay = 1
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config # Pass the config for JSON formatting later
                )
                return response
            except APIError as e:
                if e.code in [503, 429] and attempt < max_retries - 1:
                    print(f"Server busy (Status {e.code}). Retrying in {delay} seconds...")
                    time.sleep(delay)
                    delay *= 2
                else:
                    raise e

    def _generate_with_fallback(self, prompt, config=None):
        """Internal method to try 2.5-flash first, then fallback to 1.5-flash."""
        try:
            print("Attempting with gemini-2.5-flash...")
            return self._generate_with_retry(prompt, model_name="gemini-2.5-flash", config=config)
        except APIError as e:
            if e.code == 503:
                print("gemini-2.5-flash unavailable. Falling back to gemini-1.5-flash...")
                return self._generate_with_retry(prompt, model_name="gemini-1.5-flash", config=config)
            else:
                raise e

    def search_web(self, query: str, max_results=5):
        """Retrieves raw search results to form the context for the Generator."""
        try:
            results = []
            
            # Fetch news for the latest context
            try:
                news_res = self.ddgs.news(query, max_results=max_results)
                if news_res:
                    results.extend(news_res)
            except Exception:
                pass
                
            # Fetch standard text search
            try:
                text_res = self.ddgs.text(query, max_results=max_results)
                if text_res:
                    results.extend(text_res)
            except Exception:
                pass
                
            if not results:
                return "No relevant search results found on the web."
            
            context = ""
            seen_urls = set()
            count = 0
            for res in results:
                if count >= max_results:
                    break
                url = res.get('href') or res.get('url')
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                
                context += f"[Source {count+1}]: {res.get('title')}\n"
                if res.get('date'):
                    context += f"Date: {res.get('date')}\n"
                context += f"Snippet: {res.get('body')}\n"
                context += f"URL: {url}\n\n"
                count += 1
                
            if not context.strip():
                return "No relevant search results found on the web."
                
            return context
        except Exception as e:
            return f"Error retrieving search context: {str(e)}"

    def analyze_claim(self, claim: str) -> dict:
        """
        The main RAG pipeline:
        1. Formulates a search query.
        2. Retrieves context via Web Search.
        3. Prompts LLM to analyze the context against the claim.
        """
        try:
            current_date = datetime.now().strftime("%B %d, %Y")
            current_year = datetime.now().year

            # 1. Generate an optimal search query from the claim
            search_query_response = self.client.models.generate_content(
                model=self.model_name,
                contents=f"Today's date is {current_date}. Given the following claim, generate a VERY concise 3-4 word google search query to verify if it is true. Explicitly include the year {current_year} in the search query to ensure finding the latest news if the claim is about a recent event. Output only the search query. Claim: {claim}"
            )
            search_query = search_query_response.text.strip()
            # Remove any quotes if LLM added them
            search_query = search_query.replace('"', '').replace("'", "")
            
            # 2. Retrieve real-time information
            context = self.search_web(search_query, max_results=4)
            
            # 3. Analyze the claim with the retrieved context
            analysis_prompt = f"""
            You are an expert, unbiased fact-checker and journalist. 
            Today's date is {current_date}. You must evaluate the claim based on the most recent information available up to this date.
            A user has submitted the following claim for verification:
            ---
            CLAIM: "{claim}"
            ---
            
            Here is the real-time context retrieved from the web (DuckDuckGo search results):
            ---
            CONTEXT:
            {context}
            ---
            
            Based on the context provided (AND your own internal knowledge if the search context is empty, errors out, or is insufficient), determine the credibility of the claim.
            The credibility field MUST exactly match one of these values: "Real News", "Fake News", "Unverified", or "Mixed".
            Note: Even if the claim is a well-known fact (like who is the Prime Minister of a country) or extremely simple, you MUST provide a full, detailed evaluation in the "summary_points" field. DO NOT leave the summary_points blank or give a brief answer.
            
            Respond in valid JSON format ONLY, without any markdown formatting or code blocks.
            Follow this exact JSON structure:
            {{
                "credibility": "Real News",
                "confidence_score": 0,
                "summary_points": [
                    "First detailed point explaining the background/context.",
                    "Second detailed point providing evidence that verifies or debunks the claim.",
                    "Third point concluding on the overall truthfulness."
                ],
                "sources": ["<url1>", "<url2>", ...]
            }}
            """
            
            analysis_response = self.client.models.generate_content(
                model=self.model_name,
                contents=analysis_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                )
            )
            raw_text = analysis_response.text.strip()
            
            return json.loads(raw_text)
            
        except json.JSONDecodeError as e:
            return {
                "credibility": "Error parsing results",
                "confidence_score": 0,
                "summary_points": [
                    f"Failed to parse LLM response format: {str(e)}",
                    f"Raw output: {analysis_response.text}"
                ],
                "sources": []
            }
        except Exception as e:
            return {
                "credibility": "System Error",
                "confidence_score": 0,
                "summary_points": [
                    f"An error occurred during analysis: {str(e)}"
                ],
                "sources": []
            }
