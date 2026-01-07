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

function handleCredentialResponse(response) {
    // This is the ID token (JWT)
    const idToken = response.credential;

    // Send it securely to your backend
    fetch("/auth/google", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token: idToken })
    })
    .then(res => res.json())
    .then(data => console.log("Backend response:", data))
    .catch(err => console.error(err));
}

// Google Calendar API Quickstart

/* exported gapiLoaded */
/* exported gisLoaded */
/* exported handleAuthClick */
/* exported handleSignoutClick */

// Import environment variables using Vite
const CLIENT_ID = 'nuhuh';
const API_KEY = 'ehhh';

if (!CLIENT_ID || !API_KEY) {
    console.error('Missing CLIENT_ID or API_KEY in Vite environment variables');
}

// Discovery doc URL for APIs used by the quickstart
const DISCOVERY_DOC = 'https://www.googleapis.com/discovery/v1/apis/calendar/v3/rest';

// Authorization scopes required by the API; multiple scopes can be
// included, separated by spaces.
const SCOPES = 'https://www.googleapis.com/auth/calendar.readonly';

let tokenClient;
let gapiInited = false;
let gisInited = false;

document.getElementById('authorize_button').style.visibility = 'hidden';
document.getElementById('signout_button').style.visibility = 'hidden';

/**
 * Callback after api.js is loaded.
 */
function gapiLoaded() {
    gapi.load('client', initializeGapiClient);
}

/**
 * Callback after the API client is loaded. Loads the
 * discovery doc to initialize the API.
 */
async function initializeGapiClient() {
    await gapi.client.init({
    apiKey: API_KEY,
    discoveryDocs: [DISCOVERY_DOC],
    });
    gapiInited = true;
    maybeEnableButtons();
}

/**
 * Callback after Google Identity Services are loaded.
 */
function gisLoaded() {
    tokenClient = google.accounts.oauth2.initTokenClient({
    client_id: CLIENT_ID,
    scope: SCOPES,
    callback: '', // defined later
    });
    gisInited = true;
    maybeEnableButtons();
}

/**
 * Enables user interaction after all libraries are loaded.
 */
function maybeEnableButtons() {
    if (gapiInited && gisInited) {
    document.getElementById('authorize_button').style.visibility = 'visible';
    }
}

/**
 *  Sign in the user upon button click.
 */
function handleAuthClick() {
    tokenClient.callback = async (resp) => {
    if (resp.error !== undefined) {
        throw (resp);
    }
    document.getElementById('signout_button').style.visibility = 'visible';
    document.getElementById('authorize_button').innerText = 'Different Account?';
    };

    if (gapi.client.getToken() === null) {
    // Prompt the user to select a Google Account and ask for consent to share their data
    // when establishing a new session.
    tokenClient.requestAccessToken({prompt: 'consent'});
    } else {
    // Skip display of account chooser and consent dialog for an existing session.
    tokenClient.requestAccessToken({prompt: ''});
    }
}

/**
 *  Sign out the user upon button click.
 */
function handleSignoutClick() {
    console.log ('Sign out clicked');
    const token = gapi.client.getToken();
    if (token !== null) {
    google.accounts.oauth2.revoke(token.access_token);
    gapi.client.setToken('');
    document.getElementById('authorize_button').innerText = 'Log into Google';
    document.getElementById('signout_button').style.visibility = 'hidden';
    }
}

/**
 * Print the summary and start datetime/date of the next ten events in
 * the authorized user's calendar. If no events are found an
 * appropriate message is printed.
 */
async function listUpcomingEvents() {
    let response;
    try {
    const request = {
        'calendarId': 'primary',
        'timeMin': (new Date()).toISOString(),
        'showDeleted': false,
        'singleEvents': true,
        'maxResults': 10,
        'orderBy': 'startTime',
    };
    response = await gapi.client.calendar.events.list(request);
    } catch (err) {
    document.getElementById('content').innerText = err.message;
    return;
    }

    const events = response.result.items;
    if (!events || events.length == 0) {
    document.getElementById('content').innerText = 'No events found.';
    return;
    }
    // Flatten to string to display
    const output = events.reduce(
        (str, event) => `${str}${event.summary} (${event.start.dateTime || event.start.date})\n`,
        'Events:\n');
    document.getElementById('content').innerText = output;
}

