# RotiExpress - Hyperlocal Pre-Order Platform

A hyperlocal roti pre-order web application built with FastAPI, MongoDB, and Tailwind CSS.

## Project Structure

- `/backend`: FastAPI Python backend
- `/frontend`: HTML5/Tailwind/VanillaJS customer and admin frontend

## Prerequisites
- Python 3.11+
- MongoDB instance (Atlas recommended, or local)
- A virtual environment is highly recommended.

## Setup Instructions

### 1. Backend Setup
Navigate to the backend directory:
```bash
cd backend
```

Install the dependencies:
```bash
pip install -r requirements.txt
```

Set up your environment variables. Copy `.env.example` to `.env` and fill in the details:
```bash
# Example
MONGODB_URI=mongodb+srv://user:pass@cluster0.mongodb.net/
DB_NAME=rotiexpress
JWT_SECRET=your_super_secret_key
# Other config options available in config.py
```

### 2. Seed Database
You must run the seed script first to create the necessary indexes, default application settings, and the initial admin user.
```bash
python seed.py
```
This will create:
- Admin user: `admin` / `password123`
- Default price: ₹10
- Default capacity: 50 rotis per hour
- Min advance booking: 2 hours

### 3. Run the Backend Server
```bash
uvicorn main:app --reload
```
The backend API will be running at `http://127.0.0.1:8000`.

### 4. Frontend Setup
The frontend uses CDN for Tailwind and requires no build step.
Simply open `/frontend/index.html` in your browser for the customer facing app.
Open `/frontend/admin.html` in your browser to access the admin dashboard.

*Note: Since the API base URL is hardcoded in `index.html` and `admin.html` to `http://127.0.0.1:8000/api`, ensure your backend is running locally on port 8000. In production, update this constant in the JS.*

## WhatsApp Notification Integration
By default, the `WHATSAPP_API_TOKEN` is set to `mock_token`. In this mode, WhatsApp notifications are printed in the backend console logs.

To use the real Meta WhatsApp Cloud API:
1. Replace `mock_token` in your `.env` with a real permanent access token.
2. Fill out `WHATSAPP_PHONE_NUMBER_ID` and `WHATSAPP_ADMIN_NUMBER`.
3. Set your Meta approved `WHATSAPP_TEMPLATE_NAME`.

## Testing the Flow
You can place an order from the frontend, simulating UPI and COD.
- **2-hour Validation:** Attempt to select a slot less than 2 hours from now; the backend will block it.
- **Capacity Check:** Place orders totaling > 50 rotis in the same hour slot to see capacity limit kicking in.
- **Payment Modes:** If `PAYMENT_MODE="manual_qr"`, the app will generate a raw UPI intent QR code based on your `.env` VPA settings. If `PAYMENT_MODE="razorpay"`, it will create Razorpay Orders using your credentials.
