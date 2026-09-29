import React, { useState } from 'react';

/**
 * SIMULATED send-summary preview (SMS + WhatsApp).
 * Clearly labelled as a mock-up — nothing is actually sent anywhere.
 */
export default function SendSummaryModal({ profile, recommendations, onClose }) {
  const [channel, setChannel] = useState('sms');
  const [sent, setSent] = useState(false);

  const name = profile?.name ? `${profile.name} जी` : 'आप';
  const topLine = recommendations
    .map((r) => `${r.rank}. ${r.job_role} (NSQF ${r.nsqf_level})`)
    .join('\n');
  const smsText =
    `कौशल साथी सारांश (डेमो): ${name}, आपके लिए सुझाव —\n${topLine}\n` +
    `नज़दीकी केंद्र व योजना की जानकारी आधिकारिक पोर्टल पर जाँचें। यह कोई नौकरी/पात्रता गारंटी नहीं है।`;

  return (
    <div className="fixed inset-0 z-50 bg-ink/70 flex items-end sm:items-center justify-center p-3">
      <div className="bg-white rounded-3xl w-full max-w-lg p-5 max-h-[92vh] overflow-y-auto">
        <div className="flex items-center justify-between">
          <h3 className="text-2xl font-extrabold">📤 सारांश भेजें (सिमुलेशन)</h3>
          <button
            type="button"
            onClick={onClose}
            className="text-3xl leading-none px-3 min-h-[3rem]"
            aria-label="बंद करें"
          >
            ✕
          </button>
        </div>
        <p className="text-sm text-ink/70 mt-2">
          ⚠️ यह एक <b>नकली (simulated) पूर्वावलोकन</b> है। कोई असली SMS/WhatsApp संदेश नहीं भेजा जाएगा।
        </p>

        <div className="flex gap-3 mt-4">
          <button
            type="button"
            onClick={() => setChannel('sms')}
            className={`btn-big flex-1 text-lg ${channel === 'sms' ? 'bg-sky text-white' : 'bg-ink/10'}`}
          >
            💬 SMS
          </button>
          <button
            type="button"
            onClick={() => setChannel('whatsapp')}
            className={`btn-big flex-1 text-lg ${channel === 'whatsapp' ? 'bg-leaf text-white' : 'bg-ink/10'}`}
          >
            🟢 WhatsApp
          </button>
        </div>

        <div className={`mt-4 rounded-3xl p-4 ${channel === 'sms' ? 'bg-sky/10' : 'bg-leaf/10'}`}>
          <div className="text-xs font-bold text-ink/60 mb-2">
            {channel === 'sms' ? 'SMS पूर्वावलोकन (Hindi)' : 'WhatsApp वॉइस-नोट + संदेश पूर्वावलोकन (Hindi)'}
          </div>
          <div className="bg-white rounded-2xl p-4 text-lg leading-relaxed whitespace-pre-line shadow-inner">
            {smsText}
          </div>
          {channel === 'whatsapp' && (
            <div className="bg-white rounded-2xl p-4 mt-3 flex items-center gap-3 shadow-inner">
              <div className="text-4xl">🎙️</div>
              <div>
                <div className="font-bold">वॉइस नोट (सिमुलेशन) — 0:28</div>
                <div className="text-sm text-ink/60">
                  वही सारांश बोलकर भेजा जाएगा जो ऊपर लिखा है।
                </div>
              </div>
            </div>
          )}
        </div>

        {sent ? (
          <div className="mt-4 rounded-2xl bg-leaf/20 border-2 border-leaf p-4 text-center">
            <div className="text-4xl">✅</div>
            <div className="font-extrabold text-lg mt-1">सिमुलेशन सफल!</div>
            <div className="text-ink/70 text-sm">असली भेजना अगले चरण में जोड़ा जाएगा (SMS DLT / WhatsApp Business API)।</div>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => setSent(true)}
            className="btn-big w-full mt-4 bg-saffron text-white"
          >
            <span aria-hidden="true" className="text-3xl">📨</span>
            भेजें (सिमुलेशन)
          </button>
        )}
      </div>
    </div>
  );
}
