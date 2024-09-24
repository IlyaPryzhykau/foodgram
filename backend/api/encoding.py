import base64


def encode_id(id):
    """
    Кодирует целочисленный идентификатор в строку с использованием
    безопасного для URL Base64.
    """
    return base64.urlsafe_b64encode(str(id).encode()).decode()


def decode_id(encoded_id):
    """
    Декодирует строку, закодированную в безопасный для URL
    Base64, обратно в целочисленный идентификатор.
    """
    return int(base64.urlsafe_b64decode(encoded_id.encode()).decode())
