// Calendar state
let events = [];
let currentDate = new Date();
let currentView = 'month'; // month, week, or day

// Initialize calendar component
function initializeCalendar() {
    // Load initial events
    loadEvents();
    
    // Render calendar
    renderCalendar();
    
    // Add event listeners
    addCalendarEventListeners();
}

// Load events from Google Calendar
function loadEvents() {
    fetch(`${API_BASE_URL}/calendar/events`, {
        headers: window.defaultHeaders
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            events = data.events;
            renderEvents();
        }
    })
    .catch(error => {
        console.error('Error loading events:', error);
        showNotification('Error loading calendar events', 'error');
    });
}

// Render calendar grid
function renderCalendar() {
    const container = document.getElementById('calendar-container');
    container.innerHTML = `
        <div class="calendar-header">
            <div class="calendar-nav">
                <button class="prev-btn">
                    <i class="material-icons">chevron_left</i>
                </button>
                <h3 class="current-date"></h3>
                <button class="next-btn">
                    <i class="material-icons">chevron_right</i>
                </button>
            </div>
            <div class="view-options">
                <button class="view-btn" data-view="month">Month</button>
                <button class="view-btn" data-view="week">Week</button>
                <button class="view-btn" data-view="day">Day</button>
            </div>
        </div>
        <div class="calendar-grid"></div>
    `;
    
    updateCalendarView();
}

// Update calendar view based on current settings
function updateCalendarView() {
    updateHeader();
    
    switch (currentView) {
        case 'month':
            renderMonthView();
            break;
        case 'week':
            renderWeekView();
            break;
        case 'day':
            renderDayView();
            break;
    }
    
    renderEvents();
}

// Update calendar header
function updateHeader() {
    const header = document.querySelector('.current-date');
    let dateString;
    
    switch (currentView) {
        case 'month':
            dateString = currentDate.toLocaleString('default', { month: 'long', year: 'numeric' });
            break;
        case 'week':
            const weekStart = getWeekStart(currentDate);
            const weekEnd = new Date(weekStart);
            weekEnd.setDate(weekEnd.getDate() + 6);
            dateString = `${app.formatDate(weekStart)} - ${app.formatDate(weekEnd)}`;
            break;
        case 'day':
            dateString = app.formatDate(currentDate);
            break;
    }
    
    header.textContent = dateString;
}

// Render month view
function renderMonthView() {
    const grid = document.querySelector('.calendar-grid');
    grid.innerHTML = '';
    
    // Add day headers
    const dayHeaders = document.createElement('div');
    dayHeaders.className = 'day-headers';
    ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].forEach(day => {
        const header = document.createElement('div');
        header.className = 'day-header';
        header.textContent = day;
        dayHeaders.appendChild(header);
    });
    grid.appendChild(dayHeaders);
    
    // Get first day of month
    const firstDay = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
    const startingDay = firstDay.getDay();
    
    // Get number of days in month
    const lastDay = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
    const totalDays = lastDay.getDate();
    
    // Create calendar days
    let dayCount = 1;
    for (let i = 0; i < 6; i++) {
        const week = document.createElement('div');
        week.className = 'calendar-week';
        
        for (let j = 0; j < 7; j++) {
            const day = document.createElement('div');
            day.className = 'calendar-day';
            
            if (i === 0 && j < startingDay || dayCount > totalDays) {
                day.className += ' empty';
            } else {
                day.textContent = dayCount;
                day.dataset.date = `${currentDate.getFullYear()}-${String(currentDate.getMonth() + 1).padStart(2, '0')}-${String(dayCount).padStart(2, '0')}`;
                
                // Highlight current day
                if (isCurrentDay(new Date(currentDate.getFullYear(), currentDate.getMonth(), dayCount))) {
                    day.className += ' current';
                }
                
                dayCount++;
            }
            
            week.appendChild(day);
        }
        
        grid.appendChild(week);
        if (dayCount > totalDays) break;
    }
}

// Render week view
function renderWeekView() {
    const grid = document.querySelector('.calendar-grid');
    grid.innerHTML = '';
    
    const weekStart = getWeekStart(currentDate);
    
    // Add time column
    const timeColumn = document.createElement('div');
    timeColumn.className = 'time-column';
    for (let hour = 0; hour < 24; hour++) {
        const timeSlot = document.createElement('div');
        timeSlot.className = 'time-slot';
        timeSlot.textContent = `${hour.toString().padStart(2, '0')}:00`;
        timeColumn.appendChild(timeSlot);
    }
    grid.appendChild(timeColumn);
    
    // Add day columns
    for (let i = 0; i < 7; i++) {
        const day = new Date(weekStart);
        day.setDate(day.getDate() + i);
        
        const dayColumn = document.createElement('div');
        dayColumn.className = 'day-column';
        
        // Add day header
        const header = document.createElement('div');
        header.className = 'day-header';
        header.textContent = day.toLocaleString('default', { weekday: 'short', day: 'numeric' });
        if (isCurrentDay(day)) header.className += ' current';
        dayColumn.appendChild(header);
        
        // Add hour slots
        for (let hour = 0; hour < 24; hour++) {
            const hourSlot = document.createElement('div');
            hourSlot.className = 'hour-slot';
            hourSlot.dataset.date = app.formatDate(day);
            hourSlot.dataset.hour = hour;
            dayColumn.appendChild(hourSlot);
        }
        
        grid.appendChild(dayColumn);
    }
}

// Render day view
function renderDayView() {
    const grid = document.querySelector('.calendar-grid');
    grid.innerHTML = '';
    
    // Add time column
    const timeColumn = document.createElement('div');
    timeColumn.className = 'time-column';
    for (let hour = 0; hour < 24; hour++) {
        const timeSlot = document.createElement('div');
        timeSlot.className = 'time-slot';
        timeSlot.textContent = `${hour.toString().padStart(2, '0')}:00`;
        timeColumn.appendChild(timeSlot);
    }
    grid.appendChild(timeColumn);
    
    // Add day column
    const dayColumn = document.createElement('div');
    dayColumn.className = 'day-column full';
    
    // Add hour slots
    for (let hour = 0; hour < 24; hour++) {
        const hourSlot = document.createElement('div');
        hourSlot.className = 'hour-slot';
        hourSlot.dataset.date = app.formatDate(currentDate);
        hourSlot.dataset.hour = hour;
        dayColumn.appendChild(hourSlot);
    }
    
    grid.appendChild(dayColumn);
}

// Render events on calendar
function renderEvents() {
    // Clear existing events
    document.querySelectorAll('.calendar-event').forEach(el => el.remove());
    
    events.forEach(event => {
        const startDate = new Date(event.start_time);
        const endDate = new Date(event.end_time || event.start_time);
        
        switch (currentView) {
            case 'month':
                renderMonthEvent(event, startDate);
                break;
            case 'week':
                if (isInCurrentWeek(startDate)) {
                    renderTimeEvent(event, startDate, endDate);
                }
                break;
            case 'day':
                if (isSameDay(startDate, currentDate)) {
                    renderTimeEvent(event, startDate, endDate);
                }
                break;
        }
    });
}

// Render event in month view
function renderMonthEvent(event, date) {
    const dayCell = document.querySelector(`.calendar-day[data-date="${app.formatDate(date)}"]`);
    if (!dayCell) return;
    
    const eventElement = document.createElement('div');
    eventElement.className = 'calendar-event';
    eventElement.textContent = event.title;
    eventElement.title = `${event.title}\n${app.formatTime(date)}`;
    eventElement.dataset.id = event.id;
    
    dayCell.appendChild(eventElement);
}

// Render event in week/day view
function renderTimeEvent(event, startDate, endDate) {
    const dayColumn = document.querySelector(`.day-column[data-date="${app.formatDate(startDate)}"]`);
    if (!dayColumn) return;
    
    const startHour = startDate.getHours() + (startDate.getMinutes() / 60);
    const endHour = endDate.getHours() + (endDate.getMinutes() / 60);
    const duration = endHour - startHour;
    
    const eventElement = document.createElement('div');
    eventElement.className = 'calendar-event time-event';
    eventElement.textContent = event.title;
    eventElement.title = `${event.title}\n${app.formatTime(startDate)} - ${app.formatTime(endDate)}`;
    eventElement.dataset.id = event.id;
    eventElement.style.top = `${startHour * 60}px`;
    eventElement.style.height = `${duration * 60}px`;
    
    dayColumn.appendChild(eventElement);
}

// Helper functions
function getWeekStart(date) {
    const start = new Date(date);
    start.setDate(start.getDate() - start.getDay());
    return start;
}

function isCurrentDay(date) {
    const today = new Date();
    return date.getDate() === today.getDate() &&
           date.getMonth() === today.getMonth() &&
           date.getFullYear() === today.getFullYear();
}

function isInCurrentWeek(date) {
    const weekStart = getWeekStart(currentDate);
    const weekEnd = new Date(weekStart);
    weekEnd.setDate(weekEnd.getDate() + 7);
    return date >= weekStart && date < weekEnd;
}

function isSameDay(date1, date2) {
    return date1.getDate() === date2.getDate() &&
           date1.getMonth() === date2.getMonth() &&
           date1.getFullYear() === date2.getFullYear();
}

// Add event listeners
function addCalendarEventListeners() {
    // Navigation buttons
    document.querySelector('.prev-btn').addEventListener('click', () => {
        navigateCalendar('prev');
    });
    
    document.querySelector('.next-btn').addEventListener('click', () => {
        navigateCalendar('next');
    });
    
    // View buttons
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            currentView = btn.dataset.view;
            updateCalendarView();
        });
    });
}

// Navigate calendar
function navigateCalendar(direction) {
    switch (currentView) {
        case 'month':
            currentDate.setMonth(currentDate.getMonth() + (direction === 'prev' ? -1 : 1));
            break;
        case 'week':
            currentDate.setDate(currentDate.getDate() + (direction === 'prev' ? -7 : 7));
            break;
        case 'day':
            currentDate.setDate(currentDate.getDate() + (direction === 'prev' ? -1 : 1));
            break;
    }
    
    updateCalendarView();
}

// Refresh calendar
function refreshCalendar() {
    loadEvents();
} 