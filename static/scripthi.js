function showMessageBubble() {
    const bubblemsg = document.getElementById('message-bubble');
    bubblemsg.classList.add('message-bubble-visible');
    }
    
    function setPipelineStatus(status) {
  document.getElementById("mode-pipeline").innerText = status;
}

function translat() {
    setPipelineStatus("Processing...");

    const text = document.getElementById('message-input').value.trim();
    const name = document.getElementById('name').value;
    const post = document.getElementById('post').value;
    const chatArea = document.getElementById('chat-area');

    if (text === '') return;

    // Create user message bubble
    const userMessageElement = document.createElement('div');
    userMessageElement.className = 'msg user';
    userMessageElement.textContent = text;
    chatArea.appendChild(userMessageElement);
    chatArea.scrollTop = chatArea.scrollHeight;

    // Clear the input field
    document.getElementById('message-input').value = '';

    // Send message to server
    fetch('/translathi', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text: text, name: name, post: post })
    })
    .then(response => response.json())
    .then(data => {
        if (data.serial_number) {
            // Get audio from /speechhi
            fetch('/speechhi', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    serial_number: data.serial_number,
                    name: name,
                    post: post
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.audio_url) {
                    // Create audio player with mute/unmute
                    const audioDiv = document.createElement('div');
                    const audio = new Audio(data.audio_url);
                    audio.controls = false;

                    const playPauseButton = document.createElement('button');
                    playPauseButton.className = 'audio-control';
                    playPauseButton.innerHTML = "<img src='static/img/unmute.jpeg' alt='Pause'>";
                    let isPlaying = false;

                    playPauseButton.addEventListener('click', function () {
                        if (!isPlaying) {
                            audio.play();
                            playPauseButton.innerHTML = "<img src='static/img/unmute.jpeg' alt='Pause'>";
                            isPlaying = true;
                        } else {
                            audio.pause();
                            playPauseButton.innerHTML = "<img src='static/img/muted.jpeg' alt='Play'>";
                            isPlaying = false;
                        }
                    });

                    audio.addEventListener('play', () => {
                        playPauseButton.innerHTML = "<img src='static/img/unmute.jpeg' alt='Pause'>";
                        isPlaying = true;
                    });

                    audio.addEventListener('pause', () => {
                        playPauseButton.innerHTML = "<img src='static/img/muted.jpeg' alt='Play'>";
                        isPlaying = false;
                    });

                    audioDiv.className = 'audio-controls';
                    audioDiv.appendChild(playPauseButton);
                    audioDiv.appendChild(audio);
                    chatArea.appendChild(audioDiv);
                }
            });
        }

        // Show translated assistant message
        const translatedText = data.translated_text || 'Translation error.';
        const translatedMessageElement = document.createElement('div');
        translatedMessageElement.className = 'msg assistant';
        translatedMessageElement.textContent = translatedText;
        chatArea.appendChild(translatedMessageElement);
        chatArea.scrollTop = chatArea.scrollHeight;
        setTimeout(() => {
    setPipelineStatus("Idle");
  }, 1200);
    });
}

function transparent() {
const bubblemsg = document.getElementById('message-bubble');
bubblemsg.classList.remove('message-bubble-visible');
}
function moveMessages() {
const bubblemsg = document.getElementById('message-bubble');
const chatMessages = document.getElementById('chat-messages');
// Move all messages from bubblemsg to chatMessages
while (bubblemsg.firstChild) {
    chatMessages.appendChild(bubblemsg.firstChild);
}
transparent();
}
function showchat() {
document.getElementById('show').addEventListener('click', function() {
const chatContainer = document.getElementById('chat-container');
chatContainer.classList.toggle('chat-container-visible');
});
}

document.getElementById('next').addEventListener('click', moveMessages);

const myModelViewer = document.getElementById('myModelViewer');
myModelViewer.cameraOrbit = '0deg 90deg 2m';
myModelViewer.cameraTarget = '20m 59m 700m';
myModelViewer.cameraFov = '60deg';