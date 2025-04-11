import yaml,os
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import aiofiles
from fastapi.middleware.cors import CORSMiddleware
import anthropic

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            logger.error(f"Error: Config file '{CONFIG_FILE}' is empty or missing 'topics' key.")
            PROMPT_CONFIG = {'topics': {}}
    except FileNotFoundError:
        logger.error(f"Error: Config file '{CONFIG_FILE}' not found.")
        PROMPT_CONFIG = {'topics': {}}
    except yaml.YAMLError as e:
        logger.error(f"Error: Failed to parse YAML file '{CONFIG_FILE}': {e}")
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

async def stream_anthropic_api(prompt_text: str, sub_prompt_key: str, company_name: str) -> AsyncGenerator[str, None]:
    """
    Call the Anthropic API with the given prompt and stream the response.
    """
    if not prompt_text:
        yield f"Skipped {sub_prompt_key} due to empty prompt"
        return

    logger.info(f"--- Calling Anthropic API for: {sub_prompt_key} ---")
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    client = anthropic.Client(api_key=api_key)
    
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
        # response = await client.completion(
        #     prompt=prompt_template,
        #     stop_sequences=["\n\n"],
        #     max_tokens_to_sample=2000,
        #     model="claude-1"
        # )
        response = await client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=1024,
            messages=messages,
        )
        for chunk in response.get("completion").split():
            yield chunk
        
        logger.info(f"--- Completed streaming response for: {sub_prompt_key} ---")
        
    except Exception as e:
        logger.error(f"Unexpected error for {sub_prompt_key}: {e}")
        yield f"Error processing {sub_prompt_key}: {str(e)}"

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

@app.post("/generate_report_stream")
async def generate_report_stream(request: Request):
    """
    Generate a report based on the provided company name and topic with streaming response.
    """
    data = await request.json()
    company_name = data.get("company_name")
    topic = data.get("topic", [])

    if not company_name or not topic:
        raise HTTPException(status_code=400, detail="Company name and topic are required.")
    
    logger.info(f"Received request to generate streaming report for company: {company_name}, topic: {topic}")

    topic_name = topic[0]
    logger.info(f"Topic name: {topic_name}")
    if not PROMPT_CONFIG or 'topics' not in PROMPT_CONFIG:
        raise HTTPException(status_code=500, detail="Configuration file is empty or missing 'topics' key.")
    
    topic_data = PROMPT_CONFIG['topics'].get(topic_name)
    if not topic_data:
        raise HTTPException(status_code=404, detail=f"Topic '{topic_name}' not found in configuration.")
    
    sub_prompt_config = topic_data.get('sub_prompts', [])
    if not sub_prompt_config:
        raise HTTPException(status_code=404, detail=f"No sub-prompts found for topic '{topic_name}'.")

    active_sub_prompt = next(
        (sub_prompt for sub_prompt in sub_prompt_config if sub_prompt.get('active', False)), 
        None
    )

    if not active_sub_prompt:
        raise HTTPException(status_code=404, detail=f"No active sub-prompts found for topic '{topic_name}'.")

    file_path = active_sub_prompt.get('file')
    key = active_sub_prompt.get('key')
    
    if not file_path or not key:
        raise HTTPException(status_code=400, detail="Missing 'file' or 'key' in sub-prompt configuration.")

    prompt_text = await read_prompt_file(file_path)
    stream = stream_anthropic_api(prompt_text, key, company_name)
    
    return StreamingResponse(
        stream,
        media_type="text/event-stream"
    )



