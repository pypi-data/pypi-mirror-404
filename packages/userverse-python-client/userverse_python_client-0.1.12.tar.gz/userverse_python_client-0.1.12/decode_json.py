import base64
from typing import Tuple


def decode_basic_auth(auth_header: str) -> Tuple[str, str]:
    """
    Decode an HTTP Basic Authorization header.

    Args:
        auth_header: Full Authorization header value,
                     e.g. "Basic dXNlcjpwYXNzd29yZA=="

    Returns:
        (username, password)

    Raises:
        ValueError: if the header is invalid or cannot be decoded
    """
    if not auth_header.startswith("Basic "):
        raise ValueError("Authorization header must start with 'Basic '")

    encoded_part = auth_header.split(" ", 1)[1].strip()

    try:
        decoded_bytes = base64.b64decode(encoded_part)
        decoded_str = decoded_bytes.decode("utf-8")
    except Exception as exc:
        raise ValueError("Invalid Base64 Basic Auth value") from exc

    if ":" not in decoded_str:
        raise ValueError("Decoded value is not in 'username:password' format")

    username, password = decoded_str.split(":", 1)
    return username, password


if __name__ == "__main__":
    # Example usage
    test_header = "Basic c2toZW5kbGVAZ21haWwuY29tOjlkQShyOUB4SSFaLg=="
    user, pwd = decode_basic_auth(test_header)
    print(f"Decoded username: {user}")
    print(f"Decoded password: {pwd}")
