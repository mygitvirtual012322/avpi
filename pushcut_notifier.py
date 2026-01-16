"""
Pushcut Notification Module
Sends notifications via Pushcut API for PIX events
"""
import requests
import json
from datetime import datetime

# Pushcut API URLs
PUSHCUT_PIX_GENERATED_URL = "https://api.pushcut.io/XPTr5Kloj05Rr37Saz0D1/notifications/Pendente%20delivery"
PUSHCUT_PIX_PAID_URL = "https://api.pushcut.io/XPTr5Kloj05Rr37Saz0D1/notifications/Aprovado%20delivery"

def is_enabled():
    """Check if Pushcut notifications are enabled"""
    try:
        import admin_data_manager as adm
        config = adm.get_config()
        return config.get('pushcut_enabled', False)
    except:
        return False

def send_pix_generated(plate, amount, pix_code):
    """Send notification when PIX is generated"""
    if not is_enabled():
        print("Pushcut notifications disabled", flush=True)
        return False
    
    try:
        now = datetime.now().strftime('%d/%m/%Y %H:%M')
        message = f"💳 PIX Gerado!\n\n💰 Valor: R$ {amount:.2f}\n🚗 Placa: {plate}\n🕐 {now}\n\n✅ Aguardando pagamento..."
        
        payload = {
            "title": "Novo PIX Gerado",
            "text": message,
            "isTimeSensitive": True
        }
        
        print(f"Sending Pushcut notification: PIX Generated for {plate}", flush=True)
        response = requests.post(
            PUSHCUT_PIX_GENERATED_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code == 200:
            print(f"✓ Pushcut notification sent successfully", flush=True)
            return True
        else:
            print(f"✗ Pushcut notification failed: {response.status_code}", flush=True)
            return False
            
    except Exception as e:
        print(f"Error sending Pushcut notification: {e}", flush=True)
        return False

def send_pix_paid(plate, amount, transaction_id=None):
    """Send notification when PIX is paid"""
    if not is_enabled():
        print("Pushcut notifications disabled", flush=True)
        return False
    
    try:
        now = datetime.now().strftime('%d/%m/%Y %H:%M')
        message = f"✅ PIX Aprovado!\n\n💰 Valor: R$ {amount:.2f}\n🚗 Placa: {plate}\n🕐 {now}\n\n🎉 Pagamento confirmado!"
        
        if transaction_id:
            message += f"\n\n🔖 ID: {transaction_id}"
        
        payload = {
            "title": "PIX Pago - Sucesso!",
            "text": message,
            "isTimeSensitive": True
        }
        
        print(f"Sending Pushcut notification: PIX Paid for {plate}", flush=True)
        response = requests.post(
            PUSHCUT_PIX_PAID_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code == 200:
            print(f"✓ Pushcut notification sent successfully", flush=True)
            return True
        else:
            print(f"✗ Pushcut notification failed: {response.status_code}", flush=True)
            return False
            
    except Exception as e:
        print(f"Error sending Pushcut notification: {e}", flush=True)
        return False
