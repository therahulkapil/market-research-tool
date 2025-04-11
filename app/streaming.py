# import yaml
# import logging
# from fastapi import FastAPI, HTTPException, Request
# from fastapi.responses import StreamingResponse
# from typing import AsyncGenerator
# import aiofiles
# from fastapi.middleware.cors import CORSMiddleware
# import anthropic

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Load configuration from YAML file
# CONFIG_FILE = "app/prompt_config.yaml"
# PROMPT_CONFIG = {}

# def load_config():
#     """
#     Load the prompt configuration from a YAML file.
#     """
#     global PROMPT_CONFIG
#     try:
#         with open(CONFIG_FILE, 'r') as file:
#             PROMPT_CONFIG = yaml.safe_load(file)
#         if not PROMPT_CONFIG or 'topics' not in PROMPT_CONFIG:
#             logger.error(f"Error: Config file '{CONFIG_FILE}' is empty or missing 'topics' key.")
#             PROMPT_CONFIG = {'topics': {}}
#     except FileNotFoundError:
#         logger.error(f"Error: Config file '{CONFIG_FILE}' not found.")
#         PROMPT_CONFIG = {'topics': {}}
#     except yaml.YAMLError as e:
#         logger.error(f"Error: Failed to parse YAML file '{CONFIG_FILE}': {e}")
#         PROMPT_CONFIG = {'topics': {}}

# async def read_prompt_file(file_path: str) -> str:
#     """
#     Read the prompt from a file asynchronously.
#     """
#     try:
#         async with aiofiles.open(file_path, 'r') as file:
#             prompt = await file.read()
#         return prompt
#     except FileNotFoundError:
#         logger.error(f"Prompt file '{file_path}' not found.")
#         raise HTTPException(status_code=404, detail=f"Prompt file '{file_path}' not found.")
#     except Exception as e:
#         logger.error(f"Error reading prompt file '{file_path}': {e}")
#         raise HTTPException(status_code=500, detail="Error reading prompt file")

# async def stream_anthropic_api(prompt_text: str, sub_prompt_key: str, company_name: str) -> AsyncGenerator[str, None]:
#     """
#     Call the Anthropic API with the given prompt and stream the response.
#     """
#     if not prompt_text:
#         yield f"Skipped {sub_prompt_key} due to empty prompt"
#         return

#     logger.info(f"--- Calling Anthropic API for: {sub_prompt_key} ---")

#     client = anthropic.Client(api_key="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")
    
#     prompt_template = """
#     {input}
#     Company Name: {company}
#     """
#     prompts = prompt_template.format(input=prompt_text, company=company_name)

#     try:
#         persona = "you are a creative and innovative AI assistant that generates engaging professional content that may be humorous and friendly. The content you create is based on user input and can be marketing copy, an informative communication, or a sales pitch."
#         messages = [
#             {"role": "system", "content": persona},
#             {"role": "user", "content": prompts}
#         ]
#         # response = await client.completion(
#         #     prompt=prompt_template,
#         #     stop_sequences=["\n\n"],
#         #     max_tokens_to_sample=2000,
#         #     model="claude-1"
#         # )
#         response = await client.messages.create(
#             model="claude-3-7-sonnet-20250219",
#             max_tokens=1024,
#             messages=messages,
#         )
#         for chunk in response.get("completion").split():
#             yield chunk
        
#         logger.info(f"--- Completed streaming response for: {sub_prompt_key} ---")
        
#     except Exception as e:
#         logger.error(f"Unexpected error for {sub_prompt_key}: {e}")
#         yield f"Error processing {sub_prompt_key}: {str(e)}"

# app = FastAPI()
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# @app.on_event("startup")
# async def startup_event():
#     """
#     Load the configuration file at startup.
#     """
#     logger.info("Loading configuration...")
#     load_config()
#     if not PROMPT_CONFIG or not PROMPT_CONFIG.get('topics'):
#         logger.error("Configuration file is empty or missing 'topics' key.")
#         raise HTTPException(status_code=500, detail="Configuration file is empty or missing 'topics' key.")
#     else:
#         logger.info("Configuration loaded successfully.")
#     logger.info("Application started and configuration loaded.")

# @app.post("/generate_report_stream")
# async def generate_report_stream(request: Request):
#     """
#     Generate a report based on the provided company name and topic with streaming response.
#     """
#     data = await request.json()
#     company_name = data.get("company_name")
#     topic = data.get("topic", [])

#     if not company_name or not topic:
#         raise HTTPException(status_code=400, detail="Company name and topic are required.")
    
#     logger.info(f"Received request to generate streaming report for company: {company_name}, topic: {topic}")

#     topic_name = topic[0]
#     logger.info(f"Topic name: {topic_name}")
#     if not PROMPT_CONFIG or 'topics' not in PROMPT_CONFIG:
#         raise HTTPException(status_code=500, detail="Configuration file is empty or missing 'topics' key.")
    
#     topic_data = PROMPT_CONFIG['topics'].get(topic_name)
#     if not topic_data:
#         raise HTTPException(status_code=404, detail=f"Topic '{topic_name}' not found in configuration.")
    
#     sub_prompt_config = topic_data.get('sub_prompts', [])
#     if not sub_prompt_config:
#         raise HTTPException(status_code=404, detail=f"No sub-prompts found for topic '{topic_name}'.")

#     active_sub_prompt = next(
#         (sub_prompt for sub_prompt in sub_prompt_config if sub_prompt.get('active', False)), 
#         None
#     )

#     if not active_sub_prompt:
#         raise HTTPException(status_code=404, detail=f"No active sub-prompts found for topic '{topic_name}'.")

#     file_path = active_sub_prompt.get('file')
#     key = active_sub_prompt.get('key')
    
#     if not file_path or not key:
#         raise HTTPException(status_code=400, detail="Missing 'file' or 'key' in sub-prompt configuration.")

#     prompt_text = await read_prompt_file(file_path)
#     stream = stream_anthropic_api(prompt_text, key, company_name)
    
#     return StreamingResponse(
#         stream,
#         media_type="text/event-stream"
#     )



import yaml
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import openai
from openai import OpenAI, APIError, APIConnectionError, RateLimitError
import aiofiles
from fastapi.middleware.cors import CORSMiddleware

# The rest of your imports remain the same...
# configure logging
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

async def stream_gpt4_api(prompt_text: str, sub_prompt_key: str, company_name: str) -> AsyncGenerator[str, None]:
    """
    Call the GPT-4 API with the given prompt and stream the response.
    """
    client = OpenAI(
        api_key="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"
    )
    if not prompt_text:
        yield f"skipped {sub_prompt_key} due to empty prompt"
        return
    
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
        
        # Create a streaming completion
        stream = client.chat.completions.create(
            messages=messages,
            temperature=0.7,
            max_tokens=16000,
            model="gpt-4o-mini",
            frequency_penalty=0.5,
            presence_penalty=0.6,
            stream=True  # Enable streaming
        )
        
        # Stream each chunk as it arrives
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
                
        logging.info(f"--- Completed streaming response for : {sub_prompt_key} ---")
        
    except APIError as e:
        logger.error(f"OpenAI API returned an API error for {sub_prompt_key}: {e}")
        yield f"Error processing {sub_prompt_key}: API Error"
    except APIConnectionError as e:
        logger.error(f"OpenAI API connection error for {sub_prompt_key}: {e}")
        yield f"Error processing {sub_prompt_key}: Connection Error"
    except RateLimitError as e:
        logger.error(f"OpenAI API rate limit exceeded for {sub_prompt_key}: {e}")
        yield f"Error processing {sub_prompt_key}: Rate Limit Exceeded"
    except Exception as e:  
        logger.error(f"Unexpected error for {sub_prompt_key}: {e}")
        yield f"Error processing {sub_prompt_key}: Unexpected Error"
        
# Keep the original non-streaming function for backward compatibility
async def call_gpt4_api(prompt_text: str, sub_prompt_key: str, company_name: str) -> str:
    """
    Call the GPT-4 API with the given prompt (non-streaming version).
    """
    client = OpenAI(
        api_key="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"
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
            max_tokens=16000,
            model="gpt-4o-mini",
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

# Helper function to stream responses
async def stream_response_generator(stream):
    try:
        async for content in stream:
            yield content
    except Exception as e:
        logger.error(f"Error streaming response: {e}")
        yield f"Error during streaming: {str(e)}"

# @app.post("/generate_report_stream")
# async def generate_report_stream(request: Request):
#     """
#     Generate a report based on the provided company name and topic with streaming response.
#     """
#     data = await request.json()
#     company_name = data.get("company_name")
#     topic = data.get("topic", [])

#     if not company_name or not topic:
#         raise HTTPException(status_code=400, detail="Company name and topic are required.")
    
#     logger.info(f"Received request to generate streaming report for company: {company_name}, topic: {topic}")

#     # if len(topic) > 0 and 'executive_summary' not in topic:
#     #     topic.append('executive_summary')
#     # logger.info(f"Updated topic list: {topic}")
    
#     # Choose a single topic to stream (first one in the list)
#     topic_name = topic[0]
    
#     if not PROMPT_CONFIG or 'topics' not in PROMPT_CONFIG:
#         raise HTTPException(status_code=500, detail="Configuration file is empty or missing 'topics' key.")
    
#     topic_data = PROMPT_CONFIG['topics'].get(topic_name)
#     if not topic_data:
#         raise HTTPException(status_code=404, detail=f"Topic '{topic_name}' not found in configuration.")
    
#     sub_prompt_config = topic_data.get('sub_prompts', [])
#     if not sub_prompt_config:
#         raise HTTPException(status_code=404, detail=f"No sub-prompts found for topic '{topic_name}'.")
    
#     # Find the first active sub-prompt
#     active_sub_prompt = None
#     for sub_prompt in sub_prompt_config:
#         if sub_prompt.get('active', False):
#             active_sub_prompt = sub_prompt
#             break
    
#     if not active_sub_prompt:
#         raise HTTPException(status_code=404, detail=f"No active sub-prompts found for topic '{topic_name}'.")
    
#     file_path = active_sub_prompt.get('file')
#     key = active_sub_prompt.get('key')
    
#     if not file_path or not key:
#         raise HTTPException(status_code=400, detail="Missing 'file' or 'key' in sub-prompt configuration.")
    
#     # Read the prompt file and stream the response
#     prompt_text = await read_prompt_file(file_path)
#     stream = stream_gpt4_api(prompt_text, key, company_name)
    
#     return StreamingResponse(
#         stream_response_generator(stream),
#         media_type="text/event-stream"
#     )

@app.post("/generate_report_stream")
async def generate_report_stream(request: Request):
    """
    Generate a report based on the provided company name and topics with streaming response.
    Processes all sub-prompts for all requested topics.
    """
    data = await request.json()
    company_name = data.get("company_name")
    topics = data.get("topic", [])

    if not company_name or not topics:
        raise HTTPException(status_code=400, detail="Company name and at least one topic are required.")
    
    logger.info(f"Received request to generate streaming report for company: {company_name}, topics: {topics}")

    if not PROMPT_CONFIG or 'topics' not in PROMPT_CONFIG:
        raise HTTPException(status_code=500, detail="Configuration file is empty or missing 'topics' key.")
    
    async def generate_all_responses():
        """Generator function to yield responses from all sub-prompts across all topics."""
        for topic_name in topics:
            topic_data = PROMPT_CONFIG['topics'].get(topic_name)
            if not topic_data:
                yield f"Topic '{topic_name}' not found in configuration.\n"
                continue
            
            sub_prompt_config = topic_data.get('sub_prompts', [])
            if not sub_prompt_config:
                yield f"No sub-prompts found for topic '{topic_name}'.\n"
                continue
            
            # Process all active sub-prompts for this topic
            for sub_prompt in sub_prompt_config:
                if not sub_prompt.get('active', False):
                    continue
                    
                file_path = sub_prompt.get('file')
                key = sub_prompt.get('key')
                
                if not file_path or not key:
                    yield f"Missing 'file' or 'key' in sub-prompt configuration for topic '{topic_name}'.\n"
                    continue
                
                try:
                    # Read the prompt file
                    prompt_text = await read_prompt_file(file_path)
                    
                    # Yield a marker for the beginning of this sub-prompt's response
                    yield f"\n"
                    
                    # Stream the response for this sub-prompt
                    async for content in stream_gpt4_api(prompt_text, key, company_name):
                        yield content
                    
                    # Yield a marker for the end of this sub-prompt's response
                    yield f"\n\n"
                    
                except Exception as e:
                    logger.error(f"Error processing sub-prompt '{key}' for topic '{topic_name}': {e}")
                    yield f"\nError processing {topic_name} - {key}: {str(e)}\n"
    
    return StreamingResponse(
        generate_all_responses(),
        media_type="text/event-stream"
    )