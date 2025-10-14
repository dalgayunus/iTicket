import random
from datetime import timedelta
from django.utils import timezone


def generate_numeric_code(length: int = 6) -> str:
    return ''.join(str(random.randint(0, 9)) for _ in range(length))

def expiry(minutes: int = 10):
    return timezone.now() + timedelta(minutes=minutes)