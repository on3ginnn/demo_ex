import hmac

STAFF_USERNAME = 'Admin26'
STAFF_PASSWORD = 'Demo20'


def staff_password_ok(given: str) -> bool:
    return hmac.compare_digest(given, STAFF_PASSWORD)
