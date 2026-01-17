import json
import os
from datetime import datetime

ORDERS_FILE = 'admin_data/orders.json'

class OrderManager:
    """Manage complete order data with vehicle details and installments"""
    
    def __init__(self):
        os.makedirs('admin_data', exist_ok=True)
        self.orders = self._load_orders()
    
    def _load_orders(self):
        """Load orders from file"""
        if os.path.exists(ORDERS_FILE):
            with open(ORDERS_FILE, 'r') as f:
                return json.load(f)
        return []
    
    def _save_orders(self):
        """Save orders to file"""
        with open(ORDERS_FILE, 'w') as f:
            json.dump(self.orders, f, indent=2, ensure_ascii=False)
    
    def create_order(self, session_id, vehicle_data, payment_data, renavam=None, status="Sucesso", duration_ms=None, is_error=False):
        """Create a new order or update existing pending one"""
        plate = vehicle_data.get('plate')
        
        # Check for existing pending order (same plate, last 24h)
        # Only reuse if NOT an error and NOT a specific renavam search that differs
        existing = self._find_recent_pending_order(plate) if not is_error else None
        
        if existing and not is_error:
            print(f"♻️ Reusing existing order {existing['order_id']} for plate {plate}", flush=True)
            existing['session_id'] = session_id  # Update session
            existing['created_at'] = datetime.now().isoformat() # Bump to top
            
            # Update tracking info
            if renavam: existing['renavam'] = renavam
            if status: existing['status'] = status
            if duration_ms: existing['duration_ms'] = duration_ms
            
            # Update values in case they changed (although unlikely for same car)
            existing['vehicle'] = {
                'plate': plate,
                'brand': vehicle_data.get('brand'),
                'model': vehicle_data.get('model'),
                'year': vehicle_data.get('year'),
                'color': vehicle_data.get('color'),
                'fuel': vehicle_data.get('fuel'),
                'state': vehicle_data.get('state'),
                'city': vehicle_data.get('city'),
                'chassis': vehicle_data.get('chassis'),
                'engine': vehicle_data.get('engine')
            }
            # Keep payment data fresh too
            existing['payment'] = {
                'ipva_original': payment_data.get('ipva_full'),
                'ipva_discounted': payment_data.get('ipva_discounted'),
                'licensing_fee': payment_data.get('licensing_val'),
                'installment_count': 4,
                'installment_value': payment_data.get('installment_val'),
                'first_payment_total': payment_data.get('first_payment_total'),
                'discount_percentage': 70
            }
            
            self._save_orders()
            return existing

        # If no existing pending order, create a new one
        order_id = f"ORD-{len(self.orders) + 1:05d}"
        order = {
            'order_id': order_id,
            'session_id': session_id,
            'created_at': datetime.now().isoformat(),
            'renavam': renavam,
            'status': status,
            'duration_ms': duration_ms,
            'is_error': is_error,
            
            # Vehicle data
            'vehicle': {
                'plate': vehicle_data.get('plate'),
                'brand': vehicle_data.get('brand'),
                'model': vehicle_data.get('model'),
                'year': vehicle_data.get('year'),
                'color': vehicle_data.get('color'),
                'fuel': vehicle_data.get('fuel'),
                'state': vehicle_data.get('state'),
                'city': vehicle_data.get('city'),
                'chassis': vehicle_data.get('chassis'),
                'engine': vehicle_data.get('engine')
            },
            
            # Payment data
            'payment': {
                'ipva_original': payment_data.get('ipva_full'),
                'ipva_discounted': payment_data.get('ipva_discounted'),
                'licensing_fee': payment_data.get('licensing_val'),
                'installment_count': 4,
                'installment_value': payment_data.get('installment_val'),
                'first_payment_total': payment_data.get('first_payment_total'),
                'discount_percentage': 70
            },
            
            # Installments detail
            'installments': [
                {
                    'number': 1,
                    'value': payment_data.get('installment_val'),
                    'due_date': self._calculate_due_date(0),
                    'includes_licensing': True,
                    'total': payment_data.get('first_payment_total')
                },
                {
                    'number': 2,
                    'value': payment_data.get('installment_val'),
                    'due_date': self._calculate_due_date(1),
                    'includes_licensing': False,
                    'total': payment_data.get('installment_val')
                },
                {
                    'number': 3,
                    'value': payment_data.get('installment_val'),
                    'due_date': self._calculate_due_date(2),
                    'includes_licensing': False,
                    'total': payment_data.get('installment_val')
                },
                {
                    'number': 4,
                    'value': payment_data.get('installment_val'),
                    'due_date': self._calculate_due_date(3),
                    'includes_licensing': False,
                    'total': payment_data.get('installment_val')
                }
            ] if not is_error else [],
            
            # Tracking
            'pix_generated': False,
            'pix_generated_at': None,
            'pix_copied': False,
            'pix_copied_at': None,
            'pix_code': None
        }
        
        self.orders.append(order)
        self._save_orders()
        return order
    
    def _calculate_due_date(self, months_offset):
        """Calculate due date for installment"""
        from datetime import timedelta
        today = datetime.now()
        # Simple approximation: 30 days per month
        due_date = today + timedelta(days=30 * months_offset)
        return due_date.strftime('%d/%m/%Y')
    
    def get_pix_by_session_and_plate(self, session_id, plate):
        """Get existing PIX code for session and plate combination"""
        for order in self.orders:
            if (order.get("session_id") == session_id and order.get("vehicle", {}).get("plate") == plate and order.get("pix_code")):
                print(f"✓ Found existing PIX for session {session_id}, plate {plate}", flush=True)
                return {"pix_code": order.get("pix_code"), "order_id": order.get("order_id"), "pix_generated_at": order.get("pix_generated_at")}
        return None


    def mark_pix_generated(self, session_id, pix_code):
        """Mark that PIX was generated for this order"""
        for order in self.orders:
            if order['session_id'] == session_id:
                order['pix_generated'] = True
                order['pix_generated_at'] = datetime.now().isoformat()
                order['pix_code'] = pix_code
                self._save_orders()
                return True
        return False
    
    def mark_pix_copied(self, session_id):
        """Mark that PIX code was copied"""
        for order in self.orders:
            if order['session_id'] == session_id:
                order['pix_copied'] = True
                order['pix_copied_at'] = datetime.now().isoformat()
                self._save_orders()
                return True
        return False
    
    def get_all_orders(self):
        """Get all orders sorted by date (newest first)"""
        return sorted(self.orders, key=lambda x: x['created_at'], reverse=True)

    def _find_recent_pending_order(self, plate):
        """Find a recent pending order (no PIX) for the same plate in last 24h"""
        if not plate: return None
        
        now = datetime.now()
        for order in self.orders:
            # Check plate
            if order.get('vehicle', {}).get('plate') != plate:
                continue
                
            # Check if PIX already generated (if so, we want a new order)
            if order.get('pix_generated'):
                continue
                
            # Check time (last 24h)
            try:
                created_at = datetime.fromisoformat(order['created_at'])
                if (now - created_at).total_seconds() < 86400: # 24 hours
                    return order
            except:
                pass
        return None
        
    def delete_orders(self, order_ids):
        """Delete specific orders by ID"""
        original_count = len(self.orders)
        self.orders = [o for o in self.orders if o['order_id'] not in order_ids]
        if len(self.orders) < original_count:
            self._save_orders()
            return True
        return False
        
    def delete_all_orders(self):
        """Delete ALL orders"""
        self.orders = []
        self._save_orders()
        return True
    
    def get_order_by_session(self, session_id):
        """Get order by session ID"""
        for order in self.orders:
            if order['session_id'] == session_id:
                return order
        return None
    
    def get_stats(self):
        """Get order statistics"""
        total_orders = len(self.orders)
        pix_generated = sum(1 for o in self.orders if o['pix_generated'])
        pix_copied = sum(1 for o in self.orders if o['pix_copied'])
        
        total_value = sum(
            float(o['payment']['first_payment_total'].replace('R$ ', '').replace('.', '').replace(',', '.'))
            for o in self.orders
            if o.get('payment', {}).get('first_payment_total')
        )
        
        return {
            'total_orders': total_orders,
            'pix_generated': pix_generated,
            'pix_copied': pix_copied,
            'conversion_rate': (pix_copied / total_orders * 100) if total_orders > 0 else 0,
            'total_value': f"R$ {total_value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        }

# Global instance
order_manager = OrderManager()
