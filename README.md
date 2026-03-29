AI-Driven E-Commerce Scraper
A Python-based scraper built on the Apify platform. It uses Playwright to extract raw, unstructured text from JavaScript-rendered dynamic websites (like Demoblaze) and pipes the raw DOM data into OpenRouter's LLMs (Mistral/Llama/Gemma) to structure it into clean, valid JSON.

Key Features:

Handles dynamic JS loading with targeted Playwright DOM timeouts.

Implements automated LLM fallback routing to bypass API rate limits.

Outputs clean JSON arrays ready for data analysis.
