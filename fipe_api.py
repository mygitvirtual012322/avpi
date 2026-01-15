import requests
import re

def get_fipe_value(brand, model, year):
    """
    Get FIPE value for a vehicle using free FIPE API
    Returns: float value or None
    """
    try:
        print(f"DEBUG FIPE: Searching for {brand} {model} {year}", flush=True)
        
        # Clean up brand and model
        brand = brand.upper().strip()
        model = model.upper().strip()
        
        # Try BrasilAPI first (more reliable)
        # https://brasilapi.com.br/api/fipe/preco/v1/{codigo_fipe}
        # But we need to search first
        
        # Use parallelquery FIPE API (free, no auth needed)
        base_url = "https://parallelum.com.br/fipe/api/v1"
        
        # 1. Get vehicle type (assuming cars = 1)
        vehicle_type = "carros"
        
        # 2. Get brands
        brands_url = f"{base_url}/{vehicle_type}/marcas"
        brands_response = requests.get(brands_url, timeout=10)
        brands = brands_response.json()
        
        # Find matching brand
        brand_code = None
        for b in brands:
            if brand.lower() in b['nome'].lower() or b['nome'].lower() in brand.lower():
                brand_code = b['codigo']
                print(f"DEBUG FIPE: Found brand {b['nome']} (code: {brand_code})", flush=True)
                break
        
        if not brand_code:
            print(f"DEBUG FIPE: Brand not found: {brand}", flush=True)
            return None
        
        # 3. Get models for this brand
        models_url = f"{base_url}/{vehicle_type}/marcas/{brand_code}/modelos"
        models_response = requests.get(models_url, timeout=10)
        models_data = models_response.json()
        
        # Find matching model
        model_code = None
        for m in models_data.get('modelos', []):
            model_name = m['nome'].upper()
            # Fuzzy match - check if key words match
            if any(word in model_name for word in model.split() if len(word) > 3):
                model_code = m['codigo']
                print(f"DEBUG FIPE: Found model {m['nome']} (code: {model_code})", flush=True)
                break
        
        if not model_code:
            print(f"DEBUG FIPE: Model not found: {model}", flush=True)
            return None
        
        # 4. Get years for this model
        years_url = f"{base_url}/{vehicle_type}/marcas/{brand_code}/modelos/{model_code}/anos"
        years_response = requests.get(years_url, timeout=10)
        years_data = years_response.json()
        
        # Find matching year
        year_code = None
        for y in years_data:
            if str(year) in y['nome']:
                year_code = y['codigo']
                print(f"DEBUG FIPE: Found year {y['nome']} (code: {year_code})", flush=True)
                break
        
        if not year_code:
            print(f"DEBUG FIPE: Year not found: {year}", flush=True)
            return None
        
        # 5. Get FIPE value
        value_url = f"{base_url}/{vehicle_type}/marcas/{brand_code}/modelos/{model_code}/anos/{year_code}"
        value_response = requests.get(value_url, timeout=10)
        value_data = value_response.json()
        
        fipe_value_str = value_data.get('Valor', '')
        print(f"DEBUG FIPE: Raw value: {fipe_value_str}", flush=True)
        
        # Parse value "R$ 45.000,00" -> 45000.00
        if fipe_value_str:
            clean_value = fipe_value_str.replace('R$', '').replace('.', '').replace(',', '.').strip()
            fipe_value = float(clean_value)
            print(f"DEBUG FIPE: Parsed value: {fipe_value}", flush=True)
            return fipe_value
        
        return None
        
    except Exception as e:
        print(f"ERROR FIPE: {e}", flush=True)
        return None
