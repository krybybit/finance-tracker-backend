import hmac
import hashlib
from urllib.parse import parse_qs
from app.config import settings

import json
from urllib.parse import parse_qsl

def validate_telegram_init_data(init_data: str) -> bool:
    try:
        parsed = dict(parse_qsl(init_data))
        received_hash = parsed.pop('hash', None)
        if not received_hash:
            return False
        
        # Сортировка и формирование строки данных
        data_check_string = '\n'.join(f"{k}={v}" for k, v in sorted(parsed.items()))
        
        # Генерация секретного ключа
        secret_key = hmac.new(
            b'WebAppData',
            settings.BOT_TOKEN.encode(),
            hashlib.sha256
        ).digest()
        
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(calculated_hash, received_hash)
    except Exception:
        return False

def get_user_from_init_data(init_data: str) -> dict:
    """Правильное извлечение user из initData"""
    parsed = dict(parse_qsl(init_data))
    user_json = parsed.get('user', '{}')
    return json.loads(user_json)  # Теперь вернёт dict с id, username и т.д.