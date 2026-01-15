def crc16_ccitt(data):
    """
    Calculates CRC16-CCITT (0x1021) for the given string data.
    """
    crc = 0xFFFF
    polynomial = 0x1021

    for char in data:
        byte = ord(char)
        crc ^= (byte << 8)
        for _ in range(8):
            if (crc & 0x8000):
                crc = (crc << 1) ^ polynomial
            else:
                crc = crc << 1
            crc &= 0xFFFF
            
    return crc

def generate_pix_payload(pix_key, name, city, amount, txid="***"):
    """
    Generates a static PIX payload (Copy and Paste code).
    """
    
    # helper to format TLV (Type-Length-Value)
    def f(id, value):
        return f"{id:02}{len(value):02}{value}"

    # 1. Basic Fields
    payload = f("00", "01")
    
    # 2. Merchant Account (26)
    gui = f("00", "br.gov.bcb.pix")
    key = f("01", pix_key)
    merchant_account = f("26", gui + key)
    payload += merchant_account
    
    # 3. MCC (52)
    payload += f("52", "0000")
    
    # 4. Currency (53)
    payload += f("53", "986")
    
    # 5. Amount (54)
    amt_str = f"{amount:.2f}"
    payload += f("54", amt_str)
    
    # 6. Country (58)
    payload += f("58", "BR")
    
    # 7. Name (59)
    name = name[:25]
    payload += f("59", name)
    
    # 8. City (60)
    city = city[:15]
    payload += f("60", city)
    
    # 9. Additional Data (62) - TXID
    txid_field = f("05", txid)
    payload += f("62", txid_field)
    
    # 10. CRC16 (63)
    payload += "6304"
    
    # Calculate CRC16
    crc_val = crc16_ccitt(payload)
    crc_hex = hex(crc_val)[2:].upper().zfill(4)
    
    return payload + crc_hex
