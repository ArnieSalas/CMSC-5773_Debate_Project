import requests

BASE_URL = "https://port-better-operated-problems.trycloudflare.com/" # paste your actual tunnel URL here
API_KEY = "sk-local"  # dummy key, vLLM ignores it but some clients require it

payload = {
    "model": "hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Create a poem about cats"}
    ],
    "temperature": 0.7,
    "max_tokens": 128
}

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

response = requests.post(f"{BASE_URL}/v1/chat/completions", json=payload, headers=headers)
print(response.json())
print()
# print(response.json()["choices"])
print(response.json()["choices"][0]["message"]["content"])