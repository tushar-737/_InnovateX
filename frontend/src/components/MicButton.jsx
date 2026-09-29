import React from 'react';

export default function MicButton({ listening, onStart, onStop, disabled }) {
  return (
    <button
      type="button"
      onClick={listening ? onStop : onStart}
      disabled={disabled}
      aria-label={listening ? 'सुनना बंद करें' : 'बोलने के लिए दबाएँ'}
      className={`relative rounded-full shadow-xl border-4 border-white
        flex items-center justify-center transition-all active:scale-95
        w-40 h-40 text-7xl focus:outline-none focus:ring-8 focus:ring-sky/40
        ${listening ? 'bg-red-600 animate-pulse' : 'bg-sky hover:bg-blue-700'}
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
    >
      <span aria-hidden="true">{listening ? '🔴' : '🎤'}</span>
      {listening && (
        <>
          <span className="absolute inset-0 rounded-full border-8 border-red-400 animate-ping opacity-60" />
          <span className="absolute -bottom-9 whitespace-nowrap text-base font-bold text-red-700 bg-white px-3 py-1 rounded-full shadow">
            सुन रहा हूँ…
          </span>
        </>
      )}
    </button>
  );
}
