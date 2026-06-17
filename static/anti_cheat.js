
document.addEventListener("visibilitychange", function() {
    if (document.hidden) {
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
                const message = `Advertencia: salió del sistema de examen. Llevas ${data.warnings} de ${data.maxWarnings} infracciones. Si llegas a 3, serás expulsado, tu examen terminará y tu nota será 0. Te quedan ${remaining} infracciones.`;
                alert(message);

                if (warningEl) {
                    warningEl.textContent = `⚠ ${message}`;
                }
            });
    }
});
