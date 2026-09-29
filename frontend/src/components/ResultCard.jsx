import React from 'react';
import SkillGapBar from './SkillGapBar.jsx';
import WhyPanel from './WhyPanel.jsx';

const SECTOR_ICONS = {
  agriculture: '🌾', food_processing: '🍲', construction: '🧱', plumbing: '🔧',
  electrical: '⚡', apparel: '🧵', healthcare: '🏥', retail: '🛒', it_ites: '💻',
  automotive: '🏍️', beauty_wellness: '💇', hospitality: '🍽️', electronics: '📱',
  green_jobs: '♻️',
};

const PHYSICAL_LABELS = { low: 'कम', medium: 'मध्यम', high: 'ज़्यादा' };
const SELF_EMP_LABELS = { low: 'कम', medium: 'मध्यम', high: 'अच्छी' };

export function cardSpeechText(rec) {
  const gaps = rec.skill_gaps.filter((g) => !g.covered).map((g) => g.skill_name).join(', ');
  return (
    `विकल्प ${rec.rank}: ${rec.job_role}। एनएसक्यूएफ लेवल ${rec.nsqf_level}। ` +
    `${rec.why_it_fits} ट्रेनिंग: ${rec.duration_display}। ` +
    (rec.nearest_center ? `नज़दीकी केंद्र: ${rec.nearest_center.name}। ` : '') +
    (gaps ? `जो सीखना होगा: ${gaps}। ` : '') +
    `सरकारी योजना की जानकारी के लिए देखें: ${rec.scheme_pointer}।`
  );
}

export default function ResultCard({ rec, onPlay, playing }) {
  const icon = SECTOR_ICONS[rec.sector] || '💼';
  const gaps = rec.skill_gaps.filter((g) => !g.covered);
  return (
    <div className="card">
      <div className="flex items-start gap-4">
        <div className="text-6xl leading-none">{icon}</div>
        <div className="flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="bg-ink text-white text-sm font-extrabold px-3 py-1 rounded-full">
              #{rec.rank}
            </span>
            <span className="bg-sky/15 text-sky text-sm font-bold px-3 py-1 rounded-full">
              NSQF {rec.nsqf_level}
            </span>
            <span className="bg-leaf/15 text-leaf text-sm font-bold px-3 py-1 rounded-full">
              स्कोर {rec.score}/100
            </span>
          </div>
          <h3 className="text-2xl font-extrabold mt-2 leading-snug">{rec.job_role}</h3>
          <p className="text-ink/70 text-sm mt-1">
            क्षेत्र / Sector: {rec.sector.replace('_', ' ')} · शारीरिक माँग: {PHYSICAL_LABELS[rec.physical_demand] || rec.physical_demand} ·
            स्वरोज़गार संभावना: {SELF_EMP_LABELS[rec.self_employment_potential] || rec.self_employment_potential}
          </p>
        </div>
      </div>

      <div className="mt-4 rounded-2xl bg-leaf/10 border-2 border-leaf/30 p-4">
        <div className="font-extrabold text-leaf mb-1">✅ यह क्यों सही है</div>
        <p className="text-lg leading-relaxed">{rec.why_it_fits}</p>
      </div>

      <div className="grid grid-cols-2 gap-3 mt-4">
        <div className="rounded-2xl bg-ink/5 p-3">
          <div className="text-xs font-bold text-ink/60">⏱️ ट्रेनिंग समय</div>
          <div className="font-bold">{rec.duration_display}</div>
        </div>
        <div className="rounded-2xl bg-ink/5 p-3">
          <div className="text-xs font-bold text-ink/60">📍 नज़दीकी केंद्र</div>
          <div className="font-bold text-sm">
            {rec.nearest_center ? (
              <>
                {rec.nearest_center.name}
                {rec.nearest_center.distance_km != null && (
                  <span className="block text-ink/60 font-normal">
                    लगभग {rec.nearest_center.distance_km} किमी (डेमो)
                  </span>
                )}
              </>
            ) : (
              'ज़िला जोड़ने पर दिखेगा'
            )}
          </div>
        </div>
      </div>

      {rec.eligibility_note && (
        <div className="mt-3 rounded-2xl bg-amber-100 border-2 border-amber-400 p-3 text-sm text-amber-950">
          📚 {rec.eligibility_note}
        </div>
      )}

      <div className="mt-4">
        <div className="font-extrabold mb-2">📈 आपके स्किल और जो सीखना है</div>
        <SkillGapBar label="अभी जितना तैयार हैं / Current skill match" percent={rec.skill_match_percent} />
        <div className="mt-3 space-y-1">
          {rec.skill_gaps.map((g) => (
            <div key={g.skill_name} className="flex items-start gap-2 text-sm">
              <span aria-hidden="true">{g.covered ? '✅' : '📘'}</span>
              <span>
                <span className="font-bold">{g.skill_name}</span>
                <span className="text-ink/60"> — {g.note}</span>
              </span>
            </div>
          ))}
        </div>
        {gaps.length > 0 && (
          <p className="text-sm text-ink/60 mt-2">
            चिंता न करें — ये सब ट्रेनिंग में सिखाए जाते हैं।
          </p>
        )}
      </div>

      <div className="mt-4 rounded-2xl bg-amber-50 border-2 border-amber-300 p-3 text-sm">
        <span className="font-extrabold">🏛️ योजना (जाँचने के लिए):</span> {rec.scheme_pointer}
        <div className="text-ink/60 mt-1">
          यह कोई पात्रता का वादा नहीं है — अधिकारी/आधिकारिक पोर्टल से पुष्टि करें।
        </div>
      </div>

      <WhyPanel breakdown={rec.score_breakdown} />

      <button
        type="button"
        onClick={() => onPlay(rec)}
        className={`btn-big w-full mt-4 ${playing ? 'bg-red-600 text-white' : 'bg-ink text-white'}`}
      >
        <span aria-hidden="true" className="text-3xl">{playing ? '⏹️' : '🔊'}</span>
        {playing ? 'सुनना बंद करें' : 'सुनिए / Play'}
      </button>
    </div>
  );
}
