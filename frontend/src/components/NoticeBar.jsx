import React from 'react';

export default function NoticeBar({ text }) {
  return (
    <div className="rounded-2xl bg-amber-100 border-2 border-amber-400 text-amber-950 px-4 py-3 text-sm leading-relaxed">
      <span className="font-extrabold">⚠️ डेटा सूचना / Data notice:</span> {text}
    </div>
  );
}
