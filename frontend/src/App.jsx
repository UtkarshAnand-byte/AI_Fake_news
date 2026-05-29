import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sun, Moon, Brain, ShieldAlert, Sparkles, BookOpen,
  HelpCircle, Mail, Heart, FileText, CheckCircle,
  Terminal, Send, RefreshCw, Zap, Globe,
  BarChart3, Shield, ArrowRight, ChevronRight, X
} from 'lucide-react';
import CanvasNetwork from './components/CanvasNetwork';
import Dashboard from './components/Dashboard';
import TrainingCenter from './components/TrainingCenter';

const NAV_ITEMS = [
  { id: 'home',    label: 'Analyzer' },
  { id: 'train',   label: 'Training' },
  { id: 'about',   label: 'About' },
  { id: 'works',   label: 'How It Works' },
  { id: 'blog',    label: 'Blog' },
  { id: 'contact', label: 'Contact' },
];

const HERO_STATS = [
  { icon: BarChart3, label: 'Accuracy',    value: '94.2%',     color: 'text-violet-400', bg: 'bg-violet-500/10', border: 'border-violet-500/20' },
  { icon: Zap,       label: 'Latency',     value: '<150ms',    color: 'text-cyan-400',   bg: 'bg-cyan-500/10',   border: 'border-cyan-500/20' },
  { icon: Globe,     label: 'Verification',value: 'Live Web',  color: 'text-emerald-400',bg: 'bg-emerald-500/10',border: 'border-emerald-500/20' },
  { icon: Shield,    label: 'Engines',     value: 'Dual AI',   color: 'text-rose-400',   bg: 'bg-rose-500/10',   border: 'border-rose-500/20' },
];

export default function App() {
  const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
  const [isDarkMode,     setIsDarkMode]     = useState(true);
  const [activeTab,      setActiveTab]      = useState('home');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [contactName,    setContactName]    = useState('');
  const [contactEmail,   setContactEmail]   = useState('');
  const [contactMsg,     setContactMsg]     = useState('');
  const [contactSent,    setContactSent]    = useState(false);

  useEffect(() => {
    const root = window.document.documentElement;
    if (isDarkMode) root.classList.add('dark');
    else root.classList.remove('dark');
  }, [isDarkMode]);

  const handleContactSubmit = (e) => {
    e.preventDefault();
    if (!contactName || !contactEmail || !contactMsg) return;
    setContactSent(true);
    setTimeout(() => {
      setContactName(''); setContactEmail(''); setContactMsg(''); setContactSent(false);
    }, 2200);
  };

  return (
    <div className={`min-h-screen relative overflow-hidden transition-colors duration-500 ${
      isDarkMode ? 'dark bg-[#06060e] text-slate-100' : 'bg-[#f0f2f8] text-slate-900'
    }`}>

      {/* ── Aurora Background ── */}
      <div className="aurora-bg">
        <div className="aurora-orb aurora-orb-1" />
        <div className="aurora-orb aurora-orb-2" />
        <div className="aurora-orb aurora-orb-3" />
      </div>

      {/* ── Noise Texture ── */}
      <div className="noise-overlay" />

      {/* ── Canvas Particle Network ── */}
      <CanvasNetwork isDarkMode={isDarkMode} />

      {/* ── Grid ── */}
      <div className="absolute inset-0 tech-grid pointer-events-none z-0" />

      {/* ══════════════════════════════
          NAVBAR
         ══════════════════════════════ */}
      <header className="sticky top-0 z-50 w-full glass-nav">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-[58px] flex items-center justify-between">

          {/* Logo */}
          <div onClick={() => setActiveTab('home')}
            className="flex items-center gap-2.5 cursor-pointer group select-none">
            <div className="relative w-8 h-8 rounded-xl bg-gradient-to-br from-violet-600 to-violet-900 flex items-center justify-center shadow-glow-accent group-hover:shadow-[0_0_24px_rgba(124,58,237,0.6)] transition-all duration-200">
              <Brain className="w-[18px] h-[18px] text-white" />
              <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-emerald-400 border-2 border-[#06060e]" />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="font-black text-[15px] tracking-tight text-white">VeracitySuite</span>
              {isLocalhost ? (
                <span className="text-[9px] font-bold font-mono tracking-widest text-emerald-400 border border-emerald-500/25 bg-emerald-500/10 px-1.5 py-0.5 rounded-full animate-pulse">DEV sandbox</span>
              ) : (
                <span className="text-[9px] font-bold font-mono tracking-widest text-violet-400/70 border border-violet-500/25 bg-violet-500/10 px-1.5 py-0.5 rounded-full">v1.2</span>
              )}
            </div>
          </div>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center gap-0.5">
            {NAV_ITEMS.map((tab) => (
              <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                className={`px-3.5 py-2 rounded-lg text-[13px] font-medium transition-all duration-150 ${
                  activeTab === tab.id
                    ? 'bg-violet-600/15 text-violet-300 border border-violet-500/20'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.05]'
                }`}>
                {tab.label}
              </button>
            ))}
          </nav>

          {/* Right Controls */}
          <div className="flex items-center gap-2">
            <button onClick={() => setIsDarkMode(!isDarkMode)}
              className="w-9 h-9 rounded-lg flex items-center justify-center text-slate-500 hover:text-slate-200 hover:bg-white/[0.06] border border-transparent hover:border-white/[0.08] transition-all">
              {isDarkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>
            <button onClick={() => setActiveTab('home')}
              className="hidden sm:flex btn-primary text-xs px-4 py-2 rounded-lg">
              <Sparkles className="w-3.5 h-3.5" />
              Analyze Now
            </button>
            <button onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden w-9 h-9 rounded-lg flex items-center justify-center text-slate-400 hover:bg-white/[0.05]">
              {mobileMenuOpen ? <X className="w-4 h-4" /> : (
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Mobile Menu */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            className="fixed inset-x-0 top-[58px] z-40 md:hidden glass-nav border-b border-white/[0.06] p-3 flex flex-col gap-1"
            initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
          >
            {NAV_ITEMS.map((tab) => (
              <button key={tab.id}
                onClick={() => { setActiveTab(tab.id); setMobileMenuOpen(false); }}
                className={`w-full py-2.5 px-3.5 rounded-lg text-left text-sm font-medium transition-all ${
                  activeTab === tab.id ? 'bg-violet-600/15 text-violet-300' : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
                }`}>
                {tab.label}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* ══════════════════════════════
          MAIN CONTENT
         ══════════════════════════════ */}
      <main className="relative z-10">
        <AnimatePresence mode="wait">

          {/* ── HOME / ANALYZER ── */}
          {activeTab === 'home' && (
            <motion.div key="home"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}>

              {/* HERO SECTION */}
              <section className="relative w-full max-w-5xl mx-auto px-4 pt-20 pb-10 text-center flex flex-col items-center">

                {/* Badge */}
                <motion.div className="badge-accent mb-5"
                  initial={{ opacity: 0, y: -12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
                  <Zap className="w-3 h-3" />
                  Dual-Engine AI · Live Web Verification · Real-time Training
                </motion.div>

                {/* Headline */}
                <motion.h1
                  className="text-5xl sm:text-6xl lg:text-7xl font-black tracking-tight leading-[1.05] mb-6"
                  initial={{ opacity: 0, y: 22 }} animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.55, delay: 0.15 }}>
                  <span className="text-white">Detect Fake News</span>
                  <br />
                  <span className="gradient-text-hero">with Cognitive AI</span>
                </motion.h1>

                {/* Subheading */}
                <motion.p
                  className="text-[15px] sm:text-base text-slate-400 max-w-xl leading-relaxed mb-8 font-medium"
                  initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: 0.25 }}>
                  Verify headlines and articles in seconds. Our dual cognitive-syntactic models analyze semantic triggers,
                  emotional bias, and live web cross-references to defend truth with precision.
                </motion.p>

                {/* CTAs */}
                <motion.div className="flex flex-wrap items-center justify-center gap-3 mb-14"
                  initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: 0.33 }}>
                  <a href="#sandbox-anchor"
                    onClick={(e) => { e.preventDefault(); document.getElementById('sandbox-anchor')?.scrollIntoView({ behavior: 'smooth' }); }}
                    className="btn-primary">
                    <Sparkles className="w-4 h-4" />
                    Start Analyzing
                  </a>
                  <button onClick={() => setActiveTab('works')} className="btn-ghost">
                    How It Works <ChevronRight className="w-4 h-4" />
                  </button>
                </motion.div>

                {/* STATS ROW */}
                <motion.div className="grid grid-cols-2 sm:grid-cols-4 gap-3 w-full max-w-2xl"
                  initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: 0.42 }}>
                  {HERO_STATS.map((stat, i) => (
                    <div key={i} className={`stat-card text-center flex flex-col items-center`}>
                      <div className={`w-8 h-8 rounded-lg ${stat.bg} border ${stat.border} flex items-center justify-center mb-2`}>
                        <stat.icon className={`w-4 h-4 ${stat.color}`} />
                      </div>
                      <div className={`text-lg font-black font-mono ${stat.color} leading-none mb-0.5`}>{stat.value}</div>
                      <div className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider">{stat.label}</div>
                    </div>
                  ))}
                </motion.div>
              </section>

              {/* Divider */}
              <div className="w-full max-w-7xl mx-auto px-4 mb-4">
                <div className="h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
              </div>

              {/* DASHBOARD */}
              <div id="sandbox-anchor" className="w-full">
                <Dashboard />
              </div>
            </motion.div>
          )}

          {/* ── TRAINING ── */}
          {activeTab === 'train' && (
            <motion.div key="train"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.3 }}>
              <TrainingCenter />
            </motion.div>
          )}

          {/* ── ABOUT ── */}
          {activeTab === 'about' && (
            <motion.div key="about"
              initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
              className="max-w-4xl mx-auto px-4 py-16">
              <div className="text-center mb-12">
                <div className="badge-accent mx-auto w-fit mb-5"><Brain className="w-3 h-3" /> Model Architecture</div>
                <h2 className="text-4xl sm:text-5xl font-black tracking-tight text-white mb-3">
                  About the <span className="gradient-text-primary">Cognitive Engine</span>
                </h2>
                <p className="text-sm text-slate-400 max-w-xl mx-auto leading-relaxed">
                  VeracitySuite uses a dual-engine approach combining trained linguistic classifiers with live cognitive AI analysis for maximum verification accuracy.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-6">
                {[
                  { icon: Terminal, iconColor: 'text-violet-400', bg: 'bg-violet-600/12', border: 'border-violet-500/18',
                    title: 'Supervised Linguistic Classification',
                    desc: 'The core engine uses TF-IDF vectorizers to process text against thousands of labeled real and fake articles, applying weights via Logistic Regression classifiers.',
                    badge: 'models/text_clf_model.pkl', badgeColor: 'text-violet-400 bg-violet-500/10 border-violet-500/20' },
                  { icon: CheckCircle, iconColor: 'text-emerald-400', bg: 'bg-emerald-600/12', border: 'border-emerald-500/18',
                    title: 'Fallback Syntactic Telemetry',
                    desc: 'If pre-trained weights are absent, VeracitySuite hot-swaps to a Linguistic Heuristic Analyzer computing emotional intensity, capitalization patterns, and sensationalist vocabulary.',
                    badge: 'Status: Online (Auto hot-swap)', badgeColor: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' },
                ].map((card, i) => (
                  <motion.div key={i} className={`glass-panel rounded-2xl p-6 ${card.border}`}
                    initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}>
                    <div className={`w-11 h-11 rounded-xl ${card.bg} border ${card.border} flex items-center justify-center mb-4`}>
                      <card.icon className={`w-5 h-5 ${card.iconColor}`} />
                    </div>
                    <h3 className="text-base font-bold text-white mb-2">{card.title}</h3>
                    <p className="text-xs text-slate-400 leading-relaxed mb-4">{card.desc}</p>
                    <code className={`text-[10px] font-mono px-3 py-1.5 rounded-lg inline-block border ${card.badgeColor}`}>{card.badge}</code>
                  </motion.div>
                ))}
              </div>

              <div className="glass-panel rounded-2xl p-6">
                <h3 className="text-sm font-bold text-white mb-5 flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-violet-400" /> Model Specifications
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
                  {[['94.2%','Accuracy'],['<150ms','Inference'],['TF-IDF','Vectorizer'],['LogReg','Classifier']].map(([v,l], i) => (
                    <div key={i} className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.06]">
                      <span className="block text-xl font-black text-violet-400 font-mono">{v}</span>
                      <span className="text-[10px] text-slate-500 uppercase font-semibold tracking-wider">{l}</span>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}

          {/* ── HOW IT WORKS ── */}
          {activeTab === 'works' && (
            <motion.div key="works"
              initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
              className="max-w-3xl mx-auto px-4 py-16">
              <div className="text-center mb-12">
                <div className="badge-accent mx-auto w-fit mb-5"><HelpCircle className="w-3 h-3" /> Pipeline Overview</div>
                <h2 className="text-4xl sm:text-5xl font-black tracking-tight text-white mb-3">
                  How the <span className="gradient-text-primary">Analytics Pipeline</span> Operates
                </h2>
                <p className="text-sm text-slate-400 max-w-lg mx-auto">
                  A four-step computational journey from raw news paragraphs to visual telemetry reports.
                </p>
              </div>

              <div className="flex flex-col gap-4">
                {[
                  { num:'01', title:'Corpus Ingestion & Parsing', color:'violet',
                    desc:'Users paste text or upload .txt / .pdf files. For PDFs, the server uses a stream reader to extract page-by-page strings, filtering structural tags into a unified payload.' },
                  { num:'02', title:'Text Preprocessing & Tokenization', color:'cyan',
                    desc:'The raw payload enters the cleaning block. Capital letters normalize, HTML/links remove, and punctuation vectorizes to prepare a clean word array for mathematical assessment.' },
                  { num:'03', title:'Multi-Dimensional Feature Synthesis', color:'emerald',
                    desc:'The engine calculates sensationalist trigger matching, emotional bias lexicon density, aggressive formatting scores, and lexical variety profiles.' },
                  { num:'04', title:'Neural Scoring & Live Verification', color:'rose',
                    desc:'Vector payloads project onto model coefficients. Live web search cross-references verify claims against indexed global news. Returns verdict, confidence, and detailed diagnostic bullets.' },
                ].map((step, i) => {
                  const cols = { violet:'bg-violet-600/18 text-violet-400 border-violet-500/25', cyan:'bg-cyan-600/18 text-cyan-400 border-cyan-500/25', emerald:'bg-emerald-600/18 text-emerald-400 border-emerald-500/25', rose:'bg-rose-600/18 text-rose-400 border-rose-500/25' };
                  return (
                    <motion.div key={i} className="glass-panel rounded-2xl p-5 flex gap-4 items-start"
                      initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.1 }}>
                      <div className={`shrink-0 w-10 h-10 rounded-xl flex items-center justify-center font-black text-sm font-mono border ${cols[step.color]}`}>{step.num}</div>
                      <div>
                        <h3 className="text-sm font-bold text-white mb-1">{step.title}</h3>
                        <p className="text-xs text-slate-400 leading-relaxed">{step.desc}</p>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </motion.div>
          )}

          {/* ── BLOG ── */}
          {activeTab === 'blog' && (
            <motion.div key="blog"
              initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
              className="max-w-5xl mx-auto px-4 py-16">
              <div className="text-center mb-12">
                <div className="badge-accent mx-auto w-fit mb-5"><BookOpen className="w-3 h-3" /> Awareness Blog</div>
                <h2 className="text-4xl sm:text-5xl font-black tracking-tight text-white mb-3">
                  News Awareness &amp; <span className="gradient-text-primary">Fact-Checking</span>
                </h2>
                <p className="text-sm text-slate-400 max-w-lg mx-auto">
                  Arm yourself with modern fact-checking frameworks and explore how algorithms operate in the digital news stream.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                {[
                  { icon: ShieldAlert, color:'text-rose-400', grad:'from-rose-950/70 via-slate-950 to-[#06060e]',
                    tag:'Heuristics', tagCls:'text-rose-400 bg-rose-500/10 border-rose-500/20',
                    title:'Spotting the Red Flags: Clickbait and Formatting',
                    desc:'Sensationalized writing uses emotional exclamation and loaded terms like "Exposed" or "Conspiracy." Learn to identify alarmist formatting styles that signal disinformation.' },
                  { icon: Brain, color:'text-violet-400', grad:'from-violet-950/70 via-slate-950 to-[#06060e]',
                    tag:'Cognitive Research', tagCls:'text-violet-400 bg-violet-500/10 border-violet-500/20',
                    title:'The Evolution of Automated Systems and Deepfake Reports',
                    desc:'With automated tools drafting thousands of customized stories instantly, deepfakes are expanding. Understand how verification models inspect source signatures.' },
                  { icon: FileText, color:'text-emerald-400', grad:'from-emerald-950/70 via-slate-950 to-[#06060e]',
                    tag:'Fact-Checking', tagCls:'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
                    title:'Verify Like a Pro: 3 Frameworks for Daily Reading',
                    desc:'Citing institutions, tracking original study domains, and comparing cross-referenced testimonies can insulate you from corporate or individual propaganda.' },
                ].map((post, i) => (
                  <motion.div key={i} className="glass-panel rounded-2xl overflow-hidden group hover:border-white/14 transition-all duration-300"
                    initial={{ opacity: 0, y: 22 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}>
                    <div className={`h-40 bg-gradient-to-br ${post.grad} flex items-center justify-center relative`}>
                      <post.icon className={`w-10 h-10 ${post.color}`} />
                      <span className={`absolute bottom-3 left-3 text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded border ${post.tagCls}`}>{post.tag}</span>
                    </div>
                    <div className="p-5">
                      <h3 className="font-bold text-sm text-white mb-2 leading-snug group-hover:text-violet-300 transition-colors">{post.title}</h3>
                      <p className="text-xs text-slate-400 leading-relaxed mb-4">{post.desc}</p>
                      <span className="text-[10px] font-bold text-violet-400 font-mono uppercase flex items-center gap-1 cursor-pointer hover:underline">
                        Read Blueprint <ArrowRight className="w-3 h-3" />
                      </span>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          {/* ── CONTACT ── */}
          {activeTab === 'contact' && (
            <motion.div key="contact"
              initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
              className="max-w-lg mx-auto px-4 py-16">
              <div className="text-center mb-8">
                <div className="badge-accent mx-auto w-fit mb-5"><Mail className="w-3 h-3" /> Reach Out</div>
                <h2 className="text-4xl font-black text-white mb-2">Get in <span className="gradient-text-primary">Touch</span></h2>
                <p className="text-sm text-slate-400">For licensing, API access, or research integrations.</p>
              </div>

              <div className="glass-panel rounded-2xl p-6">
                {contactSent ? (
                  <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
                    className="text-center py-10 flex flex-col items-center gap-3">
                    <div className="relative w-16 h-16 flex items-center justify-center">
                      <div className="absolute inset-0 rounded-2xl bg-emerald-500/15 border border-emerald-500/25 pulse-ring" />
                      <div className="w-16 h-16 rounded-2xl bg-emerald-500/15 border border-emerald-500/25 flex items-center justify-center">
                        <CheckCircle className="w-7 h-7 text-emerald-400" />
                      </div>
                    </div>
                    <h3 className="text-base font-bold text-white">Message Sent!</h3>
                    <p className="text-xs text-slate-400">Your inquiry has been routed to the VeracitySuite team.</p>
                  </motion.div>
                ) : (
                  <form onSubmit={handleContactSubmit} className="flex flex-col gap-4">
                    {[
                      { label:'Name / Institution', type:'text', val:contactName, set:setContactName, ph:'e.g. Stanford Journalism Lab' },
                      { label:'Email Address',      type:'email', val:contactEmail, set:setContactEmail, ph:'e.g. verify@lab.edu' },
                    ].map((f, i) => (
                      <div key={i} className="flex flex-col gap-1.5">
                        <label className="text-[11px] font-bold text-slate-500 uppercase font-mono tracking-wider">{f.label}</label>
                        <input type={f.type} value={f.val} onChange={(e) => f.set(e.target.value)} placeholder={f.ph} required
                          className="w-full px-3.5 py-2.5 bg-white/[0.04] border border-white/[0.08] rounded-xl text-sm text-white placeholder-slate-600 focus-neon transition-all" />
                      </div>
                    ))}
                    <div className="flex flex-col gap-1.5">
                      <label className="text-[11px] font-bold text-slate-500 uppercase font-mono tracking-wider">Inquiry Details</label>
                      <textarea rows={4} value={contactMsg} onChange={(e) => setContactMsg(e.target.value)}
                        placeholder="Provide specifications of your research or integration requirements..."
                        required className="w-full px-3.5 py-2.5 bg-white/[0.04] border border-white/[0.08] rounded-xl text-sm text-white placeholder-slate-600 resize-none focus-neon transition-all" />
                    </div>
                    <button type="submit" className="btn-primary w-full justify-center mt-1">
                      <Send className="w-4 h-4" /> Submit Inquiry
                    </button>
                  </form>
                )}
              </div>
            </motion.div>
          )}

        </AnimatePresence>
      </main>

      {/* ══════════════════════════════
          FOOTER
         ══════════════════════════════ */}
      <footer className="relative z-10 border-t border-white/[0.06] py-8 mt-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row justify-between items-center gap-4">

          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-violet-600 to-violet-900 flex items-center justify-center">
              <Brain className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="font-black text-sm text-white">VeracitySuite</span>
          </div>

          <p className="text-xs text-slate-600 flex items-center gap-1.5">
            Built for misinformation audit &amp; truth defense.
            <span>·</span> Made with <Heart className="w-3 h-3 text-rose-500/70" /> precision.
          </p>

          <div className="flex items-center gap-2">
            {[
              <svg key="gh" className="w-4 h-4 fill-current" viewBox="0 0 24 24"><path d="M12 2A10 10 0 0 0 2 12c0 4.42 2.87 8.17 6.84 9.5.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34-.46-1.16-1.11-1.47-1.11-1.47-.9-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.9 1.52 2.34 1.07 2.91.83.09-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.92 0-1.11.38-2 1.03-2.71-.1-.25-.45-1.29.1-2.64 0 0 .84-.27 2.75 1.02.79-.22 1.65-.33 2.5-.33.85 0 1.71.11 2.5.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.35.2 2.39.1 2.64.65.71 1.03 1.6 1.03 2.71 0 3.82-2.34 4.66-4.57 4.91.36.31.69.92.69 1.85V21c0 .27.16.59.67.5C19.14 20.16 22 16.42 22 12A10 10 0 0 0 12 2z"/></svg>,
              <svg key="x" className="w-4 h-4 fill-current" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>,
            ].map((icon, i) => (
              <a key={i} href="#" className="w-8 h-8 rounded-lg bg-white/[0.04] border border-white/[0.06] flex items-center justify-center text-slate-600 hover:text-violet-400 hover:border-violet-500/30 transition-all">
                {icon}
              </a>
            ))}
          </div>
        </div>
      </footer>
    </div>
  );
}
