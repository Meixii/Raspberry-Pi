// Lights state
let patterns = [];
let currentPattern = null;
let previewInterval = null;

// Initialize lights component
function initializeLights() {
    // Load patterns
    loadPatterns();
    
    // Initialize color picker
    initializeColorPicker();
    
    // Add event listeners
    addLightEventListeners();
}

// Load light patterns
function loadPatterns() {
    fetch(`${API_BASE_URL}/lights/patterns`, {
        headers: window.defaultHeaders
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            patterns = data.patterns;
            renderPatterns();
        }
    })
    .catch(error => {
        console.error('Error loading patterns:', error);
        showNotification('Error loading light patterns', 'error');
    });
}

// Render light patterns
function renderPatterns() {
    const container = document.querySelector('.light-patterns');
    container.innerHTML = '';
    
    patterns.forEach(pattern => {
        const patternElement = createPatternElement(pattern);
        container.appendChild(patternElement);
    });
}

// Create pattern element
function createPatternElement(pattern) {
    const div = document.createElement('div');
    div.className = 'pattern-card';
    div.dataset.id = pattern.id;
    
    if (pattern.id === currentPattern?.id) {
        div.classList.add('active');
    }
    
    div.innerHTML = `
        <div class="pattern-preview" id="preview-${pattern.id}"></div>
        <div class="pattern-info">
            <div class="pattern-name">${pattern.name}</div>
            <div class="pattern-controls">
                <button class="preview-btn">
                    <i class="material-icons">visibility</i>
                </button>
                <button class="apply-btn">
                    <i class="material-icons">check</i>
                </button>
            </div>
        </div>
    `;
    
    // Add event listeners
    div.querySelector('.preview-btn').addEventListener('click', () => {
        togglePatternPreview(pattern);
    });
    
    div.querySelector('.apply-btn').addEventListener('click', () => {
        applyPattern(pattern);
    });
    
    // Initialize preview animation
    initializePreview(pattern);
    
    return div;
}

// Initialize pattern preview
function initializePreview(pattern) {
    const preview = document.getElementById(`preview-${pattern.id}`);
    
    switch (pattern.type) {
        case 'rainbow_cycle':
            animateRainbowPreview(preview);
            break;
        case 'pulse':
            animatePulsePreview(preview, pattern.color);
            break;
        case 'chase':
            animateChasePreview(preview, pattern.colors);
            break;
        case 'solid':
            preview.style.backgroundColor = pattern.color;
            break;
    }
}

// Animate rainbow preview
function animateRainbowPreview(element) {
    let hue = 0;
    
    const animate = () => {
        element.style.backgroundColor = `hsl(${hue}, 100%, 50%)`;
        hue = (hue + 1) % 360;
        requestAnimationFrame(animate);
    };
    
    animate();
}

// Animate pulse preview
function animatePulsePreview(element, color) {
    let opacity = 1;
    let decreasing = true;
    
    const animate = () => {
        element.style.backgroundColor = color;
        element.style.opacity = opacity;
        
        if (decreasing) {
            opacity -= 0.02;
            if (opacity <= 0.2) {
                decreasing = false;
            }
        } else {
            opacity += 0.02;
            if (opacity >= 1) {
                decreasing = true;
            }
        }
        
        requestAnimationFrame(animate);
    };
    
    animate();
}

// Animate chase preview
function animateChasePreview(element, colors) {
    let currentColor = 0;
    
    setInterval(() => {
        element.style.backgroundColor = colors[currentColor];
        currentColor = (currentColor + 1) % colors.length;
    }, 500);
}

// Initialize color picker
function initializeColorPicker() {
    const picker = document.querySelector('.color-picker');
    picker.innerHTML = `
        <div class="color-preview"></div>
        <input type="color" id="custom-color">
        <div class="color-controls">
            <label>
                Brightness:
                <input type="range" id="brightness" min="0" max="255" value="255">
            </label>
            <label>
                Speed:
                <input type="range" id="speed" min="10" max="100" value="50">
            </label>
        </div>
        <button class="apply-custom-btn">Apply Custom Pattern</button>
    `;
    
    // Add event listeners
    const colorInput = document.getElementById('custom-color');
    const preview = document.querySelector('.color-preview');
    
    colorInput.addEventListener('input', (e) => {
        preview.style.backgroundColor = e.target.value;
    });
    
    document.querySelector('.apply-custom-btn').addEventListener('click', () => {
        const color = colorInput.value;
        const brightness = document.getElementById('brightness').value;
        const speed = document.getElementById('speed').value;
        
        applyCustomPattern(color, brightness, speed);
    });
}

// Toggle pattern preview
function togglePatternPreview(pattern) {
    if (previewInterval) {
        clearInterval(previewInterval);
        previewInterval = null;
        stopPreview();
        return;
    }
    
    // Send preview command to server
    fetch(`${API_BASE_URL}/lights/preview`, {
        method: 'POST',
        headers: window.defaultHeaders,
        body: JSON.stringify(pattern)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Set timeout to stop preview after 10 seconds
            previewInterval = setTimeout(() => {
                stopPreview();
                previewInterval = null;
            }, 10000);
        } else {
            showNotification('Error previewing pattern', 'error');
        }
    })
    .catch(error => {
        console.error('Error previewing pattern:', error);
        showNotification('Error previewing pattern', 'error');
    });
}

// Stop pattern preview
function stopPreview() {
    fetch(`${API_BASE_URL}/lights/preview/stop`, {
        method: 'POST',
        headers: window.defaultHeaders
    })
    .catch(error => {
        console.error('Error stopping preview:', error);
    });
}

// Apply pattern
function applyPattern(pattern) {
    fetch(`${API_BASE_URL}/lights/pattern`, {
        method: 'POST',
        headers: window.defaultHeaders,
        body: JSON.stringify(pattern)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            currentPattern = pattern;
            updateActivePattern();
            showNotification('Pattern applied successfully', 'success');
        } else {
            showNotification('Error applying pattern', 'error');
        }
    })
    .catch(error => {
        console.error('Error applying pattern:', error);
        showNotification('Error applying pattern', 'error');
    });
}

// Apply custom pattern
function applyCustomPattern(color, brightness, speed) {
    const pattern = {
        type: 'custom',
        color: color,
        brightness: parseInt(brightness),
        speed: parseInt(speed)
    };
    
    applyPattern(pattern);
}

// Update active pattern indication
function updateActivePattern() {
    document.querySelectorAll('.pattern-card').forEach(card => {
        card.classList.toggle('active', card.dataset.id === currentPattern?.id);
    });
}

// Add light event listeners
function addLightEventListeners() {
    // Add any additional event listeners here
}

// Clean up lights component
function cleanupLights() {
    if (previewInterval) {
        clearInterval(previewInterval);
        previewInterval = null;
        stopPreview();
    }
}

// Refresh lights
function refreshLights() {
    loadPatterns();
} 