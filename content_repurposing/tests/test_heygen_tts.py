import os
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

HEYGEN_API_KEY = os.getenv('HEYGEN_API_KEY')
VOICE_ID = '0082e70326864107823605db0d77f5e0'

TEXT = """
A e ke vënë re si po ndryshon komplet loja? Perplexity nuk po mundohet më thjesht "ta mposhtë" Gugellin. Po kërkon paratë. Dhe po i gjen, pikërisht aty ku ndodhet jeta reale.

Filloi me kërkimin, por këtë herë, në shkurt, Perplexity Computer bëri një kthesë që s'harrohet. Pastaj u rrit shpejt. Shumë shpejt. Dhe ja çfarë solli.
"""

def test_text_to_speech():
    url = 'https://api.heygen.com/v1/audio/text_to_speech'
    headers = {
        'X-Api-Key': HEYGEN_API_KEY,
        'Content-Type': 'application/json',
    }
    payload = {
        'text': TEXT.strip(),
        'voice_id': VOICE_ID,
        'language': 'sq',
    }

    response = requests.post(url, headers=headers, json=payload)
    print(f'Status: {response.status_code}')
    print(f'Response: {response.text}')
    return response

if __name__ == '__main__':
    test_text_to_speech()
