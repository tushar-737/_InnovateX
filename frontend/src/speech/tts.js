/**
 * Text-to-Speech adapter.
 *
 * Interface:
 *   await speak('नमस्ते!', 'hi-IN');
 *   stopSpeaking();
 *
 * Demo implementation: browser SpeechSynthesis (hi-IN voice preferred).
 * Bhashini/Whisper TTS are designed as drop-in adapters later
 * (see backend/app/adapters/speech.py).
 */

let cachedVoice = null;

function pickVoice(lang) {
  if (typeof window === 'undefined' || !window.speechSynthesis) return null;
  const voices = window.speechSynthesis.getVoices();
  if (!voices.length) return null;
  const exact = voices.find((v) => v.lang === lang);
  if (exact) return exact;
  const prefix = lang.split('-')[0];
  return voices.find((v) => v.lang.startsWith(prefix)) || null;
}

export function isTTSSupported() {
  return typeof window !== 'undefined' && 'speechSynthesis' in window;
}

export function primeVoices(lang = 'hi-IN') {
  if (!isTTSSupported()) return;
  cachedVoice = pickVoice(lang);
  window.speechSynthesis.onvoiceschanged = () => {
    cachedVoice = pickVoice(lang);
  };
}

export function speak(text, lang = 'hi-IN') {
  return new Promise((resolve) => {
    if (!isTTSSupported() || !text) {
      resolve(false);
      return;
    }
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = lang;
    utter.rate = 0.92; // slightly slower — clearer for low-literacy listeners
    utter.pitch = 1.0;
    const voice = cachedVoice || pickVoice(lang);
    if (voice) utter.voice = voice;
    utter.onend = () => resolve(true);
    utter.onerror = () => resolve(false);
    window.speechSynthesis.speak(utter);
  });
}

export function stopSpeaking() {
  if (isTTSSupported()) window.speechSynthesis.cancel();
}
