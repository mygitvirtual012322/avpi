from database import SessionLocal, Order
from datetime import datetime, timedelta

class OrderManager:
    """Manage complete order data with vehicle details and installments using PostgreSQL"""
    
    def create_order(self, session_id, vehicle_data, payment_data):
        """Create new order with complete data in database"""
        db = SessionLocal()
        try:
            # Count existing orders to generate ID
            order_count = db.query(Order).count()
            
            # Calculate installments
            installments = []
            for i in range(4):
                installments.append({
                    'number': i + 1,
                    'value': payment_data.get('installment_val'),
                    'due_date': self._calculate_due_date(i),
                    'includes_licensing': (i == 0),
                    'total': payment_data.get('first_payment_total') if i == 0 else payment_data.get('installment_val')
                })
            
            order = Order(
                order_id=f"ORD-{order_count + 1:05d}",
                session_id=session_id,
                
                # Vehicle data
                plate=vehicle_data.get('plate'),
                brand=vehicle_data.get('brand'),
                model=vehicle_data.get('model'),
                year=vehicle_data.get('year'),
                color=vehicle_data.get('color'),
                fuel=vehicle_data.get('fuel'),
                state=vehicle_data.get('state'),
                city=vehicle_data.get('city'),
                chassis=vehicle_data.get('chassis'),
                engine=vehicle_data.get('engine'),
                
                # Payment data
                ipva_original=payment_data.get('ipva_full'),
                ipva_discounted=payment_data.get('ipva_discounted'),
                licensing_fee=payment_data.get('licensing_val'),
                installment_count=4,
                installment_value=payment_data.get('installment_val'),
                first_payment_total=payment_data.get('first_payment_total'),
                discount_percentage=70,
                
                # Installments
                installments=installments
            )
            
            db.add(order)
            db.commit()
            db.refresh(order)
            
            return {
                'order_id': order.order_id,
                'session_id': order.session_id,
                'created_at': order.created_at.isoformat()
            }
        except Exception as e:
            print(f"Error creating order: {e}")
            db.rollback()
            return None
        finally:
            db.close()
    
    def _calculate_due_date(self, months_offset):
        """Calculate due date for installment"""
        today = datetime.utcnow()
        # Simple approximation: 30 days per month
        due_date = today + timedelta(days=30 * months_offset)
        return due_date.strftime('%d/%m/%Y')
    
    def mark_pix_generated(self, session_id, pix_code):
        """Mark that PIX was generated for this order"""
        db = SessionLocal()
        try:
            order = db.query(Order).filter(Order.session_id == session_id).first()
            if order:
                order.pix_generated = True
                order.pix_generated_at = datetime.utcnow()
                order.pix_code = pix_code
                db.commit()
                return True
            return False
        except Exception as e:
            print(f"Error marking PIX generated: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def mark_pix_copied(self, session_id):
        """Mark that PIX code was copied"""
        db = SessionLocal()
        try:
            order = db.query(Order).filter(Order.session_id == session_id).first()
            if order:
                order.pix_copied = True
                order.pix_copied_at = datetime.utcnow()
                db.commit()
                return True
            return False
        except Exception as e:
            print(f"Error marking PIX copied: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def get_all_orders(self):
        """Get all orders from database"""
        db = SessionLocal()
        try:
            orders = db.query(Order).order_by(Order.created_at.desc()).all()
            
            return [{
                'order_id': o.order_id,
                'session_id': o.session_id,
                'created_at': o.created_at.isoformat(),
                'vehicle': {
                    'plate': o.plate,
                    'brand': o.brand,
                    'model': o.model,
                    'year': o.year,
                    'color': o.color,
                    'fuel': o.fuel,
                    'state': o.state,
                    'city': o.city,
                    'chassis': o.chassis,
                    'engine': o.engine
                },
                'payment': {
                    'ipva_original': o.ipva_original,
                    'ipva_discounted': o.ipva_discounted,
                    'licensing_fee': o.licensing_fee,
                    'installment_count': o.installment_count,
                    'installment_value': o.installment_value,
                    'first_payment_total': o.first_payment_total,
                    'discount_percentage': o.discount_percentage
                },
                'installments': o.installments,
                'pix_generated': o.pix_generated,
                'pix_generated_at': o.pix_generated_at.isoformat() if o.pix_generated_at else None,
                'pix_copied': o.pix_copied,
                'pix_copied_at': o.pix_copied_at.isoformat() if o.pix_copied_at else None,
                'pix_code': o.pix_code
            } for o in orders]
        finally:
            db.close()
    
    def get_order_by_session(self, session_id):
        """Get order by session ID"""
        db = SessionLocal()
        try:
            order = db.query(Order).filter(Order.session_id == session_id).first()
            if not order:
                return None
            
            return {
                'order_id': order.order_id,
                'session_id': order.session_id,
                'created_at': order.created_at.isoformat(),
                'vehicle': {
                    'plate': order.plate,
                    'brand': order.brand
                },
                'payment': {
                    'ipva_original': order.ipva_original,
                    'ipva_discounted': order.ipva_discounted
                },
                'pix_generated': order.pix_generated,
                'pix_copied': order.pix_copied
            }
        finally:
            db.close()
    
    def get_stats(self):
        """Get order statistics"""
        db = SessionLocal()
        try:
            total_orders = db.query(Order).count()
            pix_generated = db.query(Order).filter(Order.pix_generated == True).count()
            pix_copied = db.query(Order).filter(Order.pix_copied == True).count()
            
            # Calculate total value
            orders = db.query(Order).all()
            total_value = sum(
                float(o.first_payment_total.replace('R$ ', '').replace('.', '').replace(',', '.'))
                for o in orders
                if o.first_payment_total
            )
            
            return {
                'total_orders': total_orders,
                'pix_generated': pix_generated,
                'pix_copied': pix_copied,
                'conversion_rate': (pix_copied / total_orders * 100) if total_orders > 0 else 0,
                'total_value': f"R$ {total_value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            }
        finally:
            db.close()

# Global instance
order_manager = OrderManager()
