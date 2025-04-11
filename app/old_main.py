import os
import yaml
import asyncio
import httpx
import logging
import requests
from fastapi import FastAPI, HTTPException, Request
from typing import Dict, Any
import openai
from openai import AzureOpenAI
import aiofiles
from fastapi.middleware.cors import CORSMiddleware

# configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_token():
    """
    Generate an OAUYH2 token using client credentials to be used for OpenAI API.
    """
    token_url = "your_token_url"
    client_id = "your_client_id"
    client_secret = "your_client_secret"

    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "Mulescale"
    }

    try:
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        token_data = response.json()
        access_token = token_data["access_token"]
        return access_token
    except requests.exceptions.RequestException as e:
        logger.error(f"Error generating token: {e}")
        raise HTTPException(status_code=500, detail="Error generating token")
    
# Load configuration from YAML file
CONFIG_FILE = "app/prompt_config.yaml"
PROMPT_CONFIG = {}

def load_config():
    """
    Load the prompt configuration from a YAML file.
    """
    global PROMPT_CONFIG
    try:
        with open(CONFIG_FILE, 'r') as file:
            PROMPT_CONFIG = yaml.safe_load(file)
        if not PROMPT_CONFIG or 'topics' not in PROMPT_CONFIG:
            print(f"Error: Config file '{CONFIG_FILE}' is empty or missing 'topics' key.")
            PROMPT_CONFIG = {'topics': {}}
    except FileNotFoundError:
        print(f"Error: Config file '{CONFIG_FILE}' not found.")
        PROMPT_CONFIG = {'topics': {}}
    except yaml.YAMLError as e:
        print(f"Error: Failed to parse YAML file '{CONFIG_FILE}': {e}")
        PROMPT_CONFIG = {'topics': {}}


async def read_prompt_file(file_path: str) -> str:
    """
    Read the prompt from a file asynchronously.
    """
    try:
        async with aiofiles.open(file_path, 'r') as file:
            prompt = await file.read()
        return prompt
    except FileNotFoundError:
        logger.error(f"Prompt file '{file_path}' not found.")
        raise HTTPException(status_code=404, detail=f"Prompt file '{file_path}' not found.")
    except Exception as e:
        logger.error(f"Error reading prompt file '{file_path}': {e}")
        raise HTTPException(status_code=500, detail="Error reading prompt file")

async def call_gpt4_api(prompt_text: str, sub_prompt_key: str, company_name: str) -> str:
    """
    Call the GPT-4 API with the given prompt.
    """
    token =generate_token()
    client = AzureOpenAI(
        azure_ad_token=token,
        api_version="2023-05-15",
        azure_endpoint="https://your-azure-endpoint",
    )
    if not prompt_text:
        return f"skipped {sub_prompt_key} due to empty  prompt"
    
    logging.info(f"--- Calling GPT-4o API for : {sub_prompt_key}")

    prompt_template = """
    {input}
    Company Name: {company}
    """
    prompts = prompt_template.format(input=prompt_text, company=company_name)

    try:
        persona = "you are a creative and innovative AI assistant that generates engaging professional content that may be humorous and friendly. The content you create is based on user input and can be marketing copy, an informative communication, or a sales pitch."
        messages = [
            {"role": "system", "content": persona},
            {"role": "user", "content": prompts}
        ]
        response = await client.chat.completions.create(
            messages=messages,
            temperature=0.7,
            max_tokens=30000,
            model="gpt-4o",
            frequency_penalty=0.5,
            presence_penalty=0.6,
        )
        result = response.choices[0].message.content
        logging.info(f"--- Received response for : {sub_prompt_key} ---")
        return result if result else f"skipped {sub_prompt_key} due to empty response"
    except openai.APIError as e:
        logger.error(f"OpenAI API returned an API error for {sub_prompt_key}: {e}")
        return f"Error processing {sub_prompt_key}: API Error"
    except openai.APIConnectionError as e:
        logger.error(f"OpenAI API connection error for {sub_prompt_key}: {e}")
        return f"Error processing {sub_prompt_key}: Connection Error"
    except openai.RateLimitError as e:
        logger.error(f"OpenAI API rate limit exceeded for {sub_prompt_key}: {e}")
        return f"Error processing {sub_prompt_key}: Rate Limit Exceeded"
    except openai.InvalidRequestError as e:
        logger.error(f"OpenAI API invalid request error for {sub_prompt_key}: {e}")
        return f"Error processing {sub_prompt_key}: Invalid Request"
    except openai.OpenAIError as e:
        logger.error(f"OpenAI API error for {sub_prompt_key}: {e}")
        return f"Error processing {sub_prompt_key}: OpenAI Error"
    except Exception as e:  
        logger.error(f"Unexpected error for {sub_prompt_key}: {e}")
        return f"Error processing {sub_prompt_key}: Unexpected Error"
    
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """
    Load the configuration file at startup.
    """
    logger.info("Loading configuration...")
    load_config()
    if not PROMPT_CONFIG or not PROMPT_CONFIG.get('topics'):
        logger.error("Configuration file is empty or missing 'topics' key.")
        raise HTTPException(status_code=500, detail="Configuration file is empty or missing 'topics' key.")
    else:
        logger.info("Configuration loaded successfully.")
    logger.info("Application started and configuration loaded.")

@app.post("/generate_report")
async def generate_report(request: Request):
    """
    Generate a report based on the provided company name and topic.
    """
    data = await request.json()
    company_name = data.get("company_name")
    topic = data.get("topic", [])

    if not company_name or not topic:
        raise HTTPException(status_code=400, detail="Company name and topic are required.")
    
    logger.info(f"Received request to generate report for company: {company_name}, topic: {topic}")

    if len(topic)>0 and 'executive_summary' not in topic:
        topic.append('_executive_summary')
    logger.info(f"Updated topic list: {topic}")

    reports = {}
    for topic_name in topic:
        if not PROMPT_CONFIG or 'topics' not in PROMPT_CONFIG:
            raise HTTPException(status_code=500, detail="Configuration file is empty or missing 'topics' key.")
        
        topic_data = PROMPT_CONFIG['topics'].get(topic_name)
        if not topic_data:
            raise HTTPException(status_code=404, detail=f"Topic '{topic_name}' not found in configuration.")
        
        sub_prompt_config = topic_data.get('sub_prompt', [])
        if not sub_prompt_config:
            return {"message": f"No sub-prompts found for topic '{topic_name}'."}
        
        results = ""
        tasks = []
        for sub_prompt in sub_prompt_config:
            if sub_prompt.get('active', False):
                file_path = sub_prompt.get('file')
                key = sub_prompt.get('key')

                if not file_path or not key:
                    logger.error(f"Warning: Skipping sub_prompt due to missing 'file' or 'key' in config: {sub_prompt}")
                    continue

                async def run_sub_prompt(key, file_path):
                    prompt_text = await read_prompt_file(file_path)
                    if prompt_text:
                        api_result = await call_gpt4_api(prompt_text, key, company_name)
                        return key, api_result
                    else:
                        return key, f"skipped {key}: Could not read prompt file '{file_path}'"
                tasks.append(run_sub_prompt(key, file_path))

        if tasks:
            logger.info(f"--- Running {len(tasks)} active sub_prompts for topic: {topic_name} concurrently ---")
            task_results = await asyncio.gather(*tasks)

            for key, result in task_results:
                results += f"{result}\n\n"
            
            logger.info(f"--- Finished running sub_prompts for topic: {topic_name} ---")
        else:
            logger.info(f"--- No active sub_prompts found for topic: {topic_name} ---")

        reports[topic_name] = results
    
    return {"reports": reports}