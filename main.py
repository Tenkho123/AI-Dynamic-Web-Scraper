from apify import Actor
from playwright.async_api import async_playwright
from openai import AsyncOpenAI
import json

async def main():
    async with Actor:
        # 1. Configuration
        url = 'https://www.demoblaze.com/'
        
        # ⚠️ PASTE YOUR OPENROUTER KEY HERE FOR NOW ⚠️
        # (Before we put this on GitHub, we will hide this key!)
        OPENROUTER_API_KEY = "YOUR_OPENROUTER_API_KEY_HERE"  # Replace with your key
        
        # Initialize the AI client pointing to OpenRouter
        ai_client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )

        Actor.log.info(f'Starting scraper for {url}')

        # 2. Scrape the messy raw text using Playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url)
            
            # Wait for the actual product cards to render, give it 15 seconds
            await page.wait_for_selector('.card', timeout=15000)
            
            # Now grab the text of the container
            raw_page_text = await page.locator('#tbodyid').inner_text()
            
            await browser.close()

        Actor.log.info('Scraped raw text. Sending to AI for processing...')

        # 3. Use AI to process the messy text into clean JSON
        ai_prompt = f"""
        You are a data extraction bot. I will give you raw text scraped from an e-commerce site. 
        Extract the products and return them as a valid JSON array containing objects with the keys: 
        "title", "price", and "description". Do not include any markdown formatting or extra text.
        
        Raw Text:
        {raw_page_text}
        """

        # A list of reliable free models to try automatically
        free_models = [
            "google/gemma-2-9b-it:free",
            "microsoft/phi-3-mini-128k-instruct:free",
            "meta-llama/llama-3.1-8b-instruct:free"
        ]

        ai_output = None
        
        # Loop through the models until one works
        for model_id in free_models:
            try:
                Actor.log.info(f'Trying AI model: {model_id}...')
                response = await ai_client.chat.completions.create(
                    model=model_id, 
                    messages=[{"role": "user", "content": ai_prompt}]
                )
                ai_output = response.choices[0].message.content.strip()
                Actor.log.info(f'Success with model: {model_id}!')
                break  # Exit the loop because we got an answer!
            except Exception as e:
                Actor.log.warning(f'Model {model_id} failed or is busy. Trying next...')

        if not ai_output:
            Actor.log.error("All free models are currently busy. Try running again in 5 minutes.")
            return

        # Strip out markdown formatting if the AI includes it
        if ai_output.startswith("```"):
            ai_output = ai_output.strip("`").replace("json\n", "", 1).strip()
        
        # 4. Save the AI-cleaned data
        try:
            clean_data = json.loads(ai_output)
            await Actor.push_data(clean_data)
            Actor.log.info('Successfully cleaned and saved data using AI! Check your Dataset tab!')
        except json.JSONDecodeError:
            Actor.log.error('AI did not return valid JSON. Here is what it returned:')
            Actor.log.error(ai_output)
            Actor.log.info('Successfully cleaned and saved data using AI!')
        except json.JSONDecodeError:
            Actor.log.error('AI did not return valid JSON. Here is what it returned:')
            Actor.log.error(ai_output)
