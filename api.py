import json
from openai import OpenAI, AsyncOpenAI

import logging
logger = logging.getLogger("sand_tray")

from settings import (
    API_KEY_TEXT,
    BASE_URL_TEXT,
    MODEL_NAME_TEXT,

    API_KEY_VISION,
    BASE_URL_VISION,
    MODEL_NAME_VISION,
)

client_text = OpenAI(
    api_key=API_KEY_TEXT,
    base_url=BASE_URL_TEXT,
)

client_vision = OpenAI(
    api_key=API_KEY_VISION,
    base_url=BASE_URL_VISION,
)

client_text_async = AsyncOpenAI(
    api_key=API_KEY_TEXT,
    base_url=BASE_URL_TEXT,
)

client_vision_async = AsyncOpenAI(
    api_key=API_KEY_VISION,
    base_url=BASE_URL_VISION,
)

def get_ai_response(prompt, model_type="text", response_format=None, cnt=1):
    logger.debug(f"Send to API, {json.dumps(prompt, indent=4, separators=(',', ': '), ensure_ascii=False)}")
    try:
        response = None
        if model_type == "text":
            response = client_text.chat.completions.create(
                model=MODEL_NAME_TEXT,
                messages=prompt,
                response_format=response_format,
            )
        else:
            response = client_vision.chat.completions.create(
                model=MODEL_NAME_VISION,
                messages=prompt,
                response_format=response_format,
            )
    except Exception as e:
        if cnt>3:
            raise BaseException(f"Request API ERROR, and ther is no pssibility of countinue. STOP!")
        logger.error(f"Request API ERROR: {e}, Retry {cnt}!")
        return get_ai_response(prompt, model_type, cnt+1)

    logger.debug(f"Recived by API, {json.dumps(response.choices[0].message.content, indent=4, separators=(',', ': '), ensure_ascii=False)}")
    logger.info(f"API token usage: {response.usage.total_tokens}")
    return response.choices[0].message.content, response.usage.total_tokens


async def get_ai_response_stream(prompt, model_type="text", response_format=None):
    logger.debug(f"Send to API, {json.dumps(prompt, indent=4, separators=(',', ': '), ensure_ascii=False)}")
    try:
        response = None
        if model_type == "text":
            response = await client_text_async.chat.completions.create(
                model=MODEL_NAME_TEXT,
                messages=prompt,
                response_format=response_format,
                stream=True,
            )
        else:
            response = await client_vision_async.chat.completions.create(
                model=MODEL_NAME_VISION,
                messages=prompt,
                response_format=response_format,
                stream=True,
            )

        async for chunk in response:
            logger.debug(f"Recived Chunk: {chunk}")
            if chunk.choices:
                yield chunk.choices[0].delta.content

    except Exception as e:
        raise BaseException(f"Request API ERROR, and ther is no pssibility of countinue. STOP!")
