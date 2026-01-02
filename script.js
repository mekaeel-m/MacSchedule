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

const serverUrl = 'http://127.0.0.1:5000'; // Replace with your Flask server URL

function handleFile(file) {
    if (file) {
        const formData = new FormData();
        formData.append('file', file);

        fetch(`${serverUrl}/upload`, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                console.log('File uploaded successfully:', data.path);
            } else {
                console.error('Upload failed:', data.error);
            }
        })
        .catch(error => console.error('Error uploading file:', error));
    } else {
        console.log('No file to handle');
    }
}