// Sounds state
let sounds = [];
let currentlyPlaying = null;

// Initialize sounds component
function initializeSounds() {
    // Load sounds list
    loadSounds();
    
    // Add event listeners
    document.getElementById('sound-upload').addEventListener('change', handleSoundUpload);
}

// Load sounds from server
function loadSounds() {
    fetch(`${API_BASE_URL}/sounds`, {
        headers: window.defaultHeaders
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            sounds = data.sounds;
            renderSounds();
        }
    })
    .catch(error => {
        console.error('Error loading sounds:', error);
        showNotification('Error loading sounds', 'error');
    });
}

// Render sounds list
function renderSounds() {
    const container = document.querySelector('.sound-list');
    container.innerHTML = '';
    
    sounds.forEach(sound => {
        const soundElement = createSoundElement(sound);
        container.appendChild(soundElement);
    });
}

// Create sound element
function createSoundElement(sound) {
    const div = document.createElement('div');
    div.className = 'sound-item';
    div.dataset.id = sound.id;
    
    div.innerHTML = `
        <button class="play-btn">
            <i class="material-icons">play_arrow</i>
        </button>
        <div class="sound-info">
            <div class="sound-name">${sound.name}</div>
            <div class="sound-duration">${formatDuration(sound.duration)}</div>
        </div>
        <div class="sound-actions">
            ${sound.custom ? `
                <button class="delete-btn">
                    <i class="material-icons">delete</i>
                </button>
            ` : ''}
            <button class="set-default-btn ${sound.isDefault ? 'active' : ''}">
                <i class="material-icons">star</i>
            </button>
        </div>
    `;
    
    // Add event listeners
    const playBtn = div.querySelector('.play-btn');
    playBtn.addEventListener('click', () => {
        toggleSound(sound, playBtn);
    });
    
    const deleteBtn = div.querySelector('.delete-btn');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', () => {
            deleteSound(sound.id);
        });
    }
    
    const defaultBtn = div.querySelector('.set-default-btn');
    defaultBtn.addEventListener('click', () => {
        setDefaultSound(sound.id);
    });
    
    return div;
}

// Format duration
function formatDuration(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

// Toggle sound playback
function toggleSound(sound, button) {
    if (currentlyPlaying) {
        if (currentlyPlaying.sound.id === sound.id) {
            // Stop current sound
            currentlyPlaying.audio.pause();
            currentlyPlaying.audio.currentTime = 0;
            currentlyPlaying.button.innerHTML = '<i class="material-icons">play_arrow</i>';
            currentlyPlaying = null;
            return;
        } else {
            // Stop previous sound
            currentlyPlaying.audio.pause();
            currentlyPlaying.audio.currentTime = 0;
            currentlyPlaying.button.innerHTML = '<i class="material-icons">play_arrow</i>';
        }
    }
    
    // Play new sound
    const audio = new Audio(`${API_BASE_URL}/sounds/${sound.file}`);
    audio.addEventListener('ended', () => {
        button.innerHTML = '<i class="material-icons">play_arrow</i>';
        currentlyPlaying = null;
    });
    
    audio.play();
    button.innerHTML = '<i class="material-icons">stop</i>';
    currentlyPlaying = { sound, audio, button };
}

// Handle sound upload
function handleSoundUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    // Validate file type
    if (!file.type.startsWith('audio/')) {
        showNotification('Please upload an audio file', 'error');
        return;
    }
    
    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
        showNotification('File size must be less than 5MB', 'error');
        return;
    }
    
    // Create form data
    const formData = new FormData();
    formData.append('sound', file);
    
    // Upload sound
    fetch(`${API_BASE_URL}/sounds/upload`, {
        method: 'POST',
        headers: {
            'Authorization': window.defaultHeaders.Authorization
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            sounds.push(data.sound);
            renderSounds();
            showNotification('Sound uploaded successfully', 'success');
        } else {
            showNotification('Error uploading sound', 'error');
        }
    })
    .catch(error => {
        console.error('Error uploading sound:', error);
        showNotification('Error uploading sound', 'error');
    });
    
    // Reset file input
    e.target.value = '';
}

// Delete sound
function deleteSound(id) {
    if (!confirm('Are you sure you want to delete this sound?')) {
        return;
    }
    
    fetch(`${API_BASE_URL}/sounds/${id}`, {
        method: 'DELETE',
        headers: window.defaultHeaders
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            sounds = sounds.filter(s => s.id !== id);
            renderSounds();
            showNotification('Sound deleted successfully', 'success');
        } else {
            showNotification('Error deleting sound', 'error');
        }
    })
    .catch(error => {
        console.error('Error deleting sound:', error);
        showNotification('Error deleting sound', 'error');
    });
}

// Set default sound
function setDefaultSound(id) {
    fetch(`${API_BASE_URL}/sounds/${id}/default`, {
        method: 'POST',
        headers: window.defaultHeaders
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            sounds.forEach(sound => {
                sound.isDefault = sound.id === id;
            });
            renderSounds();
            showNotification('Default sound updated', 'success');
        } else {
            showNotification('Error updating default sound', 'error');
        }
    })
    .catch(error => {
        console.error('Error updating default sound:', error);
        showNotification('Error updating default sound', 'error');
    });
}

// Clean up sounds component
function cleanupSounds() {
    if (currentlyPlaying) {
        currentlyPlaying.audio.pause();
        currentlyPlaying = null;
    }
}

// Refresh sounds
function refreshSounds() {
    loadSounds();
} 