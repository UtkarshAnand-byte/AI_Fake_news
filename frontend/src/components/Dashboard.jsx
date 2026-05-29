import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FileText, Upload, Brain, AlertTriangle, ShieldCheck,
  History, Clock, Trash2, ArrowRight, CornerDownRight,
  ChevronRight, RefreshCw, BarChart2, Sparkles, ThumbsUp, ThumbsDown,
  Search, Send, X, Zap, Globe, Shield, Database, Code, Cpu
} from 'lucide-react';
import confetti from 'canvas-confetti';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const LOADING_PHASES = [
  'Cleaning and normalizing text payload...',
  'Extracting linguistic density metrics...',
  'Analyzing grammatical phrasing triggers...',
  'Querying advanced cognitive engine...',
  'Cross-referencing live web indexes...',
  'Synthesizing weights and scoring verdict...',
];

export default function Dashboard() {
  const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
  const [showJsonInspector, setShowJsonInspector] = useState(false);
  const [inputText,       setInputText]       = useState('');
  const [isAnalyzing,     setIsAnalyzing]     = useState(false);
  const [typingActive,    setTypingActive]    = useState(false);
  const [typingTimer,     setTypingTimer]     = useState(null);
  const [dragActive,      setDragActive]      = useState(false);
  const [uploadedFile,    setUploadedFile]    = useState(null);
  const [analysisResult,  setAnalysisResult]  = useState(null);
  const [analysisHistory, setAnalysisHistory] = useState([]);
  const [errorMessage,    setErrorMessage]    = useState('');
  const [loadingPhase,    setLoadingPhase]    = useState(LOADING_PHASES[0]);
  const textareaRef = useRef(null);

  /* ── Loading phase cycling ── */
  useEffect(() => {
    if (!isAnalyzing) { setLoadingPhase(LOADING_PHASES[0]); return; }
    let idx = 0;
    const t = setInterval(() => {
      idx = (idx + 1) % LOADING_PHASES.length;
      setLoadingPhase(LOADING_PHASES[idx]);
    }, 1400);
    return () => clearInterval(t);
  }, [isAnalyzing]);

  /* ── Fetch history ── */
  const fetchHistory = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/history?limit=6`);
      if (res.ok) setAnalysisHistory(await res.json());
    } catch (e) { console.error('History fetch failed', e); }
  };
  useEffect(() => { fetchHistory(); }, []);

  /* ── Clear history ── */
  const clearHistory = async () => {
    setErrorMessage('');
    try {
      const res = await fetch(`${API_BASE_URL}/api/history`, { method: 'DELETE' });
      if (res.ok) setAnalysisHistory([]);
      else { const d = await res.json(); setErrorMessage(d.detail || 'Failed to clear history.'); }
    } catch (e) { setErrorMessage('Could not connect to backend.'); }
  };

  /* ── Feedback ── */
  const handleFeedback = async (e, itemId, type) => {
    e.stopPropagation();
    try {
      const res = await fetch(`${API_BASE_URL}/api/feedback`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: itemId, feedback: type }),
      });
      if (res.ok) {
        setAnalysisHistory(prev => prev.map(item =>
          item.id === itemId ? { ...item, feedback: type } : item
        ));
      }
    } catch (err) { console.error(err); }
  };

  /* ── Text input ── */
  const handleTextChange = (e) => {
    const val = e.target.value;
    setInputText(val);
    setUploadedFile(null);
    setErrorMessage('');
    if (val.trim().length > 5) {
      setTypingActive(true);
      if (typingTimer) clearTimeout(typingTimer);
      setTypingTimer(setTimeout(() => setTypingActive(false), 900));
    } else { setTypingActive(false); }
  };

  /* ── Drag / Drop ── */
  const handleDrag = (e) => {
    e.preventDefault(); e.stopPropagation();
    setDragActive(e.type === 'dragenter' || e.type === 'dragover');
  };
  const handleDrop = (e) => {
    e.preventDefault(); e.stopPropagation();
    setDragActive(false); setErrorMessage('');
    if (e.dataTransfer.files?.[0]) processFile(e.dataTransfer.files[0]);
  };
  const handleFileChange = (e) => {
    setErrorMessage('');
    if (e.target.files?.[0]) processFile(e.target.files[0]);
  };
  const processFile = (file) => {
    const ext = file.name.split('.').pop().toLowerCase();
    if (ext !== 'txt' && ext !== 'pdf') { setErrorMessage('Unsupported file. Please upload .txt or .pdf.'); return; }
    setUploadedFile(file);
    setInputText(`[File Uploaded] ${file.name} (${(file.size / 1024).toFixed(1)} KB)\n\nClick "Analyze" to parse and analyze this file.`);
  };

  /* ── Analyze ── */
  const analyzeData = async () => {
    if (!inputText.trim()) { setErrorMessage('Please enter news text or upload a file first.'); return; }
    setIsAnalyzing(true); setAnalysisResult(null); setErrorMessage('');
    try {
      let response;
      if (uploadedFile) {
        const fd = new FormData();
        fd.append('file', uploadedFile);
        response = await fetch(`${API_BASE_URL}/api/predict-file`, { method: 'POST', body: fd });
      } else {
        response = await fetch(`${API_BASE_URL}/api/predict`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: inputText }),
        });
      }
      if (!response.ok) { const d = await response.json(); throw new Error(d.detail || 'Server error'); }
      const result = await response.json();
      setAnalysisResult(result);
      fetchHistory();
      if (result.prediction === 'Real') {
        confetti({ particleCount: 90, spread: 65, origin: { y: 0.75 }, colors: ['#34d399','#10b981','#6ee7b7'] });
      }
    } catch (err) {
      setErrorMessage(err.message || 'Failed to connect to the backend server.');
    } finally { setIsAnalyzing(false); }
  };

  /* ── Frontend sanitizer ── */
  const sanitize = (obj) => {
    if (typeof obj === 'string') return obj
      .replace(/gemini|google|generative ai/gi, 'Cognitive Engine')
      .replace(/machine learning/gi, 'Advanced Analytics')
      .replace(/\bml\b/gi, 'Linguistic')
      .replace(/aifakenews/gi, 'VeracitySuite')
      .replace(/\bai\b/gi, 'Cognitive Engine');
    if (Array.isArray(obj)) return obj.map(sanitize);
    if (obj && typeof obj === 'object') { const o = {}; for (const [k, v] of Object.entries(obj)) o[k] = sanitize(v); return o; }
    return obj;
  };

  /* ── Load history item ── */
  const loadHistoryItem = (item) => {
    const s = sanitize(item);
    setInputText(s.text); setUploadedFile(null); setErrorMessage('');
    const m = s.metrics || {};
    setAnalysisResult({
      prediction: s.prediction, confidence: s.confidence,
      engine: s.engine, metrics: m, explanation: s.explanation,
      final_prediction: s.prediction, final_confidence: s.confidence,
      google_verification: m.google_verification || null,
      risk_factors: m.risk_factors || [],
      ai_summary: m.ai_summary || '',
      source_reliability: m.source_reliability || '',
      processing_time: m.processing_time || '',
      ml_result: m.ml_result || null,
      gemini_result: m.gemini_result || null,
    });
  };

  const googleCheck   = analysisResult?.google_verification || analysisResult?.metrics?.google_verification;

  /* ═══════════════════════════════════════════════
     RENDER
  ═══════════════════════════════════════════════ */
  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 relative z-10 w-full max-w-7xl mx-auto px-4 py-8">

      {/* ────────────────────────────────────────
          LEFT COLUMN (8 cols on desktop)
      ──────────────────────────────────────── */}
      <div className="lg:col-span-8 flex flex-col gap-6">

        {/* INPUT PANEL */}
        <motion.div
          className="glass-panel rounded-2xl relative overflow-hidden"
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45 }}>

          {/* Active-typing gradient border pulse */}
          <AnimatePresence>
            {typingActive && (
              <motion.div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-violet-500 to-transparent animate-shimmer"
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} />
            )}
          </AnimatePresence>

          <div className="p-5 pb-0">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-violet-600/18 border border-violet-500/22 flex items-center justify-center">
                  <Brain className="w-3.5 h-3.5 text-violet-400 animate-pulse" />
                </div>
                <span className="text-xs font-bold tracking-wider uppercase text-violet-400 font-mono">Cognitive Analysis Sandbox</span>
              </div>
              <AnimatePresence>
                {typingActive && (
                  <motion.div className="flex items-center gap-1.5 text-[11px] text-violet-400 font-mono"
                    initial={{ opacity: 0, x: 8 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0 }}>
                    <div className="flex gap-0.5">
                      <span className="typing-dot" /> <span className="typing-dot" /> <span className="typing-dot" />
                    </div>
                    Extracting features...
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            <h2 className="text-lg font-bold text-white mb-1">Input News Corpus</h2>
            <p className="text-xs text-slate-500 mb-4">Paste a headline, full article, or drag & drop a <code className="text-violet-400">.txt</code> / <code className="text-violet-400">.pdf</code> file below.</p>
          </div>

          {/* Drag & Drop Textarea */}
          <div className={`mx-5 rounded-xl border-2 border-dashed transition-all duration-300 ${
            dragActive ? 'border-violet-500/60 bg-violet-500/[0.06]' : 'border-white/[0.08] bg-white/[0.02]'
          }`}
            onDragEnter={handleDrag} onDragOver={handleDrag} onDragLeave={handleDrag} onDrop={handleDrop}>
            <textarea
              ref={textareaRef}
              className="w-full h-52 p-4 font-sans text-sm bg-transparent text-slate-200 placeholder-slate-600 border-0 resize-none rounded-xl focus-neon focus:outline-none"
              placeholder="Paste suspicious headline or news paragraphs here… (minimum 10 characters)"
              value={inputText} onChange={handleTextChange} disabled={isAnalyzing} />
            {!inputText.trim() && (
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none text-slate-600 gap-2 p-6 text-center">
                <Upload className="w-8 h-8 text-violet-500/40 mb-1" />
                <p className="text-sm font-semibold text-slate-500">Drag & drop a news file here</p>
                <p className="text-xs text-slate-600">Supports .txt and .pdf (max 5MB)</p>
              </div>
            )}
          </div>

          {/* Footer Actions */}
          <div className="flex items-center justify-between p-5 pt-4 gap-4 flex-wrap">
            <div className="flex items-center gap-2.5">
              <label className="flex items-center gap-2 cursor-pointer bg-white/[0.04] hover:bg-white/[0.08] text-slate-400 hover:text-slate-200 py-2 px-3.5 rounded-lg text-xs font-semibold border border-white/[0.07] transition-all">
                <FileText className="w-3.5 h-3.5 text-violet-400" />
                Upload File
                <input type="file" accept=".txt,.pdf" className="hidden" onChange={handleFileChange} disabled={isAnalyzing} />
              </label>
              {uploadedFile && (
                <div className="flex items-center gap-1.5 text-[10px] bg-violet-500/10 text-violet-300 py-1 px-2.5 rounded-full font-mono border border-violet-500/25 animate-pulse">
                  <span className="w-1.5 h-1.5 bg-violet-400 rounded-full" />
                  {uploadedFile.name}
                  <button onClick={() => { setUploadedFile(null); setInputText(''); }} className="ml-0.5 hover:text-red-400 transition-colors">
                    <X className="w-3 h-3" />
                  </button>
                </div>
              )}
            </div>

            <div className="flex items-center gap-3">
              <span className="text-[11px] text-slate-600 font-mono">{inputText.trim().length} chars</span>
              <button id="analyze-btn" onClick={analyzeData}
                disabled={isAnalyzing || inputText.trim().length < 10}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-violet-700 hover:from-violet-500 hover:to-violet-600 text-white font-bold text-sm shadow-[0_0_22px_rgba(124,58,237,0.3)] hover:shadow-[0_0_32px_rgba(124,58,237,0.55)] transition-all duration-200 disabled:opacity-35 disabled:cursor-not-allowed disabled:shadow-none">
                {isAnalyzing
                  ? <><RefreshCw className="w-4 h-4 animate-spin" /> Analyzing...</>
                  : <><Search className="w-4 h-4" /> Analyze</>}
              </button>
            </div>
          </div>

          {/* Error Toast */}
          <AnimatePresence>
            {errorMessage && (
              <motion.div className="mx-5 mb-5 p-3 border border-rose-500/20 bg-rose-500/[0.08] text-rose-400 rounded-xl text-xs flex items-center gap-2 font-mono"
                initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                {errorMessage}
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* LOCAL DEVELOPER HUD & TELEMETRY */}
        {isLocalhost && (
          <motion.div
            className="glass-panel rounded-2xl p-5 border border-emerald-500/18 shadow-glow-emerald bg-emerald-950/[0.01]"
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45, delay: 0.05 }}>
            
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-emerald-500/10 border border-emerald-500/22 flex items-center justify-center animate-pulse">
                  <Database className="w-3.5 h-3.5 text-emerald-400" />
                </div>
                <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
                  VeracitySuite Local Developer HUD
                  <span className="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/18">ONLINE</span>
                </h3>
              </div>
              
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400 border border-emerald-500/30 animate-ping" />
                <span className="text-[10px] text-slate-500 font-mono">localhost:8000</span>
              </div>
            </div>
            
            <p className="text-xs text-slate-400 mb-4 leading-relaxed">
              Detected local host execution. This HUD provides real-time system metrics, automated claim injectors, and direct JSON payload inspection.
            </p>
            
            {/* System Status Indicators */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-4">
              {[
                { label: 'PostgreSQL DB', val: 'Neon Active', color: 'text-emerald-400 bg-emerald-500/5 border-emerald-500/15' },
                { label: 'Primary ML Engine', val: 'LinearSVC', color: 'text-violet-400 bg-violet-500/5 border-violet-500/15' },
                { label: 'Web Fact Grounder', val: 'Google+DDG', color: 'text-cyan-400 bg-cyan-500/5 border-cyan-500/15' },
                { label: 'Cognitive Engine', val: 'Gemini 2.5', color: 'text-amber-400 bg-amber-500/5 border-amber-500/15' },
              ].map((s, idx) => (
                <div key={idx} className={`p-2.5 rounded-xl border ${s.color} text-center flex flex-col gap-0.5`}>
                  <span className="text-[8px] font-bold uppercase tracking-wider text-slate-500 font-mono">{s.label}</span>
                  <span className="text-xs font-black font-mono leading-none mt-0.5">{s.val}</span>
                </div>
              ))}
            </div>

            {/* Quick Test Claim Injectors */}
            <div className="mb-4">
              <span className="text-[9px] uppercase font-bold tracking-widest text-slate-500 font-mono mb-2 block">Quick Sandbox Injectors</span>
              <div className="flex flex-col gap-1.5">
                {[
                  { text: "US inflation rose to 3.8% in April, eroding Americans' paychecks", label: "REAL NEWS", style: "border-emerald-500/20 text-emerald-400 hover:bg-emerald-500/10" },
                  { text: "LEAKED: Private billionaire email confirms space lasers are heating up the ocean to boil lobsters directly", label: "FAKE NEWS", style: "border-rose-500/20 text-rose-400 hover:bg-rose-500/10" },
                  { text: "The European Union has announced a new regulatory framework targeting carbon emissions", label: "REAL NEWS", style: "border-violet-500/20 text-violet-400 hover:bg-violet-500/10" },
                ].map((item, idx) => (
                  <button key={idx} onClick={() => { setInputText(item.text); setUploadedFile(null); setErrorMessage(''); }}
                    className={`text-[11px] font-semibold font-mono text-left px-3 py-2 border rounded-xl bg-white/[0.015] transition-all hover:translate-x-1 ${item.style}`}>
                    <span className="opacity-50">[{item.label}]</span> {item.text}
                  </button>
                ))}
              </div>
            </div>

            {/* Collapsible JSON payload inspector */}
            {analysisResult && (
              <div className="mt-3 pt-3 border-t border-white/[0.06]">
                <button onClick={() => setShowJsonInspector(!showJsonInspector)}
                  className="flex items-center justify-between w-full text-[10px] font-bold text-slate-500 hover:text-slate-300 font-mono uppercase tracking-wider">
                  <span className="flex items-center gap-1.5"><Code className="w-3 h-3 text-emerald-400" /> Inspect Raw API Response Payload</span>
                  <span>{showJsonInspector ? 'Collapse [-]' : 'Expand [+]'}</span>
                </button>
                
                <AnimatePresence>
                  {showJsonInspector && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden mt-2">
                      <pre className="font-mono text-[9px] bg-slate-950 p-3.5 rounded-xl border border-white/[0.08] text-slate-300 overflow-x-auto max-h-52 custom-scrollbar leading-relaxed">
                        {JSON.stringify(analysisResult, null, 2)}
                      </pre>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            )}
            
          </motion.div>
        )}

        {/* HISTORY PANEL */}
        <motion.div className="glass-panel rounded-2xl p-5"
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45, delay: 0.1 }}>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-slate-800/60 border border-white/[0.07] flex items-center justify-center">
                <History className="w-3.5 h-3.5 text-slate-400" />
              </div>
              <h3 className="text-sm font-bold text-white">Analysis History</h3>
              {analysisHistory.length > 0 && (
                <span className="text-[10px] font-mono text-slate-500 bg-white/[0.04] px-2 py-0.5 rounded-full border border-white/[0.06]">
                  {analysisHistory.length} records
                </span>
              )}
            </div>
            {analysisHistory.length > 0 && (
              <button onClick={clearHistory}
                className="text-[11px] text-rose-500/70 hover:text-rose-400 transition-colors flex items-center gap-1 font-medium">
                <Trash2 className="w-3 h-3" /> Wipe Logs
              </button>
            )}
          </div>

          {analysisHistory.length === 0 ? (
            <div className="text-center py-8 flex flex-col items-center gap-2">
              <div className="w-10 h-10 rounded-xl bg-white/[0.03] border border-white/[0.06] flex items-center justify-center">
                <History className="w-5 h-5 text-slate-600" />
              </div>
              <p className="text-xs text-slate-600">No historical data yet. Analyze something to begin.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {analysisHistory.map((item) => (
                <div key={item.id} onClick={() => loadHistoryItem(item)}
                  className="history-card flex justify-between items-start gap-2 p-3.5 rounded-xl border border-white/[0.06] bg-white/[0.025]">
                  <div className="flex flex-col gap-1.5 min-w-0">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <Clock className="w-3 h-3 text-slate-600 shrink-0" />
                      <span className="text-[10px] text-slate-600 font-mono">{item.created_at}</span>
                      <span className={`text-[9px] font-black uppercase font-mono px-2 py-0.5 rounded-full border ${
                        item.prediction === 'Fake'
                          ? 'text-rose-400 bg-rose-500/10 border-rose-500/20'
                          : 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
                      }`}>{item.prediction}</span>
                    </div>
                    <p className="text-[11px] text-slate-400 font-medium truncate group-hover:text-violet-300 transition-colors">{item.title}</p>
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    <button onClick={(e) => handleFeedback(e, item.id, 'correct')}
                      className={`p-1.5 rounded-lg border transition-all ${item.feedback === 'correct' ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/25' : 'text-slate-600 border-transparent hover:text-emerald-400 hover:bg-emerald-500/10'}`}
                      title="Mark as Correct"><ThumbsUp className="w-3 h-3" /></button>
                    <button onClick={(e) => handleFeedback(e, item.id, 'incorrect')}
                      className={`p-1.5 rounded-lg border transition-all ${item.feedback === 'incorrect' ? 'text-rose-400 bg-rose-500/10 border-rose-500/25' : 'text-slate-600 border-transparent hover:text-rose-400 hover:bg-rose-500/10'}`}
                      title="Mark as Incorrect"><ThumbsDown className="w-3 h-3" /></button>
                    <ChevronRight className="w-3.5 h-3.5 text-slate-700" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </motion.div>
      </div>

      {/* ────────────────────────────────────────
          RIGHT COLUMN (4 cols on desktop)
      ──────────────────────────────────────── */}
      <div className="lg:col-span-4 flex flex-col gap-6">
        <AnimatePresence mode="wait">

          {/* LOADING CARD */}
          {isAnalyzing && (
            <motion.div key="loading"
              className="glass-panel rounded-2xl p-6 flex flex-col items-center justify-center text-center min-h-[580px] relative overflow-hidden"
              initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.96 }}>
              <div className="absolute inset-0 tech-grid opacity-20 pointer-events-none" />
              <div className="scan-line" />

              <div className="relative w-28 h-28 mb-6">
                <div className="absolute inset-0 rounded-full cyber-spinner" />
                <div className="absolute inset-4 rounded-full border border-dashed border-violet-500/25 animate-spin [animation-duration:14s]" />
                <Brain className="absolute inset-0 m-auto w-9 h-9 text-violet-400 animate-pulse" />
              </div>

              <h3 className="text-base font-bold text-white mb-2">Quantum Hybrid Evaluation</h3>
              <div className="min-h-[36px] flex items-center justify-center px-3 mb-4">
                <AnimatePresence mode="wait">
                  <motion.p key={loadingPhase}
                    className="text-[11px] text-violet-400 font-mono glow-text-accent text-center leading-relaxed"
                    initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }}
                    transition={{ duration: 0.25 }}>
                    {loadingPhase}
                  </motion.p>
                </AnimatePresence>
              </div>

              <div className="flex gap-1 mb-4">
                <span className="typing-dot" /><span className="typing-dot" /><span className="typing-dot" />
              </div>
              <p className="text-[10px] text-slate-600 max-w-[200px] leading-relaxed font-mono">
                Dual-intelligence pipeline engaged. Do not close sandbox window.
              </p>
            </motion.div>
          )}

          {/* IDLE CARD */}
          {!isAnalyzing && !analysisResult && (
            <motion.div key="idle"
              className="glass-panel rounded-2xl p-6 flex flex-col items-center justify-center text-center min-h-[580px] relative"
              initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.96 }}>
              <div className="absolute inset-0 tech-grid opacity-10 pointer-events-none" />

              <div className="relative w-20 h-20 mb-5">
                <div className="absolute inset-0 rounded-2xl bg-violet-600/10 border border-violet-500/15 animate-pulse" />
                <div className="w-20 h-20 rounded-2xl bg-violet-600/8 border border-violet-500/12 flex items-center justify-center">
                  <BarChart2 className="w-9 h-9 text-violet-500/60" />
                </div>
              </div>

              <h3 className="text-base font-bold text-white mb-2">Diagnostic Telemetry</h3>
              <p className="text-xs text-slate-500 max-w-[210px] leading-relaxed mb-6">
                No active corpus loaded. Input an article in the sandbox and submit for real-time classification.
              </p>

              <div className="w-full flex flex-col gap-2 text-left">
                {[
                  { icon: Zap, label: 'Linguistic ML Classifier', color: 'text-violet-400' },
                  { icon: Globe, label: 'Live Google News Cross-ref', color: 'text-cyan-400' },
                  { icon: Shield, label: 'Heuristic Fallback Engine', color: 'text-emerald-400' },
                ].map((f, i) => (
                  <div key={i} className="flex items-center gap-2.5 p-2.5 rounded-lg bg-white/[0.025] border border-white/[0.05]">
                    <f.icon className={`w-3.5 h-3.5 ${f.color} shrink-0`} />
                    <span className="text-[11px] text-slate-400 font-medium">{f.label}</span>
                    <span className="ml-auto text-[9px] font-mono text-emerald-500 bg-emerald-500/10 border border-emerald-500/20 px-1.5 py-0.5 rounded-full">READY</span>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {/* RESULTS CARD */}
          {!isAnalyzing && analysisResult && (() => {
            const geminiResult    = analysisResult.gemini_result    || analysisResult.metrics?.gemini_result;
            const mlResult        = analysisResult.ml_result        || analysisResult.metrics?.ml_result;
            const aiSummary       = analysisResult.ai_summary       || analysisResult.metrics?.ai_summary;
            const riskFactors     = analysisResult.risk_factors     || analysisResult.metrics?.risk_factors || [];
            const finalPrediction = analysisResult.final_prediction || analysisResult.metrics?.final_prediction || analysisResult.prediction;
            const finalConfidence = analysisResult.final_confidence || analysisResult.metrics?.final_confidence || analysisResult.confidence;
            const processingTime  = analysisResult.processing_time  || analysisResult.metrics?.processing_time;
            const sourceReliance  = analysisResult.source_reliability || analysisResult.metrics?.source_reliability;

            const isFake  = finalPrediction === 'Fake';
            const isReal  = finalPrediction === 'Real';
            const isSusp  = !isFake && !isReal;

            const verdictColor  = isFake ? '#fb7185'  : isReal  ? '#34d399'  : '#a78bfa';
            const verdictClass  = isFake ? 'verdict-fake' : isReal ? 'verdict-real' : 'verdict-suspicious';
            const scanClass     = isFake ? 'scan-line-red' : isReal ? 'scan-line-green' : 'scan-line-violet';

            return (
              <motion.div key="result"
                className={`glass-panel rounded-2xl flex flex-col gap-4 pb-5 relative overflow-hidden ${verdictClass} result-enter`}
                initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.96 }}>
                <div className={`scan-line ${scanClass}`} />

                {/* VERDICT HEADER */}
                <div className="px-5 pt-5">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <p className="text-[10px] font-mono font-bold text-slate-500 tracking-widest uppercase">Decision Telemetry</p>
                      {processingTime && <p className="text-[9px] font-mono text-slate-600">Latency: {processingTime}</p>}
                    </div>
                    {geminiResult && (
                      <span className="text-[9px] font-bold font-mono tracking-wider bg-violet-600/12 text-violet-400 px-2 py-0.5 rounded border border-violet-500/22 animate-pulse shrink-0">
                        Cognitive Context
                      </span>
                    )}
                  </div>

                  {/* Verdict Banner */}
                  <div className={`flex items-center gap-3 p-4 rounded-xl mb-3 ${
                    isFake ? 'bg-rose-500/[0.08] border border-rose-500/20' :
                    isReal ? 'bg-emerald-500/[0.08] border border-emerald-500/20' :
                             'bg-violet-500/[0.08] border border-violet-500/20'
                  }`}>
                    <div className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 ${
                      isFake ? 'bg-rose-500/15 border border-rose-500/25' :
                      isReal ? 'bg-emerald-500/15 border border-emerald-500/25' :
                               'bg-violet-500/15 border border-violet-500/25'
                    }`}>
                      {isFake  ? <AlertTriangle className="w-5 h-5 text-rose-400" />    :
                       isReal  ? <ShieldCheck   className="w-5 h-5 text-emerald-400" /> :
                                 <AlertTriangle className="w-5 h-5 text-violet-400" />}
                    </div>
                    <div>
                      <h4 className={`text-xl font-black uppercase tracking-tight leading-none ${
                        isFake ? 'text-rose-400 glow-text-rose' : isReal ? 'text-emerald-400 glow-text-emerald' : 'text-violet-400 glow-text-accent'
                      }`}>
                        {isFake ? 'FAKE NEWS' : isReal ? 'REAL NEWS' : 'SUSPICIOUS'}
                      </h4>
                      <p className="text-[10px] text-slate-500 font-mono mt-0.5">
                        {isFake ? 'Sensationalism alert flagged' : isReal ? 'Journalistic structure verified' : 'Multi-engine conflict registered'}
                      </p>
                    </div>
                  </div>

                  {/* RADIAL CONFIDENCE GAUGE */}
                  <div className="flex items-center justify-center mb-2 relative">
                    <svg className="w-28 h-28 -rotate-90">
                      <circle cx="56" cy="56" r="46" className="stroke-white/[0.05]" strokeWidth="8" fill="transparent" />
                      <circle cx="56" cy="56" r="46"
                        stroke={verdictColor} strokeWidth="8" fill="transparent"
                        strokeDasharray={2 * Math.PI * 46}
                        strokeDashoffset={2 * Math.PI * 46 * (1 - Number(finalConfidence) / 100)}
                        strokeLinecap="round"
                        style={{ transition: 'stroke-dashoffset 1.2s cubic-bezier(0.34,1.56,0.64,1)', filter: `drop-shadow(0 0 8px ${verdictColor}66)` }} />
                    </svg>
                    <div className="absolute flex flex-col items-center">
                      <span className="text-2xl font-black text-white">{Number(finalConfidence).toFixed(0)}%</span>
                      <span className="text-[9px] text-slate-500 font-mono uppercase tracking-wider">Confidence</span>
                    </div>
                  </div>
                </div>

                {/* RISK FACTORS */}
                {riskFactors.length > 0 && (
                  <div className="px-5">
                    <p className="text-[9px] uppercase font-bold tracking-widest text-slate-600 font-mono mb-2">Risk Factors</p>
                    <div className="flex flex-wrap gap-1">
                      {riskFactors.map((rf, i) => (
                        <span key={i} className="text-[9px] font-bold font-mono px-2 py-0.5 rounded bg-rose-500/[0.08] text-rose-400 border border-rose-500/18">
                          ⚠ {rf}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* AI SUMMARY */}
                {aiSummary && (
                  <div className="px-5">
                    <div className="p-3.5 rounded-xl bg-violet-500/[0.07] border border-violet-500/15">
                      <div className="flex items-center gap-1.5 mb-2">
                        <Sparkles className="w-3 h-3 text-violet-400 animate-spin [animation-duration:8s]" />
                        <span className="text-[9px] uppercase font-bold tracking-widest text-violet-400 font-mono">Cognitive Diagnostic</span>
                      </div>
                      <p className="text-[11px] text-slate-300 leading-relaxed font-medium">{aiSummary}</p>
                      {geminiResult?.clickbait_score !== undefined && (
                        <div className="grid grid-cols-2 gap-2 mt-2.5 pt-2 border-t border-violet-500/10">
                          <div className="text-[10px] font-mono text-slate-500">Bias: <span className="text-violet-400 font-bold">{geminiResult.bias_detected ? 'Detected' : 'None'}</span></div>
                          <div className="text-[10px] font-mono text-slate-500 text-right">Clickbait: <span className="text-violet-400 font-bold">{geminiResult.clickbait_score}%</span></div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* LINGUISTIC METRICS */}
                <div className="px-5">
                  <p className="text-[9px] uppercase font-bold tracking-widest text-slate-600 font-mono mb-3">Linguistic Heuristics</p>
                  <div className="flex flex-col gap-2.5">
                    {[
                      { label: 'Sensationalist Tone', value: analysisResult.metrics?.sensationalism ?? 0, delay: 0 },
                      { label: 'Subjective Bias',     value: analysisResult.metrics?.emotional_bias   ?? 0, delay: 0.1 },
                      { label: 'Aggressive Format',   value: analysisResult.metrics?.formatting_style ?? 0, delay: 0.2 },
                    ].map((m, i) => (
                      <div key={i}>
                        <div className="flex justify-between text-[10px] font-mono text-slate-500 mb-1">
                          <span>{m.label}</span>
                          <span className={m.value > 60 ? 'text-rose-400' : m.value > 30 ? 'text-amber-400' : 'text-emerald-400'}>{m.value}%</span>
                        </div>
                        <div className="progress-track">
                          <motion.div className={`${m.value > 60 ? 'progress-fill-rose' : m.value > 30 ? '' : 'progress-fill-emerald'} h-full rounded-full`}
                            style={{ background: m.value > 60 ? 'linear-gradient(90deg,#e11d48,#fb7185)' : m.value > 30 ? 'linear-gradient(90deg,#d97706,#fbbf24)' : 'linear-gradient(90deg,#059669,#34d399)' }}
                            initial={{ width: 0 }} animate={{ width: `${Math.min(m.value, 100)}%` }}
                            transition={{ duration: 0.9, delay: m.delay, ease: [0.34, 1.56, 0.64, 1] }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* SOURCE VERIFIABILITY */}
                {(googleCheck?.search_performed || sourceReliance) && (
                  <div className="px-5">
                    <div className="p-3.5 rounded-xl bg-white/[0.025] border border-white/[0.06]">
                      <div className="flex justify-between items-center mb-2">
                        <p className="text-[9px] uppercase font-bold tracking-widest text-slate-600 font-mono flex items-center gap-1">
                          <Globe className="w-3 h-3" /> Source Verifiability
                        </p>
                        {googleCheck?.verification_score !== undefined && (
                          <span className={`text-[9px] font-bold font-mono px-2 py-0.5 rounded-full border ${
                            googleCheck.verification_score >= 80 ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' :
                            googleCheck.verification_score >= 50 ? 'text-amber-400 bg-amber-500/10 border-amber-500/20' :
                            'text-rose-400 bg-rose-500/10 border-rose-500/20'
                          }`}>{googleCheck.verification_score}%</span>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-400 leading-snug">{sourceReliance || googleCheck?.status}</p>
                      {googleCheck?.outlets_found?.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {googleCheck.outlets_found.map((o, i) => (
                            <span key={i} className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-white/[0.04] text-slate-500 border border-white/[0.05]">{o}</span>
                          ))}
                        </div>
                      )}
                      {googleCheck?.search_results?.length > 0 && (
                        <div className="mt-3.5 pt-3 border-t border-white/[0.05] flex flex-col gap-2">
                          <p className="text-[8px] uppercase font-bold tracking-widest text-slate-500 font-mono mb-0.5">Grounding References</p>
                          <div className="flex flex-col gap-2 max-h-48 overflow-y-auto pr-1 custom-scrollbar">
                            {googleCheck.search_results.slice(0, 3).map((res, idx) => {
                              let domain = res.engine || "News Source";
                              if (res.url) {
                                try {
                                  domain = new URL(res.url).hostname.replace('news.google.com', 'Google News').replace('www.', '');
                                } catch (_) {}
                              }
                              return (
                                <a key={idx} href={res.url} target="_blank" rel="noopener noreferrer"
                                  className="group/ref p-2 rounded-xl bg-white/[0.015] border border-white/[0.04] hover:bg-violet-500/[0.04] hover:border-violet-500/25 transition-all duration-200 flex flex-col gap-1 text-left relative overflow-hidden">
                                  <div className="flex items-start justify-between gap-3">
                                    <span className="text-[10px] font-bold text-slate-300 group-hover/ref:text-violet-400 transition-colors line-clamp-2 leading-relaxed">{res.title}</span>
                                    <span className="text-[8px] font-mono font-bold px-1.5 py-0.5 rounded bg-violet-500/10 text-violet-400 shrink-0 border border-violet-500/15 uppercase tracking-wide">{domain}</span>
                                  </div>
                                  {res.snippet && <p className="text-[9.5px] text-slate-500 leading-normal line-clamp-2">{res.snippet}</p>}
                                </a>
                              );
                            })}
                          </div>
                        </div>
                      )}
                      {googleCheck?.query_url && (
                        <a href={googleCheck.query_url} target="_blank" rel="noopener noreferrer"
                          className="text-[9px] text-violet-400 hover:underline flex items-center gap-1 mt-2.5 font-mono pt-1">
                          Verify on Search Index <ArrowRight className="w-2.5 h-2.5" />
                        </a>
                      )}
                    </div>
                  </div>
                )}

                {/* EXPLANATION LOG */}
                <div className="px-5 pb-1">
                  <p className="text-[9px] uppercase font-bold tracking-widest text-slate-600 font-mono mb-2">Diagnostic Log</p>
                  <ul className="flex flex-col gap-1.5 max-h-[130px] overflow-y-auto custom-scrollbar pr-1">
                    {(analysisResult.explanation ?? []).map((bullet, i) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <CornerDownRight className="w-3 h-3 text-violet-500 shrink-0 mt-0.5" />
                        <span className="text-[11px] text-slate-400 leading-relaxed">{bullet}</span>
                      </li>
                    ))}
                    {!analysisResult.explanation?.length && (
                      <li className="text-[11px] text-slate-600">No diagnostic log available.</li>
                    )}
                  </ul>
                </div>
              </motion.div>
            );
          })()}

        </AnimatePresence>
      </div>
    </div>
  );
}
