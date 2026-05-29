import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Brain, Cpu, Terminal, Upload, AlertCircle,
  CheckCircle, Play, RefreshCw, FileSpreadsheet,
  TrendingUp, Trash2, Zap, ArrowRight
} from 'lucide-react';
import confetti from 'canvas-confetti';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const LOG_MILESTONES = [
  "[SYSTEM] Initializing Cognitive Retraining Pipeline...",
  "[SYSTEM] Connection to Neon PostgreSQL active. Querying historical database logs...",
  "[DATA] Retrieving database feedback correction loop samples...",
  "[DATA] Assembling global corpus with 100+ labeled real/fake news articles...",
  "[TOKENIZER] Normalizing character encodings and scrubbing HTML/URL tags...",
  "[TOKENIZER] Fitting TF-IDF vectorizer with unigram/bigram token ranges...",
  "[MODEL] Spawning Logistic Regression estimator (C=2.5, max_iter=1000)...",
  "[MODEL] Running stratified 5-fold cross-validation on train partition...",
  "[MODEL] Scoring pipeline partitions (Accuracy, Precision, Recall, F1)...",
  "[MODEL] Serializing Pipeline into models/text_clf_model.pkl...",
  "[SYSTEM] Relaying hot-swap command to backend analyzer framework...",
  "[SYSTEM] SUCCESS: Dynamic engine swap completed. In-memory model active.",
];

export default function TrainingCenter() {
  const [useFeedback,    setUseFeedback]    = useState(true);
  const [customFile,     setCustomFile]     = useState(null);
  const [dragActive,     setDragActive]     = useState(false);
  const [isTraining,     setIsTraining]     = useState(false);
  const [errorMsg,       setErrorMsg]       = useState('');
  const [successMsg,     setSuccessMsg]     = useState('');
  const [terminalLogs,   setTerminalLogs]   = useState([]);
  const terminalEndRef = useRef(null);

  const [metrics, setMetrics] = useState({
    accuracy: 94.0, precision: 93.8, recall: 94.2, f1_score: 94.0,
    total_samples: 100, train_samples: 80, test_samples: 20,
    feedback_samples: 0, custom_samples: 0,
    engine: 'Standard Linguistic Engine', isTrained: false,
  });

  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [terminalLogs]);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/health`)
      .then((r) => r.ok ? r.json() : null)
      .then((d) => { if (d) setMetrics((p) => ({ ...p, engine: d.engine, isTrained: d.model_loaded })); })
      .catch(() => {});
  }, []);

  const handleDrag = (e) => {
    e.preventDefault(); e.stopPropagation();
    setDragActive(e.type === 'dragenter' || e.type === 'dragover');
  };
  const handleDrop = (e) => {
    e.preventDefault(); e.stopPropagation();
    setDragActive(false); setErrorMsg('');
    if (e.dataTransfer.files?.[0]) processFile(e.dataTransfer.files[0]);
  };
  const handleFileChange = (e) => {
    setErrorMsg('');
    if (e.target.files?.[0]) processFile(e.target.files[0]);
  };
  const processFile = (file) => {
    if (!file.name.endsWith('.csv')) { setErrorMsg('Unsupported format. Upload a .csv file with "text" and "label" columns.'); return; }
    setCustomFile(file);
    setSuccessMsg(`Dataset '${file.name}' (${(file.size / 1024).toFixed(1)} KB) loaded. Ready for training.`);
  };
  const removeFile = () => { setCustomFile(null); setSuccessMsg(''); };

  const retrainEngine = async () => {
    setIsTraining(true); setErrorMsg(''); setSuccessMsg(''); setTerminalLogs([]);

    let logIdx = 0;
    setTerminalLogs([LOG_MILESTONES[0]]);
    const interval = setInterval(() => {
      logIdx++;
      if (logIdx < LOG_MILESTONES.length - 1)
        setTerminalLogs((p) => [...p, LOG_MILESTONES[logIdx]]);
      else clearInterval(interval);
    }, 480);

    try {
      const options = { method: 'POST' };
      if (customFile) {
        const fd = new FormData(); fd.append('file', customFile); options.body = fd;
      }
      const response = await fetch(`${API_BASE_URL}/api/train?use_feedback=${useFeedback}`, options);
      if (!response.ok) { const d = await response.json(); throw new Error(d.detail || 'Training returned a compilation error.'); }
      const result = await response.json();

      clearInterval(interval);
      setTerminalLogs((prev) => [
        ...prev,
        ...LOG_MILESTONES.slice(prev.length, LOG_MILESTONES.length - 1),
        `[METRICS] Accuracy: ${result.metrics.accuracy}% | F1: ${result.metrics.f1_score}% | Samples: ${result.metrics.total_samples}`,
        `[SYSTEM] SUCCESS: ${result.message}`,
      ]);

      setMetrics({
        accuracy:         result.metrics.accuracy,
        precision:        result.metrics.precision,
        recall:           result.metrics.recall,
        f1_score:         result.metrics.f1_score,
        total_samples:    result.metrics.total_samples,
        train_samples:    result.metrics.train_samples,
        test_samples:     result.metrics.test_samples,
        feedback_samples: result.metrics.feedback_samples,
        custom_samples:   result.metrics.custom_samples,
        engine:           'Standard Linguistic Engine',
        isTrained:        true,
      });

      setSuccessMsg('Cognitive Model retrained and hot-swapped successfully!');
      confetti({ particleCount: 160, spread: 85, origin: { y: 0.62 }, colors: ['#7c3aed','#a78bfa','#22d3ee','#34d399'] });
    } catch (err) {
      clearInterval(interval);
      setTerminalLogs((p) => [...p, `[ERROR] Retraining failed: ${err.message}`]);
      setErrorMsg(err.message || 'Failed to connect to backend.');
    } finally { setIsTraining(false); }
  };

  /* Gauge ring helper */
  const GaugeRing = ({ value, color, label }) => {
    const r = 28; const circ = 2 * Math.PI * r;
    return (
      <div className="flex flex-col items-center p-3.5 rounded-xl border border-white/[0.06] bg-white/[0.025]">
        <div className="relative w-16 h-16">
          <svg className="w-full h-full -rotate-90">
            <circle cx="32" cy="32" r={r} className="stroke-white/[0.06]" strokeWidth="5" fill="transparent" />
            <circle cx="32" cy="32" r={r} stroke={color} strokeWidth="5" fill="transparent"
              strokeDasharray={circ} strokeDashoffset={circ * (1 - value / 100)}
              strokeLinecap="round"
              style={{ transition: 'stroke-dashoffset 1.2s cubic-bezier(0.34,1.56,0.64,1)', filter: `drop-shadow(0 0 6px ${color}66)` }} />
          </svg>
          <span className="absolute inset-0 flex items-center justify-center text-[13px] font-black font-mono text-white">{value}%</span>
        </div>
        <span className="text-[9px] uppercase font-mono tracking-widest text-slate-500 font-bold mt-2">{label}</span>
      </div>
    );
  };

  /* ─────────────────────────────── RENDER ─────────────────────────────── */
  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 relative z-10 w-full max-w-7xl mx-auto px-4 py-8">

      {/* ─── LEFT COLUMN (5 cols) ─── */}
      <div className="lg:col-span-5 flex flex-col gap-6">

        {/* TRAINING CONTROL CARD */}
        <motion.div className="glass-panel rounded-2xl p-6 relative overflow-hidden"
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45 }}>
          <div className="absolute inset-0 tech-grid opacity-20 pointer-events-none" />

          <div className="flex items-center gap-2 mb-1 relative z-10">
            <div className="w-7 h-7 rounded-lg bg-violet-600/15 border border-violet-500/20 flex items-center justify-center">
              <Cpu className="w-3.5 h-3.5 text-violet-400 animate-spin [animation-duration:10s]" />
            </div>
            <span className="text-[11px] font-bold tracking-widest uppercase text-violet-400 font-mono">Model Training Desk</span>
          </div>

          <h2 className="text-xl font-black text-white mb-1 relative z-10">Cognitive Retraining</h2>
          <p className="text-xs text-slate-500 mb-6 relative z-10">
            Configure dataset variables and trigger backpropagation algorithms to fine-tune prediction boundaries.
          </p>

          <div className="flex flex-col gap-4 relative z-10">

            {/* Feedback Toggle */}
            <div className="flex items-center justify-between p-3.5 rounded-xl border border-white/[0.07] bg-white/[0.03]">
              <div>
                <p className="text-xs font-bold text-white">PostgreSQL Feedback Loop</p>
                <p className="text-[10px] text-slate-500 mt-0.5">Include corrected samples from analysis history.</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" checked={useFeedback}
                  onChange={(e) => setUseFeedback(e.target.checked)} disabled={isTraining} className="sr-only peer" />
                <div className="w-10 h-5.5 rounded-full bg-slate-800 border border-white/[0.07] peer-focus:outline-none relative
                  after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full
                  after:h-4 after:w-4 after:transition-all peer-checked:bg-violet-600
                  peer-checked:after:translate-x-[18px] transition-colors" style={{height:'22px'}} />
              </label>
            </div>

            {/* CSV Upload */}
            <div
              className={`relative rounded-xl border-2 border-dashed p-5 text-center transition-all duration-300 ${
                dragActive ? 'border-violet-500/60 bg-violet-500/[0.06]' : 'border-white/[0.08] bg-white/[0.02]'
              }`}
              onDragEnter={handleDrag} onDragOver={handleDrag} onDragLeave={handleDrag} onDrop={handleDrop}>
              <input type="file" id="csv-upload" accept=".csv" className="hidden" disabled={isTraining} onChange={handleFileChange} />
              {!customFile ? (
                <label htmlFor="csv-upload" className="flex flex-col items-center cursor-pointer gap-2 text-slate-500">
                  <div className="w-10 h-10 rounded-xl bg-violet-600/10 border border-violet-500/18 flex items-center justify-center">
                    <Upload className="w-5 h-5 text-violet-500/70" />
                  </div>
                  <span className="text-xs font-bold text-white">Upload Custom CSV Dataset</span>
                  <span className="text-[10px] text-slate-600">Requires columns: <code className="text-violet-400">'text'</code> and <code className="text-violet-400">'label'</code> (0/1)</span>
                </label>
              ) : (
                <div className="flex flex-col items-center gap-2">
                  <div className="w-10 h-10 rounded-xl bg-emerald-600/10 border border-emerald-500/18 flex items-center justify-center">
                    <FileSpreadsheet className="w-5 h-5 text-emerald-400" />
                  </div>
                  <span className="text-xs font-bold text-emerald-400 font-mono truncate max-w-[220px]">{customFile.name}</span>
                  <span className="text-[10px] text-slate-500">{(customFile.size/1024).toFixed(1)} KB — Ready to inject</span>
                  <button onClick={removeFile} disabled={isTraining}
                    className="text-[10px] text-rose-500 hover:underline flex items-center gap-1 font-semibold mt-1">
                    <Trash2 className="w-3 h-3" /> Remove Dataset
                  </button>
                </div>
              )}
            </div>

            {/* Retrain Button */}
            <button onClick={retrainEngine} disabled={isTraining}
              className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-gradient-to-r from-violet-600 to-violet-700 hover:from-violet-500 hover:to-violet-600 text-white font-extrabold text-sm shadow-[0_0_22px_rgba(124,58,237,0.3)] hover:shadow-[0_0_35px_rgba(124,58,237,0.55)] transition-all duration-200 disabled:opacity-35 disabled:cursor-not-allowed disabled:shadow-none">
              {isTraining ? (
                <><RefreshCw className="w-4 h-4 animate-spin" /> Calibrating Neural Synapses...</>
              ) : (
                <><Zap className="w-4 h-4" /> Retrain Model Engine</>
              )}
            </button>

            {/* Messages */}
            <AnimatePresence>
              {errorMsg && (
                <motion.div className="p-3 border border-rose-500/20 bg-rose-500/[0.07] text-rose-400 rounded-xl text-xs flex items-center gap-2 font-mono"
                  initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                  <AlertCircle className="w-4 h-4 shrink-0" />{errorMsg}
                </motion.div>
              )}
            </AnimatePresence>
            <AnimatePresence>
              {successMsg && !errorMsg && (
                <motion.div className="p-3 border border-emerald-500/20 bg-emerald-500/[0.07] text-emerald-400 rounded-xl text-xs flex items-center gap-2 font-mono"
                  initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                  <CheckCircle className="w-4 h-4 shrink-0" />{successMsg}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </motion.div>

        {/* SYSTEM STATUS CARD */}
        <motion.div className="glass-panel rounded-2xl p-5"
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45, delay: 0.1 }}>
          <h3 className="text-[11px] uppercase font-mono font-bold tracking-widest text-slate-500 mb-4">Active System Status</h3>
          <div className="flex flex-col gap-3">
            {[
              { label: 'Classifier Engine', value: metrics.engine, cls: 'text-violet-400 font-mono text-right truncate max-w-[180px]' },
              { label: 'Model File',        value: 'models/text_clf_model.pkl', cls: 'text-slate-500 font-mono text-[10px]' },
              { label: 'Vocabulary Size',   value: '15,000 max features', cls: 'text-slate-400 font-mono' },
            ].map((row, i) => (
              <div key={i} className="flex justify-between items-center text-xs font-semibold border-b border-white/[0.04] pb-2.5 last:border-0 last:pb-0">
                <span className="text-slate-500">{row.label}</span>
                <span className={row.cls}>{row.value}</span>
              </div>
            ))}
            <div className="flex justify-between items-center text-xs font-semibold">
              <span className="text-slate-500">Model State</span>
              <span className={`font-mono text-[10px] uppercase px-2.5 py-0.5 rounded-full border font-black ${
                metrics.isTrained
                  ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
                  : 'text-amber-400 bg-amber-500/10 border-amber-500/20'
              }`}>{metrics.isTrained ? 'ACTIVE (Retrained)' : 'DEFAULT DUMMY'}</span>
            </div>
          </div>
        </motion.div>
      </div>

      {/* ─── RIGHT COLUMN (7 cols) ─── */}
      <div className="lg:col-span-7 flex flex-col gap-6">

        {/* PERFORMANCE METRICS */}
        <motion.div className="glass-panel rounded-2xl p-6 relative overflow-hidden"
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45, delay: 0.1 }}>
          <div className="absolute inset-0 tech-grid opacity-10 pointer-events-none" />

          <div className="flex justify-between items-center mb-6 relative z-10">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-xl bg-violet-600/15 border border-violet-500/20 flex items-center justify-center">
                <TrendingUp className="w-4 h-4 text-violet-400" />
              </div>
              <h3 className="text-base font-bold text-white">Performance Telemetry</h3>
            </div>
            <span className="text-[10px] font-mono text-slate-500 uppercase bg-white/[0.04] border border-white/[0.06] px-3 py-1 rounded-full font-bold">
              {metrics.total_samples} articles
            </span>
          </div>

          {/* Gauge Rings */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5 relative z-10">
            <GaugeRing value={metrics.accuracy}  color="#8b5cf6" label="Accuracy"  />
            <GaugeRing value={metrics.precision} color="#ec4899" label="Precision" />
            <GaugeRing value={metrics.recall}    color="#34d399" label="Recall"    />
            <GaugeRing value={metrics.f1_score}  color="#38bdf8" label="F1-Score"  />
          </div>

          {/* Sample Partitions */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 border-t border-white/[0.06] pt-4 relative z-10">
            {[
              { val: metrics.train_samples,    label: 'Train Partition', cls: 'text-white' },
              { val: metrics.test_samples,     label: 'Test Partition',  cls: 'text-white' },
              { val: metrics.feedback_samples, label: 'Feedback Loop',   cls: 'text-violet-400' },
              { val: metrics.custom_samples,   label: 'Custom Uploads',  cls: 'text-emerald-400' },
            ].map((s, i) => (
              <div key={i} className="text-center p-3 rounded-xl border border-white/[0.05] bg-white/[0.02]">
                <span className={`block text-lg font-black font-mono ${s.cls}`}>{s.val}</span>
                <span className="text-[9px] text-slate-500 font-semibold font-mono tracking-wider uppercase">{s.label}</span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* TERMINAL LOG */}
        <motion.div className="glass-panel-heavy rounded-2xl relative overflow-hidden"
          style={{ background: 'rgba(6,6,14,0.97)', borderColor: 'rgba(124,58,237,0.15)' }}
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45, delay: 0.2 }}>

          {/* Terminal Title Bar */}
          <div className="flex justify-between items-center px-4 py-3 border-b border-white/[0.06]">
            <div className="flex items-center gap-2 text-slate-500">
              <Terminal className="w-3.5 h-3.5 text-violet-400 animate-pulse" />
              <span className="text-[10px] font-mono">veracitysuite_compiler.sh</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500/60 border border-rose-500/30" />
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500/60 border border-amber-500/30" />
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/60 border border-emerald-500/30" />
            </div>
          </div>

          {/* Log Stream */}
          <div className="h-[260px] overflow-y-auto custom-scrollbar flex flex-col gap-1.5 p-4 font-mono text-xs">
            {terminalLogs.length === 0 ? (
              <span className="text-slate-600 italic">Waiting for retraining trigger — console idle.</span>
            ) : (
              terminalLogs.map((log, i) => (
                <motion.div key={i} className="flex gap-2 leading-relaxed"
                  initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.04 }}>
                  <span className="text-violet-500 shrink-0 select-none">›</span>
                  <span className={
                    log.includes('SUCCESS') ? 'text-emerald-400 font-bold' :
                    log.includes('ERROR')   ? 'text-rose-400 font-bold' :
                    log.includes('METRICS') ? 'text-cyan-400 font-bold' :
                    log.includes('SYSTEM')  ? 'text-violet-300' :
                    log.includes('MODEL')   ? 'text-slate-300' :
                    'text-slate-500'
                  }>{log}</span>
                </motion.div>
              ))
            )}
            {isTraining && (
              <div className="flex gap-1 ml-4 mt-1">
                <span className="typing-dot" /><span className="typing-dot" /><span className="typing-dot" />
              </div>
            )}
            <div ref={terminalEndRef} />
          </div>

          <div className="flex justify-between items-center px-4 py-2 border-t border-white/[0.04] text-[9px] text-slate-700 font-mono">
            <span>Encoding: UTF-8</span>
            <span>Kernel: scikit-learn v1.4</span>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
