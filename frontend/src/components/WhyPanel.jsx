import React, { useState } from 'react';

const COMPONENTS = [
  { key: 'similarity', weight: 0.3, label: 'आपकी प्रोफ़ाइल से मेल / Profile match (TF-IDF)' },
  { key: 'education', weight: 0.2, label: 'पढ़ाई की शर्त / Education eligibility' },
  { key: 'demand', weight: 0.2, label: 'ज़िले में माँग / Local demand' },
  { key: 'mobility', weight: 0.15, label: 'शारीरिक-यात्रा फ़िट / Mobility & physical fit' },
  { key: 'preference', weight: 0.15, label: 'नौकरी/स्वरोज़गार पसंद / Job preference' },
];

export default function WhyPanel({ breakdown }) {
  const [open, setOpen] = useState(false);
  if (!breakdown) return null;
  return (
    <div className="mt-4">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="w-full min-h-[3.25rem] rounded-2xl bg-ink/5 border-2 border-ink/15
          font-bold text-lg flex items-center justify-between px-4 py-3
          hover:bg-ink/10 focus:outline-none focus:ring-4 focus:ring-sky/30"
        aria-expanded={open}
      >
        <span>🔍 यह क्यों? / Why this?</span>
        <span className="text-2xl">{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <div className="mt-3 space-y-3 rounded-2xl bg-white/80 border-2 border-ink/10 p-4">
          <p className="text-sm text-ink/70">
            स्कोर = नीचे दिए 5 हिस्सों का तौला हुआ योग (कुल 100 में से)। कोई छिपा हुआ गणित नहीं।
          </p>
          {COMPONENTS.map((c) => {
            const value = Number(breakdown[c.key] ?? 0);
            const percent = Math.max(0, Math.min(100, Math.round(value * 100)));
            return (
              <div key={c.key}>
                <div className="flex justify-between text-sm font-bold">
                  <span>{c.label} <span className="text-ink/50 font-normal">(भार {Math.round(c.weight * 100)}%)</span></span>
                  <span>{percent}%</span>
                </div>
                <div className="h-3 rounded-full bg-ink/10 overflow-hidden my-1">
                  <div className="h-full rounded-full bg-sky" style={{ width: `${percent}%` }} />
                </div>
                {breakdown.notes && breakdown.notes[c.key] && (
                  <div className="text-xs text-ink/60">{breakdown.notes[c.key]}</div>
                )}
              </div>
            );
          })}
          <div className="text-sm font-bold border-t-2 border-ink/10 pt-2">
            कुल स्कोर / Total: {Math.max(0, Math.min(100, Math.round((breakdown.total ?? 0) * 100)))} / 100
          </div>
        </div>
      )}
    </div>
  );
}
