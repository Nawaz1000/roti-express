import qrcode
import base64
from io import BytesIO
import razorpay
from ..config import settings
import hmac
import hashlib

# Initialize Razorpay client if configured
razorpay_client = None
if settings.PAYMENT_MODE == "razorpay" and settings.RAZORPAY_KEY_ID:
    razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def generate_upi_qr_base64(order_code: str, amount: float) -> str:
    """
    Generates a base64 encoded PNG of a UPI QR code.
    """
    if not settings.UPI_VPA:
        # Fallback if no VPA provided for testing
        vpa = "test@upi"
        name = "TestPayee"
    else:
        vpa = settings.UPI_VPA
        name = settings.UPI_PAYEE_NAME

    # UPI deep link format
    upi_url = f"upi://pay?pa={vpa}&pn={name}&am={amount:.2f}&tn={order_code}&cu=INR"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(upi_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    return f"data:image/png;base64,{img_str}"

def create_razorpay_order(order_code: str, amount: float) -> dict:
    """
    Calls Razorpay Orders API to create a payment-linked order.
    Returns the Razorpay order object.
    """
    if not razorpay_client:
        return {}
    
    data = {
        "amount": int(amount * 100),  # in paise
        "currency": "INR",
        "receipt": order_code,
        "payment_capture": 1
    }
    return razorpay_client.order.create(data=data)

def verify_razorpay_signature(payload_body: str, signature: str) -> bool:
    """
    Verifies the Razorpay webhook signature.
    """
    if not settings.RAZORPAY_WEBHOOK_SECRET:
        return False
    
    expected_signature = hmac.new(
        bytes(settings.RAZORPAY_WEBHOOK_SECRET, 'utf-8'),
        msg=bytes(payload_body, 'utf-8'),
        digestmod=hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)
