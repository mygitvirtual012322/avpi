import json
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
try:
    from selenium_stealth import stealth
    STEALTH_AVAILABLE = True
    print("INFO: selenium-stealth loaded successfully", flush=True)
except ImportError as e:
    print(f"WARNING: selenium-stealth not available: {e}", flush=True)
    STEALTH_AVAILABLE = False
    stealth = None
import time
import os
import sys # Added for logging
from config import IPVA_ALIQUOTA, PROMO_DISCOUNT_RATE, LICENSING_FEE

def get_car_info_from_ipvabr(plate):
    """
    Uses Selenium with Stealth to scrape vehicle info and Venal Value from ipvabr.com.br.
    Target URL: https://www.ipvabr.com.br/placa/{plate}
    """
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    # Point to the binary just in case
    if os.environ.get('CHROME_BIN'):
        print(f"DEBUG: Using Chrome Bin: {os.environ.get('CHROME_BIN')}", flush=True)
        options.binary_location = os.environ.get('CHROME_BIN')

    try:
        # Check for system chromedriver (Docker)
        system_driver_path = os.environ.get('CHROMEDRIVER_PATH', '/usr/bin/chromedriver')
        print(f"DEBUG: Checking driver path: {system_driver_path}", flush=True)
        
        if os.path.exists(system_driver_path):
            print("DEBUG: System driver found", flush=True)
            service = Service(system_driver_path)
        else:
            print("DEBUG: System driver NOT found, trying ChromeDriverManager", flush=True)
            # Fallback for local Mac/Windows
            service = Service(ChromeDriverManager().install())
            
        print("DEBUG: Initializing WebDriver...", flush=True)
        driver = webdriver.Chrome(service=service, options=options)
        print("DEBUG: WebDriver Initialized.", flush=True)
        
        # Apply Stealth if available
        if STEALTH_AVAILABLE:
            print("DEBUG: Applying Stealth...", flush=True)
            stealth(driver,
                languages=["pt-BR", "pt"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
            )
            print("DEBUG: Stealth Applied.", flush=True)
        else:
            print("DEBUG: Stealth not available, proceeding without it.", flush=True)
        
        print("DEBUG: Starting scrape...", flush=True)
        
    except Exception as e:
        print(f"Error initializing Chrome driver: {e}", flush=True)
        return None

    result_data = {}
    
    try:
        url = f"https://www.ipvabr.com.br/placa/{plate}"
        driver.get(url)
        
        # Wait for page load (reduced timeout for better performance)
        wait = WebDriverWait(driver, 15)
        
        # Wait for the Brand/Model table (looking for 'Marca:')
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, "//td[contains(text(), 'Marca:')]")))
        except:
            print(f"Timeout waiting for results for plate {plate}")
            print(f"DEBUG: Page Title: {driver.title}") # Log title to see if it's 403/Cloudflare
            return None
        
        # Helper to extract cell text next to a label
        def get_value_by_label(label_text):
            try:
                # Find TD with label, get next sibling TD
                elem = driver.find_element(By.XPATH, f"//td[contains(text(), '{label_text}')]/following-sibling::td")
                return elem.text.strip()
            except:
                return None

        brand = get_value_by_label("Marca:")
        model = get_value_by_label("Modelo:")
        
        if brand and model:
            result_data['brand_model'] = f"{brand} {model}"
        elif brand:
            result_data['brand_model'] = brand
        else:
            result_data['brand_model'] = None

        result_data['year'] = get_value_by_label("Ano Fabricação:")
        result_data['color'] = get_value_by_label("Cor:")
        result_data['fuel'] = get_value_by_label("Combustível:")
        result_data['engine'] = get_value_by_label("Motor:")
        result_data['state'] = get_value_by_label("Estado:")
        result_data['city'] = get_value_by_label("Município:")
        result_data['venal_value_str'] = get_value_by_label("Valor Venal") # e.g. "R$ 115.469,00"
        result_data['chassis'] = get_value_by_label("Chassi:")  # e.g. "*****M074366"
        
        # Try alternative labels if primary ones fail
        if not result_data['year']:
            result_data['year'] = get_value_by_label("Ano:")
            
        # Regex Fallback for Year (find 19xx or 20xx in the whole page text or specific cells)
        if not result_data['year']:
            try:
                # Search in all td elements for a year pattern
                tds = driver.find_elements(By.TAG_NAME, "td")
                for td in tds:
                    text = td.text
                    # Match 4 digits starting with 19 or 20, isolated or bound by non-digits
                    match = re.search(r'\b(19|20)\d{2}\b', text)
                    if match:
                        # Check if it looks like a model year (often near "Ano" or "Fabricação")
                        # This is a bit risky but better than null
                        # Check if it looks like a model year (often near "Ano" or "Fabricação")
                        try:
                            lbl_chk = td.find_element(By.XPATH, "./preceding-sibling::td").text
                        except:
                            lbl_chk = ""
                        
                        if "Ano" in lbl_chk or "Fabricação" in lbl_chk or "Modelo" in lbl_chk:
                            result_data['year'] = match.group(0)
                            break
            except:
                pass
        if not result_data['venal_value_str']:
            result_data['venal_value_str'] = get_value_by_label("Valor Venal:")
        
        # Specific fix for "Cor" and "Combustível" if sometimes they don't have colons or match exactly
        if not result_data['color']: result_data['color'] = get_value_by_label("Cor")
        if not result_data['fuel']: result_data['fuel'] = get_value_by_label("Combustível")
        if not result_data['state']: result_data['state'] = get_value_by_label("Estado")
        if not result_data['city']: result_data['city'] = get_value_by_label("Município")
        
        # DEBUG: Print scraped data
        print(f"DEBUG Scraped Data:", flush=True)
        print(f"  Brand/Model: {result_data.get('brand_model')}", flush=True)
        print(f"  Venal Value: {result_data.get('venal_value_str')}", flush=True)
        print(f"  Year: {result_data.get('year')}", flush=True)
        print(f"  Color: {result_data.get('color')}", flush=True)
        print(f"  State: {result_data.get('state')}", flush=True)
        print(f"  Chassis: {result_data.get('chassis')}", flush=True)
        
        # If we failed to get critical data
        if not result_data['brand_model']:
            print(f"DEBUG: Missing brand_model. Page title: {driver.title}", flush=True)
            print(f"DEBUG: Page source length: {len(driver.page_source)}", flush=True)
            return None
            
        if not result_data['venal_value_str']:
            print(f"DEBUG: Missing venal_value. Will try FIPE API as fallback.", flush=True)
            # Don't return None - let the function continue and return partial data
            # The FIPE fallback will handle this in calculate_ipva_data()
              
        # Parse Venal Value (only if we have it)
        if result_data.get('venal_value_str'):
            # Remove R$, dot, replace comma with dot
            raw_val = result_data['venal_value_str'].replace("R$", "").replace(".", "").replace(",", ".").strip()
            try:
                result_data['venal_value'] = float(raw_val)
            except ValueError:
                print(f"DEBUG: Error parsing venal value: {raw_val}")
                # Don't return None - let FIPE handle it
        
        return result_data
        
    except Exception as e:
        print(f"Error scraping ipvabr: {e}")
        return None
    finally:
        if 'driver' in locals():
            driver.quit()

def calculate_ipva_data(plate):
    print("=" * 50, flush=True)
    print(f"FUNCTION START: calculate_ipva_data({plate})", flush=True)
    print("=" * 50, flush=True)
    
    # 1. Scrape ipvabr.com.br
    print(f"Consulta placa {plate} no ipvabr.com.br...", flush=True)
    scraped_data = get_car_info_from_ipvabr(plate)
    
    if not scraped_data:
        print(f"ERROR: Failed to scrape data for plate {plate}", flush=True)
        return {"error": "Veículo não encontrado ou dados incompletos. Verifique a placa e tente novamente."}
    
    # If venal value is missing, try FIPE API as fallback
    if 'venal_value' not in scraped_data or not scraped_data.get('venal_value'):
        print(f"INFO: Venal value missing, trying FIPE API...", flush=True)
        from fipe_api import get_fipe_value
        
        brand_model = scraped_data.get('brand_model', '')
        year = scraped_data.get('year', '')
        
        # Extract brand and model
        parts = brand_model.split(' ', 1)
        brand = parts[0] if parts else ''
        model = parts[1] if len(parts) > 1 else brand_model
        
        fipe_value = get_fipe_value(brand, model, year)
        
        if fipe_value:
            print(f"SUCCESS: Got FIPE value: R$ {fipe_value:,.2f}", flush=True)
            scraped_data['venal_value'] = fipe_value
            scraped_data['venal_value_str'] = f"R$ {fipe_value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        else:
            print(f"ERROR: FIPE API also failed", flush=True)
            return {"error": "Não foi possível obter o valor do veículo. A API FIPE está temporariamente indisponível. Por favor, tente novamente em alguns minutos."}
        
    venal_val = scraped_data['venal_value']
    
    # 2. Calculate Values
    ipva_full = venal_val * IPVA_ALIQUOTA
    licensing = LICENSING_FEE
    total_full = ipva_full + licensing
    
    # Promo
    ipva_discounted = ipva_full * (1 - PROMO_DISCOUNT_RATE)
    total_discounted = ipva_discounted + licensing
    
    # Installments: 4 parcels of IPVA only (licensing paid with 1st installment)
    installment_val = ipva_discounted / 4
    
    # First payment = 1st installment + licensing fee
    first_payment = installment_val + licensing
    
    # Formatting
    def fmt(val):
        return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    return {
        "plate": plate,
        "brand": scraped_data['brand_model'],
        "year": scraped_data.get('year', '-'),
        "color": scraped_data.get('color', '-'),
        "fuel": scraped_data.get('fuel', '-'),
        "engine": scraped_data.get('engine', '-'),
        "state": scraped_data.get('state', '-'),
        "city": scraped_data.get('city', '-'),
        "venal_value": fmt(venal_val),
        "ipva_full": fmt(ipva_full),
        "licensing_val": fmt(licensing),
        "total_full": fmt(total_full),
        
        # Discounted
        "ipva_discounted": fmt(ipva_discounted),
        "total_with_discount": fmt(total_discounted),
        
        # Installments
        "installment_val": fmt(installment_val),
        "installments": 4,  # 4 parcelas
        
        # Additional fields
        "chassis": scraped_data.get('chassis', '-'),
        
        # Raw values for frontend math if needed
        "raw_total_discounted": total_discounted,
        "raw_installment_val": installment_val,  # Numeric value for calculations
        "raw_licensing_val": licensing,  # Numeric value for calculations
        "raw_first_payment_total": first_payment,  # Numeric value for PIX (1st installment + licensing)
        "first_payment_total": fmt(first_payment) # Formatted string for display
    }
