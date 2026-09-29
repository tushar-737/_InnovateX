import React, { useState } from 'react';
import ResultCard, { cardSpeechText } from '../components/ResultCard.jsx';
import SendSummaryModal from '../components/SendSummaryModal.jsx';
import NoticeBar from '../components/NoticeBar.jsx';
import { speak, stopSpeaking } from '../speech/index.js';
import { api } from '../api/client.js';

export default function ResultsPage({ profile, recommendations, districtNote, dataNotice, onRestart }) {
  const [playingId, setPlayingId] = useState(null);
  const [showSend, setShowSend] = useState(false);
  const [deleted, setDeleted] = useState(null);

  const playCard = async (rec) => {
    if (playingId === rec.role_id) {
      stopSpeaking();
      setPlayingId(null);
      return;
    }
    setPlayingId(rec.role_id);
    await speak(cardSpeechText(rec), 'hi-IN');
    setPlayingId(null);
  };

  const deleteData = async () => {
    if (!window.confirm('क्या आप पक्का अपनी सारी जानकारी मिटाना चाहते हैं?')) return;
    try {
      const res = await api.deleteMyData(profile.session_id);
      setDeleted(res.detail);
      stopSpeaking();
    } catch (e) {
      setDeleted('डेटा मिटाने में दिक्कत: ' + String(e.message || e));
    }
  };

  return (
    <div className="min-h-screen max-w-xl mx-auto w-full px-4 py-6">
      <header className="text-center mb-5">
        <div className="text-5xl">🎯</div>
        <h1 className="text-3xl font-extrabold mt-1">आपके लिए 3 रास्ते</h1>
        <p className="text-ink/70">आपकी बातों, ज़िले की माँग और नज़दीकी ट्रेनिंग के आधार पर</p>
        {districtNote && (
          <p className="mt-2 rounded-2xl bg-sky/10 border-2 border-sky/25 px-4 py-2 text-ink/80">
            📍 {districtNote}
          </p>
        )}
      </header>

      <div className="space-y-6">
        {recommendations.map((rec) => (
          <ResultCard
            key={rec.role_id}
            rec={rec}
            onPlay={playCard}
            playing={playingId === rec.role_id}
          />
        ))}
      </div>

      <div className="mt-6 space-y-3">
        <button
          type="button"
          onClick={() => setShowSend(true)}
          className="btn-big w-full bg-saffron text-white"
        >
          <span aria-hidden="true" className="text-3xl">📤</span>
          सारांश भेजें / Send summary
        </button>

        <button type="button" onClick={onRestart} className="btn-big w-full bg-ink text-white">
          <span aria-hidden="true" className="text-3xl">🔄</span>
          नई बातचीत शुरू करें
        </button>

        <button
          type="button"
          onClick={deleteData}
          className="btn-big w-full bg-white text-red-700 border-2 border-red-300"
        >
          <span aria-hidden="true" className="text-3xl">🗑️</span>
          मेरा डेटा मिटाएँ / Delete my data
        </button>

        {deleted && (
          <div className="rounded-2xl bg-leaf/15 border-2 border-leaf px-4 py-3 text-center">
            {deleted}
          </div>
        )}

        <NoticeBar text={dataNotice} />
        <p className="text-xs text-ink/60 leading-relaxed pb-6">
          यह एक प्रोटोटाइप (SIH 2026 डेमो) है। योजनाओं के नाम केवल संकेत हैं — आधिकारिक पोर्टल
          (skillindia.gov.in, ncs.gov.in, MoSJE) पर पुष्टि करें। कोई वेतन/प्लेसमेंट/पात्रता दावा
          नहीं किया जाता।
        </p>
      </div>

      {showSend && (
        <SendSummaryModal
          profile={profile}
          recommendations={recommendations}
          onClose={() => setShowSend(false)}
        />
      )}
    </div>
  );
}
