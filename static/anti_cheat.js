
document.addEventListener("visibilitychange", function() {
    if(document.hidden){
        fetch('/warning', {method:'POST'});
    }
});
