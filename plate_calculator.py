import json
import requests
from bs4 import BeautifulSoup
import re
from config import IPVA_ALIQUOTA, PROMO_DISCOUNT_RATE, LICENSING_FEE

def get_car_info_from_ipvabr(plate):
    """
    Uses Requests + BeautifulSoup to scrape vehicle info.
    """
    url = f"https://www.ipvabr.com.br/placa/{plate}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.google.com/",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-User": "?1",
        "Connection": "keep-alive"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        # Cloudflare Blocking Handling
        if response.status_code == 403 or response.status_code == 503:
            print(f"DEBUG: Blocked by Cloudflare (Status {response.status_code}).")
            return None
        
        if response.status_code != 200:
            print(f"DEBUG: Failed to fetch page. Status: {response.status_code}")
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        result_data = {}
        
        # Helper to find data in the table structure of ipvabr.com.br
        # Expected structure: <td>Label:</td> <td>Value</td>
        def get_value_by_label(label_text):
            # Find the td containing the label
            label_td = soup.find('td', string=lambda text: text and label_text in text)
            if label_td:
                # Get the next sibling td which contains the value
                value_td = label_td.find_next_sibling('td')
                if value_td:
                    return value_td.get_text(strip=True)
            return None

        # Data Extraction
        brand = get_value_by_label("Marca:")
        model = get_value_by_label("Modelo:")
        
        if brand and model:
            result_data['brand_model'] = f"{brand} {model}"
        elif brand:
             result_data['brand_model'] = brand
        elif model:
             result_data['brand_model'] = model
        else:
            result_data['brand_model'] = None

        result_data['year'] = get_value_by_label("Ano Fabricação:")
        result_data['color'] = get_value_by_label("Cor:")
        result_data['fuel'] = get_value_by_label("Combustível:")
        result_data['state'] = get_value_by_label("Estado:")
        result_data['city'] = get_value_by_label("Município:") 
        result_data['chassis'] = get_value_by_label("Chassi:")
        result_data['engine'] = get_value_by_label("Motor:")
        result_data['venal_value_str'] = get_value_by_label("Valor Venal") # e.g. "R$ 115.469,00"
        
        # Fallbacks for labels without colon
        if not result_data['color']: result_data['color'] = get_value_by_label("Cor")
        if not result_data['fuel']: result_data['fuel'] = get_value_by_label("Combustível")
        if not result_data['state']: result_data['state'] = get_value_by_label("Estado")
        if not result_data['city']: result_data['city'] = get_value_by_label("Município")
        
        # If we failed to get critical data, try alternative parsing (sometimes labels are different)
        if not result_data['brand_model']:
            # Fallback: Try to grab from title or other elements if specific table structure fails
            # But for now, valid check is enough
            pass

        if not result_data['venal_value_str']:
             print(f"DEBUG: Critical data missing (Venal Value). Data found: {json.dumps(result_data)}")
             # Fallback for old cars or different layout?
             # Let's try to find any price looking string if specific label fails
             pass

        if not result_data['brand_model'] or not result_data['venal_value_str']:
             print(f"DEBUG: Missing critical info. {result_data}")
             return None
             
        # Parse Venal Value
        # "R$ 115.469,00" -> 115469.00
        try:
            raw_val = result_data['venal_value_str'].replace("R$", "").replace(".", "").replace(",", ".").strip()
            result_data['venal_value'] = float(raw_val)
        except ValueError:
            print(f"DEBUG: Could not parse value: {result_data['venal_value_str']}")
            return None
        
        return result_data

    except Exception as e:
        print(f"Error scraping ipvabr with requests: {e}")
        return None

def calculate_ipva_data(plate):
    # 1. Scrape ipvabr.com.br
    print(f"Consulta placa {plate} no ipvabr.com.br (via requests)...")
    scraped_data = get_car_info_from_ipvabr(plate)
    
    if not scraped_data:
        # Fallback Mock Data if scraping fails (to prevent 500 error in demo)
        # Uncomment below to enable fallback or just return Error
        return {"error": "Veículo não encontrado ou serviço indisponível."}
        
    venal_val = scraped_data['venal_value']
    
    # 2. Calculate Tax (using configured aliquota)
    ipva_full = venal_val * IPVA_ALIQUOTA
    
    # 3. Apply Promo Discount (from config)
    ipva_discounted = ipva_full * (1 - PROMO_DISCOUNT_RATE)
    
    # 4. Installments & Licensing (from config)
    licensing_val = LICENSING_FEE
    
    # The discounted IPVA is split into 4 installments
    installment_val = ipva_discounted / 4
    
    # First payment MUST include Licensing
    # This is the key "hook"
    first_payment_total = installment_val + licensing_val

    # Format Currency Helper
    def fmt(val):
        return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    return {
        "plate": plate.upper(),
        "brand": scraped_data['brand_model'],
        "vehicle": scraped_data['brand_model'],
        "model": scraped_data['brand_model'],
        "year": scraped_data['year'],
        "color": scraped_data['color'],
        "fuel": scraped_data['fuel'],
        "state": scraped_data['state'],
        "city": scraped_data['city'],
        "chassis": scraped_data['chassis'],
        "engine": scraped_data['engine'],
        "fipe_value": scraped_data['venal_value_str'],
        "ipva_full": fmt(ipva_full),
        "ipva_discounted": fmt(ipva_discounted), # Total to pay (IPVA only)
        "licensing_val": fmt(licensing_val),
        "discount_saved": fmt(ipva_full * PROMO_DISCOUNT_RATE),
        "installment_val": fmt(installment_val),
        "first_payment_total": fmt(first_payment_total),
        
        # Raw values for PIX generation (frontend can pass these back or we recalculate)
        "raw_installment_val": installment_val,
        "raw_licensing_val": licensing_val,
        "raw_first_payment_total": first_payment_total
    }

if __name__ == "__main__":
    test_plate = "RJU0H81"
    print(f"Testing calculator with plate: {test_plate}...")
    result = calculate_ipva_data(test_plate)
    print(json.dumps(result, indent=4, ensure_ascii=False))
