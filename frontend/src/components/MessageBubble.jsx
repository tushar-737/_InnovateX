import React from 'react';

export default function MessageBubble({ role, text, textEn }) {
  const isUser = role === 'user';
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[85%] rounded-3xl px-5 py-4 text-lg leading-relaxed shadow
          ${isUser ? 'bg-sky text-white rounded-br-md' : 'bg-white text-ink rounded-bl-md border-2 border-ink/10'}`}
      >
        {!isUser && (
          <div className="text-sm font-extrabold text-saffron mb-1">कौशल साथी 🌾</div>
        )}
        <div>{text}</div>
        {textEn && !isUser && (
          <div className="text-sm text-ink/60 mt-2 italic">{textEn}</div>
        )}
      </div>
    </div>
  );
}
