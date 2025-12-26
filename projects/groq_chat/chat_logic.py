# chat_logic.py

from typing import Dict, List, Optional, Tuple, Union

from config import IMAGE_MODEL, TEXT_MODEL
from utils import encode_image, resize_image


def build_chat_input(
    user_text: str,
    user_file: Optional[bytes],
    image_history: List[Dict]
) -> Tuple[str, Dict[str, Union[str, List[Dict]]], Optional[bytes], str]:
    user_text = user_text or "Describe this image."

    if user_file:
        resized_bytes = resize_image(user_file)
        b64_image = encode_image(resized_bytes)

        user_msg = {
            "role": "user",
            "content": [
                {"type": "text", "text": user_text},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/jpeg;base64,{b64_image}"
                }},
            ],
        }

        return IMAGE_MODEL, user_msg, resized_bytes, user_text

    else:
        if image_history:
            user_msg = {
                "role": "user",
                "content": [{"type": "text", "text": user_text}],
            }
            return IMAGE_MODEL, user_msg, None, user_text
        else:
            user_msg = {
                "role": "user",
                "content": user_text,
            }
            return TEXT_MODEL, user_msg, None, user_text
