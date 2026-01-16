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
import random

# Try to import Fazenda API client (optional)
try:
    from fazenda_api_client import get_ipva_data_official
    FAZENDA_API_AVAILABLE = True
except ImportError:
    FAZENDA_API_AVAILABLE = False
    print("⚠️ Fazenda API client not available, using scraping only")
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
            result_data['year'] = get_value_by_label("Ano Modelo:")
        
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

def parse_official_debts(official_data):
    """
    Parses the official API data to extract exact values for 2026 and history for 2025/2024.
    Returns a dict with formatted values and raw numbers.
    """
    parsed = {
        'ipva_full': 0.0,
        'licensing_val': 0.0,
        'total_full': 0.0,
        'ipva_discounted': 0.0,
        'installment_val': 0.0,
        'history': []
    }
    
    current_year = 2026
    
    if 'extratoDebitos' in official_data:
        for debito in official_data['extratoDebitos']:
            ano = debito.get('anoExercicio')
            
            # Process 2026 (Current Year)
            if ano == current_year:
                # Cota Unica (Discounted Total)
                parsed['ipva_discounted'] = debito.get('valorTotalIpvaComDescontoBomPagador', 0.0)
                parsed['ipva_full'] = debito.get('valorTotalIpvaSemDesconto', 0.0)
                
                # Check parcels to find Licensing fee and Installment value
                for parcela in debito.get('parcelas', []):
                    desc = parcela.get('descricao', '').upper()
                    val = parcela.get('valorTotal', 0.0)
                    
                    if "LIC" in desc or "TAXA" in desc:
                        parsed['licensing_val'] = val
                    
                    # Store one IPVA installment value (typically Parcel 1 has the standard value)
                    if "IPVA 1" in desc:
                        parsed['installment_val'] = val
                        
            # Process History (2025, 2024)
            elif ano in [2025, 2024]:
                # Calculate total debt for this year
                total_ano = 0.0
                detailed_items = [] 
                status = "Em dia"
                
                for parcela in debito.get('parcelas', []):
                    if not parcela.get('estaPago', False):
                        val_parcela = parcela.get('valorTotal', 0.0)
                        total_ano += val_parcela
                        
                        # Add detailed item for checkboxes
                        detailed_items.append({
                            'description': parcela.get('descricao'),
                            'value': val_parcela,
                            'formatted_value': f"R$ {val_parcela:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        })
                        
                        status = "Pendente"
                
                if total_ano > 0:
                    parsed['history'].append({
                        'year': ano,
                        'status': status,
                        'total': total_ano,
                        'items': detailed_items # Now a List of Dicts
                    })

    # Calculate Totals
    # Total Full = IPVA Full + Licensing (Standard Check)
    parsed['total_full'] = parsed['ipva_full'] + parsed['licensing_val'] 
    
    # Total Discounted (Cota Unica)
    # The API returns 'valorTotalIpvaComDescontoBomPagador' which usually includes ONLY IPVA.
    # We need to add licensing to Get the real 'Pay Everything Now' price.
    parsed['total_with_discount'] = parsed['ipva_discounted'] + parsed['licensing_val']
    
    # First Payment (Installment 1 + Licensing)
    # If installment_val is 0 (maybe single quota only available?), fallback to math
    if parsed['installment_val'] == 0 and parsed['ipva_full'] > 0:
         parsed['installment_val'] = parsed['ipva_full'] / 3 # Estimate 3 parcels if not found
         
    parsed['first_payment_total'] = parsed['installment_val'] + parsed['licensing_val']
    
    return parsed

def calculate_ipva_data(identifier):
    print("=" * 50, flush=True)
    print(f"FUNCTION START: calculate_ipva_data({identifier})", flush=True)
    print("=" * 50, flush=True)
    
    # Clean identifier
    identifier = str(identifier).replace("-", "").replace(".", "").strip().upper()
    
    is_renavam = identifier.isdigit() and len(identifier) == 11
    
    scraped_data = {}
    official_data = None
    
    # --- FLOW 1: RENAVAM INPUT ---
    if is_renavam:
        print(f"INFO: Input identificado como RENAVAM: {identifier}", flush=True)
        if FAZENDA_API_AVAILABLE:
            try:
                official_data = get_ipva_data_official(plate=None, renavam=identifier)
                if not official_data:
                    return {"error": "RENAVAM_NOT_FOUND", "message": "RENAVAM não encontrado ou API indisponível. Por favor, digite a Placa."}
            except Exception as e:
                print(f"ERROR: Falha na consulta por RENAVAM: {e}")
                return {"error": "API_ERROR", "message": "Erro ao consultar. Tente com a Placa."}
        else:
             return {"error": "Configuração incompleta. API indisponível."}
             
    # --- FLOW 2: PLATE INPUT ---
    else:
        print(f"INFO: Input identificado como PLACA: {identifier}", flush=True)
        # 1. Scrape ipvabr.com.br to get basic data and RENAVAM
        scraped_data = get_car_info_from_ipvabr(identifier)
        
        if not scraped_data:
            print(f"ERROR: Failed to scrape data for plate {identifier}", flush=True)
            return {"error": "Veículo não encontrado. Verifique a placa e tente novamente."}
        
        renavam = scraped_data.get('chassis')
        
        # 2. Try official API with RENAVAM from scraping
        if FAZENDA_API_AVAILABLE and renavam:
            print(f"INFO: Tentando API oficial da Fazenda com RENAVAM obtido...", flush=True)
            try:
                official_data = get_ipva_data_official(identifier, renavam)
            except Exception as e:
                print(f"WARNING: Erro ao consultar API oficial: {e}", flush=True)

    # --- MERGE DATA ---
    final_data = {}
    
    # Helper formatter
    def fmt(val):
        if val is None: return "R$ 0,00"
        return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    # If we have official data (from either flow), use it for VALUES
    if official_data:
        print("SUCCESS: Usando dados oficiais para cálculos!", flush=True)
        parsed_values = parse_official_debts(official_data)
        
        # Populate Vehicle Info from Official
        if 'veiculo' in official_data:
            v = official_data['veiculo']
            final_data['brand'] = v.get('marcaModelo', scraped_data.get('brand_model')) or "Modelo não informado"
            final_data['year'] = str(v.get('anoFabricacao', scraped_data.get('year')))
            final_data['color'] = v.get('cor', scraped_data.get('color'))
            final_data['fuel'] = v.get('combustivel', scraped_data.get('fuel'))
            final_data['state'] = "MG" # API is MG specific
            # Use 'or' to fallback if API returns empty string ""
            final_data['plate'] = v.get('placa') or identifier
            final_data['renavam'] = v.get('renavam') or identifier
            final_data['chassis'] = v.get('chassi') or "**********"
            final_data['engine'] = v.get('motor') or "**********"
            
        if 'proprietario' in official_data:
            p = official_data['proprietario']
            final_data['owner_name'] = p.get('nome')
            final_data['owner_doc'] = p.get('cpfCnpj')
            final_data['city'] = p.get('municipio', scraped_data.get('city'))
        
        # Populate Financials (REAL VALUES)
        final_data['venal_value'] = fmt(0) # Not returned by debt API
        final_data['ipva_full'] = fmt(parsed_values['ipva_full'])
        final_data['licensing_val'] = fmt(parsed_values['licensing_val'])
        final_data['total_full'] = fmt(parsed_values['total_full'])
        
        final_data['ipva_discounted'] = fmt(parsed_values['ipva_discounted'])
        final_data['total_with_discount'] = fmt(parsed_values['total_with_discount'])
        
        # --- PROMO LOGIC OVERRIDE ---
        # User requirement: FORCE 70% discount (30% of full value) and split into 4 installments
        # We ignore parsed_values['ipva_discounted'] because API might return full value there if user not eligible.
        # But for this site ("Promo"), we want to show the discounted price.
        
        promo_ipva_total = parsed_values['ipva_full'] * 0.30
        print(f"DEBUG_CALC: Forced Promo Total (30% of {parsed_values['ipva_full']}): {promo_ipva_total}")

        # Update the 'discounted' fields to reflect this forced math
        # So the Frontend receives consistent values
        parsed_values['ipva_discounted'] = promo_ipva_total
        parsed_values['total_with_discount'] = promo_ipva_total + parsed_values['licensing_val']

        final_data['ipva_discounted'] = fmt(promo_ipva_total)
        final_data['total_with_discount'] = fmt(parsed_values['total_with_discount'])
             
        promo_installment_val = promo_ipva_total / 4
        print(f"DEBUG_CALC: Promo Installment: {promo_installment_val} (Total: {promo_ipva_total} / 4)")
        
        promo_first_payment = promo_installment_val + parsed_values['licensing_val']
        
        final_data['installment_val'] = fmt(promo_installment_val)
        final_data['installments'] = 4
        final_data['first_payment_total'] = fmt(promo_first_payment)
        
        # Raw vars for frontend math
        final_data['raw_total_discounted'] = parsed_values['total_with_discount'] if parsed_values['total_with_discount'] > 0 else (promo_ipva_total + parsed_values['licensing_val'])
        final_data['raw_installment_val'] = promo_installment_val
        final_data['raw_licensing_val'] = parsed_values['licensing_val']
        final_data['raw_first_payment_total'] = promo_first_payment
        
        # History
        final_data['history'] = parsed_values['history']

    # --- FALLBACK: USE SCRAPED/ESTIMATED DATA ---
    else:
        if is_renavam:
             # Should have been caught by "RENAVAM_NOT_FOUND" earlier, but safe fallback
             return {"error": "RENAVAM_NOT_FOUND", "message": "Falha ao obter dados. Tente com a Placa."}
             
        print("INFO: Usando dados estimados (Fallback)...", flush=True)
        # Use existing estimation logic
        # 3. If venal value missing, try FIPE
        if 'venal_value' not in scraped_data or not scraped_data.get('venal_value'):
            from fipe_api import get_fipe_value
            # ... (FIPE logic same as before, abbreviated here)
            brand_model = scraped_data.get('brand_model', '')
            parts = brand_model.split(' ', 1)
            brand = parts[0] if parts else ''
            model = parts[1] if len(parts) > 1 else brand_model
            fipe_val = get_fipe_value(brand, model, scraped_data.get('year'))
            if fipe_val:
                scraped_data['venal_value'] = fipe_val
            else:
                 return {"error": "Dados insuficientes. Tente novamente mais tarde."}

        # Calculate Estimates
        venal_val = scraped_data['venal_value']
        ipva_full = venal_val * IPVA_ALIQUOTA
        licensing = LICENSING_FEE
        total_full = ipva_full + licensing
        ipva_discounted = ipva_full * (1 - PROMO_DISCOUNT_RATE)
        total_discounted = ipva_discounted + licensing
        installment_val = ipva_discounted / 4
        first_payment = installment_val + licensing
        
        final_data = {
            "plate": identifier,
            "brand": scraped_data.get('brand_model'),
            "year": scraped_data.get('year'),
            "color": scraped_data.get('color'),
            "fuel": scraped_data.get('fuel'),
            "state": scraped_data.get('state'),
            "city": scraped_data.get('city'),
            "venal_value": fmt(venal_val),
            "ipva_full": fmt(ipva_full),
            "licensing_val": fmt(licensing),
            "total_full": fmt(total_full),
            "ipva_discounted": fmt(ipva_discounted),
            "total_with_discount": fmt(total_discounted),
            "installment_val": fmt(installment_val),
            "installments": 4,
            "first_payment_total": fmt(first_payment),
            "raw_total_discounted": total_discounted,
            "raw_installment_val": installment_val,
            "raw_licensing_val": licensing,
            "raw_first_payment_total": first_payment,
            "history": [] # No history in fallback
        }

    return final_data

