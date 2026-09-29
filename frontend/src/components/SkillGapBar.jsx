import React from 'react';

/**
 * Skill-gap bar — value is a REAL ratio (covered core skills / total core skills),
 * clamped 0–100 by the backend. Never an unbounded number.
 */
export default function SkillGapBar({ label, percent }) {
  const value = Math.max(0, Math.min(100, Number(percent) || 0));
  return (
    <div>
      <div className="flex justify-between text-sm font-bold mb-1">
        <span>{label}</span>
        <span>{value}%</span>
      </div>
      <div className="h-5 rounded-full bg-ink/10 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${value >= 66 ? 'bg-leaf' : value >= 33 ? 'bg-amber-500' : 'bg-saffron'}`}
          style={{ width: `${value}%` }}
          role="progressbar"
          aria-valuenow={value}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={label}
        />
      </div>
    </div>
  );
}
