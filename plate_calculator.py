import json
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
from config import IPVA_ALIQUOTA, PROMO_DISCOUNT_RATE, LICENSING_FEE

def get_car_info_from_ipvabr(plate):
    """
    Uses Selenium to scrape vehicle info and Venal Value from ipvabr.com.br.
    Target URL: https://www.ipvabr.com.br/placa/{plate}
    """
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
    
    # Performance Optimizations
    options.page_load_strategy = 'eager' # Don't wait for full load
    prefs = {"profile.managed_default_content_settings.images": 2, "profile.default_content_settings.css": 2}
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    result_data = {}
    
    try:
        url = f"https://www.ipvabr.com.br/placa/{plate}"
        driver.get(url)
        wait = WebDriverWait(driver, 15)
        
        # Wait for the Brand/Model table (looking for 'Marca:')
        wait.until(EC.presence_of_element_located((By.XPATH, "//td[contains(text(), 'Marca:')]")))
        
        # Helper to extract cell text next to a label
        def get_value_by_label(label_text):
            try:
                # Find TD with label, get next sibling TD
                # Use normalize-space to handle whitespace issues
                elem = driver.find_element(By.XPATH, f"//td[contains(text(), '{label_text}')]/following-sibling::td")
                return elem.text.strip()
            except:
                return None

        brand = get_value_by_label("Marca:")
        model = get_value_by_label("Modelo:")
        
        if brand and model:
            result_data['brand_model'] = f"{brand} {model}"
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
        
        # Specific fix for "Cor" and "Combustível" sometimes having colons or not
        if not result_data['color']: result_data['color'] = get_value_by_label("Cor")
        if not result_data['fuel']: result_data['fuel'] = get_value_by_label("Combustível")
        if not result_data['state']: result_data['state'] = get_value_by_label("Estado")
        if not result_data['city']: result_data['city'] = get_value_by_label("Município") # Try without colon or different case
        
        # If we failed to get critical data
        if not result_data['brand_model'] or not result_data['venal_value_str']:
             print(f"DEBUG: Critical data missing. Found: {json.dumps(result_data)}")
             return None
             
        # Parse Venal Value
        # "R$ 115.469,00" -> 115469.00
        raw_val = result_data['venal_value_str'].replace("R$", "").replace(".", "").replace(",", ".").strip()
        result_data['venal_value'] = float(raw_val)
        
        return result_data

    except Exception as e:
        print(f"Error scraping ipvabr: {e}")
        try:
            driver.save_screenshot("debug_ipvabr_error.png")
        except:
            pass
        return None
    finally:
        driver.quit()

def calculate_ipva_data(plate):
    # 1. Scrape ipvabr.com.br
    print(f"Consulta placa {plate} no ipvabr.com.br...")
    scraped_data = get_car_info_from_ipvabr(plate)
    
    if not scraped_data:
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
