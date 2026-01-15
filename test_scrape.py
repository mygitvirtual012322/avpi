from plate_calculator import calculate_ipva_data
import time

plate = "EDS9499"
print(f"--- INICIANDO TESTE PARA PLACA {plate} ---")
start = time.time()

try:
    result = calculate_ipva_data(plate)
    print("\n--- RESULTADO ---")
    print(result)
except Exception as e:
    print(f"\n--- ERRO ---")
    print(e)

print(f"\n--- TEMPO TOTAL: {time.time() - start:.2f}s ---")
