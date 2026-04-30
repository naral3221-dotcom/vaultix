def parse_admin_emails(value: str) -> set[str]:
    return {email.strip().lower() for email in value.split(",") if email.strip()}


def is_configured_admin_email(email_lower: str, admin_emails: str) -> bool:
    return email_lower in parse_admin_emails(admin_emails)
