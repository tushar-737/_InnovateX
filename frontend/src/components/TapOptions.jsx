import React from 'react';

export default function TapOptions({ options, onPick, expanded }) {
  if (!options || options.length === 0) return null;
  const shown = expanded ? options : options.slice(0, 4);
  return (
    <div className="flex flex-wrap gap-3 justify-center">
      {shown.map((opt) => (
        <button
          key={opt}
          type="button"
          onClick={() => onPick(opt)}
          className="min-h-[3.25rem] px-5 py-3 rounded-2xl text-lg font-bold
            bg-white text-ink border-2 border-ink/20 shadow active:scale-95
            hover:border-sky hover:bg-sky/10 focus:outline-none focus:ring-4 focus:ring-sky/40"
        >
          {opt}
        </button>
      ))}
    </div>
  );
}
