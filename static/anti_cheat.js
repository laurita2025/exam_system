let lastWarningTime = 0;
const warningCooldown = 3000;

function shouldWarn() {
    const now = Date.now();
    if (now - lastWarningTime < warningCooldown) {
        return false;
    }
    lastWarningTime = now;
    return true;
}

function sendWarning(reason) {
    if (!shouldWarn()) {
        return;
    }

    fetch('/warning', {method:'POST'})
        .then(response => response.json())
        .then(data => {
            const warningEl = document.getElementById("warning-message");

            if (data.expelled) {
                alert('Advertencia final: Usted ha sido expulsado del examen. Si comete 3 infracciones, su examen termina, no puede continuar y su nota será 0.');
                window.location.href = '/exam';
                return;
            }

            const remaining = data.maxWarnings - data.warnings;
            const message = `${reason} Esto se considera una infracción. Llevas ${data.warnings} de ${data.maxWarnings} infracciones. Si llegas a 3, serás expulsado, tu examen terminará y tu nota será 0. Te quedan ${remaining} infracciones.`;
            alert(message);

            if (warningEl) {
                warningEl.textContent = `⚠ ${message}`;
            }
        });
}

document.addEventListener("visibilitychange", function() {
    if (document.hidden) {
        sendWarning('Has minimizado la ventana o cambiado de pestaña. No abras otros programas en paralelo, como archivos PDF o Word.');
    }
});

window.addEventListener('blur', function() {
    if (!document.hidden) {
        sendWarning('Has cambiado el foco fuera del examen. No abras otros programas en paralelo, como archivos PDF o Word.');
    }
});
