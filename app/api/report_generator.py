from fastapi import APIRouter, Request, HTTPException
from app.config import config_loader
from app.utils.prompt_reader import read_prompt_file
from app.services.gpt_service import call_gpt4_api
import logging
import asyncio

# configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/generate_report")
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

    # if len(topic)>0 and 'executive_summary' not in topic:
    #     topic.append('_executive_summary')
    # logger.info(f"Updated topic list: {topic}")

    reports = {}
    for topic_name in topic:
        if not config_loader.PROMPT_CONFIG or 'topics' not in config_loader.PROMPT_CONFIG:
            raise HTTPException(status_code=500, detail="Configuration file is empty or missing 'topics' key.")
        
        topic_data = config_loader.PROMPT_CONFIG['topics'].get(topic_name)
        print(f"topic_data: {topic_data}")
        logger.info(f"topic_data: {topic_data}")
        if not topic_data:
            raise HTTPException(status_code=404, detail=f"Topic '{topic_name}' not found in configuration.")
        
        sub_prompt_config = topic_data.get('sub_prompts', [])
        print(f"sub_prompt_config: {sub_prompt_config}")
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