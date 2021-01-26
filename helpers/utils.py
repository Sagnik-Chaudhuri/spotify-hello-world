from datetime import datetime, timedelta, timezone as datetime_timezone


def _check_if_access_token_expired(session):
    current_timestamp = datetime.utcnow().replace(
        tzinfo=datetime_timezone.utc)
    return session['tokens']['token_expiry_timestamp'] - timedelta(seconds=30) < current_timestamp
