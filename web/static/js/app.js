/**
 * AI Brain — Frontend App
 * 
 * Handles: Chat, Voice Input (Web Speech API), Voice Output (edge-tts),
 * and all UI interactions.
 */

// ═══════════════════════════════════════════════════
// State
// ═══════════════════════════════════════════════════
const state = {
    connected: false,
    isListening: false,
    isSpeaking: false,
    isProcessing: false,
    recognition: null,
    currentAudio: null,
    messageCount: 0,
};

// ═══════════════════════════════════════════════════
// DOM Elements
// ═══════════════════════════════════════════════════
const $ = (id) => document.getElementById(id);
const chatArea = $('chat-area');
const messageInput = $('message-input');
const sendBtn = $('send-btn');
const micBtn = $('mic-btn');
const brainIcon = $('brain-icon');
const statusText = $('status-text');
const voiceStatus = $('voice-status');
const setupModal = $('setup-modal');
const welcome = $('welcome');

// ═══════════════════════════════════════════════════
// Initialization
// ═══════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
    initSpeechRecognition();
    initTextareaAutoResize();
    checkConnection();

    // Enter to send
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
});

async function checkConnection() {
    try {
        const res = await fetch('/api/actions');
        if (res.ok) {
            setConnected(true);
        } else {
            showSetup();
        }
    } catch {
        showSetup();
    }
}

function setConnected(connected) {
    state.connected = connected;
    statusText.textContent = connected ? 'Operativo' : 'Desconectado';
    statusText.className = connected ? 'status online' : 'status';
    brainIcon.className = connected ? 'brain-icon active' : 'brain-icon';
}

// ═══════════════════════════════════════════════════
// API Key Setup
// ═══════════════════════════════════════════════════
function showSetup() {
    setupModal.style.display = 'flex';
}

async function saveApiKey() {
    const input = $('api-key-input');
    const key = input.value.trim();
    if (!key) return;

    const btn = $('save-key-btn');
    btn.querySelector('.btn-text').style.display = 'none';
    btn.querySelector('.btn-loader').style.display = 'inline';

    try {
        const res = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_key: key }),
        });

        const data = await res.json();
        if (data.success) {
            setupModal.style.display = 'none';
            setConnected(true);
        } else {
            alert('Error: ' + data.error);
        }
    } catch (e) {
        alert('Error de conexión: ' + e.message);
    }

    btn.querySelector('.btn-text').style.display = 'inline';
    btn.querySelector('.btn-loader').style.display = 'none';
}

// ═══════════════════════════════════════════════════
// Chat
// ═══════════════════════════════════════════════════
async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text || state.isProcessing) return;

    // Hide welcome
    if (welcome) welcome.style.display = 'none';

    // Add user message
    addMessage('user', text);
    messageInput.value = '';
    messageInput.style.height = 'auto';

    // Show typing
    const typingEl = showTyping();

    state.isProcessing = true;
    sendBtn.disabled = true;

    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text }),
        });

        const data = await res.json();
        removeTyping(typingEl);

        if (data.error) {
            if (data.error.includes('API key') || data.error.includes('GEMINI_API_KEY')) {
                showSetup();
            }
            addMessage('agent', '❌ ' + data.error);
        } else {
            addMessage('agent', data.response);
            updateStats(data.stats);

            // Auto-speak if enabled
            if ($('auto-speak')?.checked) {
                speakText(data.response);
            }
        }
    } catch (e) {
        removeTyping(typingEl);
        addMessage('agent', '❌ Error de conexión: ' + e.message);
    }

    state.isProcessing = false;
    sendBtn.disabled = false;
    messageInput.focus();
}

function sendQuick(text) {
    messageInput.value = text;
    sendMessage();
}

// ═══════════════════════════════════════════════════
// Messages
// ═══════════════════════════════════════════════════
function addMessage(role, text) {
    state.messageCount++;
    const id = `msg-${state.messageCount}`;

    const msgEl = document.createElement('div');
    msgEl.className = `message ${role}`;
    msgEl.id = id;

    const avatar = role === 'user' ? '👤' : '🧠';
    const time = new Date().toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit' });

    const formattedText = formatText(text);

    msgEl.innerHTML = `
        <div class="msg-avatar">${avatar}</div>
        <div class="msg-body">
            <div class="msg-content">${formattedText}</div>
            <div class="msg-meta">
                <span>${time}</span>
                ${role === 'agent' ? `<button class="msg-speak-btn" onclick="speakText(\`${escapeForTemplate(text)}\`)" title="Escuchar">🔊</button>` : ''}
            </div>
        </div>
    `;

    chatArea.appendChild(msgEl);
    scrollToBottom();
}

function formatText(text) {
    // Escape HTML
    let html = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    // Code blocks
    html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => {
        return `<pre><code>${code.trim()}</code></pre>`;
    });

    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Bold
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

    // Italic
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

    // Line breaks
    html = html.replace(/\n/g, '<br>');

    return html;
}

function escapeForTemplate(text) {
    return text.replace(/`/g, '\\`').replace(/\$/g, '\\$').replace(/\\/g, '\\\\');
}

function showTyping() {
    const el = document.createElement('div');
    el.className = 'message agent';
    el.id = 'typing-msg';
    el.innerHTML = `
        <div class="msg-avatar">🧠</div>
        <div class="msg-body">
            <div class="msg-content typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
    `;
    chatArea.appendChild(el);
    scrollToBottom();
    return el;
}

function removeTyping(el) {
    if (el && el.parentNode) {
        el.parentNode.removeChild(el);
    }
}

function scrollToBottom() {
    requestAnimationFrame(() => {
        chatArea.scrollTop = chatArea.scrollHeight;
    });
}

// ═══════════════════════════════════════════════════
// Stats
// ═══════════════════════════════════════════════════
function updateStats(stats) {
    if (!stats) return;
    $('stat-actions').textContent = `⚡ ${stats.actions}`;
    $('stat-success').textContent = `✅ ${stats.success_rate}`;
}

// ═══════════════════════════════════════════════════
// Voice Input — Web Speech API
// ═══════════════════════════════════════════════════
function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        console.warn('Speech Recognition no soportado');
        micBtn.style.display = 'none';
        return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'es-MX';
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event) => {
        let transcript = '';
        let isFinal = false;

        for (let i = event.resultIndex; i < event.results.length; i++) {
            transcript += event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                isFinal = true;
            }
        }

        messageInput.value = transcript;

        if (isFinal) {
            stopListening();
            // Auto-send after voice input
            setTimeout(() => sendMessage(), 300);
        }
    };

    recognition.onend = () => {
        stopListening();
    };

    recognition.onerror = (event) => {
        console.error('Speech error:', event.error);
        stopListening();
        if (event.error === 'no-speech') {
            // Silently ignore
        } else if (event.error === 'not-allowed') {
            alert('Permiso de micrófono denegado. Habilítalo en la configuración del navegador.');
        }
    };

    state.recognition = recognition;
}

function toggleVoice() {
    if (state.isListening) {
        stopListening();
    } else {
        startListening();
    }
}

function startListening() {
    if (!state.recognition) return;

    // Stop any ongoing audio
    stopSpeaking();

    state.isListening = true;
    micBtn.classList.add('listening');
    micBtn.querySelector('.mic-ripple').style.display = 'block';
    voiceStatus.style.display = 'inline';
    messageInput.placeholder = '🎤 Escuchando...';

    try {
        state.recognition.start();
    } catch (e) {
        console.error('Error starting recognition:', e);
        stopListening();
    }
}

function stopListening() {
    state.isListening = false;
    micBtn.classList.remove('listening');
    micBtn.querySelector('.mic-ripple').style.display = 'none';
    voiceStatus.style.display = 'none';
    messageInput.placeholder = 'Escribe una instrucción o presiona 🎤 para hablar...';

    try {
        state.recognition?.stop();
    } catch { }
}

// ═══════════════════════════════════════════════════
// Voice Output — edge-tts
// ═══════════════════════════════════════════════════
async function speakText(text) {
    if (!text) return;

    // Stop current audio
    stopSpeaking();

    // Clean text for TTS (remove markdown, code blocks, etc.)
    let cleanText = text
        .replace(/```[\s\S]*?```/g, ' (bloque de código) ')
        .replace(/`[^`]+`/g, '')
        .replace(/\[.*?\]/g, '')
        .replace(/#{1,6}\s/g, '')
        .replace(/\*{1,2}(.*?)\*{1,2}/g, '$1')
        .replace(/\n+/g, '. ')
        .replace(/\s{2,}/g, ' ')
        .trim();

    if (!cleanText || cleanText.length < 3) return;

    const voice = $('tts-voice-select')?.value || 'es-MX-DaliaNeural';

    try {
        state.isSpeaking = true;

        const res = await fetch('/api/tts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: cleanText, voice: voice }),
        });

        if (!res.ok) {
            console.error('TTS error:', await res.text());
            state.isSpeaking = false;
            return;
        }

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);

        const audio = new Audio(url);
        state.currentAudio = audio;

        audio.onended = () => {
            state.isSpeaking = false;
            URL.revokeObjectURL(url);
            state.currentAudio = null;
        };

        audio.onerror = () => {
            state.isSpeaking = false;
            URL.revokeObjectURL(url);
            state.currentAudio = null;
        };

        await audio.play();
    } catch (e) {
        console.error('Error playing TTS:', e);
        state.isSpeaking = false;
    }
}

function stopSpeaking() {
    if (state.currentAudio) {
        state.currentAudio.pause();
        state.currentAudio = null;
    }
    state.isSpeaking = false;
}

function testVoice() {
    speakText('Hola, soy tu asistente de inteligencia artificial. Estoy lista para ayudarte.');
}

// ═══════════════════════════════════════════════════
// Voice Panel
// ═══════════════════════════════════════════════════
function toggleVoicePanel() {
    const panel = $('voice-panel');
    panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
}

// ═══════════════════════════════════════════════════
// Agent Control
// ═══════════════════════════════════════════════════
async function resetAgent() {
    try {
        await fetch('/api/reset', { method: 'POST' });
        // Clear chat
        chatArea.innerHTML = '';
        if (welcome) {
            chatArea.appendChild(welcome);
            welcome.style.display = 'flex';
        }
        state.messageCount = 0;
        $('stat-actions').textContent = '⚡ 0';
        $('stat-success').textContent = '✅ 100%';
    } catch (e) {
        console.error('Reset error:', e);
    }
}

// ═══════════════════════════════════════════════════
// Textarea Auto-resize
// ═══════════════════════════════════════════════════
function initTextareaAutoResize() {
    messageInput.addEventListener('input', () => {
        messageInput.style.height = 'auto';
        messageInput.style.height = Math.min(messageInput.scrollHeight, 150) + 'px';
    });
}
