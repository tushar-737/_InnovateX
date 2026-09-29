import React, { useEffect, useRef, useState } from 'react';
import { api } from '../api/client.js';
import { createSTT, isSTTSupported, speak, stopSpeaking } from '../speech/index.js';
import MicButton from '../components/MicButton.jsx';
import MessageBubble from '../components/MessageBubble.jsx';
import TapOptions from '../components/TapOptions.jsx';

export default function ChatPage({ sessionId, onComplete }) {
  const [messages, setMessages] = useState([]);
  const [liveTranscript, setLiveTranscript] = useState('');
  const [listening, setListening] = useState(false);
  const [thinking, setThinking] = useState(false);
  const [tapOptions, setTapOptions] = useState([]);
  const [sttFailures, setSttFailures] = useState(0);
  const [textInput, setTextInput] = useState('');
  const [done, setDone] = useState(false);
  const [lastProfileHint, setLastProfileHint] = useState(null);
  const scrollRef = useRef(null);
  const sttRef = useRef(null);

  const pushMessage = (msg) => setMessages((prev) => [...prev, msg]);

  const handleAssistant = (body) => {
    pushMessage({
      role: 'assistant',
      text: body.reply_text,
      textEn: body.reply_text_en,
    });
    setTapOptions(body.tap_options || []);
    speak(body.reply_text, 'hi-IN');
    if (body.is_complete) {
      setDone(true);
      setLastProfileHint(body);
    }
  };

  const sendText = async (text) => {
    const trimmed = (text || '').trim();
    if (!trimmed || thinking) return;
    stopSpeaking();
    setTextInput('');
    setLiveTranscript('');
    pushMessage({ role: 'user', text: trimmed });
    setThinking(true);
    try {
      const body = await api.turn(sessionId, trimmed);
      handleAssistant(body);
    } catch (e) {
      pushMessage({
        role: 'assistant',
        text: 'माफ़ कीजिए, कनेक्शन में दिक्कत है। कृपया फिर से बोलिए या नीचे से जवाब चुनिए।',
        textEn: 'Sorry, connection issue. Please speak again or pick an answer below.',
      });
    } finally {
      setThinking(false);
    }
  };

  // Kick off the conversation with a greeting so the engine asks the first question.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const body = await api.turn(sessionId, 'नमस्ते');
        if (!cancelled) handleAssistant(body);
      } catch (_) {
        if (!cancelled) {
          pushMessage({
            role: 'assistant',
            text: 'नमस्ते! मैं कौशल साथी हूँ। सबसे पहले, आपका नाम क्या है?',
            textEn: 'Hello! I am Kaushal Saathi. First, may I know your name?',
          });
        }
      }
    })();
    return () => {
      cancelled = true;
      stopSpeaking();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, liveTranscript]);

  const startListening = () => {
    if (!isSTTSupported()) {
      setSttFailures(99);
      return;
    }
    stopSpeaking();
    const stt = createSTT('hi-IN', {
      onPartial: setLiveTranscript,
      onFinal: (finalText) => {
        setListening(false);
        sendText(finalText);
      },
      onError: () => {
        setListening(false);
        setSttFailures((n) => n + 1);
      },
      onEnd: () => setListening(false),
    });
    sttRef.current = stt;
    if (!stt) {
      setSttFailures(99);
      return;
    }
    setLiveTranscript('');
    setListening(true);
    stt.start();
  };

  const stopListening = () => {
    if (sttRef.current) sttRef.current.stop();
    setListening(false);
    if (liveTranscript.trim()) sendText(liveTranscript);
  };

  return (
    <div className="min-h-screen flex flex-col max-w-xl mx-auto w-full px-4 pt-4 pb-2">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-extrabold">🎙️ बातचीत</h1>
        <span className="text-sm text-ink/60 bg-ink/5 px-3 py-1 rounded-full">
          {messages.filter((m) => m.role === 'user').length} जवाब
        </span>
      </header>

      <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-4 py-4" style={{ maxHeight: '58vh' }}>
        {messages.map((m, i) => (
          <MessageBubble key={i} role={m.role} text={m.text} textEn={m.textEn} />
        ))}
        {thinking && (
          <div className="flex justify-start">
            <div className="bg-white rounded-3xl rounded-bl-md px-5 py-4 border-2 border-ink/10 shadow text-ink/60">
              सोच रहा हूँ… <span className="inline-block animate-bounce">🤔</span>
            </div>
          </div>
        )}
        {liveTranscript && (
          <div className="flex justify-end">
            <div className="max-w-[85%] rounded-3xl rounded-br-md px-5 py-3 bg-sky/20 border-2 border-sky border-dashed text-ink">
              <span className="text-xs font-bold text-sky">सुन रहा हूँ…</span>
              <div>{liveTranscript}</div>
            </div>
          </div>
        )}
      </div>

      <div className="space-y-4">
        {sttFailures >= 2 && (
          <div className="rounded-2xl bg-amber-100 border-2 border-amber-400 text-amber-950 px-4 py-3 text-center font-bold">
            🔇 आवाज़ नहीं सुनाई दी। नीचे दिए बटनों से जवाब चुनें या लिखकर बताएं।
          </div>
        )}
        <TapOptions options={tapOptions} onPick={sendText} expanded={sttFailures >= 2} />

        <div className="flex gap-2">
          <input
            type="text"
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendText(textInput)}
            placeholder="लिखकर भी बता सकते हैं…"
            className="flex-1 min-h-touch px-4 rounded-2xl border-2 border-ink/20 text-lg focus:border-sky focus:outline-none"
            aria-label="लिखकर जवाब"
          />
          <button
            type="button"
            onClick={() => sendText(textInput)}
            disabled={!textInput.trim() || thinking}
            className="btn-big bg-ink text-white px-5 disabled:opacity-50"
          >
            ➤
          </button>
        </div>

        <div className="flex flex-col items-center gap-3 pt-1">
          <MicButton
            listening={listening}
            onStart={startListening}
            onStop={stopListening}
            disabled={thinking || done}
          />
          <p className="text-sm text-ink/60">
            {done ? 'जानकारी पूरी हो गई!' : '🎤 बोलने के लिए दबाएँ'}
          </p>
        </div>

        {done && (
          <button
            type="button"
            onClick={() => onComplete(lastProfileHint)}
            className="btn-big w-full bg-leaf text-white"
          >
            <span aria-hidden="true" className="text-3xl">✅</span>
            आगे बढ़ें — जानकारी जाँचें
          </button>
        )}
        <div className="h-2" />
      </div>
    </div>
  );
}
