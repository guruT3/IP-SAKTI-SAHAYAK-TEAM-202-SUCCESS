/**
 * IP-SAKTI SAHAYAK — AI Website Copilot Client
 * =============================================
 * Handles floating panel interactions, dynamic website context collection,
 * multi-intent routing, General AI conversation, Web Speech API Voice Input
 * & Output state machine, and real-time Voice Assistant modal.
 */

(function () {
  'use strict';

  // Voice State Machine Enum
  const VoiceState = {
    IDLE: 'IDLE',
    LISTENING: 'LISTENING',
    PROCESSING: 'PROCESSING',
    THINKING: 'THINKING',
    SPEAKING: 'SPEAKING',
    ERROR: 'ERROR',
  };

  // State Management
  const state = {
    isOpen: false,
    history: [],
    currentLang: 'en',
    speechRecognition: null,
    isListening: false,
    isProcessingQuery: false,
    voiceState: VoiceState.IDLE,
    synth: window.speechSynthesis,
    activeUtterance: null,
    isVoiceModalOpen: false,
  };

  // DOM Elements Injection
  function injectCopilotDOM() {
    if (document.getElementById('copilot-launcher')) return;

    const launcherHTML = `
      <div id="copilot-launcher" class="copilot-launcher" title="Open AI Copilot (Alt+C)" role="button" tabindex="0">
        <span class="sparkle-icon">✨</span>
        <span>IP-SAKTI Copilot</span>
      </div>

      <div id="copilot-panel" class="copilot-panel" aria-label="IP-SAKTI Copilot Assistant">
        <div class="copilot-header">
          <div class="copilot-header-info">
            <div class="copilot-avatar">✨</div>
            <div>
              <div class="copilot-header-title">IP-SAKTI Copilot</div>
              <div class="copilot-header-subtitle">Your AI Guide for General & IP Workflows</div>
            </div>
          </div>
          <div class="copilot-controls">
            <select id="copilot-lang-select" class="copilot-lang-select" title="Change Language">
              <option value="en">English</option>
              <option value="hi">हिंदी (Hindi)</option>
              <option value="or">ଓଡ଼ିଆ (Odia)</option>
            </select>
            <button id="copilot-voice-modal-btn" class="copilot-btn-icon" title="Voice Assistant Mode">🎙</button>
            <button id="copilot-new-chat-btn" class="copilot-btn-icon" title="New Conversation">🔄</button>
            <button id="copilot-close-btn" class="copilot-btn-icon" title="Close Panel">✕</button>
          </div>
        </div>

        <div id="copilot-body" class="copilot-body">
          <div class="copilot-welcome-card">
            <div class="copilot-welcome-title">👋 Hello! I'm your IP-SAKTI Copilot</div>
            <div class="copilot-welcome-desc">
              I can chat with you normally like ChatGPT, explain website features, navigate the platform, or answer legal, patent, and regulatory questions.
            </div>
            <div id="copilot-suggestions" class="copilot-suggestions">
              <!-- Dynamically populated based on page context -->
            </div>
          </div>
        </div>

        <div class="copilot-footer">
          <div class="copilot-input-row">
            <input type="text" id="copilot-input" class="copilot-input" placeholder="Ask general questions, website help, or IP laws..." autocomplete="off" />
            <button id="copilot-mic-btn" class="copilot-mic-btn" title="Voice Input">🎙</button>
            <button id="copilot-send-btn" class="copilot-send-btn" title="Send Query">➤</button>
          </div>
        </div>
      </div>

      <!-- Real-time Voice Assistant Modal -->
      <div id="voice-modal-overlay" class="voice-modal-overlay">
        <div class="voice-modal-card">
          <div id="voice-status-badge" class="voice-status-badge">LISTENING...</div>
          <div class="voice-waveform">
            <div class="voice-waveform-bar"></div>
            <div class="voice-waveform-bar"></div>
            <div class="voice-waveform-bar"></div>
            <div class="voice-waveform-bar"></div>
            <div class="voice-waveform-bar"></div>
          </div>
          <div id="voice-transcript-text" class="voice-transcript-text">Speak now... I am listening to your query.</div>
          <div class="voice-modal-controls">
            <button id="voice-btn-close" class="voice-btn-close">Close Voice Mode</button>
          </div>
        </div>
      </div>
    `;

    const container = document.createElement('div');
    container.innerHTML = launcherHTML;
    document.body.appendChild(container);
  }

  // Page Context Extractor
  function getPageContext() {
    return {
      current_route: window.location.pathname,
      current_title: document.title,
      search_query: (document.getElementById('query') || {}).value || null,
      jurisdiction: (document.getElementById('jurisdiction') || {}).value || null,
      country: (document.getElementById('country') || {}).value || null,
    };
  }

  // Load Context-Aware Prompt Suggestions
  async function loadPageSuggestions() {
    const suggestionsContainer = document.getElementById('copilot-suggestions');
    if (!suggestionsContainer) return;

    try {
      const route = window.location.pathname;
      const res = await fetch(`/api/copilot/context?route=${encodeURIComponent(route)}`);
      const data = await res.json();
      if (data.success && data.page_info && data.page_info.suggested_prompts) {
        suggestionsContainer.innerHTML = '';
        data.page_info.suggested_prompts.forEach((promptText) => {
          const chip = document.createElement('div');
          chip.className = 'copilot-chip';
          chip.textContent = promptText;
          chip.onclick = () => {
            document.getElementById('copilot-input').value = promptText;
            sendCopilotQuery();
          };
          suggestionsContainer.appendChild(chip);
        });
      }
    } catch (e) {
      console.warn('Failed to load page suggestions:', e);
    }
  }

  // Formatting Helper: Simple Markdown to HTML
  function formatMarkdown(text) {
    if (!text) return '';
    let html = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // Headings
    html = html.replace(/^### (.*$)/gim, '<strong style="font-size:13px; color:#0f4c81; display:block; margin:6px 0 2px 0;">$1</strong>');
    html = html.replace(/^## (.*$)/gim, '<strong style="font-size:14px; color:#0f4c81; display:block; margin:8px 0 4px 0;">$1</strong>');

    // Bold & Code
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/`(.*?)`/g, '<code style="background:#f1f5f9; padding:2px 4px; border-radius:4px; font-family:monospace; font-size:11px;">$1</code>');

    // Bullet Points
    html = html.replace(/^\- (.*$)/gim, '<li style="margin-left:14px; margin-bottom:2px;">$1</li>');
    html = html.replace(/(<li.*?>.*?<\/li>)/gs, '<ul style="margin:4px 0; padding:0;">$1</ul>');

    // Linebreaks
    html = html.replace(/\n\n/g, '<br/><br/>').replace(/\n/g, '<br/>');
    return html;
  }

  // Text-to-Speech Player
  function speakText(text, lang) {
    if (!state.synth) return;
    try {
      state.synth.cancel(); // Stop any active speech

      const cleanText = text.replace(/<[^>]*>?/gm, '').replace(/\*/g, '').replace(/`/g, '');
      const utterance = new SpeechSynthesisUtterance(cleanText);

      if (lang === 'hi') utterance.lang = 'hi-IN';
      else if (lang === 'or') utterance.lang = 'or-IN';
      else utterance.lang = 'en-US';

      utterance.onend = () => {
        setVoiceState(VoiceState.IDLE);
      };

      utterance.onerror = () => {
        setVoiceState(VoiceState.IDLE);
      };

      state.activeUtterance = utterance;
      setVoiceState(VoiceState.SPEAKING);
      state.synth.speak(utterance);
    } catch (e) {
      console.warn('Speech synthesis error:', e);
      setVoiceState(VoiceState.IDLE);
    }
  }

  // Update Voice State Machine Visualizer
  function setVoiceState(newState, detailText = null) {
    state.voiceState = newState;
    const badge = document.getElementById('voice-status-badge');
    const statusDiv = document.getElementById('voice-transcript-text');

    if (badge) badge.textContent = newState;

    if (newState === VoiceState.LISTENING) {
      if (statusDiv && detailText) statusDiv.textContent = detailText;
    } else if (newState === VoiceState.PROCESSING) {
      if (statusDiv) statusDiv.textContent = 'Transcribing voice input...';
    } else if (newState === VoiceState.THINKING) {
      if (statusDiv) statusDiv.textContent = 'Copilot is processing answer...';
    } else if (newState === VoiceState.ERROR) {
      if (statusDiv && detailText) statusDiv.textContent = detailText;
    }
  }

  // Render Assistant Message Bubble
  function appendAssistantMessage(data) {
    const body = document.getElementById('copilot-body');
    const msgDiv = document.createElement('div');
    msgDiv.className = 'copilot-msg assistant';

    let contentHTML = `<div class="copilot-msg-bubble">${formatMarkdown(data.message)}`;

    // Render Actions / Deep Links
    if (data.actions && data.actions.length > 0) {
      contentHTML += `<div class="copilot-actions-group">`;
      data.actions.forEach((act) => {
        contentHTML += `<button class="copilot-action-btn" onclick="window.location.href='${act.route}'">🚀 ${act.label}</button>`;
      });
      contentHTML += `</div>`;
    }

    // Render Citations
    if (data.citations && data.citations.length > 0) {
      contentHTML += `<div class="copilot-citations"><strong>Sources & Citations:</strong><br/>`;
      data.citations.forEach((c) => {
        contentHTML += `<span class="copilot-citation-item" onclick="alert('${c.source_name || 'Source'} Section ${c.section || ''}')">📜 ${c.source_name || 'Source'} (${c.section || 'General'})</span> `;
      });
      contentHTML += `</div>`;
    }

    contentHTML += `</div>`;

    // Render Meta Bar & TTS Audio Control
    contentHTML += `
      <div class="copilot-msg-meta">
        <span class="copilot-confidence-tag copilot-confidence-${data.confidence_level || 'HIGH'}">${data.confidence_level || 'HIGH'} CONFIDENCE</span>
        <div class="copilot-audio-ctrl">
          <button class="copilot-audio-btn play-audio-btn" title="Read Aloud">🔊 Play</button>
          <button class="copilot-audio-btn stop-audio-btn" title="Stop">⏹ Stop</button>
        </div>
      </div>
    `;

    msgDiv.innerHTML = contentHTML;

    // Attach Audio Listeners
    const playBtn = msgDiv.querySelector('.play-audio-btn');
    const stopBtn = msgDiv.querySelector('.stop-audio-btn');
    if (playBtn) playBtn.onclick = () => speakText(data.message, data.language || state.currentLang);
    if (stopBtn) stopBtn.onclick = () => state.synth && state.synth.cancel();

    body.appendChild(msgDiv);
    body.scrollTop = body.scrollHeight;
  }

  // Render User Message Bubble
  function appendUserMessage(text) {
    const body = document.getElementById('copilot-body');
    const msgDiv = document.createElement('div');
    msgDiv.className = 'copilot-msg user';
    msgDiv.innerHTML = `<div class="copilot-msg-bubble">${formatMarkdown(text)}</div>`;
    body.appendChild(msgDiv);
    body.scrollTop = body.scrollHeight;
  }

  // Render Typing Indicator
  function showTypingIndicator() {
    const body = document.getElementById('copilot-body');
    const typingDiv = document.createElement('div');
    typingDiv.id = 'copilot-typing-indicator';
    typingDiv.className = 'copilot-msg assistant';
    typingDiv.innerHTML = `
      <div class="copilot-typing">
        <span></span><span></span><span></span>
      </div>
    `;
    body.appendChild(typingDiv);
    body.scrollTop = body.scrollHeight;
  }

  function hideTypingIndicator() {
    const indicator = document.getElementById('copilot-typing-indicator');
    if (indicator) indicator.remove();
  }

  // Send Query to Copilot Backend
  async function sendCopilotQuery(overrideQuery = null) {
    if (state.isProcessingQuery) return;

    const input = document.getElementById('copilot-input');
    const query = (overrideQuery || input.value || '').trim();
    if (!query) return;

    if (!overrideQuery) input.value = '';

    state.isProcessingQuery = true;
    appendUserMessage(query);
    showTypingIndicator();
    setVoiceState(VoiceState.THINKING);

    try {
      const res = await fetch('/api/copilot/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query,
          page_context: getPageContext(),
          history: state.history,
          language: state.currentLang,
        }),
      });

      const data = await res.json();
      hideTypingIndicator();
      state.isProcessingQuery = false;

      if (data.success) {
        appendAssistantMessage(data);
        state.history.push({ role: 'user', content: query });
        state.history.push({ role: 'assistant', content: data.message });

        if (state.isVoiceModalOpen) {
          document.getElementById('voice-transcript-text').textContent = data.message;
          speakText(data.message, data.language || state.currentLang);
        } else {
          setVoiceState(VoiceState.IDLE);
        }
      } else {
        appendAssistantMessage({
          message: data.error || 'Something went wrong.',
          confidence_level: 'LOW',
        });
        setVoiceState(VoiceState.IDLE);
      }
    } catch (e) {
      state.isProcessingQuery = false;
      hideTypingIndicator();
      appendAssistantMessage({
        message: 'Network error communicating with AI Copilot.',
        confidence_level: 'LOW',
      });
      setVoiceState(VoiceState.IDLE);
    }
  }

  // Speech Recognition (Web Speech API)
  function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn('Web Speech API is not supported in this browser environment.');
      return;
    }

    const rec = new SpeechRecognition();
    rec.continuous = false;
    rec.interimResults = true;

    rec.onstart = () => {
      state.isListening = true;
      setVoiceState(VoiceState.LISTENING, 'Listening to your speech...');
      const micBtn = document.getElementById('copilot-mic-btn');
      if (micBtn) micBtn.classList.add('listening');
    };

    rec.onresult = (event) => {
      let transcript = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }
      document.getElementById('copilot-input').value = transcript;
      if (state.isVoiceModalOpen) {
        document.getElementById('voice-transcript-text').textContent = transcript;
      }
      setVoiceState(VoiceState.PROCESSING);
    };

    rec.onerror = (event) => {
      console.warn('Speech recognition error:', event.error);
      stopSpeechRecognition();
      if (event.error === 'not-allowed' || event.error === 'permission-denied') {
        setVoiceState(VoiceState.ERROR, 'Microphone permission denied. Allow mic access in browser settings.');
      } else if (event.error === 'no-speech') {
        setVoiceState(VoiceState.ERROR, 'I couldn\'t hear anything. Please try speaking again.');
      } else {
        setVoiceState(VoiceState.ERROR, 'Could not capture speech. Please try again.');
      }
    };

    rec.onend = () => {
      stopSpeechRecognition();
      const val = document.getElementById('copilot-input').value.trim();
      if (val && !state.isProcessingQuery) {
        sendCopilotQuery();
      } else if (!state.isProcessingQuery) {
        setVoiceState(VoiceState.IDLE);
      }
    };

    state.speechRecognition = rec;
  }

  function startSpeechRecognition() {
    if (!state.speechRecognition) initSpeechRecognition();
    if (!state.speechRecognition) {
      alert('Voice speech input (Web Speech API) is not available in this browser. You can type your question in the input box.');
      setVoiceState(VoiceState.ERROR, 'Voice recognition not supported in browser.');
      return;
    }

    if (state.isListening) {
      stopSpeechRecognition();
      return;
    }

    if (state.currentLang === 'hi') state.speechRecognition.lang = 'hi-IN';
    else if (state.currentLang === 'or') state.speechRecognition.lang = 'or-IN';
    else state.speechRecognition.lang = 'en-US';

    try {
      state.speechRecognition.start();
    } catch (e) {
      console.warn('Speech recognition start failed:', e);
      state.isListening = false;
    }
  }

  function stopSpeechRecognition() {
    state.isListening = false;
    const micBtn = document.getElementById('copilot-mic-btn');
    if (micBtn) micBtn.classList.remove('listening');
    if (state.speechRecognition) {
      try {
        state.speechRecognition.stop();
      } catch (e) {}
    }
  }

  // Voice Assistant Modal Controls
  function openVoiceModal() {
    state.isVoiceModalOpen = true;
    document.getElementById('voice-modal-overlay').classList.add('open');
    startSpeechRecognition();
  }

  function closeVoiceModal() {
    state.isVoiceModalOpen = false;
    document.getElementById('voice-modal-overlay').classList.remove('open');
    stopSpeechRecognition();
    if (state.synth) state.synth.cancel();
    setVoiceState(VoiceState.IDLE);
  }

  // Initialize Event Listeners
  function initEvents() {
    const launcher = document.getElementById('copilot-launcher');
    const panel = document.getElementById('copilot-panel');
    const closeBtn = document.getElementById('copilot-close-btn');
    const sendBtn = document.getElementById('copilot-send-btn');
    const input = document.getElementById('copilot-input');
    const micBtn = document.getElementById('copilot-mic-btn');
    const newChatBtn = document.getElementById('copilot-new-chat-btn');
    const langSelect = document.getElementById('copilot-lang-select');
    const voiceModalBtn = document.getElementById('copilot-voice-modal-btn');
    const voiceCloseBtn = document.getElementById('voice-btn-close');

    launcher.onclick = () => {
      state.isOpen = !state.isOpen;
      if (state.isOpen) {
        panel.classList.add('open');
        loadPageSuggestions();
      } else {
        panel.classList.remove('open');
      }
    };

    closeBtn.onclick = () => {
      state.isOpen = false;
      panel.classList.remove('open');
    };

    sendBtn.onclick = () => sendCopilotQuery();

    input.onkeydown = (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendCopilotQuery();
      }
    };

    micBtn.onclick = () => {
      if (state.voiceState === VoiceState.LISTENING) stopSpeechRecognition();
      else startSpeechRecognition();
    };

    newChatBtn.onclick = () => {
      state.history = [];
      const body = document.getElementById('copilot-body');
      body.innerHTML = '';
      loadPageSuggestions();
    };

    langSelect.onchange = (e) => {
      state.currentLang = e.target.value;
    };

    if (voiceModalBtn) voiceModalBtn.onclick = () => openVoiceModal();
    if (voiceCloseBtn) voiceCloseBtn.onclick = () => closeVoiceModal();

    // Keyboard shortcut (Alt+C) to toggle copilot
    document.addEventListener('keydown', (e) => {
      if (e.altKey && (e.key === 'c' || e.key === 'C')) {
        e.preventDefault();
        launcher.click();
      }
    });
  }

  // Auto-init on page load
  document.addEventListener('DOMContentLoaded', () => {
    injectCopilotDOM();
    initEvents();
    initSpeechRecognition();
  });
})();
