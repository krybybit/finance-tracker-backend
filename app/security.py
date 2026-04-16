import hmac
import hashlib
import json
from urllib.parse import parse_qs
from app.config import settings

def validate_telegram_init_data(init_data: str) -> bool:
    try:
        parsed_data = parse_qs(init_data)
        received_hash = parsed_data.get('hash', [None])[0]
        if not received_hash:
            return False
        
        data_to_check = {k: v[0] for k, v in parsed_data.items() if k != 'hash'}
        sorted_data = sorted(data_to_check.items())

        data_string = '\n'.join(f"{k}={v}" for k, v in sorted_data)
        
        secret_key = hmac.new(
            b'WebAppData',
            settings.BOT_TOKEN.encode(),
            hashlib.sha256
        ).digest()
        
        calculated_hash = hmac.new(
            secret_key,
            data_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(calculated_hash, received_hash)
    except Exception as e:
        print(f"Validation error: {e}")
        return False

def get_user_from_init_data(init_data: str) -> dict:
    parsed_data = parse_qs(init_data)
    user_json = parsed_data.get('user', ['{}'])[0]
    return json.loads(user_json) 
    