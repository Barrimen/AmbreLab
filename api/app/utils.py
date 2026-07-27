import random
import string


def generate_session_code(length: int = 6) -> str:
    """Génère un code court pour rejoindre une session (ex: 'K3P9XZ')."""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))
