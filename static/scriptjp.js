function showMessageBubble() {
    const bubblemsg = document.getElementById('message-bubble');
    if (bubblemsg) {
        bubblemsg.classList.add('message-bubble-visible');
    }
}

function setPipelineStatus(status) {
    const pipeline = document.getElementById("mode-pipeline");
    if (pipeline) {
        pipeline.innerText = status;
    }
}

function translatjp() {

    const textInput = document.getElementById('message-input');
    const chatArea = document.getElementById('chat-area');
    const unique_id = document.getElementById('unique_id')?.value;

    if (!textInput || !chatArea || !unique_id) return;

    const text = textInput.value.trim();
    if (text === '') return;

    setPipelineStatus("Processing...");
    textInput.disabled = true;

    /* ---------- USER MESSAGE ---------- */

    const userMessageElement = document.createElement('div');
    userMessageElement.className = 'msg user';
    userMessageElement.textContent = text;
    chatArea.appendChild(userMessageElement);
    chatArea.scrollTop = chatArea.scrollHeight;

    textInput.value = '';

    /* ---------- SEND TO SERVER ---------- */

    fetch('/translatjp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            text: text,
            unique_id: unique_id
        })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.error || "Server error");
            });
        }
        return response.json();
    })
    .then(data => {

        const translatedText = data.translated_text;

        /* ---------- ASSISTANT MESSAGE ---------- */

        const translatedMessageElement = document.createElement('div');
        translatedMessageElement.className = 'msg assistant';

        const textSpan = document.createElement('span');
        textSpan.textContent = translatedText;
        translatedMessageElement.appendChild(textSpan);

        chatArea.appendChild(translatedMessageElement);
        chatArea.scrollTop = chatArea.scrollHeight;

        /* ---------- TEXT TO SPEECH ---------- */

        if (data.serial_number) {

            fetch('/speechjp', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    serial_number: data.serial_number,
                    unique_id: unique_id
                })
            })
            .then(res => res.json())
            .then(audioData => {

                if (audioData.audio_url) {

                    // Prevent caching
                    const audio = new Audio(audioData.audio_url + "?t=" + new Date().getTime());

                    const playPauseButton = document.createElement('button');
                    playPauseButton.className = 'audio-control';
                    playPauseButton.innerHTML = "🔊";

                    let isPlaying = false;

                    playPauseButton.addEventListener('click', function () {
                        if (!isPlaying) {
                            audio.play();
                            playPauseButton.innerHTML = "⏸";
                            isPlaying = true;
                        } else {
                            audio.pause();
                            playPauseButton.innerHTML = "🔊";
                            isPlaying = false;
                        }
                    });

                    audio.addEventListener('ended', () => {
                        playPauseButton.innerHTML = "🔊";
                        isPlaying = false;
                    });

                    translatedMessageElement.appendChild(playPauseButton);
                }
            });
        }

        setPipelineStatus("Idle");
        textInput.disabled = false;
    })
    .catch(error => {
        console.error("Translation error:", error);
        setPipelineStatus("Error");
        textInput.disabled = false;
    });
}

/* ---------- Optional UI Utilities ---------- */

function transparent() {
    const bubblemsg = document.getElementById('message-bubble');
    if (bubblemsg) {
        bubblemsg.classList.remove('message-bubble-visible');
    }
}

function moveMessages() {
    const bubblemsg = document.getElementById('message-bubble');
    const chatMessages = document.getElementById('chat-messages');

    if (!bubblemsg || !chatMessages) return;

    while (bubblemsg.firstChild) {
        chatMessages.appendChild(bubblemsg.firstChild);
    }

    transparent();
}

function showchat() {
    const showBtn = document.getElementById('show');
    const chatContainer = document.getElementById('chat-container');

    if (!showBtn || !chatContainer) return;

    showBtn.addEventListener('click', function() {
        chatContainer.classList.toggle('chat-container-visible');
    });
}

const nextBtn = document.getElementById('next');
if (nextBtn) {
    nextBtn.addEventListener('click', moveMessages);
}

/* ---------- Model Viewer Safety ---------- */

const myModelViewer = document.getElementById('myModelViewer');
if (myModelViewer) {
    myModelViewer.cameraOrbit = '0deg 90deg 2m';
    myModelViewer.cameraTarget = '20m 59m 700m';
    myModelViewer.cameraFov = '60deg';
}
function toggleSidebar() {
  document.getElementById("sidebar").classList.toggle("collapsed");
  document.getElementById("main-content").classList.toggle("collapsed");
}

/* Navigation WITH unique_id */

function goToImage() {
  const name = document.getElementById("name").value;
  const post = document.getElementById("post").value;
  const unique_id = document.getElementById("unique_id").value;

  window.location.href =
    `/image_jp?name=${encodeURIComponent(name)}&post=${encodeURIComponent(post)}&unique_id=${encodeURIComponent(unique_id)}`;
}

function goToRecord() {
  const name = document.getElementById("name").value;
  const post = document.getElementById("post").value;
  const unique_id = document.getElementById("unique_id").value;

  window.location.href =
    `/recordjp?name=${encodeURIComponent(name)}&post=${encodeURIComponent(post)}&unique_id=${encodeURIComponent(unique_id)}`;
}

/* Profile Dropdown */

document.addEventListener('DOMContentLoaded', function () {
  const button = document.getElementById('profilebutton');
  const dropdown = document.querySelector('.dropdown-menu');

  button.addEventListener('mouseenter', () => dropdown.style.display = 'block');
  button.addEventListener('mouseleave', () => {
    setTimeout(() => {
      if (!dropdown.matches(':hover')) {
        dropdown.style.display = 'none';
      }
    }, 200);
  });

  dropdown.addEventListener('mouseenter', () => dropdown.style.display = 'block');
  dropdown.addEventListener('mouseleave', () => dropdown.style.display = 'none');
});

/* Service Worker */

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/static/sw.js")
    .then(() => console.log("Service Worker Registered"));
}
