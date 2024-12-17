// Alarms state
let alarms = [
    {
        id: 1,
        title: 'Wake Up',
        time: '07:00',
        days: ['mon', 'tue', 'wed', 'thu', 'fri'],
        sound: 'morning-dew.mp3',
        enabled: true
    },
    {
        id: 2,
        title: 'Lunch Break',
        time: '12:00',
        days: ['mon', 'tue', 'wed', 'thu', 'fri'],
        sound: 'digital.mp3',
        enabled: true
    }
];

// Initialize alarms component
function initializeAlarms() {
    renderAlarms();
    addAlarmEventListeners();
}

// Render alarms list
function renderAlarms() {
    const alarmList = document.querySelector('.alarm-list');
    if (!alarmList) return;

    if (alarms.length === 0) {
        alarmList.innerHTML = `
            <div class="empty-state">
                <i class="material-icons">alarm_off</i>
                <p>No alarms set</p>
                <p>Click the + button to add an alarm</p>
            </div>
        `;
        return;
    }

    alarmList.innerHTML = alarms.map(alarm => `
        <div class="alarm-card" data-id="${alarm.id}">
            <div class="alarm-header">
                <div class="alarm-time">${alarm.time}</div>
                <label class="switch">
                    <input type="checkbox" ${alarm.enabled ? 'checked' : ''}>
                    <span class="slider round"></span>
                </label>
            </div>
            <div class="alarm-details">
                <div class="alarm-title">${alarm.title}</div>
                <div class="alarm-days">
                    ${formatDays(alarm.days)}
                </div>
                <div class="alarm-sound">
                    <i class="material-icons">music_note</i>
                    ${formatSoundName(alarm.sound)}
                </div>
            </div>
            <div class="alarm-actions">
                <button class="edit-btn">
                    <i class="material-icons">edit</i>
                </button>
                <button class="delete-btn">
                    <i class="material-icons">delete</i>
                </button>
            </div>
        </div>
    `).join('');

    // Add styles for alarm cards
    const style = document.createElement('style');
    style.textContent = `
        .alarm-list {
            display: grid;
            gap: 1rem;
            padding: 1rem;
        }

        .empty-state {
            text-align: center;
            padding: 2rem;
            color: var(--text-secondary);
        }

        .empty-state i {
            font-size: 3rem;
            margin-bottom: 1rem;
        }

        .alarm-card {
            background: var(--surface);
            border-radius: 8px;
            padding: 1rem;
            display: grid;
            gap: 1rem;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .alarm-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .alarm-time {
            font-size: 2rem;
            font-weight: 500;
            color: var(--text-primary);
        }

        .alarm-details {
            display: grid;
            gap: 0.5rem;
        }

        .alarm-title {
            font-weight: 500;
            color: var(--text-primary);
        }

        .alarm-days {
            color: var(--text-secondary);
            font-size: 0.9rem;
        }

        .alarm-sound {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: var(--text-secondary);
            font-size: 0.9rem;
        }

        .alarm-actions {
            display: flex;
            justify-content: flex-end;
            gap: 0.5rem;
        }

        .alarm-actions button {
            background: none;
            border: none;
            color: var(--text-secondary);
            cursor: pointer;
            padding: 0.5rem;
            border-radius: 4px;
            transition: all 0.3s ease;
        }

        .alarm-actions button:hover {
            background: var(--hover);
            color: var(--text-primary);
        }

        /* Switch styles */
        .switch {
            position: relative;
            display: inline-block;
            width: 60px;
            height: 34px;
        }

        .switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }

        .slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: var(--surface-variant);
            transition: .4s;
            border-radius: 34px;
        }

        .slider:before {
            position: absolute;
            content: "";
            height: 26px;
            width: 26px;
            left: 4px;
            bottom: 4px;
            background-color: white;
            transition: .4s;
            border-radius: 50%;
        }

        input:checked + .slider {
            background-color: var(--primary);
        }

        input:checked + .slider:before {
            transform: translateX(26px);
        }
    `;
    document.head.appendChild(style);
}

// Add alarm event listeners
function addAlarmEventListeners() {
    document.querySelectorAll('.alarm-card').forEach(card => {
        // Toggle switch
        const toggle = card.querySelector('input[type="checkbox"]');
        toggle?.addEventListener('change', (e) => {
            const alarmId = parseInt(card.dataset.id);
            const alarm = alarms.find(a => a.id === alarmId);
            if (alarm) {
                alarm.enabled = e.target.checked;
                app.showNotification(`Alarm ${alarm.enabled ? 'enabled' : 'disabled'}`);
            }
        });

        // Edit button
        const editBtn = card.querySelector('.edit-btn');
        editBtn?.addEventListener('click', () => {
            const alarmId = parseInt(card.dataset.id);
            editAlarm(alarmId);
        });

        // Delete button
        const deleteBtn = card.querySelector('.delete-btn');
        deleteBtn?.addEventListener('click', () => {
            const alarmId = parseInt(card.dataset.id);
            deleteAlarm(alarmId);
        });
    });

    // Add new alarm form handler
    const alarmForm = document.getElementById('add-alarm-form');
    alarmForm?.addEventListener('submit', (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const newAlarm = {
            id: alarms.length + 1,
            title: formData.get('alarm-title') || 'Alarm',
            time: formData.get('alarm-time'),
            days: [...document.querySelectorAll('.day-selector input:checked')].map(input => input.value),
            sound: formData.get('alarm-sound') || 'digital.mp3',
            enabled: true
        };
        alarms.push(newAlarm);
        renderAlarms();
        document.getElementById('modal-container').classList.remove('active');
        app.showNotification('Alarm added successfully');
    });
}

// Format days for display
function formatDays(days) {
    const dayNames = {
        'sun': 'Sunday',
        'mon': 'Monday',
        'tue': 'Tuesday',
        'wed': 'Wednesday',
        'thu': 'Thursday',
        'fri': 'Friday',
        'sat': 'Saturday'
    };

    if (days.length === 7) return 'Every day';
    if (days.length === 5 && !days.includes('sun') && !days.includes('sat')) return 'Weekdays';
    if (days.length === 2 && days.includes('sat') && days.includes('sun')) return 'Weekends';
    
    return days.map(d => dayNames[d].slice(0, 3)).join(', ');
}

// Format sound name for display
function formatSoundName(sound) {
    return sound.replace('.mp3', '').split('-').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
}

// Edit alarm
function editAlarm(alarmId) {
    const alarm = alarms.find(a => a.id === alarmId);
    if (!alarm) return;

    // Populate form
    document.getElementById('alarm-time').value = alarm.time;
    document.getElementById('alarm-title').value = alarm.title;
    document.querySelectorAll('.day-selector input').forEach(input => {
        input.checked = alarm.days.includes(input.value);
    });
    document.getElementById('alarm-sound').value = alarm.sound;

    // Show modal
    document.getElementById('modal-container').classList.add('active');
}

// Delete alarm
function deleteAlarm(alarmId) {
    if (!confirm('Are you sure you want to delete this alarm?')) return;
    
    alarms = alarms.filter(a => a.id !== alarmId);
    renderAlarms();
    app.showNotification('Alarm deleted successfully');
}

// Refresh alarms
function refreshAlarms() {
    renderAlarms();
}

// Initialize when app.js loads it
window.initializeAlarms = initializeAlarms; 