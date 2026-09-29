import React, { useEffect, useState } from 'react';
import { api } from './api/client.js';
import { primeVoices, stopSpeaking } from './speech/index.js';
import ConsentPage from './pages/ConsentPage.jsx';
import ChatPage from './pages/ChatPage.jsx';
import ConfirmPage from './pages/ConfirmPage.jsx';
import ResultsPage from './pages/ResultsPage.jsx';

const STEPS = ['consent', 'chat', 'confirm', 'results'];

export default function App() {
  const [step, setStep] = useState('consent');
  const [sessionId, setSessionId] = useState(null);
  const [profile, setProfile] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [districtNote, setDistrictNote] = useState('');
  const [meta, setMeta] = useState(null);
  const [loadingResults, setLoadingResults] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    primeVoices('hi-IN');
    api.meta().then(setMeta).catch(() => {});
  }, []);

  const handleConfirmed = async (confirmedProfile) => {
    setLoadingResults(true);
    setError(null);
    try {
      const resp = await api.recommend(confirmedProfile);
      setProfile({ ...confirmedProfile, session_id: sessionId });
      setRecommendations(resp.recommendations);
      setDistrictNote(resp.district_note);
      setMeta((m) => ({ ...(m || {}), data_notice: resp.data_notice }));
      setStep('results');
    } catch (e) {
      setError('सुझाव बनाने में दिक्कत हुई: ' + String(e.message || e));
    } finally {
      setLoadingResults(false);
    }
  };

  const restart = () => {
    stopSpeaking();
    setSessionId(null);
    setProfile(null);
    setRecommendations([]);
    setStep('consent');
    setError(null);
    window.location.reload();
  };

  return (
    <div className="min-h-screen">
      {/* Step progress dots */}
      <div className="sticky top-0 z-40 bg-cream/95 backdrop-blur border-b-2 border-ink/10">
        <div className="max-w-xl mx-auto flex items-center justify-center gap-2 py-2 px-4">
          {STEPS.map((s, i) => (
            <div
              key={s}
              className={`h-2.5 rounded-full transition-all ${
                i <= STEPS.indexOf(step) ? 'bg-leaf w-10' : 'bg-ink/15 w-6'
              }`}
              aria-hidden="true"
            />
          ))}
          <span className="sr-only">चरण {STEPS.indexOf(step) + 1} / {STEPS.length}</span>
        </div>
      </div>

      {error && (
        <div className="max-w-xl mx-auto px-4 pt-3">
          <div className="rounded-2xl bg-red-100 border-2 border-red-400 text-red-900 px-4 py-3">
            {error}
          </div>
        </div>
      )}

      {step === 'consent' && (
        <ConsentPage
          dataNotice={meta?.data_notice}
          onAccepted={(sid) => {
            setSessionId(sid);
            setStep('chat');
          }}
        />
      )}

      {step === 'chat' && sessionId && (
        <ChatPage
          sessionId={sessionId}
          onComplete={() => setStep('confirm')}
        />
      )}

      {step === 'confirm' && sessionId && (
        <ConfirmPage sessionId={sessionId} onConfirmed={handleConfirmed} />
      )}

      {step === 'results' && profile && (
        <ResultsPage
          profile={profile}
          recommendations={recommendations}
          districtNote={districtNote}
          dataNotice={meta?.data_notice}
          onRestart={restart}
        />
      )}

      {loadingResults && (
        <div className="fixed inset-0 z-50 bg-ink/60 flex flex-col items-center justify-center gap-4">
          <div className="text-6xl animate-bounce">🔎</div>
          <div className="text-white text-2xl font-bold">आपके लिए रास्ते ढूँढ रहा हूँ…</div>
        </div>
      )}
    </div>
  );
}
