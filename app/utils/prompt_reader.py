import aiofiles
import logging
from fastapi import HTTPException

async def read_prompt_file(file_path: str) -> str:
    try:
        async with aiofiles.open(file_path, 'r') as file:
            return await file.read()
    except FileNotFoundError:
        logging.error(f"Prompt file '{file_path}' not found.")
        raise HTTPException(status_code=404, detail="Prompt file not found.")
