// Local previews only. The server validates content, correspondence and attestations.
const input = document.querySelector('input[name="fotos"]');
const preview = document.querySelector('[data-upload-preview]');
let urls = [];
input?.addEventListener('change', () => {
    urls.forEach(url => URL.revokeObjectURL(url));
    urls = [];
    preview.replaceChildren();
    for (const file of [...input.files].slice(0, 8)) {
        if (!file.type.startsWith('image/')) continue;
        const figure = document.createElement('figure');
        const image = document.createElement('img');
        const caption = document.createElement('figcaption');
        const url = URL.createObjectURL(file);
        urls.push(url);
        image.src = url;
        image.alt = `Prévia local: ${file.name}`;
        image.width = 150;
        image.height = 160;
        caption.textContent = file.name;
        figure.append(image, caption);
        preview.append(figure);
    }
});
window.addEventListener('pagehide', () => urls.forEach(url => URL.revokeObjectURL(url)));
