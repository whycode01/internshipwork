import os
import requests

API_URL = os.getenv("API_URL", "http://localhost:8001/api/v1")

def anonymize(text: str, language: str = "en") -> (str, str):
    """
    Sends text to the AnonyAPI and returns (anonymized_text, token).
    """
    resp = requests.post(
        f"{API_URL}/anonymize",
        json={"text": text, "language": language}
    )
    resp.raise_for_status()
    data = resp.json()
    return data["anonymized_text"], data["token"]

def denonymize(anonymized_text: str, token: str) -> str:
    """
    Sends anonymized_text and token to the AnonyAPI and returns the deanonymized text.
    """
    resp = requests.post(
        f"{API_URL}/denonymize",
        json={"anonymized_text": anonymized_text, "token": token}
    )
    resp.raise_for_status()
    data = resp.json()
    return data["deanonymized_text"]
