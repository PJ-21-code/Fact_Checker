# Fake News Predictor - Project Guide

Welcome to the Fake News Predictor project! This guide will provide an overview of the project, explain the core technologies used, and detail the step-by-step workflow of how the application assesses claims in real-time.

## Project Overview

The Fake News Predictor is a web-based application designed to determine the credibility of news articles, social media posts, or general claims. Instead of relying solely on a static, pre-trained machine learning model, it leverages a **Retrieval-Augmented Generation (RAG)** approach. This means the system fetches real-time information from the web to give an up-to-date assessment using Large Language Models (LLMs).

## Core Technologies

Here is a breakdown of the primary libraries and technologies utilized in this project:

*   **Streamlit (`streamlit`)**: The framework used to build the interactive web frontend (`predictor_app.py`). It allows users to input text and displays the analysis results dynamically.
*   **Google GenAI SDK (`google-genai`)**: The official SDK used to communicate with Google's Gemini models (`gemini-2.5-flash`). It is responsible for both generating optimized search queries and performing the final structured analysis.
*   **DuckDuckGo Search (`duckduckgo-search`)**: The web scraping tool used to perform real-time searches. It pulls both latest news and general text results from the web to provide context to the LLM.
*   **Python Dotenv (`python-dotenv`)**: Used to securely load environment variables, specifically the `GEMINI_API_KEY`, from a local `.env` file.

## Step-by-Step Workflow

When a user pastes a claim into the application and clicks "Analyze Claim", the following sequence of events occurs:

### Step 1: User Input (Frontend)
The user interacts with the `predictor_app.py` Streamlit interface. The provided text is sent to the backend `FactCheckerRAG` class instantiated in `model.py`.

### Step 2: Search Query Generation
Instead of searching the web using the user's raw (and potentially long) text, the application first asks the `gemini-2.5-flash` model to distill the claim into a highly concise 3-4 word search query (including the current year for relevancy).

### Step 3: Real-Time Web Retrieval (The "R" in RAG)
The generated search query is passed to the `DuckDuckGo Search` tool (`self.search_web`). The tool searches for recent news articles and general web text, compiling the top results (titles, snippets, and URLs) into a "context string."

### Step 4: LLM Analysis (The "G" in RAG)
The application constructs a large prompt that includes:
1.  The user's original claim.
2.  The real-time context retrieved from DuckDuckGo.
3.  Instructions to act as an unbiased fact-checker and enforce a strict JSON output format.

This prompt is sent back to `gemini-2.5-flash`, which analyzes the provided context against the claim.

### Step 5: Structured Output
The Gemini model returns a structured JSON response containing:
*   **Credibility**: Categorized strictly as "Real News", "Fake News", "Unverified", or "Mixed".
*   **Confidence Score**: A numerical value reflecting certainty.
*   **Summary Points**: A detailed 3-point breakdown explaining the background, the evidence, and the conclusion.
*   **Sources**: URLs of the web pages used for the assessment.

### Step 6: UI Rendering
Streamlit receives the parsed JSON data and dynamically renders the results to the user. It uses different colors and icons (e.g., green for Real News, red for Fake News) and displays the summary bullets and source links for full transparency.
