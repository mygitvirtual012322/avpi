#!/bin/bash
# Cleanup script - Remove test and scraping files from other states

echo "🧹 Starting project cleanup..."
echo "This will remove test files from other states and keep only essential files"
echo ""

# Files to remove - State-specific scrapers and test files
FILES_TO_REMOVE=(
    # State scraping files
    "ba_ipva.py"
    "ba_home.html"
    "ba_ipva_dae.html"
    "ba_ipva_form.html"
    "ba_ipva_historico.html"
    "ba_ipva_landing.html"
    "ba_ipva_valor.html"
    "ce_ipva.html"
    "df_home.html"
    "df_ipva_landing.html"
    "es_ipva.html"
    "es_legacy.html"
    "go_ipva.html"
    "mg_page.html"
    "pb_ipva.html"
    "pr_page.html"
    "rj_darj.html"
    "rj_portal_spa.html"
    "rj_sefaz.html"
    "rr_ipva.html"
    "rs_main.js"
    "rs_page.html"
    "rs_real_page.html"
    "sc_page.html"
    "sc_real_page.html"
    "se_ipva.html"
    "se_ipva_retry.html"
    "sp_page.html"
    "to_ipva.html"
    "to_probe.html"
    "veicular_rj.html"
    "veicular_rj_result.html"
    
    # Test and debug files
    "bradesco_grt.html"
    "debug_ipvabr_error.png"
    "debug_response.html"
    "debug_scrape_error.png"
    "find_fipe_debug.py"
    "fipe_api_test.json"
    "fipe_placa.html"
    "list_jetta_models.py"
    "list_jetta_models_v2.py"
    "placaipva.html"
    "test_ba_api.py"
    "veicular_api_response.json"
    "curl_error.log"
    "portal_error.log"
    
    # Markdown documentation (keep only if needed)
    "CONFIGURAR_PIX.md"
    "MELHORIAS.md"
    "SISTEMA_COMPLETO.md"
    
    # Old admin
    "admin.html"
    
    # Backup server
    "server_backup.py"
)

# Count files
TOTAL=${#FILES_TO_REMOVE[@]}
REMOVED=0
NOTFOUND=0

echo "Found $TOTAL files to remove"
echo ""

# Remove files
for file in "${FILES_TO_REMOVE[@]}"; do
    if [ -f "$file" ]; then
        rm "$file"
        echo "✅ Removed: $file"
        ((REMOVED++))
    else
        echo "⚠️  Not found: $file"
        ((NOTFOUND++))
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ Cleanup complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Removed: $REMOVED files"
echo "⚠️  Not found: $NOTFOUND files"
echo ""
echo "Essential files preserved:"
echo "  ✓ index.html"
echo "  ✓ resultado.html"
echo "  ✓ server.py"
echo "  ✓ plate_calculator.py"
echo "  ✓ admin_new.html"
echo "  ✓ admin_auth.py"
echo "  ✓ session_tracker.py"
echo "  ✓ meta_pixel.py"
echo "  ✓ config.py"
echo "  ✓ pix_utils.py"
echo "  ✓ style.css"
echo "  ✓ script.js"
echo ""
echo "🚀 Project is now production-ready!"
