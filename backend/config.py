from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGODB_URI: str
    DB_NAME: str

    JWT_SECRET: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    WHATSAPP_API_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_TEMPLATE_NAME: str = "order_confirmation"
    WHATSAPP_ADMIN_NUMBER: str = ""

    PAYMENT_MODE: str = "manual_qr"
    UPI_VPA: str = ""
    UPI_PAYEE_NAME: str = ""

    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""

    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""

    class Config:
        env_file = "backend/.env"

settings = Settings()
