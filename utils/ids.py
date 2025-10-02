import time
import random
import string


def create_id_with_prefix(prefix: str) -> str:
    # timestamp + 4 random chars
    stamp = int(time.time() * 1000)
    rand = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"{prefix}_{stamp}_{rand}"
