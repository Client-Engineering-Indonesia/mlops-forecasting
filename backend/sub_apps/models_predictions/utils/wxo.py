import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load env vars
load_dotenv()

wxo_api_key = os.getenv("WXO_API_KEY")
region_code = os.getenv("REGION_CODE")
tenant_id = os.getenv("TENANT_ID")
agent_id = os.getenv("AGENT_ID")


# --------------------------
# IBM TOKEN GENERATOR
# --------------------------
def generate_ibm_token():
    url = "https://iam.platform.saas.ibm.com/siusermgr/api/1.0/apikeys/token"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    data = {
        "apikey": wxo_api_key
    }
    
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()  # will raise if 4xx/5xx

    return response.json()["token"]


# --------------------------
# LLM FUNCTION
# --------------------------
def multiprocess_llm_answer(case: dict) -> dict:

    url = (
        f"https://api.{region_code}.watson-orchestrate.ibm.com/instances/"
        f"{tenant_id}/v1/orchestrate/{agent_id}/chat/completions"
    )

    bearer_token = generate_ibm_token()

    payload = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "response_type": "text",
                        "text": case["input_prompt"]
                    }
                ]
            }
        ],
        "stream": False
    }

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Accept": "application/json"
    }

    if "thread_id" in case.keys():
        headers["X-Ibm-Thread-Id"] = case["thread_id"]

    response = requests.post(url, json=payload, headers=headers)

    try:
        json_response = response.json()
        # Adjust this if IBM’s structure differs
        case["llm_answer"] = json_response["choices"][0]["message"]["content"]
        case["thread_id"] = json_response["thread_id"]
    except Exception:
        case["llm_answer"] = "Maaf, terjadi kesalahan saat memproses jawaban."

    return case