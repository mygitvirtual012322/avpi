from database import SessionLocal, Config, Consultation, PixGenerated
from datetime import datetime

# ===== CONFIG MANAGEMENT =====

def get_config():
    """Get current PIX configuration from database"""
    db = SessionLocal()
    try:
        config = db.query(Config).first()
        if not config:
            # Create default config
            config = Config(
                pix_key="00000000000",
                pix_name="SEF MG PAGAMENTOS",
                pix_city="BELO HORIZONTE",
                pix_description="IPVA 2026"
            )
            db.add(config)
            db.commit()
            db.refresh(config)
        
        return {
            "pix_key": config.pix_key,
            "pix_name": config.pix_name,
            "pix_city": config.pix_city,
            "pix_description": config.pix_description
        }
    finally:
        db.close()

def save_config(pix_key, pix_name, pix_city):
    """Save PIX configuration to database"""
    db = SessionLocal()
    try:
        config = db.query(Config).first()
        if config:
            config.pix_key = pix_key
            config.pix_name = pix_name
            config.pix_city = pix_city
            config.updated_at = datetime.utcnow()
        else:
            config = Config(
                pix_key=pix_key,
                pix_name=pix_name,
                pix_city=pix_city,
                pix_description="IPVA 2026"
            )
            db.add(config)
        
        db.commit()
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        db.rollback()
        return False
    finally:
        db.close()

# ===== CONSULTAS TRACKING =====

def log_consulta(plate, vehicle, ipva_value):
    """Log a new vehicle consultation to database"""
    db = SessionLocal()
    try:
        consulta = Consultation(
            plate=plate,
            vehicle=vehicle,
            ipva_value=ipva_value
        )
        db.add(consulta)
        db.commit()
        return True
    except Exception as e:
        print(f"Error logging consultation: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def get_consultas():
    """Get all consultations from database (last 100)"""
    db = SessionLocal()
    try:
        consultas = db.query(Consultation)\
            .order_by(Consultation.timestamp.desc())\
            .limit(100)\
            .all()
        
        return [{
            "timestamp": c.timestamp.strftime("%d/%m/%Y %H:%M:%S"),
            "plate": c.plate,
            "vehicle": c.vehicle,
            "ipva_value": c.ipva_value
        } for c in consultas]
    finally:
        db.close()

# ===== PIX TRACKING =====

def log_pix(plate, amount, pix_code):
    """Log a generated PIX code to database"""
    db = SessionLocal()
    try:
        pix = PixGenerated(
            plate=plate,
            amount=amount,
            code=pix_code
        )
        db.add(pix)
        db.commit()
        return True
    except Exception as e:
        print(f"Error logging PIX: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def get_pix_generated():
    """Get all generated PIX codes from database (last 100)"""
    db = SessionLocal()
    try:
        pix_list = db.query(PixGenerated)\
            .order_by(PixGenerated.timestamp.desc())\
            .limit(100)\
            .all()
        
        return [{
            "timestamp": p.timestamp.strftime("%d/%m/%Y %H:%M:%S"),
            "plate": p.plate,
            "amount": p.amount,
            "code": p.code
        } for p in pix_list]
    finally:
        db.close()

# ===== STATS =====

def get_stats():
    """Get dashboard statistics from database"""
    db = SessionLocal()
    try:
        consultas_count = db.query(Consultation).count()
        pix_count = db.query(PixGenerated).count()
        
        # Calculate total value from PIX
        pix_list = db.query(PixGenerated).all()
        total_value = 0
        for pix in pix_list:
            try:
                # Extract numeric value from "R$ 247,22" format
                amount_str = pix.amount.replace('R$', '').replace('.', '').replace(',', '.').strip()
                total_value += float(amount_str)
            except:
                pass
        
        total_value_formatted = f"R$ {total_value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        # Get recent data
        consultas_list = get_consultas()[:20]
        pix_list_formatted = get_pix_generated()[:20]
        
        return {
            "consultas": consultas_count,
            "pix_gerados": pix_count,
            "usuarios_online": 0,  # Will be handled by session_tracker
            "valor_total": total_value_formatted,
            "consultas_list": consultas_list,
            "pix_list": pix_list_formatted,
            "online_users": []  # Will be handled by session_tracker
        }
    finally:
        db.close()

# Legacy function for compatibility (no longer needed with PostgreSQL)
def log_pix_generated(plate, amount, pix_code):
    """Alias for log_pix for backward compatibility"""
    return log_pix(plate, amount, pix_code)
