import json
import os
import sys
from unittest.mock import patch, MagicMock

# Add current dir to path
sys.path.append(os.getcwd())

# Mock scraping to avoid overhead and Selenium
with patch('plate_calculator.get_car_info_from_ipvabr') as mock_scrape:
    # Setup mock return for scraping (needed to get to API step)
    mock_scrape.return_value = {
        'brand_model': 'VW/GOL (Scraped)',
        'year': '2020',
        'color': 'BRANCA',
        'fuel': 'FLEX',
        'chassis': '1293554640', # Used as RENAVAM in logic
        'venal_value': 50000.00,
        'state': 'MG',
        'city': 'BH'
    }
    
    # Import function to test
    from plate_calculator import calculate_ipva_data
    
    # Load captured official data
    with open('/tmp/fazenda_final.json', 'r') as f:
        official_json = json.load(f)
        
    print("📋 Dados oficiais carregados do JSON:")
    print(f"   Nome: {official_json['proprietario']['nome']}")
    print(f"   CPF: {official_json['proprietario']['cpfCnpj']}")
    print("-" * 50)

    # Mock official API call
    with patch('plate_calculator.get_ipva_data_official') as mock_api:
        mock_api.return_value = official_json
        
        print("🚀 Executando calculate_ipva_data('SCA3E32')...")
        result = calculate_ipva_data('SCA3E32')
        
        print("\n✅ RESULTADO FINAL (Para o Frontend):")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # Validation
        if result['owner_name'] == "WILLIANS DIAS DE CARVALHO":
            print("\n✅ Nome do proprietário CONFIRMADO!")
        else:
            print(f"\n❌ Erro no nome: {result.get('owner_name')}")
            
        if result['owner_doc'] == "***.244.276-**":
            print("✅ Documento do proprietário CONFIRMADO!")
        else:
            print(f"❌ Erro no documento: {result.get('owner_doc')}")
            
        if result['brand_model'] == "VW/GOL 1.0L MC4":
             print("✅ Modelo atualizado pela API oficial!")
        else:
             print(f"⚠️ Modelo mantido do scrape: {result.get('brand_model')}")
