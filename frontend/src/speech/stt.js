/**
 * Speech-to-Text adapter.
 *
 * Interface (so Bhashini/Whisper can be swapped in later):
 *   const stt = createSTT('hi-IN', { onPartial, onFinal, onError, onEnd });
 *   stt.start(); stt.stop(); stt.destroy();
 *
 * Demo implementation: browser Web Speech API (webkitSpeechRecognition).
 * BhashiniAdapter / WhisperAdapter are DESIGNED, not implemented in this prototype
 * (see backend/app/adapters/speech.py for the server-side contract).
 */

export function isSTTSupported() {
  return typeof window !== 'undefined' &&
    !!(window.SpeechRecognition || window.webkitSpeechRecognition);
}

class BrowserSTT {
  constructor(lang, handlers = {}) {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    this.recognition = new SR();
    this.recognition.lang = lang || 'hi-IN';
    this.recognition.continuous = false;
    this.recognition.interimResults = true;
    this.recognition.maxAlternatives = 1;
    this.handlers = handlers;
    this._bind();
  }

  _bind() {
    this.recognition.onresult = (event) => {
      let interim = '';
      let final = '';
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const chunk = event.results[i][0].transcript;
        if (event.results[i].isFinal) final += chunk;
        else interim += chunk;
      }
      if (interim && this.handlers.onPartial) this.handlers.onPartial(interim.trim());
      if (final && this.handlers.onFinal) this.handlers.onFinal(final.trim());
    };
    this.recognition.onerror = (event) => {
      if (this.handlers.onError) this.handlers.onError(event.error || 'unknown');
    };
    this.recognition.onend = () => {
      if (this.handlers.onEnd) this.handlers.onEnd();
    };
  }

  start() {
    try {
      this.recognition.start();
    } catch (_) {
      // already started — safe to ignore
    }
  }

  stop() {
    try {
      this.recognition.stop();
    } catch (_) {
      /* ignore */
    }
  }

  destroy() {
    this.stop();
  }
}

/** Factory — swap this to plug in Bhashini/Whisper later. */
export function createSTT(lang, handlers) {
  if (!isSTTSupported()) return null;
  return new BrowserSTT(lang, handlers);
}
