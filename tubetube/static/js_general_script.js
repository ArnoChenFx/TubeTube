const socket = io();
const folderSelect = document.getElementById('folder-location-select');
const mediaTypeSwitch = document.getElementById('media-type-switch');
const downloadButton = document.getElementById('download-button');
const spinnerBorder = document.getElementById('spinner-border');
const urlInput = document.getElementById('download-url');

let folderData = {
    audio: {},
    video: {}
};

function populateDropdown() {
    folderSelect.innerHTML = '<option value="" selected>Select folder location</option>';

    const mediaType = mediaTypeSwitch.checked ? 'audio' : 'video';
    const dataToUse = folderData[mediaType];

    Object.keys(dataToUse).forEach(name => {
        const option = document.createElement('option');
        option.value = name;
        option.textContent = name;
        folderSelect.appendChild(option);
    });

    const selectedFolder = localStorage.getItem(`selectedFolder_${mediaType}`);
    if (selectedFolder && dataToUse[selectedFolder]) {
        folderSelect.value = selectedFolder;
    } else {
        folderSelect.value = '';
    }
}

function saveSelection() {
    const mediaType = mediaTypeSwitch.checked ? 'audio' : 'video';
    localStorage.setItem(`selectedFolder_${mediaType}`, folderSelect.value);
    localStorage.setItem('mediaType', mediaType);
}

socket.on('update_folder_locations', function (data) {
    folderData = data;
    const savedMediaType = localStorage.getItem('mediaType') || 'video';
    mediaTypeSwitch.checked = savedMediaType === 'audio';
    populateDropdown();
});

mediaTypeSwitch.addEventListener('change', function () {
    populateDropdown();
    saveSelection();
});

folderSelect.addEventListener('change', saveSelection);

function initiateDownload() {
    const url = urlInput;

    if (!url.value.trim()) {
        alert('The URL is empty. Please provide a URL to download.');
        return;
    }

    const folderName = folderSelect.value;
    if (folderName === "Select folder location" || folderName === "") {
        alert('No folder selected. Please select a valid folder.');
        return;
    }

    const audioOnly = mediaTypeSwitch.checked;
    socket.emit('download', { url: url.value, folder_name: folderName, audio_only: audioOnly });
    url.disabled = true;
    downloadButton.disabled = true;
    spinnerBorder.style.display = 'inline-block';

    setTimeout(() => {
        spinnerBorder.style.display = 'none';
        url.value = '';
        url.disabled = false;
        downloadButton.disabled = false;
    }, 2500);
}

downloadButton.addEventListener('click', initiateDownload);

urlInput.addEventListener('keydown', function (event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        initiateDownload();
    }
});

socket.on("toast", function (data) {
    document.getElementById('toast-title').innerText = data.title;
    document.getElementById('toast-message').innerText = data.body;
    document.getElementById('toast-time').innerText = new Date().toLocaleTimeString();

    var toastElement = document.getElementById('toast');
    var toast = new bootstrap.Toast(toastElement);
    toast.show();
});