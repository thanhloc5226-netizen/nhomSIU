function toggleColumn(className) {
    document.querySelectorAll('.' + className).forEach(el => {
        el.style.display = (el.style.display === 'none') ? '' : 'none';
    });
}