const dropZone = document.getElementById('dropZone');
const imageInput = document.getElementById('imageInput');
const imagePreview = document.getElementById('imagePreview');
const loginButton = document.getElementById('login');
const serverUrl = 'http://127.0.0.1:5000'; // Replace with your Flask server URL


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

let authURL;

async function authorizeURL() {
    await fetch(`${serverUrl}/authorizeurl`, {
        method: 'GET'
    })
    .then(response => response.text())
    .then(data => {
        console.log('Authorization URL received:', data);
        authURL = data;
    })
    .catch(error => console.error('Error fetching authorization URL:', error));

}

loginButton.addEventListener('click', (event) => {
    console.log('Login button clicked');
    window.location.href = authURL;
});


let classData;

async function handleFile(file) {
    if (file) {
        const formData = new FormData();
        formData.append('file', file);

        await fetch(`${serverUrl}/upload`, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            console.log('File uploaded successfully:', data);
            classData = data;
        })
        .catch(error => console.error('Error uploading file:', error));
    } else {
        console.log('No file to handle');
    }
    document.getElementById('content').innerText = JSON.stringify(classData, null, 2);
}

authorizeURL();