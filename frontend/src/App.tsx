import React, { useState, useEffect, useRef } from 'react';
import {
  Sparkles,
  Play,
  Pause,
  RotateCcw,
  Download,
  Settings2,
  FileText,
  AlertTriangle,
  Clock,
  Layers,
  ChevronDown,
  ChevronUp,
  Headphones,
  ShieldCheck,
  Wand2,
  ListOrdered,
  Upload,
  Trash2,
  PanelLeftClose,
  PanelLeft,
  X,
  Volume2,
  Activity,
  Star,
  Check
} from 'lucide-react';

interface VoiceProfile {
  voice_id: string;
  name: string;
  gender: string;
  language: string;
  locale: string;
  style: string;
  provider: string;
  description: string;
  qc_rating: number;
}

interface RankedVoice {
  voice: VoiceProfile;
  confidence: number;
  reason: string;
}

interface ChunkPlan {
  id?: string;
  chunk_index: number;
  text: string;
  spoken_text?: string;
  normalized_text?: string;
  emotion: string;
  speed: number;
  pitch: string;
  rate: string;
  pause_before_ms: number;
  pause_after_ms: number;
  audio_path?: string;
  audio_file?: string;
  duration: number;
  start_time: number;
  end_time: number;
  qc_status?: string;
  qc_pass?: boolean;
  qc_message?: string;
}

interface ProjectRecord {
  id: string;
  title: string;
  raw_input: string;
  status: string;
  language: string;
  voice_name?: string;
  voice_id?: string;
  style?: string;
  emotion?: string;
  progress_percentage: number;
  current_step_description: string;
  total_duration_seconds: number;
  final_audio_mp3?: string;
  final_audio_wav?: string;
  final_srt?: string;
  final_vtt?: string;
  final_timings_json?: string;
  error_message?: string;
  created_at?: string;
  chunks?: ChunkPlan[];
}

export default function App() {
  // Navigation tabs: 'composer' | 'voices' | 'settings'
  const [activeTab, setActiveTab] = useState<'composer' | 'voices' | 'settings'>('composer');
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(true);

  // Script composer state
  const [scriptText, setScriptText] = useState<string>(
    "In 1944 during WWII, the B-25 bomber vanished over the misty mountains. Suddenly, the radio crackled with a mysterious signal."
  );
  const [selectedVoice, setSelectedVoice] = useState<string>("auto");
  const [stylePreference, setStylePreference] = useState<string>("Cinematic");
  const [emotionMode, setEmotionMode] = useState<string>("auto");
  const [languageHint, setLanguageHint] = useState<string>("auto");
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);
  const [enableMastering, setEnableMastering] = useState<boolean>(true);

  // Data from backend
  const [voices, setVoices] = useState<RankedVoice[]>([]);
  const [projectsHistory, setProjectsHistory] = useState<ProjectRecord[]>([]);
  const [activeProject, setActiveProject] = useState<ProjectRecord | null>(null);
  const [favoriteVoices, setFavoriteVoices] = useState<string[]>(['vox-cinematic-male']);
  const [pronunciations, setPronunciations] = useState<Record<string, string>>({});
  const [newWord, setNewWord] = useState<string>("");
  const [newReplacement, setNewReplacement] = useState<string>("");

  // Generation state
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [progressPct, setProgressPct] = useState<number>(0);
  const [progressMsg, setProgressMsg] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Audio Player State
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const chunkAudioRef = useRef<HTMLAudioElement | null>(null);
  const previewAudioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [currentTime, setCurrentTime] = useState<number>(0);
  const [audioDuration, setAudioDuration] = useState<number>(0);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1.0);
  const [volume, setVolume] = useState<number>(1.0);
  const [playingChunkIdx, setPlayingChunkIdx] = useState<number | null>(null);
  const [redoingChunkIdx, setRedoingChunkIdx] = useState<number | null>(null);
  const [previewingVoiceId, setPreviewingVoiceId] = useState<string | null>(null);

  // Health modal
  const [showHealthModal, setShowHealthModal] = useState<boolean>(false);
  const [healthStatus, setHealthStatus] = useState<any>(null);

  // On mount
  useEffect(() => {
    loadVoices();
    loadProjects();
    loadPronunciations();
  }, []);

  const loadVoices = async () => {
    try {
      const res = await fetch('/api/voices');
      if (res.ok) {
        const data = await res.json();
        setVoices(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const loadProjects = async () => {
    try {
      const res = await fetch('/api/projects');
      if (res.ok) {
        const data = await res.json();
        setProjectsHistory(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const loadPronunciations = async () => {
    try {
      const res = await fetch('/api/pronunciations');
      if (res.ok) {
        const data = await res.json();
        setPronunciations(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const checkHealth = async () => {
    try {
      const res = await fetch('/api/health');
      if (res.ok) {
        const data = await res.json();
        setHealthStatus(data);
        setShowHealthModal(true);
      }
    } catch (e) {
      alert("Failed to reach health endpoint");
    }
  };

  // Drag and Drop & File Upload
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        if (event.target?.result) {
          setScriptText(event.target.result as string);
        }
      };
      reader.readAsText(file);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        if (event.target?.result) {
          setScriptText(event.target.result as string);
        }
      };
      reader.readAsText(file);
    }
  };

  // Keyboard shortcut Ctrl+Enter to generate
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      handleGenerate();
    }
  };

  // Start Generation
  const handleGenerate = async () => {
    if (!scriptText.trim() || isGenerating) return;
    setErrorMessage(null);
    setIsGenerating(true);
    setProgressPct(10);
    setProgressMsg("Analyzing your script...");

    try {
      // 1. Create project first
      const createRes = await fetch('/api/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: scriptText,
          voice_id: selectedVoice,
          style_preference: stylePreference,
          emotion_mode: emotionMode,
          language_hint: languageHint
        })
      });
      if (!createRes.ok) throw new Error("Failed to initialize project.");
      const proj: ProjectRecord = await createRes.json();
      setActiveProject(proj);

      // 2. Trigger generation
      setProgressPct(25);
      setProgressMsg("Planning narration & breath pacing ✓");

      const genRes = await fetch(`/api/projects/${proj.id}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: scriptText,
          voice_id: selectedVoice,
          style_preference: stylePreference,
          emotion_mode: emotionMode,
          language_hint: languageHint,
          enable_audio_mastering: enableMastering
        })
      });

      if (!genRes.ok) {
        const errText = await genRes.text();
        throw new Error(errText);
      }

      const completedProject: ProjectRecord = await genRes.json();
      setActiveProject(completedProject);
      setIsGenerating(false);
      setProgressPct(100);
      setProgressMsg("Ready ✓");
      loadProjects();

      // Autoload audio
      if (audioRef.current && completedProject.id) {
        audioRef.current.src = `/api/projects/${completedProject.id}/audio?format=mp3&t=${Date.now()}`;
        audioRef.current.load();
      }
    } catch (err: any) {
      setErrorMessage(err.message || "We couldn't generate this voice. Please try again.");
      setIsGenerating(false);
    }
  };

  // Cancel Generation
  const handleCancel = async () => {
    if (activeProject?.id) {
      await fetch(`/api/projects/${activeProject.id}/cancel`, { method: 'POST' });
      setIsGenerating(false);
      setProgressMsg("Generation cancelled");
    }
  };

  // Line-by-Line Redo
  const handleRedoChunk = async (chunkIndex: number) => {
    if (!activeProject?.id) return;
    setRedoingChunkIdx(chunkIndex);
    try {
      const res = await fetch(`/api/projects/${activeProject.id}/chunks/${chunkIndex}/redo`, {
        method: 'POST'
      });
      if (!res.ok) throw new Error("Failed to redo chunk.");
      const updated: ProjectRecord = await res.json();
      setActiveProject(updated);

      if (audioRef.current && updated.id) {
        audioRef.current.src = `/api/projects/${updated.id}/audio?format=mp3&t=${Date.now()}`;
        audioRef.current.load();
      }
    } catch (e: any) {
      alert("Chunk redo error: " + e.message);
    } finally {
      setRedoingChunkIdx(null);
    }
  };

  // Play single chunk snippet
  const playChunkSnippet = (chunk: ChunkPlan) => {
    const audioPath = chunk.audio_path || chunk.audio_file;
    if (!audioPath) return;
    if (chunkAudioRef.current) {
      chunkAudioRef.current.src = `/api/audio/stream?path=${encodeURIComponent(audioPath)}`;
      chunkAudioRef.current.play();
      setPlayingChunkIdx(chunk.chunk_index);
      chunkAudioRef.current.onended = () => setPlayingChunkIdx(null);
    }
  };

  // Play voice sample preview
  const playVoicePreview = async (voiceId: string) => {
    if (previewAudioRef.current) {
      setPreviewingVoiceId(voiceId);
      previewAudioRef.current.src = `/api/voices/${voiceId}/preview`;
      previewAudioRef.current.play();
      previewAudioRef.current.onended = () => setPreviewingVoiceId(null);
    }
  };

  // Master audio controls
  const togglePlayMaster = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play();
      setIsPlaying(true);
    }
  };

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
      setAudioDuration(audioRef.current.duration || 0);
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseFloat(e.target.value);
    if (audioRef.current) {
      audioRef.current.currentTime = val;
      setCurrentTime(val);
    }
  };

  const changeSpeed = (speed: number) => {
    setPlaybackSpeed(speed);
    if (audioRef.current) {
      audioRef.current.playbackRate = speed;
    }
  };

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = parseFloat(e.target.value);
    setVolume(v);
    if (audioRef.current) {
      audioRef.current.volume = v;
    }
  };

  // Pronunciation Add & Delete
  const handleAddPronunciation = async () => {
    if (newWord && newReplacement) {
      await fetch('/api/pronunciations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ word: newWord, replacement: newReplacement })
      });
      setPronunciations(prev => ({ ...prev, [newWord]: newReplacement }));
      setNewWord("");
      setNewReplacement("");
    }
  };

  const handleDeletePronunciation = async (w: string) => {
    await fetch(`/api/pronunciations/${w}`, { method: 'DELETE' });
    setPronunciations(prev => {
      const copy = { ...prev };
      delete copy[w];
      return copy;
    });
  };

  // Calculations
  const wordCount = scriptText.trim() ? scriptText.trim().split(/\s+/).length : 0;
  const charCount = scriptText.length;
  // Estimated duration: ~150 words per minute = 2.5 words/sec
  const estimatedSeconds = Math.round(wordCount / 2.5);

  const formatTime = (secs: number) => {
    if (isNaN(secs)) return "00:00";
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="flex h-screen w-screen bg-[#fcfcfd] text-[#111827] overflow-hidden font-sans">
      <audio
        ref={audioRef}
        onTimeUpdate={handleTimeUpdate}
        onEnded={() => setIsPlaying(false)}
      />
      <audio ref={chunkAudioRef} />
      <audio ref={previewAudioRef} />

      {/* SIDEBAR: Soft grey Claude/ChatGPT Style */}
      <aside
        className={`${
          sidebarOpen ? 'w-64' : 'w-0 -ml-64'
        } bg-[#f9fafb] border-r border-[#e5e7eb] flex flex-col justify-between shrink-0 transition-all duration-300 ease-in-out overflow-hidden z-20`}
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="p-4 border-b border-[#e5e7eb] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-blue-600 text-white flex items-center justify-center shadow-sm">
                <Sparkles className="w-4 h-4" />
              </div>
              <span className="font-semibold text-sm tracking-tight text-gray-900">Aura Voice</span>
            </div>
            <button
              onClick={() => setSidebarOpen(false)}
              className="p-1 text-gray-400 hover:text-gray-700 hover:bg-gray-200 rounded-md transition-all"
            >
              <PanelLeftClose className="w-4 h-4" />
            </button>
          </div>

          {/* New Narration Button */}
          <div className="p-3">
            <button
              onClick={() => {
                setActiveProject(null);
                setScriptText("");
                setActiveTab('composer');
              }}
              className="w-full flex items-center justify-center gap-2 bg-white hover:bg-gray-50 text-gray-800 border border-gray-200 text-xs font-medium py-2 px-3 rounded-lg shadow-sm transition-all"
            >
              <Wand2 className="w-3.5 h-3.5 text-blue-600" />
              + New Narration
            </button>
          </div>

          {/* Navigation Links */}
          <div className="px-3 space-y-1">
            <button
              onClick={() => setActiveTab('composer')}
              className={`w-full flex items-center gap-2 px-3 py-2 text-xs rounded-lg font-medium transition-all ${
                activeTab === 'composer' ? 'bg-gray-200 text-gray-900' : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <FileText className="w-4 h-4 text-gray-500" />
              Narration Studio
            </button>
            <button
              onClick={() => setActiveTab('voices')}
              className={`w-full flex items-center justify-between px-3 py-2 text-xs rounded-lg font-medium transition-all ${
                activeTab === 'voices' ? 'bg-gray-200 text-gray-900' : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <span className="flex items-center gap-2">
                <Headphones className="w-4 h-4 text-gray-500" />
                Voice Catalog
              </span>
              <span className="text-[10px] bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded-full font-mono">
                {voices.length}
              </span>
            </button>
            <button
              onClick={() => setActiveTab('settings')}
              className={`w-full flex items-center gap-2 px-3 py-2 text-xs rounded-lg font-medium transition-all ${
                activeTab === 'settings' ? 'bg-gray-200 text-gray-900' : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <Settings2 className="w-4 h-4 text-gray-500" />
              Settings & Pronunciation
            </button>
          </div>

          {/* Recent Projects List */}
          <div className="mt-4 px-3 flex-1 overflow-y-auto">
            <p className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider px-2 mb-1.5">
              Recent Projects
            </p>
            <div className="space-y-1">
              {projectsHistory.length === 0 ? (
                <p className="text-xs text-gray-400 px-2 py-2 italic">No past projects</p>
              ) : (
                projectsHistory.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => {
                      fetch(`/api/projects/${p.id}`)
                        .then(r => r.json())
                        .then(data => {
                          setActiveProject(data);
                          setActiveTab('composer');
                          if (audioRef.current && data.id) {
                            audioRef.current.src = `/api/projects/${data.id}/audio?format=mp3&t=${Date.now()}`;
                            audioRef.current.load();
                          }
                        });
                    }}
                    className={`w-full text-left px-2.5 py-2 rounded-lg text-xs transition-all flex flex-col gap-0.5 ${
                      activeProject?.id === p.id
                        ? 'bg-blue-50 text-blue-900 border border-blue-200 font-medium'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    <span className="truncate">{p.title || "Untitled Project"}</span>
                    <span className="text-[10px] text-gray-400 flex items-center gap-1.5">
                      <Clock className="w-2.5 h-2.5" />
                      {p.total_duration_seconds ? `${p.total_duration_seconds.toFixed(1)}s` : 'Saved'} • {p.id}
                    </span>
                  </button>
                ))
              )}
            </div>
          </div>

          {/* Bottom Engine Status */}
          <div className="p-3 border-t border-[#e5e7eb] bg-gray-50">
            <button
              onClick={checkHealth}
              className="w-full flex items-center justify-between text-xs text-gray-600 hover:text-gray-900 transition-all"
            >
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                System Health
              </span>
              <Activity className="w-3.5 h-3.5 text-gray-400" />
            </button>
          </div>
        </div>
      </aside>

      {/* MAIN CONTAINER */}
      <main className="flex-1 flex flex-col h-full bg-[#fcfcfd] overflow-y-auto">
        {/* Navbar */}
        <header className="h-14 border-b border-[#e5e7eb] px-6 flex items-center justify-between bg-white sticky top-0 z-10">
          <div className="flex items-center gap-3">
            {!sidebarOpen && (
              <button
                onClick={() => setSidebarOpen(true)}
                className="p-1.5 text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-all"
              >
                <PanelLeft className="w-4 h-4" />
              </button>
            )}
            <span className="text-sm font-semibold text-gray-800">
              {activeTab === 'composer' ? 'Narration Studio' : activeTab === 'voices' ? 'Voice Catalog' : 'Preferences'}
            </span>
            {activeProject && (
              <span className="text-[11px] px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 font-mono">
                {activeProject.id}
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <div className="text-xs text-gray-500 flex items-center gap-1.5 bg-gray-50 px-2.5 py-1 rounded-md border border-gray-200">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              <span>Voice Consent Gate: </span>
              <strong className="text-emerald-700 font-medium">Verified</strong>
            </div>
          </div>
        </header>

        {/* WORKSPACE CONTENT AREA */}
        <div className="flex-1 max-w-4xl w-full mx-auto p-6 space-y-6">

          {/* TAB 1: COMPOSER WORKSPACE */}
          {activeTab === 'composer' && (
            <>
              {/* HERO GREETING */}
              <div className="text-center py-2 space-y-1">
                <h2 className="text-2xl font-semibold tracking-tight text-gray-900">
                  What would you like me to voice?
                </h2>
                <p className="text-xs text-gray-500">
                  Paste your text, story, or video voiceover script below.
                </p>
              </div>

              {/* CHAT-LIKE INPUT CONTAINER (White Card with subtle shadow) */}
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDrop}
                className="bg-white border border-[#e5e7eb] focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-100 rounded-2xl p-4 shadow-sm transition-all"
              >
                {/* Textarea */}
                <textarea
                  value={scriptText}
                  onChange={(e) => setScriptText(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Paste your script here, drag a .txt or .md file, or type anything..."
                  rows={5}
                  className="w-full bg-transparent text-gray-900 placeholder-gray-400 text-sm outline-none resize-none leading-relaxed"
                />

                {/* Metrics & Upload Row */}
                <div className="flex items-center justify-between text-[11px] text-gray-400 pt-2 border-t border-gray-100">
                  <div className="flex items-center gap-3 font-mono">
                    <span>{wordCount} words</span>
                    <span>•</span>
                    <span>{charCount} characters</span>
                    <span>•</span>
                    <span>~{estimatedSeconds}s audio</span>
                  </div>

                  <div className="flex items-center gap-2">
                    <label className="cursor-pointer text-gray-500 hover:text-blue-600 transition-all flex items-center gap-1">
                      <Upload className="w-3.5 h-3.5" />
                      <span>Upload TXT/MD</span>
                      <input type="file" accept=".txt,.md" onChange={handleFileUpload} className="hidden" />
                    </label>
                    {scriptText && (
                      <button
                        onClick={() => setScriptText("")}
                        className="text-gray-400 hover:text-red-500 transition-all ml-1"
                        title="Clear script"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>

                {/* SMART CONTROL BAR (Compact Dropdowns) */}
                <div className="mt-4 pt-3 border-t border-gray-100 flex flex-wrap items-center justify-between gap-3">
                  <div className="flex flex-wrap items-center gap-2 text-xs">
                    {/* Voice Dropdown */}
                    <div className="flex items-center gap-1 bg-gray-50 border border-gray-200 rounded-lg px-2.5 py-1.5">
                      <span className="text-gray-400 text-[11px]">Voice:</span>
                      <select
                        value={selectedVoice}
                        onChange={(e) => setSelectedVoice(e.target.value)}
                        className="bg-transparent text-gray-800 text-xs outline-none cursor-pointer font-medium"
                      >
                        <option value="auto">Auto (Smart Match)</option>
                        {voices.map(({ voice }) => (
                          <option key={voice.voice_id} value={voice.voice_id}>
                            {voice.name} ({voice.style})
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Style Dropdown */}
                    <div className="flex items-center gap-1 bg-gray-50 border border-gray-200 rounded-lg px-2.5 py-1.5">
                      <span className="text-gray-400 text-[11px]">Style:</span>
                      <select
                        value={stylePreference}
                        onChange={(e) => setStylePreference(e.target.value)}
                        className="bg-transparent text-gray-800 text-xs outline-none cursor-pointer font-medium"
                      >
                        <option value="Cinematic">Cinematic</option>
                        <option value="Documentary">Documentary</option>
                        <option value="Storyteller">Storyteller</option>
                        <option value="Dramatic">Dramatic</option>
                        <option value="Conversational">Conversational</option>
                      </select>
                    </div>

                    {/* Emotion Dropdown */}
                    <div className="flex items-center gap-1 bg-gray-50 border border-gray-200 rounded-lg px-2.5 py-1.5">
                      <span className="text-gray-400 text-[11px]">Emotion:</span>
                      <select
                        value={emotionMode}
                        onChange={(e) => setEmotionMode(e.target.value)}
                        className="bg-transparent text-gray-800 text-xs outline-none cursor-pointer font-medium"
                      >
                        <option value="auto">Auto Dynamic</option>
                        <option value="suspense">Suspense</option>
                        <option value="horror">Horror / Fear</option>
                        <option value="excited">Excited</option>
                        <option value="dramatic">Dramatic</option>
                        <option value="whisper">Whisper</option>
                      </select>
                    </div>

                    {/* Language Hint */}
                    <div className="flex items-center gap-1 bg-gray-50 border border-gray-200 rounded-lg px-2.5 py-1.5">
                      <span className="text-gray-400 text-[11px]">Lang:</span>
                      <select
                        value={languageHint}
                        onChange={(e) => setLanguageHint(e.target.value)}
                        className="bg-transparent text-gray-800 text-xs outline-none cursor-pointer font-medium"
                      >
                        <option value="auto">Auto Detect</option>
                        <option value="en">English</option>
                        <option value="ur">Urdu (اردو)</option>
                        <option value="roman_urdu">Roman Urdu / Hinglish</option>
                      </select>
                    </div>

                    {/* Advanced toggle */}
                    <button
                      onClick={() => setShowAdvanced(!showAdvanced)}
                      className="text-gray-400 hover:text-gray-700 p-1 rounded transition-all flex items-center gap-1 text-[11px]"
                    >
                      <Settings2 className="w-3.5 h-3.5" />
                      <span>Advanced</span>
                      {showAdvanced ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                    </button>
                  </div>

                  {/* Generate Button */}
                  <div className="flex items-center gap-2">
                    {isGenerating && (
                      <button
                        onClick={handleCancel}
                        className="text-xs text-red-600 hover:text-red-700 px-3 py-2 rounded-lg font-medium border border-red-200 hover:bg-red-50 transition-all"
                      >
                        Cancel
                      </button>
                    )}
                    <button
                      disabled={isGenerating || !scriptText.trim()}
                      onClick={handleGenerate}
                      className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium text-xs px-5 py-2.5 rounded-xl shadow-sm transition-all cursor-pointer"
                    >
                      {isGenerating ? (
                        <>
                          <div className="w-3.5 h-3.5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                          <span>Generating...</span>
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-3.5 h-3.5" />
                          <span>Generate Voice</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>

                {/* ADVANCED SETTINGS (Collapsed by default) */}
                {showAdvanced && (
                  <div className="mt-4 pt-4 border-t border-gray-100 grid grid-cols-1 md:grid-cols-2 gap-4 text-xs bg-gray-50/50 p-3 rounded-xl border">
                    <div>
                      <h4 className="font-semibold text-gray-700 mb-1">Audio Mastering</h4>
                      <label className="flex items-center gap-2 cursor-pointer text-gray-600">
                        <input
                          type="checkbox"
                          checked={enableMastering}
                          onChange={(e) => setEnableMastering(e.target.checked)}
                          className="rounded accent-blue-600"
                        />
                        <span>EBU R128 Loudness Normalization (-14 LUFS target)</span>
                      </label>
                      <p className="text-[11px] text-gray-400 mt-1">
                        High-pass 60Hz de-rumble & non-destructive speech compression.
                      </p>
                    </div>

                    <div>
                      <h4 className="font-semibold text-gray-700 mb-1">Keyboard Shortcuts</h4>
                      <p className="text-[11px] text-gray-500">
                        Press <kbd className="px-1.5 py-0.5 bg-white border border-gray-200 rounded font-mono text-[10px]">Ctrl+Enter</kbd> to immediately trigger voice generation.
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* QUICK EXAMPLE CHIPS */}
              <div className="flex flex-wrap items-center justify-center gap-2 pt-1">
                <span className="text-[11px] text-gray-400">Try sample:</span>
                <button
                  onClick={() =>
                    setScriptText(
                      "In 1944 during WWII, the B-25 bomber vanished over the misty mountains. Suddenly, the radio crackled with a mysterious signal."
                    )
                  }
                  className="text-[11px] bg-white hover:bg-gray-50 text-gray-600 border border-gray-200 px-2.5 py-1 rounded-full transition-all"
                >
                  WWII War Archive
                </button>
                <button
                  onClick={() =>
                    setScriptText(
                      "Suddenly usne darwaza khola... and then everything went silent. Shikarpur ke us purane makan mein koi aisi taqat thi jo shayed insani nahi thi."
                    )
                  }
                  className="text-[11px] bg-white hover:bg-gray-50 text-gray-600 border border-gray-200 px-2.5 py-1 rounded-full transition-all"
                >
                  Roman Urdu Mystery
                </button>
                <button
                  onClick={() =>
                    setScriptText(
                      "Welcome back. In today's deep dive, we explore how autonomous AI agents plan, execute, and verify complex multi-step workflows."
                    )
                  }
                  className="text-[11px] bg-white hover:bg-gray-50 text-gray-600 border border-gray-200 px-2.5 py-1 rounded-full transition-all"
                >
                  Tech Explainer
                </button>
              </div>

              {/* ERROR UX CARD (Graceful error handling) */}
              {errorMessage && (
                <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
                  <div className="flex-1 space-y-1">
                    <h4 className="text-xs font-semibold text-red-900">We couldn't generate this voice.</h4>
                    <p className="text-xs text-red-700">{errorMessage}</p>
                    <div className="pt-2">
                      <button
                        onClick={handleGenerate}
                        className="text-xs bg-red-600 hover:bg-red-700 text-white px-3 py-1.5 rounded-lg font-medium transition-all"
                      >
                        Retry Generation
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* LIVE AGENT PROGRESS (Specification Section 8) */}
              {isGenerating && (
                <div className="bg-white border border-blue-200 rounded-2xl p-4 shadow-sm space-y-3">
                  <div className="flex items-center justify-between text-xs font-medium">
                    <span className="text-blue-600 flex items-center gap-2">
                      <Sparkles className="w-4 h-4 animate-spin text-blue-500" />
                      {progressMsg}
                    </span>
                    <span className="text-gray-400 font-mono">{progressPct}%</span>
                  </div>
                  <div className="w-full bg-gray-100 h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-blue-600 h-full transition-all duration-300"
                      style={{ width: `${progressPct}%` }}
                    />
                  </div>
                </div>
              )}

              {/* GENERATED AUDIO PLAYER & STUDIO (Specification Section 11 & 12) */}
              {activeProject && activeProject.status === 'COMPLETED' && (
                <div className="bg-white border border-[#e5e7eb] rounded-2xl p-5 shadow-sm space-y-5">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <h3 className="text-base font-semibold text-gray-900">
                          {activeProject.title || "Voice Narration Master"}
                        </h3>
                        <span className="text-[10px] bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-full font-medium">
                          Mastered ✓
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 flex items-center gap-3">
                        <span>Voice: <strong className="text-gray-800">{activeProject.voice_name || "Aura Neural"}</strong></span>
                        <span>Language: <strong className="text-blue-600 uppercase">{activeProject.language}</strong></span>
                        <span>Duration: <strong className="text-gray-800">{activeProject.total_duration_seconds.toFixed(2)}s</strong></span>
                      </p>
                    </div>

                    {/* Export Hub */}
                    <div className="flex items-center gap-1.5">
                      <a
                        href={`/api/projects/${activeProject.id}/audio?format=mp3`}
                        download={`${activeProject.id}_final.mp3`}
                        className="flex items-center gap-1 bg-gray-50 hover:bg-gray-100 text-gray-700 text-xs px-2.5 py-1.5 rounded-lg border border-gray-200 transition-all"
                      >
                        <Download className="w-3.5 h-3.5 text-blue-600" />
                        MP3
                      </a>
                      <a
                        href={`/api/projects/${activeProject.id}/audio?format=wav`}
                        download={`${activeProject.id}_final.wav`}
                        className="flex items-center gap-1 bg-gray-50 hover:bg-gray-100 text-gray-700 text-xs px-2.5 py-1.5 rounded-lg border border-gray-200 transition-all"
                      >
                        <Download className="w-3.5 h-3.5 text-purple-600" />
                        WAV
                      </a>
                      <a
                        href={`/api/projects/${activeProject.id}/subtitles?format=srt`}
                        download={`${activeProject.id}_subtitles.srt`}
                        className="flex items-center gap-1 bg-gray-50 hover:bg-gray-100 text-gray-700 text-xs px-2.5 py-1.5 rounded-lg border border-gray-200 transition-all"
                      >
                        <FileText className="w-3.5 h-3.5 text-emerald-600" />
                        SRT
                      </a>
                      <a
                        href={`/api/projects/${activeProject.id}/subtitles?format=vtt`}
                        download={`${activeProject.id}_subtitles.vtt`}
                        className="flex items-center gap-1 bg-gray-50 hover:bg-gray-100 text-gray-700 text-xs px-2.5 py-1.5 rounded-lg border border-gray-200 transition-all"
                      >
                        <FileText className="w-3.5 h-3.5 text-teal-600" />
                        VTT
                      </a>
                      <a
                        href={`/api/projects/${activeProject.id}/subtitles?format=json`}
                        download={`${activeProject.id}_timings.json`}
                        className="flex items-center gap-1 bg-gray-50 hover:bg-gray-100 text-gray-700 text-xs px-2.5 py-1.5 rounded-lg border border-gray-200 transition-all"
                      >
                        <ListOrdered className="w-3.5 h-3.5 text-amber-600" />
                        JSON
                      </a>
                    </div>
                  </div>

                  {/* Player Bar */}
                  <div className="bg-[#f9fafb] p-4 rounded-xl border border-gray-200 space-y-3">
                    <div className="flex items-center gap-4">
                      <button
                        onClick={togglePlayMaster}
                        className="w-10 h-10 rounded-full bg-blue-600 hover:bg-blue-700 flex items-center justify-center text-white shadow-sm transition-all cursor-pointer shrink-0"
                      >
                        {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 ml-0.5" />}
                      </button>

                      <div className="flex-1 space-y-1">
                        <input
                          type="range"
                          min={0}
                          max={audioDuration || activeProject.total_duration_seconds || 1}
                          step={0.01}
                          value={currentTime}
                          onChange={handleSeek}
                          className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                        />
                        <div className="flex items-center justify-between text-[11px] text-gray-400 font-mono">
                          <span>{formatTime(currentTime)}</span>
                          <span>{formatTime(audioDuration || activeProject.total_duration_seconds)}</span>
                        </div>
                      </div>

                      {/* Speed Buttons */}
                      <div className="flex items-center gap-1 bg-white p-1 rounded-lg border border-gray-200">
                        {[0.75, 0.85, 1.0, 1.15, 1.25, 1.5].map((s) => (
                          <button
                            key={s}
                            onClick={() => changeSpeed(s)}
                            className={`text-[10px] px-1.5 py-0.5 rounded font-mono transition-all ${
                              playbackSpeed === s
                                ? 'bg-blue-600 text-white font-semibold'
                                : 'text-gray-500 hover:text-gray-900'
                            }`}
                          >
                            {s}x
                          </button>
                        ))}
                      </div>

                      {/* Volume Slider */}
                      <div className="flex items-center gap-1.5 text-gray-400">
                        <Volume2 className="w-4 h-4" />
                        <input
                          type="range"
                          min={0}
                          max={1}
                          step={0.05}
                          value={volume}
                          onChange={handleVolumeChange}
                          className="w-16 h-1 bg-gray-200 rounded appearance-none cursor-pointer accent-blue-600"
                        />
                      </div>
                    </div>
                  </div>

                  {/* LINE-BY-LINE STUDIO (Specification Section 12) */}
                  <div className="space-y-3 pt-2">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-500 flex items-center gap-2">
                        <Layers className="w-3.5 h-3.5 text-blue-600" />
                        Line-by-Line Narration Studio ({activeProject.chunks?.length || 0} Chunks)
                      </h4>
                      <span className="text-[11px] text-gray-400">
                        Targeted surgical repair available per line
                      </span>
                    </div>

                    <div className="space-y-2">
                      {activeProject.chunks?.map((chunk) => (
                        <div
                          key={chunk.chunk_index}
                          className="bg-white border border-gray-200 hover:border-gray-300 rounded-xl p-3 flex items-center justify-between gap-4 transition-all shadow-xs"
                        >
                          <div className="flex items-start gap-3 min-w-0 flex-1">
                            <span className="text-[11px] font-mono text-gray-400 bg-gray-50 px-1.5 py-0.5 rounded border border-gray-200 shrink-0 mt-0.5">
                              #{chunk.chunk_index.toString().padStart(2, '0')}
                            </span>
                            <div className="min-w-0 flex-1 space-y-1">
                              <p className="text-xs font-medium text-gray-800 leading-snug">
                                {chunk.text}
                              </p>
                              <div className="flex flex-wrap items-center gap-2 text-[10px]">
                                <span className="text-gray-500">
                                  Spoken: <span className="text-blue-700 font-mono">{chunk.spoken_text || chunk.normalized_text}</span>
                                </span>
                                <span className="bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded border border-blue-100">
                                  {chunk.emotion}
                                </span>
                                <span className="text-gray-400 font-mono">
                                  {chunk.start_time.toFixed(2)}s — {chunk.end_time.toFixed(2)}s
                                </span>
                              </div>
                            </div>
                          </div>

                          <div className="flex items-center gap-2 shrink-0">
                            <button
                              onClick={() => playChunkSnippet(chunk)}
                              className="flex items-center gap-1 bg-gray-50 hover:bg-gray-100 text-gray-700 text-xs px-2.5 py-1.5 rounded-lg border border-gray-200 transition-all cursor-pointer"
                            >
                              <Play className={`w-3 h-3 ${playingChunkIdx === chunk.chunk_index ? 'text-blue-600 animate-pulse' : ''}`} />
                              Play
                            </button>
                            <button
                              disabled={redoingChunkIdx === chunk.chunk_index}
                              onClick={() => handleRedoChunk(chunk.chunk_index)}
                              className="flex items-center gap-1 bg-red-50 hover:bg-red-100 text-red-700 text-xs px-2.5 py-1.5 rounded-lg border border-red-200 transition-all cursor-pointer disabled:opacity-50"
                            >
                              <RotateCcw className={`w-3 h-3 ${redoingChunkIdx === chunk.chunk_index ? 'animate-spin' : ''}`} />
                              {redoingChunkIdx === chunk.chunk_index ? 'Repairing...' : 'Redo'}
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </>
          )}

          {/* TAB 2: VOICE CATALOG VIEW (Specification Section 13) */}
          {activeTab === 'voices' && (
            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Licensed Voice Catalog</h3>
                <p className="text-xs text-gray-500">
                  Every voice profile is compliant and licensed for high-fidelity production narration.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {voices.map(({ voice, confidence, reason }) => {
                  const isFav = favoriteVoices.includes(voice.voice_id);
                  const isSelected = selectedVoice === voice.voice_id;

                  return (
                    <div
                      key={voice.voice_id}
                      className={`bg-white border rounded-xl p-4 space-y-3 transition-all ${
                        isSelected ? 'border-blue-500 ring-2 ring-blue-50' : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="flex items-center gap-2">
                            <h4 className="font-semibold text-sm text-gray-900">{voice.name}</h4>
                            <span className="text-[10px] bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded font-mono">
                              {voice.locale}
                            </span>
                          </div>
                          <p className="text-xs text-blue-600 font-medium">{voice.style} Narration</p>
                        </div>

                        <button
                          onClick={() => {
                            setFavoriteVoices(prev =>
                              isFav ? prev.filter(f => f !== voice.voice_id) : [...prev, voice.voice_id]
                            );
                          }}
                          className="text-gray-300 hover:text-amber-500 p-1"
                        >
                          <Star className={`w-4 h-4 ${isFav ? 'fill-amber-400 text-amber-400' : ''}`} />
                        </button>
                      </div>

                      <p className="text-xs text-gray-600 leading-relaxed">{voice.description}</p>
                      {reason && (
                        <p className="text-[11px] text-blue-700 bg-blue-50/50 px-2 py-1 rounded border border-blue-100">
                          {reason}
                        </p>
                      )}

                      <div className="text-[11px] text-gray-400 font-mono flex items-center justify-between pt-1">
                        <span>Suitability match: {(confidence * 100).toFixed(0)}%</span>
                        <span className="text-emerald-600">QC score: {(voice.qc_rating * 100).toFixed(0)}%</span>
                      </div>

                      <div className="flex items-center gap-2 pt-2 border-t border-gray-100">
                        <button
                          onClick={() => playVoicePreview(voice.voice_id)}
                          className="flex-1 flex items-center justify-center gap-1.5 bg-gray-50 hover:bg-gray-100 text-gray-700 text-xs py-1.5 px-3 rounded-lg border border-gray-200 transition-all font-medium"
                        >
                          <Play className={`w-3.5 h-3.5 ${previewingVoiceId === voice.voice_id ? 'text-blue-600 animate-pulse' : ''}`} />
                          {previewingVoiceId === voice.voice_id ? 'Playing...' : 'Preview Sample'}
                        </button>
                        <button
                          onClick={() => {
                            setSelectedVoice(voice.voice_id);
                            setStylePreference(voice.style);
                            setActiveTab('composer');
                          }}
                          className={`flex-1 flex items-center justify-center gap-1.5 text-xs py-1.5 px-3 rounded-lg font-medium transition-all ${
                            isSelected
                              ? 'bg-blue-600 text-white'
                              : 'bg-white hover:bg-blue-50 text-blue-600 border border-blue-200'
                          }`}
                        >
                          <Check className="w-3.5 h-3.5" />
                          {isSelected ? 'Selected' : 'Use Voice'}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* TAB 3: SETTINGS & PRONUNCIATION DICTIONARY */}
          {activeTab === 'settings' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Pronunciation & Engine Settings</h3>
                <p className="text-xs text-gray-500">
                  Manage phonetic pronunciation overrides and persistence preferences.
                </p>
              </div>

              {/* Pronunciation Table Card */}
              <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm space-y-4">
                <h4 className="text-sm font-semibold text-gray-800">
                  Phonetic Pronunciation Dictionary
                </h4>
                <p className="text-xs text-gray-500">
                  Define custom spoken replacements for names, historical terms, or non-English words.
                </p>

                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Word (e.g. Shikarpur)"
                    value={newWord}
                    onChange={(e) => setNewWord(e.target.value)}
                    className="flex-1 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-xs outline-none focus:border-blue-500"
                  />
                  <input
                    type="text"
                    placeholder="Spoken (e.g. Shi-kar-pur)"
                    value={newReplacement}
                    onChange={(e) => setNewReplacement(e.target.value)}
                    className="flex-1 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-xs outline-none focus:border-blue-500"
                  />
                  <button
                    onClick={handleAddPronunciation}
                    className="bg-blue-600 hover:bg-blue-700 text-white text-xs px-4 py-2 rounded-lg font-medium transition-all"
                  >
                    Add Entry
                  </button>
                </div>

                <div className="border border-gray-200 rounded-lg overflow-hidden">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-gray-50 border-b border-gray-200 text-gray-500">
                      <tr>
                        <th className="px-4 py-2.5 font-medium">Original Word</th>
                        <th className="px-4 py-2.5 font-medium">Spoken Pronunciation</th>
                        <th className="px-4 py-2.5 text-right font-medium">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {Object.entries(pronunciations).map(([w, r]) => (
                        <tr key={w} className="hover:bg-gray-50/50">
                          <td className="px-4 py-2.5 font-medium text-gray-900">{w}</td>
                          <td className="px-4 py-2.5 text-blue-700 font-mono">{r}</td>
                          <td className="px-4 py-2.5 text-right">
                            <button
                              onClick={() => handleDeletePronunciation(w)}
                              className="text-gray-400 hover:text-red-600 p-1 transition-all"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* SYSTEM HEALTH MODAL (Specification Section 34) */}
      {showHealthModal && healthStatus && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white border border-gray-200 rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-gray-100 pb-3">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-emerald-600" />
                <h3 className="font-semibold text-sm text-gray-900">System Diagnostics & Health</h3>
              </div>
              <button
                onClick={() => setShowHealthModal(false)}
                className="text-gray-400 hover:text-gray-700"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-2.5 text-xs">
              {Object.entries(healthStatus.services || {}).map(([service, status]: [string, any]) => (
                <div key={service} className="flex items-center justify-between py-1.5 border-b border-gray-50">
                  <span className="capitalize text-gray-600">{service.replace('_', ' ')}</span>
                  <span className="font-mono text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                    {status}
                  </span>
                </div>
              ))}
            </div>

            <div className="pt-2">
              <button
                onClick={() => setShowHealthModal(false)}
                className="w-full bg-gray-100 hover:bg-gray-200 text-gray-800 text-xs py-2 rounded-lg font-medium transition-all"
              >
                Close Diagnostics
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
