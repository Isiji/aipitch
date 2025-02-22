from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, g
import google.generativeai as genai
import requests
from requests.auth import HTTPBasicAuth
import base64
from datetime import datetime
import sqlite3
import logging
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from functools import wraps
import json

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-here')

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Directory setup
PDF_DIR = "static/pitches"
os.makedirs(PDF_DIR, exist_ok=True)

# API Configurations
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyDJg_6FdCqAGScGWQ3lQsW1rbVOJkGOeoU')
genai.configure(api_key=GEMINI_API_KEY)

# Daraja API Constants
DARAJA_CONFIG = {
    'API_URL': "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
    'CONSUMER_KEY': os.environ.get('MPESA_CONSUMER_KEY', '77bgGpmlOxlgJu6oEXhEgUgnu0j2WYxA'),
    'CONSUMER_SECRET': os.environ.get('MPESA_CONSUMER_SECRET', 'viM8ejHgtEmtPTHd'),
    'BUSINESS_SHORTCODE': "174379",
    'PASSKEY': os.environ.get('MPESA_PASSKEY', 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'),
    'CALLBACK_URL': "https://yourwebsite.com/callback",
    'OAUTH_URL': "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials",
    'QUERY_URL': "https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query"
}

# Database setup
def get_db():
    """Get database connection within application context"""
    if not hasattr(g, 'db'):
        g.db = sqlite3.connect('business.db')
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    if 'db' in g:
        g.db.close()

def init_db():
    """Initialize the database tables"""
    db = get_db()
    cursor = db.cursor()
    
    # Create transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            mpesa_receipt TEXT UNIQUE,
            transaction_date TEXT,
            phone_number TEXT,
            status TEXT
        )
    ''')
    
    # Create pitches table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pitches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT NOT NULL,
            industry TEXT NOT NULL,
            pitch_text TEXT,
            pdf_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    db.commit()

# Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('payment_verified'):
            return redirect(url_for('payment'))
        return f(*args, **kwargs)
    return decorated_function

def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {str(e)}")
            return jsonify({"error": "An internal error occurred"}), 500
    return decorated_function

# Daraja API Helper Functions
class DarajaAPI:
    @staticmethod
    def generate_access_token():
        try:
            response = requests.get(
                DARAJA_CONFIG['OAUTH_URL'],
                auth=HTTPBasicAuth(
                    DARAJA_CONFIG['CONSUMER_KEY'],
                    DARAJA_CONFIG['CONSUMER_SECRET']
                )
            )
            return response.json()['access_token']
        except Exception as e:
            logger.error(f"Token generation error: {e}")
            return None

    @staticmethod
    def generate_password():
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        data_to_encode = f"{DARAJA_CONFIG['BUSINESS_SHORTCODE']}{DARAJA_CONFIG['PASSKEY']}{timestamp}"
        encoded = base64.b64encode(data_to_encode.encode())
        return encoded.decode('utf-8'), timestamp

# Business Pitch Generation
class PitchGenerator:
    @staticmethod
    def generate_pitch(data):
        prompt = f"""
        Create a professional business pitch for:

        Business Name: {data['businessName']}
        Industry: {data['industry']}
        Problem Statement: {data['problemStatement']}
        Target Market: {data['targetMarket']}
        Revenue Model: {data['revenueModel']}
        {"Competitor Analysis: " + data['competitorAnalysis'] if 'competitorAnalysis' in data else ""}

        Format the pitch with these sections:
        🎯 Problem Statement
        💡 Solution Overview
        📊 Market Opportunity
        💰 Revenue Model
        🏆 Competitive Advantage
        ⚡ Call to Action
        """

        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        return response.text if response else None

    @staticmethod
    def create_pdf(text, filepath):
        c = canvas.Canvas(filepath, pagesize=letter)
        width, height = letter
        c.setFont("Helvetica", 12)
        y_position = height - 40

        for line in text.split("\n"):
            if y_position < 40:
                c.showPage()
                c.setFont("Helvetica", 12)
                y_position = height - 40
            c.drawString(50, y_position, line.strip())
            y_position -= 20

        c.save()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/payment')
def payment():
    return render_template('payment.html')

@app.route('/generate-pitch', methods=['POST'])
@handle_errors
def generate_pitch():
    data = request.json
    required_fields = ['businessName', 'industry', 'problemStatement', 'targetMarket', 'revenueModel']
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    generated_pitch = PitchGenerator.generate_pitch(data)
    if not generated_pitch:
        return jsonify({"error": "Failed to generate pitch"}), 500

    pdf_filename = f"{data['businessName'].replace(' ', '_')}_pitch.pdf"
    pdf_path = os.path.join(PDF_DIR, pdf_filename)
    
    PitchGenerator.create_pdf(generated_pitch, pdf_path)

    return jsonify({
        "pitch": generated_pitch,
        "pdf_download_url": f"/download-pdf/{pdf_filename}"
    })

@app.route('/stk_push', methods=['POST'])
@handle_errors
def stk_push():
    data = request.json
    phone_number = data.get("phone_number")
    amount = data.get("amount")
    
    if not all([phone_number, amount]):
        return jsonify({"error": "Missing required parameters"}), 400

    access_token = DarajaAPI.generate_access_token()
    if not access_token:
        return jsonify({"error": "Could not generate access token"}), 500

    password, timestamp = DarajaAPI.generate_password()

    payload = {
        "BusinessShortCode": DARAJA_CONFIG['BUSINESS_SHORTCODE'],
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(float(amount)),
        "PartyA": phone_number,
        "PartyB": DARAJA_CONFIG['BUSINESS_SHORTCODE'],
        "PhoneNumber": phone_number,
        "CallBackURL": DARAJA_CONFIG['CALLBACK_URL'],
        "AccountReference": "BusinessPitch",
        "TransactionDesc": "Business Pitch Generator Payment"
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(DARAJA_CONFIG['API_URL'], json=payload, headers=headers)
    
    if response.ok:
        checkout_data = response.json()
        if 'CheckoutRequestID' in checkout_data:
            session['checkout_request_id'] = checkout_data['CheckoutRequestID']
            session['phone_number'] = phone_number
        return jsonify(checkout_data)
    
    return jsonify({"error": "Payment initiation failed"}), 500

@app.route('/callback', methods=['POST'])
@handle_errors
def callback():
    data = request.json
    logger.info(f"M-Pesa Callback Data: {json.dumps(data)}")
    
    callback_data = data.get('Body', {}).get('stkCallback', {})
    result_code = callback_data.get('ResultCode')
    
    if result_code == 0:
        items = callback_data.get('CallbackMetadata', {}).get('Item', [])
        transaction_data = {
            'amount': next((i['Value'] for i in items if i['Name'] == 'Amount'), None),
            'mpesa_receipt': next((i['Value'] for i in items if i['Name'] == 'MpesaReceiptNumber'), None),
            'transaction_date': next((i['Value'] for i in items if i['Name'] == 'TransactionDate'), None),
            'phone_number': next((i['Value'] for i in items if i['Name'] == 'PhoneNumber'), None)
        }
        
        db = get_db()
        db.execute(
            'INSERT INTO transactions (amount, mpesa_receipt, transaction_date, phone_number, status) VALUES (?, ?, ?, ?, ?)',
            [transaction_data['amount'], transaction_data['mpesa_receipt'], 
             transaction_data['transaction_date'], transaction_data['phone_number'], 'success']
        )
        db.commit()
        
        session['payment_verified'] = True
        session['phone_number'] = transaction_data['phone_number']
        
        return jsonify({"ResultCode": 0, "ResultDesc": "Success"})
    
    return jsonify({"ResultCode": 1, "ResultDesc": "Failed"})

@app.route('/download-pdf/<filename>')
@login_required
def download_pdf(filename):
    pdf_path = os.path.join(PDF_DIR, filename)
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True)
    return jsonify({"error": "File not found"}), 404

# Initialize the database
def init_app():
    with app.app_context():
        init_db()
        logger.info("Database initialized successfully")

if __name__ == '__main__':
    init_app()
    app.run(debug=True)