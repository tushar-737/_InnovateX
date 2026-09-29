import React, { useEffect, useState } from 'react';
import { api } from '../api/client.js';
import { speak, stopSpeaking, isTTSSupported } from '../speech/index.js';
import NoticeBar from '../components/NoticeBar.jsx';

export default function ConsentPage({ onAccepted, dataNotice }) {
  const [consent, setConsent] = useState(null);
  const [playing, setPlaying] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    api
      .createSession(false, 'hi-IN')
      .then(setConsent)
      .catch(() => setError('सर्वर से जुड़ने में दिक्कत है। कृपया दोबारा कोशिश करें।'));
  }, []);

  const playConsent = async () => {
    if (!consent) return;
    if (playing) {
      stopSpeaking();
      setPlaying(false);
      return;
    }
    setPlaying(true);
    await speak(consent.consent_read_text, 'hi-IN');
    setPlaying(false);
  };

  const accept = async () => {
    stopSpeaking();
    try {
      // Re-create the session with consent recorded (the pre-created one had consent=false).
      const session = await api.createSession(true, 'hi-IN');
      onAccepted(session.session_id, session);
    } catch (e) {
      setError(String(e.message || e));
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center px-4 py-6">
      <div className="w-full max-w-xl flex flex-col gap-5">
        <header className="text-center">
          <div className="text-6xl">🤝</div>
          <h1 className="text-4xl font-extrabold mt-2">कौशल साथी</h1>
          <p className="text-lg text-ink/70">आपका अपना कौशल साथी · Kaushal Saathi</p>
        </header>

        <div className="card">
          <h2 className="text-2xl font-extrabold mb-3">📜 ज़रूरी बात (सहमति)</h2>
          <p className="text-lg leading-relaxed">
            {consent ? consent.consent_text : 'लोड हो रहा है…'}
          </p>
          <p className="text-sm text-ink/60 italic mt-3">
            {consent ? consent.consent_text_en : ''}
          </p>

          <button
            type="button"
            onClick={playConsent}
            disabled={!consent || !isTTSSupported()}
            className="btn-big w-full mt-4 bg-ink text-white disabled:opacity-50"
          >
            <span aria-hidden="true" className="text-3xl">{playing ? '⏹️' : '🔊'}</span>
            {playing ? 'सुनना बंद करें' : 'पढ़कर सुनाएँ / Read aloud'}
          </button>
        </div>

        <NoticeBar text={dataNotice || 'लोड हो रहा है…'} />

        {error && (
          <div className="rounded-2xl bg-red-100 border-2 border-red-400 text-red-900 px-4 py-3">
            {error}
          </div>
        )}

        <button type="button" onClick={accept} className="btn-big w-full bg-leaf text-white">
          <span aria-hidden="true" className="text-3xl">✅</span>
          हाँ, आगे बढ़ें / I agree
        </button>
        <p className="text-center text-sm text-ink/60 pb-4">
          आप कभी भी अपना डेटा मिटा सकते हैं। · You can delete your data any time.
        </p>
      </div>
    </div>
  );
}
