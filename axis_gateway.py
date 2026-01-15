import requests
import base64
import json
import os
from datetime import datetime

# Configuration file
AXIS_CONFIG_FILE = 'admin_data/axis_config.json'

def get_axis_config():
    """Get Axis Banking configuration"""
    os.makedirs('admin_data', exist_ok=True)
    
    if not os.path.exists(AXIS_CONFIG_FILE):
        # Default config
        default_config = {
            'enabled': False,
            'api_key': '',
            'postback_url': '',
            'updated_at': datetime.now().isoformat()
        }
        with open(AXIS_CONFIG_FILE, 'w') as f:
            json.dump(default_config, f, indent=2)
        return default_config
    
    with open(AXIS_CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_axis_config(enabled, api_key, postback_url):
    """Save Axis Banking configuration"""
    os.makedirs('admin_data', exist_ok=True)
    
    config = {
        'enabled': enabled,
        'api_key': api_key,
        'postback_url': postback_url,
        'updated_at': datetime.now().isoformat()
    }
    
    with open(AXIS_CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    
    return config

def is_axis_enabled():
    """Check if Axis integration is enabled"""
    config = get_axis_config()
    return config.get('enabled', False) and config.get('api_key', '')

def generate_auth_header(api_key):
    """Generate Basic Auth header for Axis API"""
    # Format: Basic base64(secret:API_KEY)
    auth_string = f"secret:{api_key}"
    encoded = base64.b64encode(auth_string.encode()).decode()
    return f"Basic {encoded}"

def generate_axis_pix(name, email, cpf, phone, amount, description, external_id, plate=''):
    """
    Generate PIX payment via Axis Banking API
    
    Args:
        name: Customer name
        email: Customer email
        cpf: Customer CPF (numbers only)
        phone: Customer phone (numbers only)
        amount: Amount in BRL (float, e.g., 354.80)
        description: Payment description
        external_id: Unique order ID
        plate: Vehicle plate (optional, for description)
    
    Returns:
        dict: {
            'success': bool,
            'pix_code': str (if success),
            'qr_code': str (if success),
            'transaction_id': str (if success),
            'error': str (if failure)
        }
    """
    try:
        print(f"DEBUG AXIS: Generating PIX for {name} - R$ {amount:.2f}", flush=True)
        
        config = get_axis_config()
        api_key = config.get('api_key')
        postback_url = config.get('postback_url', '')
        
        if not api_key:
            return {'success': False, 'error': 'Axis API key not configured'}
        
        # Convert amount to centavos (integer)
        amount_centavos = int(amount * 100)
        
        # Build description
        full_description = f"{description} - Placa {plate}" if plate else description
        
        # Prepare payload
        payload = {
            "name": name,
            "email": email,
            "cpf": cpf,
            "phone": phone,
            "amount": amount_centavos,
            "description": full_description[:100],  # Limit description
            "responsibleDocument": cpf,
            "responsibleExternalId": external_id,
            "externalId": external_id,
            "postbackUrl": postback_url,
            "paymentMethod": "PIX",
            "currency": "BRL"
        }
        
        # Generate auth header
        auth_header = generate_auth_header(api_key)
        
        # Make API request
        headers = {
            'Authorization': auth_header,
            'Content-Type': 'application/json'
        }
        
        print(f"DEBUG AXIS: Calling API...", flush=True)
        response = requests.post(
            'https://api.axisbanking.com.br/transactions/v2/purchase',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"DEBUG AXIS: Response status: {response.status_code}", flush=True)
        
        if response.status_code == 200 or response.status_code == 201:
            data = response.json()
            print(f"DEBUG AXIS: Success! Transaction ID: {data.get('transactionId')}", flush=True)
            
            return {
                'success': True,
                'pix_code': data.get('pixCode', ''),
                'qr_code': data.get('qrCode', ''),
                'transaction_id': data.get('transactionId', ''),
                'expires_at': data.get('expiresAt', '')
            }
        else:
            error_msg = response.text
            print(f"ERROR AXIS: {response.status_code} - {error_msg}", flush=True)
            return {
                'success': False,
                'error': f'Axis API error: {response.status_code}'
            }
            
    except requests.exceptions.Timeout:
        print(f"ERROR AXIS: Timeout", flush=True)
        return {'success': False, 'error': 'Axis API timeout'}
    except Exception as e:
        print(f"ERROR AXIS: {str(e)}", flush=True)
        return {'success': False, 'error': str(e)}

def test_axis_connection():
    """Test Axis API connection with a minimal request"""
    try:
        config = get_axis_config()
        api_key = config.get('api_key')
        
        if not api_key:
            return {'success': False, 'error': 'API key not configured'}
        
        # Test with minimal payload (R$ 0.01)
        result = generate_axis_pix(
            name="Test User",
            email="test@example.com",
            cpf="12345678901",
            phone="11999999999",
            amount=0.01,
            description="Test transaction",
            external_id=f"test_{datetime.now().timestamp()}"
        )
        
        return result
        
    except Exception as e:
        return {'success': False, 'error': str(e)}
