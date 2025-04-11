from openai import AzureOpenAI, OpenAI
from app.utils.token_generator import generate_token
import logging, os

async def call_gpt4_api(prompt_text: str, sub_prompt_key: str, company_name: str) -> str:
    # token = generate_token()
    # client = AzureOpenAI(
    #     azure_ad_token=token,
    #     api_version="2023-05-15",
    #     azure_endpoint="https://your-azure-endpoint",
    # )

    # use this key for testing
    # key="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"
    client = OpenAI(
        api_key=os.environ.get('API_KEY'),
    )

    if not prompt_text:
        return f"Skipped {sub_prompt_key} due to empty prompt"

    try:
        messages = [
            {"role": "system", "content": "You are a creative AI assistant."},
            {"role": "user", "content": f"{prompt_text}\nCompany Name: {company_name}"}
        ]
        response =  client.chat.completions.create(
            messages=messages,
            temperature=0.7,
            max_tokens=16000,
            model="gpt-4o-mini"
        )
        return response.choices[0].message.content if response else f"Skipped {sub_prompt_key} due to empty response"
    except Exception as e:
        logging.error(f"GPT-4 API error: {e}")
        return f"Error processing {sub_prompt_key}"