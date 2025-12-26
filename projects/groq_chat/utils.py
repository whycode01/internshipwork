# utils.py

import base64
from io import BytesIO

from PIL import Image

from config import MAX_IMAGE_WIDTH


def resize_image(img_bytes):
    image = Image.open(BytesIO(img_bytes)).convert("RGB")
    if image.width > MAX_IMAGE_WIDTH:
        ratio = MAX_IMAGE_WIDTH / float(image.width)
        new_height = int(float(image.height) * ratio)
        image = image.resize((MAX_IMAGE_WIDTH, new_height), Image.Resampling.LANCZOS)
    output = BytesIO()
    image.save(output, format="JPEG", quality=80)
    return output.getvalue()

def encode_image(img_bytes):
    return base64.b64encode(img_bytes).decode("utf-8")



