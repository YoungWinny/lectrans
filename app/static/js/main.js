document.addEventListener('DOMContentLoaded', function () {
    // Recording variables
    let mediaRecorder;
    let audioChunks = [];
    let startTime;
    let durationTimer;

    // DOM Elements
    const classSelect = document.getElementById('class');
    const courseSelect = document.getElementById('course');
    const startButton = document.getElementById('startRecord');
    const stopButton = document.getElementById('stopRecord');
    const playButton = document.getElementById('playRecord');
    const saveButton = document.getElementById('saveRecording');
    const audioPlayback = document.getElementById('audioPlayback');
    const recordingIndicator = document.getElementById('recordingIndicator');
    const recordingStatus = document.getElementById('recordingStatus');
    const durationDisplay = document.getElementById('duration');

    // Update courses when class is selected
    if (classSelect) {
        classSelect.addEventListener('change', function () {
            const classId = this.value;
            courseSelect.disabled = !classId;

            if (classId) {
                fetch(`/api/courses/${classId}`)
                    .then(response => response.json())
                    .then(courses => {
                        courseSelect.innerHTML = '<option value="">Select a course</option>';
                        courses.forEach(course => {
                            courseSelect.innerHTML += `<option value="${course.id}">${course.name}</option>`;
                        });
                    });
            }
        });
    }

    // Recording functionality
    if (startButton) {
        startButton.addEventListener('click', async () => {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);

                mediaRecorder.ondataavailable = event => {
                    audioChunks.push(event.data);
                };

                mediaRecorder.onstop = () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    const audioUrl = URL.createObjectURL(audioBlob);
                    audioPlayback.src = audioUrl;
                    audioPlayback.style.display = 'block';
                    playButton.disabled = false;
                    saveButton.disabled = false;
                };

                // Start recording
                mediaRecorder.start();
                audioChunks = [];
                startTime = Date.now();
                updateDuration();

                // Update UI
                startButton.disabled = true;
                stopButton.disabled = false;
                recordingIndicator.classList.add('active');
                recordingStatus.textContent = 'Recording...';

            } catch (err) {
                console.error('Error accessing microphone:', err);
                alert('Error accessing microphone. Please ensure microphone permissions are granted.');
            }
        });
    }

    // Stop recording
    if (stopButton) {
        stopButton.addEventListener('click', () => {
            if (mediaRecorder && mediaRecorder.state === 'recording') {
                mediaRecorder.stop();
                clearInterval(durationTimer);

                // Update UI
                startButton.disabled = false;
                stopButton.disabled = true;
                recordingIndicator.classList.remove('active');
                recordingStatus.textContent = 'Recording stopped';
            }
        });
    }


    if (saveButton) {
        document.getElementById('recordingForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = new FormData();

            // Get the blob from the recorded chunks
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });  // Use webm format
            formData.append('audio', audioBlob, 'recording.webm');
            formData.append('course_id', courseSelect.value);
            formData.append('chapter', document.getElementById('chapter').value);
            formData.append('name', document.getElementById('name').value);

            saveButton.disabled = true;
            saveButton.textContent = 'Saving...';

            try {
                const response = await fetch('/api/save-recording', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();
                if (data.success) {
                    window.location.href = `/lecture/${data.lecture_id}`;
                } else {
                    alert('Error saving recording: ' + (data.error || 'Unknown error'));
                    saveButton.disabled = false;
                    saveButton.textContent = 'Save Recording';
                }
            } catch (err) {
                console.error('Error saving recording:', err);
                alert('Error saving recording. Please try again.');
                saveButton.disabled = false;
                saveButton.textContent = 'Save Recording';
            }
        });
    }

    // Duration update function
    function updateDuration() {
        durationTimer = setInterval(() => {
            const duration = Math.floor((Date.now() - startTime) / 1000);
            const hours = Math.floor(duration / 3600);
            const minutes = Math.floor((duration % 3600) / 60);
            const seconds = duration % 60;
            durationDisplay.textContent =
                `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);
    }

    // Synchronization for lecture view
    const lectureAudio = document.getElementById('lectureAudio');
    const transcriptionText = document.getElementById('transcriptionText');

    if (lectureAudio && transcriptionText) {
        lectureAudio.addEventListener('timeupdate', () => {
            const currentTime = lectureAudio.currentTime;
            const timestamps = transcriptionText.querySelectorAll('p[data-timestamp]');

            timestamps.forEach(timestamp => {
                const time = parseFloat(timestamp.dataset.timestamp);
                if (time <= currentTime) {
                    // Remove highlight from all timestamps
                    timestamps.forEach(t => t.classList.remove('highlight'));
                    // Highlight current timestamp
                    timestamp.classList.add('highlight');
                    // Scroll to current timestamp
                    timestamp.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            });
        });
    }
});