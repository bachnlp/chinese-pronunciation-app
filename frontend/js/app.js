let mediaRecorder;
let audioChunks = [];
let isRecording = false;

// DOM Elements
const recordBtn = document.getElementById('recordBtn');
const btnIcon = document.getElementById('btnIcon');
const btnText = document.getElementById('btnText');
const statusText = document.getElementById('statusText');

const uploadBtn = document.getElementById('uploadBtn');
const audioFileInput = document.getElementById('audioFileInput');
const uploadStatusText = document.getElementById('uploadStatusText');

const resultBox = document.getElementById('resultBox');
const toggleResultBtn = document.getElementById('toggleResultBtn');
const similarityScoreEl = document.getElementById('similarityScore');
const diffContainer = document.getElementById('diffContainer');
const recognizedTextEl = document.getElementById('recognizedText');

toggleResultBtn.addEventListener('click', () => {
    setResultVisible(resultBox.style.display === 'none');
});

function setResultVisible(visible) {
    resultBox.style.display = visible ? 'block' : 'none';
    toggleResultBtn.setAttribute('aria-expanded', String(visible));
    toggleResultBtn.textContent = visible ? 'Ẩn kết quả' : 'Hiện kết quả';
}

// Chuyển đổi giữa tab Ghi âm và Tải file
const tabBtns = document.querySelectorAll('.tab-btn');
tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        tabBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        const targetId = btn.getAttribute('data-target');
        document.querySelectorAll('.input-section').forEach(section => {
            section.style.display = 'none';
        });
        document.getElementById(targetId).style.display = 'block';
        setResultVisible(false);
    });
});

// 1. Xử lý Ghi âm trực tiếp
recordBtn.addEventListener('click', async () => {
    if (!isRecording) {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];

            mediaRecorder.ondataavailable = event => {
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                await sendAudioToBackend(audioBlob, "recording.webm");
            };

            mediaRecorder.start();
            isRecording = true;
            recordBtn.classList.add('recording');
            btnIcon.textContent = '⏹️';
            btnText.textContent = 'Dừng & Chấm điểm';
            statusText.textContent = 'Đang ghi âm... Hãy đọc to câu tiếng Trung của bạn!';
            setResultVisible(false);
        } catch (err) {
            console.error("Không thể truy cập Micro:", err);
            alert("Không thể truy cập micro. Vui lòng cấp quyền cho trình duyệt!");
        }
    } else {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
        
        isRecording = false;
        recordBtn.classList.remove('recording');
        btnIcon.textContent = '🔴';
        btnText.textContent = 'Nhấn để ghi âm';
        statusText.textContent = 'Đang xử lý kết quả với Backend...';
    }
});

// 2. Xử lý Tải file lên
uploadBtn.addEventListener('click', async () => {
    const file = audioFileInput.files[0];
    if (!file) {
        uploadStatusText.textContent = 'Vui lòng chọn một file audio (.mp3, .wav, .webm) trước.';
        return;
    }

    uploadStatusText.textContent = 'Đang gửi file lên Backend...';
    setResultVisible(false);
    uploadBtn.disabled = true;
    try {
        const succeeded = await sendAudioToBackend(file, file.name);
        if (succeeded) {
            uploadStatusText.textContent = 'Chấm điểm hoàn tất!';
        }
    } finally {
        uploadBtn.disabled = false;
    }
});

// Hàm chung gửi file audio lên FastAPI Backend
async function sendAudioToBackend(audioBlob, filename) {
    const referenceText = document.getElementById('referenceText').value.trim();
    if (!referenceText) {
        statusText.textContent = 'Chưa nhập câu mẫu.';
        uploadStatusText.textContent = 'Chưa nhập câu mẫu.';
        return false;
    }

    const formData = new FormData();
    formData.append("audio", audioBlob, filename);
    formData.append("reference_text", referenceText);

    try {
        const backendUrl = window.location.origin.includes("127.0.0.1") 
    ? "http://127.0.0.1:8000/api/v1/check-pronunciation"
    : "https://ten-mien-backend-cua-ban.com/api/v1/check-pronunciation";
        const response = await fetch(backendUrl, {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `Lỗi server: ${response.status} ${response.statusText}`);
        }

        const result = await response.json();
        displayResult(result);
        statusText.textContent = 'Chấm điểm hoàn tất!';
        uploadStatusText.textContent = 'Chấm điểm hoàn tất!';
        return true;
    } catch (error) {
        console.error("Lỗi kết nối API:", error);
        const message = error instanceof TypeError
            ? 'Không thể kết nối tới Backend FastAPI ở cổng 8000. Hãy kiểm tra server.'
            : `Không thể chấm điểm audio: ${error.message}`;
        statusText.textContent = message;
        uploadStatusText.textContent = message;
        return false;
    }
}

// Hiển thị kết quả lên giao diện
function displayResult(data) {
    toggleResultBtn.hidden = false;
    setResultVisible(true);
    similarityScoreEl.textContent = data.similarity_score;
    recognizedTextEl.textContent = data.recognized_text || "(Không nhận diện được)";

    diffContainer.innerHTML = '';

    if (data.detailed_diff && data.detailed_diff.length > 0) {
        data.detailed_diff.forEach(item => {
            const span = document.createElement('span');
            span.textContent = item.char;

            if (item.status === 'correct') {
                span.className = 'char-correct';
            } else if (item.status === 'incorrect') {
                span.className = 'char-incorrect';
                span.title = `Đọc lệch thành: ${item.recognized_as || '?'}`;
            } else if (item.status === 'missing') {
                span.className = 'char-missing';
                span.title = 'Bỏ sót ký tự này';
            } else {
                span.className = '';
            }

            diffContainer.appendChild(span);
        });
    } else {
        diffContainer.textContent = data.reference_text;
    }

    resultBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}