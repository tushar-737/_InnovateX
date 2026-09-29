import React, { useEffect, useState } from 'react';
import { api } from '../api/client.js';
import { speak, stopSpeaking } from '../speech/index.js';

const FIELD_LABELS = {
  name: '👤 नाम',
  age: '🎂 उम्र',
  district: '📍 ज़िला',
  education: '📚 पढ़ाई',
  family_occupation: '🏠 घर का काम',
  current_livelihood: '🧰 अभी का काम',
  skills: '🛠️ आने वाले काम',
  interests: '❤️ रुचि',
  constraints: '⚠️ दिक्कत',
  preference: '🎯 पसंद',
  mobility: '🚌 यात्रा',
};

const EDITABLE_FIELDS = [
  'name', 'age', 'district', 'education', 'family_occupation',
  'current_livelihood', 'skills', 'interests', 'constraints', 'preference', 'mobility',
];

export default function ConfirmPage({ sessionId, onConfirmed }) {
  const [readback, setReadback] = useState(null);
  const [profile, setProfile] = useState(null);
  const [reply, setReply] = useState('');
  const [playing, setPlaying] = useState(false);
  const [editField, setEditField] = useState(null);
  const [editValue, setEditValue] = useState('');
  const [busy, setBusy] = useState(false);

  const load = async () => {
    const body = await api.confirm(sessionId, null);
    setReadback(body.readback_text);
    setProfile(body.profile);
    setReply(body.reply_text);
    return body;
  };

  useEffect(() => {
    load().catch(() => setReply('सर्वर से जुड़ने में दिक्कत है।'));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const playReadback = async () => {
    if (!readback) return;
    if (playing) {
      stopSpeaking();
      setPlaying(false);
      return;
    }
    setPlaying(true);
    await speak(readback, 'hi-IN');
    setPlaying(false);
  };

  const sayCorrection = async (text) => {
    setBusy(true);
    try {
      const body = await api.confirm(sessionId, text);
      setReadback(body.readback_text);
      setProfile(body.profile);
      setReply(body.reply_text);
      speak(body.reply_text, 'hi-IN');
      if (body.is_confirmed) onConfirmed(body.profile);
    } finally {
      setBusy(false);
    }
  };

  const confirmYes = async () => {
    setBusy(true);
    stopSpeaking();
    try {
      const body = await api.confirm(sessionId, 'हाँ, सही है');
      speak(body.reply_text, 'hi-IN');
      onConfirmed(body.profile);
    } finally {
      setBusy(false);
    }
  };

  const saveEdit = () => {
    if (!editField) return;
    const text = `${editField === 'age' ? 'umar' : editField} ${editValue}`;
    setEditField(null);
    setEditValue('');
    sayCorrection(text);
  };

  return (
    <div className="min-h-screen flex flex-col items-center px-4 py-6">
      <div className="w-full max-w-xl flex flex-col gap-5">
        <header className="text-center">
          <div className="text-5xl">🧾</div>
          <h1 className="text-3xl font-extrabold mt-1">आपने जो बताया</h1>
          <p className="text-ink/70">सुनिए और जाँच लें — कुछ भी बदल सकते हैं</p>
        </header>

        <button
          type="button"
          onClick={playReadback}
          className={`btn-big w-full ${playing ? 'bg-red-600 text-white' : 'bg-ink text-white'}`}
        >
          <span aria-hidden="true" className="text-3xl">{playing ? '⏹️' : '🔊'}</span>
          {playing ? 'सुनना बंद करें' : 'पढ़कर सुनाएँ / Read aloud'}
        </button>

        {reply && (
          <div className="rounded-2xl bg-sky/10 border-2 border-sky/30 px-4 py-3 text-lg">
            🌾 {reply}
          </div>
        )}

        <div className="card">
          <h2 className="text-xl font-extrabold mb-3">प्रोफ़ाइल (टैप करके बदलें)</h2>
          <div className="space-y-2">
            {EDITABLE_FIELDS.map((field) => {
              const value = Array.isArray(profile?.[field])
                ? profile[field].join(', ')
                : profile?.[field];
              return (
                <button
                  key={field}
                  type="button"
                  onClick={() => {
                    setEditField(field);
                    setEditValue(String(value ?? ''));
                  }}
                  className="w-full flex items-center justify-between gap-3 min-h-[3.5rem]
                    rounded-2xl border-2 border-ink/15 px-4 py-3 text-left hover:border-sky
                    focus:outline-none focus:ring-4 focus:ring-sky/30"
                >
                  <span className="font-bold">{FIELD_LABELS[field]}</span>
                  <span className={`text-right ${value ? 'text-ink' : 'text-ink/40 italic'}`}>
                    {value || '— नहीं बताया —'}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {editField && (
          <div className="card">
            <h3 className="font-extrabold text-lg mb-2">{FIELD_LABELS[editField]} बदलें</h3>
            <input
              type="text"
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && saveEdit()}
              className="w-full min-h-touch px-4 rounded-2xl border-2 border-ink/20 text-lg focus:border-sky focus:outline-none"
              autoFocus
            />
            <div className="flex gap-3 mt-3">
              <button type="button" onClick={saveEdit} className="btn-big flex-1 bg-leaf text-white">
                सहेजें
              </button>
              <button type="button" onClick={() => setEditField(null)} className="btn-big flex-1 bg-ink/10">
                रद्द करें
              </button>
            </div>
          </div>
        )}

        <button
          type="button"
          onClick={confirmYes}
          disabled={busy}
          className="btn-big w-full bg-leaf text-white disabled:opacity-60"
        >
          <span aria-hidden="true" className="text-3xl">✅</span>
          हाँ, यह सही है / Correct
        </button>

        <div className="rounded-2xl border-2 border-ink/15 p-4">
          <div className="font-bold mb-2">कुछ बदलना है? बोलकर या लिखकर बताएं:</div>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="जैसे: umar 26 hai"
              className="flex-1 min-h-touch px-4 rounded-2xl border-2 border-ink/20 focus:border-sky focus:outline-none"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && e.currentTarget.value.trim()) {
                  sayCorrection(e.currentTarget.value.trim());
                  e.currentTarget.value = '';
                }
              }}
              disabled={busy}
            />
          </div>
          <p className="text-xs text-ink/60 mt-2">
            उदाहरण: "umar 26 hai", "silai bhi aati hai", "district barmer"
          </p>
        </div>
        <div className="h-2" />
      </div>
    </div>
  );
}
