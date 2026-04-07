import google.generativeai as genai
from duckduckgo_search import DDGS
import json
import re

class FactCheckerRAG:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        # Using gemini-1.5-flash for faster real-time generation, 
        # but you can upgrade to gemini-1.5-pro for higher reasoning.
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.ddgs = DDGS()

    def search_web(self, query: str, max_results=5):
        """Retrieves raw search results to form the context for the Generator."""
        try:
            results = self.ddgs.text(query, max_results=max_results)
            if not results:
                return "No relevant search results found on the web."
            
            context = ""
            for i, res in enumerate(results):
                context += f"[Source {i+1}]: {res.get('title')}\n"
                context += f"Snippet: {res.get('body')}\n"
                context += f"URL: {res.get('href')}\n\n"
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
            # 1. Generate an optimal search query from the claim
            search_query_response = self.model.generate_content(
                f"Given the following claim, generate a VERY concise 3-4 word google search query to verify if it is true. Output only the search query. Claim: {claim}"
            )
            search_query = search_query_response.text.strip()
            # Remove any quotes if LLM added them
            search_query = search_query.replace('"', '').replace("'", "")
            
            # 2. Retrieve real-time information
            context = self.search_web(search_query, max_results=4)
            
            # 3. Analyze the claim with the retrieved context
            analysis_prompt = f"""
            You are an expert, unbiased fact-checker and journalist. 
            A user has submitted the following claim for verification:
            ---
            CLAIM: "{claim}"
            ---
            
            Here is the real-time context retrieved from the web (DuckDuckGo search results):
            ---
            CONTEXT:
            {context}
            ---
            
            Based ONLY on the context provided, determine the credibility of the claim.
            Respond in valid JSON format ONLY, without any markdown formatting or code blocks.
            Follow this exact JSON structure:
            {{
                "credibility": "Real News | Fake News | Unverified | Mixed",
                "confidence_score": <int between 0 and 100>,
                "summary": "<A detailed 2-3 paragraph summary explaining the facts, highlighting any discrepancies, and concluding on the truthfulness of the claim.>",
                "sources": ["<url1>", "<url2>", ...]
            }}
            """
            
            analysis_response = self.model.generate_content(analysis_prompt)
            raw_text = analysis_response.text.strip()
            
            # Cleanup potential markdown JSON wrappers
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
                
            return json.loads(raw_text.strip())
            
        except json.JSONDecodeError as e:
            return {
                "credibility": "Error parsing results",
                "confidence_score": 0,
                "summary": f"Failed to parse LLM response format: {str(e)}\n\nRaw output: {analysis_response.text}",
                "sources": []
            }
        except Exception as e:
            return {
                "credibility": "System Error",
                "confidence_score": 0,
                "summary": f"An error occurred during analysis: {str(e)}",
                "sources": []
            }
