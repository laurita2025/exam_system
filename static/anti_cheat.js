
document.addEventListener("visibilitychange", function() {
    if (document.hidden) {
        fetch('/warning', {method:'POST'})
            .then(response => response.json())
            .then(data => {
                if (data.expelled) {
                    alert('Usted ha sido expulsado por copiar y no seguir las reglas del examen.');
                    window.location.href = '/exam';
                }
            });
    }
});
