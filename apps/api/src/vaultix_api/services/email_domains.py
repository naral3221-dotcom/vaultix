DISPOSABLE_EMAIL_DOMAINS = {
    "10minutemail.com",
    "guerrillamail.com",
    "mailinator.com",
    "tempmail.com",
    "yopmail.com",
}


def is_disposable_email(email_lower: str) -> bool:
    _, _, domain = email_lower.rpartition("@")
    return domain in DISPOSABLE_EMAIL_DOMAINS
