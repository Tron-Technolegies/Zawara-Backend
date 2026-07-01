import razorpay
from django.conf import settings


def get_razorpay_client():
    """
    Returns a Razorpay client initialized with credentials from settings.
    Raises a clear ValueError if keys are missing.
    """
    key_id = settings.RAZORPAY_KEY_ID
    key_secret = settings.RAZORPAY_KEY_SECRET

    if not key_id or not key_secret:
        raise ValueError(
            "Razorpay credentials are missing. "
            "Please set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET "
            "in your environment variables."
        )

    return razorpay.Client(auth=(key_id, key_secret))


# Keep backward-compatible `client` for any other usages,
# but create it lazily via the function above to avoid import-time failures.
client = get_razorpay_client()