const dropZone = document.getElementById('dropZone');
const imageInput = document.getElementById('imageInput');
const imagePreview = document.getElementById('imagePreview');

console.log('Script loaded successfully');

dropZone.addEventListener('click', () => {
    console.log('Drop zone clicked');
    imageInput.click();
});

dropZone.addEventListener('dragover', (event) => {
    event.preventDefault();
    console.log('Drag over event');
    dropZone.style.backgroundColor = '#e0ffe0';
});

dropZone.addEventListener('dragleave', () => {
    console.log('Drag leave event');
    dropZone.style.backgroundColor = '';
});

dropZone.addEventListener('drop', (event) => {
    event.preventDefault();
    console.log('Drop event');
    dropZone.style.backgroundColor = '';

    const file = event.dataTransfer.files[0];
    console.log('File dropped:', file);
    handleFile(file);
});

dropZone.addEventListener('paste', (event) => {
    console.log('Paste event');
    const items = event.clipboardData.items;
    for (let item of items) {
        if (item.type.startsWith('image/')) {
            const file = item.getAsFile();
            console.log('File pasted:', file);
            handleFile(file);
        }
    }
});

imageInput.addEventListener('change', (event) => {
    console.log('File input changed');
    const file = event.target.files[0];
    console.log('File selected:', file);
    handleFile(file);
});

function handleFile(file) {
    if (file) {
        const reader = new FileReader();

        reader.onload = function(e) {
            console.log('File read successfully');
            imagePreview.style.display = 'block';
            imagePreview.innerHTML = `<img src="${e.target.result}" alt="Uploaded Image" style="max-width: 100%; height: auto;">`;
        };

        reader.readAsDataURL(file);
    } else {
        console.log('No file to handle');
        imagePreview.style.display = 'none';
        imagePreview.innerHTML = '';
    }
}