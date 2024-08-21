// script.js
const WEBSOCKET_URL = 'ws://localhost:8765';
const ENABLE_REAL_TIME_FEEDBACK = 'enable_real_time_feedback';
const DISABLE_REAL_TIME_FEEDBACK = 'disable_real_time_feedback';
const RECONNECT_TIMEOUT = 5000; // 5 seconds

let socket;

function initWebSocket() {
    socket = new WebSocket(WEBSOCKET_URL);
    socket.onopen = handleConnectionOpen;
    socket.onmessage = handleIncomingMessage;
    socket.onerror = handleConnectionError;
    socket.onclose = handleConnectionClose;
}

function handleConnectionOpen() {
    console.log('Connection established');
    output.innerHTML = '<p>Connected to server</p>';
    // Send a "ping" message to the server to keep the connection alive
    setInterval(() => {
        socket.send(JSON.stringify({ action: 'ping' }));
    }, 30000); // 30 seconds
}

function handleIncomingMessage(event) {
    const data = JSON.parse(event.data);
    switch (data.action) {
        case 'load_student_work':
            handleLoadStudentWork(data.content);
            break;
        case 'load_selected_student_work':
            handleLoadSelectedStudentWork(data.content);
            break;
        default:
            output.innerHTML += `<h3>${data.action}</h3><p>${data.response}</p>`;
    }
}

function handleConnectionError(error) {
    console.error(`WebSocket Error: ${error}`);
    output.innerHTML += `<p class="error">WebSocket Error: ${error}</p>`;
    // Reconnect to the server after a timeout
    setTimeout(initWebSocket, RECONNECT_TIMEOUT);
}

function handleConnectionClose(event) {
    if (event.wasClean) {
        console.log(`Connection closed cleanly, code=${event.code}, reason=${event.reason}`);
    } else {
        console.error('Connection died');
    }
    output.innerHTML += `<p class="error">Connection closed</p>`;
    // Reconnect to the server after a timeout
    setTimeout(initWebSocket, RECONNECT_TIMEOUT);
}

function reconnect() {
    socket.close();
    initWebSocket();
}

function clearOutput() {
    document.getElementById('output').innerHTML = '';
}

function saveStudentWork() {
    const studentWork = document.getElementById('studentWork').value;
    const assessmentType = document.getElementById('assessmentType').value;
    const message = {
        action: 'save_student_work',
        content: {
            student_work: studentWork,
            assessment_type: assessmentType
        }
    };
    socket.send(JSON.stringify(message));
output.innerHTML += `<p>Student work saved successfully!</p>`;
}

function loadStudentWork() {
    const assessmentType = document.getElementById('assessmentType').value;
    const message = {
        action: 'load_student_work',
        content: {
            assessment_type: assessmentType
        }
    };
    socket.send(JSON.stringify(message));
}

function handleLoadStudentWork(content) {
    const savedStudentWorkSelect = document.getElementById('savedStudentWork');
    savedStudentWorkSelect.innerHTML = '';
    content.saved_student_works.forEach(function(work) {
        const option = document.createElement('option');
        option.value = work.id;
        option.text = work.title;
        savedStudentWorkSelect.appendChild(option);
    });
}

function handleLoadSelectedStudentWork(content) {
    const studentWorkTextarea = document.getElementById('studentWork');
    studentWorkTextarea.value = content.student_work;
}

initWebSocket();

const output = document.getElementById('output');
const savedStudentWorkSelect = document.getElementById('savedStudentWork');

savedStudentWorkSelect.addEventListener('change', function() {
    const selectedWorkId = this.value;
    const message = {
        action: 'load_selected_student_work',
        content: {
            work_id: selectedWorkId
        }
    };
    socket.send(JSON.stringify(message));
});
