import os
import json
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

HEYGEN_API_KEY = os.getenv('HEYGEN_API_KEY')
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), 'voices_heygen.json')

def test_get_voices():
    url = 'https://api.heygen.com/v1/audio/voices'
    headers = {
        'x-api-key': HEYGEN_API_KEY,
        'accept': 'application/json',
    }
    params = {
        'type': 'public',
        'limit': 100,
    }

    response = requests.get(url, headers=headers, params=params)
    print(f'Status: {response.status_code}')

    if not response.ok:
        print(f'Error: {response.text}')
        return response

    data = response.json()

    filtered = [
        v for v in data.get('data', [])
        if v.get('gender') == 'female' and v.get('language') == 'English'
    ]
    output = {**data, 'data': filtered}

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f'Saved {len(filtered)} female English voices to voices_heygen.json')
    return response

if __name__ == '__main__':
    test_get_voices()
