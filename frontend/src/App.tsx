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
  Users,
  Lock,
  Unlock,
  Search,
  RefreshCw,
  CheckCircle2
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

interface ProjectCharacter {
  character_id: string;
  speaker_name: string;
  voice_id: string;
  provider: string;
  is_locked: boolean;
  style: string;
  confidence: number;
  reason: string;
}

interface ScenePlan {
  scene_id: string;
  scene_index: number;
  scene_name: string;
  location: string;
  time_of_day: string;
  mood: string;
  dramatic_intensity: number;
  characters: string[];
}

interface ChunkPlan {
  id?: string;
  chunk_index: number;
  text: string;
  spoken_text?: string;
  normalized_text?: string;
  speaker?: string;
  speaker_name?: string;
  character_id?: string;
  voice_id?: string;
  assigned_voice_id?: string;
  emotion: string;
  emotion_intensity?: number;
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
  characters?: ProjectCharacter[];
  scenes?: ScenePlan[];
  qc_report?: any;
  chunks?: ChunkPlan[];
}

interface VoiceChangeTarget {
  type: 'character' | 'project';
  characterId?: string;
  characterName?: string;
  currentVoiceId: string;
  newVoiceId: string;
  affectedLinesCount: number;
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
  const [chunkVoiceSelections, setChunkVoiceSelections] = useState<Record<number, string>>({});
  const [chunkEmotionSelections, setChunkEmotionSelections] = useState<Record<number, string>>({});
  const [chunkSpeedSelections, setChunkSpeedSelections] = useState<Record<number, number>>({});
  const [voiceSearchQuery, setVoiceSearchQuery] = useState<string>("");
  const [selectedGenderFilter, setSelectedGenderFilter] = useState<string>("All");
  const [selectedStyleFilter, setSelectedStyleFilter] = useState<string>("All");

  // Recently used voices tracking (stored in localStorage)
  const [recentVoices, setRecentVoices] = useState<string[]>(() => {
    try {
      const stored = localStorage.getItem('auravoice_recent_voices');
      if (stored) return JSON.parse(stored);
      return ["en-US-ChristopherNeural", "en-US-GuyNeural", "ur-PK-AsadNeural", "en-US-JennyNeural"];
    } catch {
      return ["en-US-ChristopherNeural", "en-US-GuyNeural", "ur-PK-AsadNeural", "en-US-JennyNeural"];
    }
  });

  const trackVoiceUsage = (voiceId: string) => {
    if (!voiceId || voiceId === 'auto') return;
    setRecentVoices(prev => {
      const updated = [voiceId, ...prev.filter(id => id !== voiceId)].slice(0, 10);
      try {
        localStorage.setItem('auravoice_recent_voices', JSON.stringify(updated));
      } catch {}
      return updated;
    });
  };

  const handleSelectVoiceAndOpen = (voiceId: string, style?: string) => {
    setSelectedVoice(voiceId);
    if (style) setStylePreference(style);
    trackVoiceUsage(voiceId);
    setActiveTab('composer');
  };

  const handleOpenProject = async (projectId: string) => {
    try {
      const res = await fetch(`/api/projects/${projectId}`);
      if (!res.ok) throw new Error("Could not load project");
      const data: ProjectRecord = await res.json();
      
      setActiveProject(data);
      // Restore script text into composer
      setScriptText(data.raw_input || (data as any).original_text || (data as any).spoken_text || "");
      if (data.voice_id) {
        setSelectedVoice(data.voice_id);
        trackVoiceUsage(data.voice_id);
      }
      if (data.style) setStylePreference(data.style);
      if (data.emotion) setEmotionMode(data.emotion);
      if (data.language) setLanguageHint(data.language);
      setIsGenerating(false);
      setErrorMessage(null);
      setProgressPct(100);
      setActiveTab('composer');

      // Initialize audio element
      if (audioRef.current && data.id) {
        audioRef.current.src = `/api/projects/${data.id}/audio?format=mp3&t=${Date.now()}`;
        audioRef.current.load();
      }
      setIsPlaying(false);
      setCurrentTime(0);
    } catch (e: any) {
      alert("Error loading project: " + e.message);
    }
  };

  const handleDeleteProject = async (e: React.MouseEvent, projectId: string) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this project?")) return;
    try {
      const res = await fetch(`/api/projects/${projectId}`, { method: 'DELETE' });
      if (res.ok) {
        if (activeProject?.id === projectId) {
          setActiveProject(null);
          setScriptText("");
        }
        await loadProjects();
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Voice replacement state & confirmation modal
  const [voiceChangeModal, setVoiceChangeModal] = useState<VoiceChangeTarget | null>(null);
  const [isReplacingVoice, setIsReplacingVoice] = useState<boolean>(false);
  const [voiceChangeSuccess, setVoiceChangeSuccess] = useState<string | null>(null);
  const [showProjectVoicePicker, setShowProjectVoicePicker] = useState<boolean>(false);

  // Open confirmation modal for replacing character voiceover
  const requestCharacterVoiceChange = (char: ProjectCharacter, newVoiceId: string) => {
    if (newVoiceId === char.voice_id) return;
    const charKey = (char.speaker_name || char.character_id).toLowerCase().trim();
    const count = activeProject?.chunks?.filter(c => {
      const spk = (c.speaker_name || c.speaker || c.character_id || "").toLowerCase().trim();
      return spk === charKey || (c.character_id && c.character_id.toLowerCase().trim() === charKey);
    }).length || 1;

    setVoiceChangeModal({
      type: 'character',
      characterId: char.character_id,
      characterName: char.speaker_name,
      currentVoiceId: char.voice_id,
      newVoiceId: newVoiceId,
      affectedLinesCount: count
    });
  };

  // Open confirmation modal for replacing entire project/narration voiceover
  const requestProjectVoiceChange = (newVoiceId: string) => {
    if (!activeProject || newVoiceId === activeProject.voice_id) return;
    setVoiceChangeModal({
      type: 'project',
      currentVoiceId: activeProject.voice_id || 'en-US-GuyNeural',
      newVoiceId: newVoiceId,
      affectedLinesCount: activeProject.chunks?.length || 1
    });
    setShowProjectVoicePicker(false);
  };

  // Confirm and execute voiceover replacement
  const handleConfirmVoiceChange = async () => {
    if (!voiceChangeModal || !activeProject?.id) return;
    setIsReplacingVoice(true);
    try {
      let res;
      if (voiceChangeModal.type === 'character' && voiceChangeModal.characterId) {
        res = await fetch(`/api/projects/${activeProject.id}/characters/${voiceChangeModal.characterId}/replace-voice`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ voice_id: voiceChangeModal.newVoiceId })
        });
      } else {
        res = await fetch(`/api/projects/${activeProject.id}/replace-voice`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ voice_id: voiceChangeModal.newVoiceId })
        });
      }

      if (!res.ok) {
        const err = await res.text();
        throw new Error(err);
      }

      const updated: ProjectRecord = await res.json();
      setActiveProject(updated);
      trackVoiceUsage(voiceChangeModal.newVoiceId);
      
      // Autoload updated audio
      if (audioRef.current && updated.id) {
        audioRef.current.src = `/api/projects/${updated.id}/audio?format=mp3&t=${Date.now()}`;
        audioRef.current.load();
      }
      setIsPlaying(false);
      setCurrentTime(0);

      const targetLabel = voiceChangeModal.type === 'character' 
        ? `Character "${voiceChangeModal.characterName}"` 
        : 'Full Narration';
      const newVoiceName = voices.find(v => v.voice.voice_id === voiceChangeModal.newVoiceId)?.voice.name || voiceChangeModal.newVoiceId;

      setVoiceChangeSuccess(`✓ ${targetLabel} voiceover successfully changed to ${newVoiceName}! Final audio has been regenerated and remastered.`);
      setTimeout(() => setVoiceChangeSuccess(null), 6000);
      setVoiceChangeModal(null);
      await loadProjects();
    } catch (e: any) {
      alert("Voice replacement error: " + e.message);
    } finally {
      setIsReplacingVoice(false);
    }
  };

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
      trackVoiceUsage(selectedVoice);
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

  // Character Voice Management Handlers (Step 5, 7)
  const handleUpdateCharacter = async (charId: string, newVoiceId: string, isLocked?: boolean) => {
    if (!activeProject?.id) return;
    try {
      const res = await fetch(`/api/projects/${activeProject.id}/characters/${charId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ voice_id: newVoiceId, is_locked: isLocked })
      });
      if (res.ok) {
        const updated = await res.json();
        setActiveProject(updated);
      }
    } catch (e: any) {
      console.error(e);
    }
  };

  const handleToggleLockCharacter = async (char: ProjectCharacter) => {
    await handleUpdateCharacter(char.character_id, char.voice_id, !char.is_locked);
  };

  // Line-by-Line Redo (Step 11: supports voice, speed, and emotion overrides)
  const handleRedoChunk = async (
    chunkIndex: number,
    customVoiceId?: string,
    customSpeed?: number,
    customEmotion?: string
  ) => {
    if (!activeProject?.id) return;
    setRedoingChunkIdx(chunkIndex);
    try {
      const res = await fetch(`/api/projects/${activeProject.id}/chunks/${chunkIndex}/redo`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: activeProject.id,
          chunk_index: chunkIndex,
          custom_voice_id: customVoiceId,
          custom_speed: customSpeed,
          custom_emotion: customEmotion
        })
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
      try {
        setPreviewingVoiceId(voiceId);
        trackVoiceUsage(voiceId);
        previewAudioRef.current.src = `/api/voices/${voiceId}/preview?t=${Date.now()}`;
        previewAudioRef.current.load();
        await previewAudioRef.current.play();
        previewAudioRef.current.onended = () => setPreviewingVoiceId(null);
        previewAudioRef.current.onerror = () => setPreviewingVoiceId(null);
      } catch (err) {
        console.error("Voice preview playback failed:", err);
        setPreviewingVoiceId(null);
      }
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
            <div className="flex items-center justify-between px-2 mb-1.5">
              <p className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">
                Recent Projects
              </p>
              <span className="text-[10px] text-gray-400 font-mono">
                {projectsHistory.length}
              </span>
            </div>
            <div className="space-y-1">
              {projectsHistory.length === 0 ? (
                <p className="text-xs text-gray-400 px-2 py-2 italic">No past projects</p>
              ) : (
                projectsHistory.map((p) => {
                  const isActive = activeProject?.id === p.id;
                  return (
                    <div
                      key={p.id}
                      onClick={() => handleOpenProject(p.id)}
                      className={`group w-full text-left px-2.5 py-2 rounded-lg text-xs transition-all flex items-center justify-between cursor-pointer ${
                        isActive
                          ? 'bg-blue-50 text-blue-900 border border-blue-200 font-medium'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      <div className="truncate flex-1 pr-2 flex flex-col gap-0.5">
                        <span className="truncate">{p.title || "Untitled Project"}</span>
                        <span className="text-[10px] text-gray-400 flex items-center gap-1.5 font-mono">
                          <Clock className="w-2.5 h-2.5 shrink-0" />
                          {p.total_duration_seconds ? `${p.total_duration_seconds.toFixed(1)}s` : 'Saved'} • {p.id}
                        </span>
                      </div>
                      <button
                        onClick={(e) => handleDeleteProject(e, p.id)}
                        className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-600 transition-all rounded hover:bg-red-50 shrink-0"
                        title="Delete project"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  );
                })
              )}
            </div>

            {/* Recently Used Voices in Sidebar */}
            {recentVoices.length > 0 && (
              <div className="mt-4 pt-3 border-t border-gray-200">
                <div className="flex items-center justify-between px-2 mb-1.5">
                  <p className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">
                    Recent Voices
                  </p>
                  <button
                    onClick={() => {
                      setSelectedStyleFilter('All');
                      setSelectedGenderFilter('All');
                      setActiveTab('voices');
                    }}
                    className="text-[10px] text-blue-600 hover:underline cursor-pointer"
                  >
                    Catalog
                  </button>
                </div>
                <div className="space-y-1">
                  {recentVoices.slice(0, 4).map((vid) => {
                    const vObj = voices.find(v => v.voice.voice_id === vid)?.voice;
                    if (!vObj) return null;
                    const isCur = selectedVoice === vid;
                    return (
                      <div
                        key={vid}
                        onClick={() => handleSelectVoiceAndOpen(vid, vObj.style)}
                        className={`group flex items-center justify-between px-2 py-1.5 rounded-lg text-xs cursor-pointer transition-all ${
                          isCur
                            ? 'bg-blue-50 text-blue-900 border border-blue-200 font-medium'
                            : 'text-gray-600 hover:bg-gray-100'
                        }`}
                        title="Click to select and open in Narration Studio"
                      >
                        <div className="flex items-center gap-2 truncate">
                          <Volume2 className={`w-3.5 h-3.5 shrink-0 ${isCur ? 'text-blue-600' : 'text-gray-400'}`} />
                          <span className="truncate">{vObj.name.replace('Aura ', '')}</span>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            playVoicePreview(vid);
                          }}
                          className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-blue-600 transition-all rounded"
                          title="Preview sample"
                        >
                          <Play className={`w-3 h-3 ${previewingVoiceId === vid ? 'text-blue-600 animate-pulse' : ''}`} />
                        </button>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
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
                      "Narrator: The old castle gates swung open with a slow screech.\nCommander: Keep your shields raised! We don't know what is waiting in the dark.\nWitch: You fools! None of you shall leave this realm alive.\nDoctor: Wait... look at those glowing runes on the wall."
                    )
                  }
                  className="text-[11px] bg-purple-50 hover:bg-purple-100 text-purple-700 border border-purple-200 px-2.5 py-1 rounded-full transition-all font-medium"
                >
                  🎭 Multi-Character Story
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
                  {/* Voice Change Success Banner */}
                  {voiceChangeSuccess && (
                    <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl p-3 text-xs flex items-center justify-between shadow-xs">
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                        <span>{voiceChangeSuccess}</span>
                      </div>
                      <button onClick={() => setVoiceChangeSuccess(null)} className="text-emerald-500 hover:text-emerald-700 p-0.5 cursor-pointer">
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}

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

                    {/* Action & Export Hub */}
                    <div className="flex flex-wrap items-center gap-1.5">
                      <button
                        onClick={() => setShowProjectVoicePicker(true)}
                        className="flex items-center gap-1.5 bg-purple-50 hover:bg-purple-100 text-purple-700 text-xs px-2.5 py-1.5 rounded-lg border border-purple-200 font-medium transition-all cursor-pointer shadow-xs"
                        title="Change voiceover for the entire narration with confirmation"
                      >
                        <RefreshCw className="w-3.5 h-3.5 text-purple-600" />
                        <span>Change Voiceover</span>
                      </button>

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

                  {/* CHARACTER CASTING & CONSISTENCY PANEL (Step 5, 7) */}
                  {activeProject.characters && activeProject.characters.length > 0 && (
                    <div className="bg-white border border-gray-200 rounded-2xl p-4 shadow-xs space-y-3">
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-500 flex items-center gap-2">
                          <Users className="w-3.5 h-3.5 text-purple-600" />
                          Character Voice Cast ({activeProject.characters.length} Characters)
                        </h4>
                        <span className="text-[11px] text-gray-400">
                          Cast mapping locked across entire script
                        </span>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        {activeProject.characters.map((char) => {
                          const vProfile = voices.find(v => v.voice.voice_id === char.voice_id)?.voice;
                          return (
                            <div
                              key={char.character_id}
                              className="border border-gray-200 hover:border-purple-200 bg-gray-50/50 rounded-xl p-3 space-y-2 transition-all"
                            >
                              <div className="flex items-center justify-between">
                                <span className="font-semibold text-xs text-gray-900 flex items-center gap-1.5">
                                  <span className="w-2 h-2 rounded-full bg-purple-600"></span>
                                  {char.speaker_name}
                                </span>
                                <button
                                  onClick={() => handleToggleLockCharacter(char)}
                                  className={`text-[10px] px-2 py-0.5 rounded-full flex items-center gap-1 border transition-all cursor-pointer ${
                                    char.is_locked
                                      ? 'bg-amber-50 text-amber-700 border-amber-200 font-semibold'
                                      : 'bg-white text-gray-500 border-gray-200 hover:bg-gray-100'
                                  }`}
                                  title={char.is_locked ? "Voice locked (Auto Cast cannot change)" : "Lock this character voice"}
                                >
                                  {char.is_locked ? <Lock className="w-2.5 h-2.5" /> : <Unlock className="w-2.5 h-2.5" />}
                                  {char.is_locked ? "Locked" : "Unlocked"}
                                </button>
                              </div>

                              <div className="space-y-1 text-[11px]">
                                <div className="flex items-center justify-between">
                                  <span className="text-gray-400">Voice:</span>
                                  <span className="font-medium text-gray-800 truncate max-w-[130px]">{vProfile?.name || char.voice_id}</span>
                                </div>
                                <div className="flex items-center justify-between">
                                  <span className="text-gray-400">Style:</span>
                                  <span className="text-purple-700 font-mono text-[10px]">{char.style}</span>
                                </div>
                                {char.reason && (
                                  <p className="text-[10px] text-gray-500 italic bg-white p-1.5 rounded border border-gray-100 leading-snug">
                                    "{char.reason}"
                                  </p>
                                )}
                              </div>

                              <div className="space-y-1.5 pt-1">
                                <div className="flex items-center gap-1.5">
                                  <button
                                    onClick={() => playVoicePreview(char.voice_id)}
                                    className="flex items-center gap-1 bg-white hover:bg-gray-100 text-gray-700 text-[11px] px-2 py-1.5 rounded-md border border-gray-200 justify-center transition-all cursor-pointer shrink-0"
                                    title="Listen to current character voice"
                                  >
                                    <Play className={`w-3 h-3 ${previewingVoiceId === char.voice_id ? 'text-blue-600 animate-pulse' : ''}`} />
                                    <span>Preview</span>
                                  </button>
                                  <select
                                    value={char.voice_id}
                                    onChange={(e) => requestCharacterVoiceChange(char, e.target.value)}
                                    className="text-[11px] bg-white border border-gray-200 hover:border-purple-300 rounded-md px-2 py-1.5 text-gray-800 flex-1 cursor-pointer truncate font-medium transition-colors"
                                    title="Select new voice to trigger confirmation dialog"
                                  >
                                    {voices.map(({ voice }) => (
                                      <option key={voice.voice_id} value={voice.voice_id}>
                                        {voice.name} ({voice.style})
                                      </option>
                                    ))}
                                  </select>
                                </div>

                                <button
                                  onClick={() => {
                                    const nextVoice = voices.find(v => v.voice.voice_id !== char.voice_id && v.voice.gender === (vProfile?.gender || 'Male'))?.voice.voice_id || 'en-US-GuyNeural';
                                    requestCharacterVoiceChange(char, nextVoice);
                                  }}
                                  className="w-full flex items-center justify-center gap-1.5 bg-purple-50 hover:bg-purple-100 text-purple-700 text-[11px] py-1 px-2 rounded-md border border-purple-200 font-medium transition-all cursor-pointer"
                                  title="Change voiceover with confirmation dialog"
                                >
                                  <RefreshCw className="w-3 h-3 text-purple-600" />
                                  <span>Change Voiceover</span>
                                </button>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* LINE-BY-LINE STUDIO (Specification Section 11, 12) */}
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
                      {activeProject.chunks?.map((chunk) => {
                        const currentVoiceId =
                          chunkVoiceSelections[chunk.chunk_index] ||
                          chunk.voice_id ||
                          chunk.assigned_voice_id ||
                          activeProject.voice_id;
                        const currentVoiceProfile = voices.find(
                          (v) => v.voice.voice_id === currentVoiceId
                        )?.voice;
                        const currentEmotion =
                          chunkEmotionSelections[chunk.chunk_index] ||
                          chunk.emotion ||
                          "auto";
                        const currentSpeed =
                          chunkSpeedSelections[chunk.chunk_index] ||
                          chunk.speed ||
                          1.0;

                        return (
                          <div
                            key={chunk.chunk_index}
                            className="bg-white border border-gray-200 hover:border-gray-300 rounded-xl p-3 flex flex-col md:flex-row md:items-center justify-between gap-3 transition-all shadow-xs"
                          >
                            <div className="flex items-start gap-3 min-w-0 flex-1">
                              <span className="text-[11px] font-mono text-gray-400 bg-gray-50 px-1.5 py-0.5 rounded border border-gray-200 shrink-0 mt-0.5">
                                #{chunk.chunk_index.toString().padStart(2, '0')}
                              </span>
                              <div className="min-w-0 flex-1 space-y-1.5">
                                <div className="flex items-center gap-2 flex-wrap">
                                  {chunk.speaker && (
                                    <span className="inline-flex items-center gap-1.5 bg-purple-50 text-purple-700 font-semibold text-[11px] px-2.5 py-0.5 rounded-full border border-purple-200 shadow-xs">
                                      <span className="w-1.5 h-1.5 rounded-full bg-purple-600 animate-pulse"></span>
                                      {chunk.speaker}
                                    </span>
                                  )}
                                  <p className="text-xs font-medium text-gray-900 leading-snug">
                                    {chunk.text}
                                  </p>
                                </div>
                                <div className="flex flex-wrap items-center gap-2 text-[10px]">
                                  <span className="text-gray-500">
                                    Spoken: <span className="text-blue-700 font-mono">{chunk.spoken_text || chunk.normalized_text}</span>
                                  </span>
                                  <span className="bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded border border-blue-100 font-medium">
                                    {chunk.emotion}
                                  </span>
                                  <span className="bg-gray-100 text-gray-700 px-2 py-0.5 rounded border border-gray-200">
                                    Voice: <span className="font-semibold text-gray-900">{currentVoiceProfile?.name || currentVoiceId || "Standard"}</span>
                                  </span>
                                  <span className="text-gray-400 font-mono">
                                    {chunk.start_time.toFixed(2)}s — {chunk.end_time.toFixed(2)}s
                                  </span>
                                </div>
                              </div>
                            </div>

                            <div className="flex items-center gap-2 shrink-0 self-end md:self-center flex-wrap">
                              {/* Character Voice Dropdown */}
                              <select
                                value={currentVoiceId}
                                onChange={(e) =>
                                  setChunkVoiceSelections((prev) => ({
                                    ...prev,
                                    [chunk.chunk_index]: e.target.value,
                                  }))
                                }
                                className="text-[11px] bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg px-2 py-1.5 text-gray-700 focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer max-w-[130px] truncate"
                                title="Change voice for this line"
                              >
                                {voices.map(({ voice }) => (
                                  <option key={voice.voice_id} value={voice.voice_id}>
                                    {voice.name}
                                  </option>
                                ))}
                              </select>

                              {/* Emotion Selector */}
                              <select
                                value={currentEmotion}
                                onChange={(e) =>
                                  setChunkEmotionSelections((prev) => ({
                                    ...prev,
                                    [chunk.chunk_index]: e.target.value,
                                  }))
                                }
                                className="text-[11px] bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg px-2 py-1.5 text-gray-700 cursor-pointer"
                                title="Change emotion"
                              >
                                <option value="auto">Auto</option>
                                <option value="suspense">Suspense</option>
                                <option value="dramatic">Dramatic</option>
                                <option value="excited">Excited</option>
                                <option value="horror">Horror</option>
                                <option value="whisper">Whisper</option>
                              </select>

                              {/* Speed Selector */}
                              <select
                                value={currentSpeed}
                                onChange={(e) =>
                                  setChunkSpeedSelections((prev) => ({
                                    ...prev,
                                    [chunk.chunk_index]: parseFloat(e.target.value),
                                  }))
                                }
                                className="text-[11px] bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg px-2 py-1.5 text-gray-700 cursor-pointer"
                                title="Change speed"
                              >
                                <option value={0.85}>0.85x</option>
                                <option value={0.92}>0.92x</option>
                                <option value={1.0}>1.00x</option>
                                <option value={1.08}>1.08x</option>
                                <option value={1.15}>1.15x</option>
                              </select>

                              <button
                                onClick={() => playChunkSnippet(chunk)}
                                className="flex items-center gap-1 bg-gray-50 hover:bg-gray-100 text-gray-700 text-xs px-2.5 py-1.5 rounded-lg border border-gray-200 transition-all cursor-pointer"
                                title="Play line audio snippet"
                              >
                                <Play className={`w-3 h-3 ${playingChunkIdx === chunk.chunk_index ? 'text-blue-600 animate-pulse' : ''}`} />
                                Play
                              </button>
                              <button
                                disabled={redoingChunkIdx === chunk.chunk_index}
                                onClick={() => handleRedoChunk(chunk.chunk_index, currentVoiceId, currentSpeed, currentEmotion)}
                                className="flex items-center gap-1 bg-red-50 hover:bg-red-100 text-red-700 text-xs px-2.5 py-1.5 rounded-lg border border-red-200 transition-all cursor-pointer disabled:opacity-50"
                                title="Surgically redo this line with custom parameters"
                              >
                                <RotateCcw className={`w-3 h-3 ${redoingChunkIdx === chunk.chunk_index ? 'animate-spin' : ''}`} />
                                {redoingChunkIdx === chunk.chunk_index ? 'Repairing...' : 'Redo'}
                              </button>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              )}
            </>
          )}

          {/* TAB 2: VOICE CATALOG VIEW (Specification Section 14) */}
          {activeTab === 'voices' && (
            <div className="space-y-4">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Licensed Voice Catalog ({voices.length} Voices)</h3>
                  <p className="text-xs text-gray-500">
                    Compliant, licensed voices across cinematic, dramatic, and multi-lingual archetypes.
                  </p>
                </div>

                {/* Search Bar */}
                <div className="relative w-full md:w-64">
                  <Search className="w-4 h-4 text-gray-400 absolute left-3 top-2.5" />
                  <input
                    type="text"
                    value={voiceSearchQuery}
                    onChange={(e) => setVoiceSearchQuery(e.target.value)}
                    placeholder="Search voice, accent, style..."
                    className="w-full text-xs pl-9 pr-3 py-2 bg-white border border-gray-200 rounded-xl outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              {/* Category Filter Chips */}
              <div className="flex flex-wrap items-center gap-2 pt-1">
                <span className="text-xs text-gray-400">View:</span>
                {[
                  { id: 'All', label: 'All Voices' },
                  { id: 'Recent', label: `🕒 Recent (${recentVoices.length})` },
                  { id: 'Favorites', label: `⭐ Favorites (${favoriteVoices.length})` },
                  { id: 'Male', label: 'Male' },
                  { id: 'Female', label: 'Female' }
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setSelectedGenderFilter(tab.id)}
                    className={`text-xs px-2.5 py-1 rounded-lg border transition-all cursor-pointer ${
                      selectedGenderFilter === tab.id
                        ? 'bg-blue-600 text-white border-blue-600 font-medium'
                        : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}

                <span className="text-xs text-gray-400 ml-2">Style:</span>
                {['All', 'Cinematic', 'Dramatic', 'Storyteller', 'Documentary', 'Conversational'].map((st) => (
                  <button
                    key={st}
                    onClick={() => setSelectedStyleFilter(st)}
                    className={`text-xs px-2.5 py-1 rounded-lg border transition-all cursor-pointer ${
                      selectedStyleFilter === st
                        ? 'bg-purple-600 text-white border-purple-600 font-medium'
                        : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'
                    }`}
                  >
                    {st}
                  </button>
                ))}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {voices
                  .filter(({ voice }) => {
                    const matchQ =
                      !voiceSearchQuery ||
                      voice.name.toLowerCase().includes(voiceSearchQuery.toLowerCase()) ||
                      voice.description.toLowerCase().includes(voiceSearchQuery.toLowerCase()) ||
                      voice.locale.toLowerCase().includes(voiceSearchQuery.toLowerCase()) ||
                      voice.style.toLowerCase().includes(voiceSearchQuery.toLowerCase());
                    
                    let matchG = true;
                    if (selectedGenderFilter === 'Recent') {
                      matchG = recentVoices.includes(voice.voice_id);
                    } else if (selectedGenderFilter === 'Favorites') {
                      matchG = favoriteVoices.includes(voice.voice_id);
                    } else if (selectedGenderFilter === 'Male') {
                      matchG = voice.gender === 'Male';
                    } else if (selectedGenderFilter === 'Female') {
                      matchG = voice.gender === 'Female';
                    }

                    const matchS = selectedStyleFilter === 'All' || voice.style === selectedStyleFilter;
                    return matchQ && matchG && matchS;
                  })
                  .map(({ voice, confidence, reason }) => {
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
                          <div 
                            className="cursor-pointer"
                            onClick={() => handleSelectVoiceAndOpen(voice.voice_id, voice.style)}
                            title="Click to select and open in Narration Studio"
                          >
                            <div className="flex items-center gap-2">
                              <h4 className="font-semibold text-sm text-gray-900 hover:text-blue-600 transition-colors">{voice.name}</h4>
                              <span className="text-[10px] bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded font-mono">
                                {voice.locale}
                              </span>
                              <span className="text-[10px] bg-purple-50 text-purple-700 px-1.5 py-0.5 rounded font-medium border border-purple-100">
                                {voice.gender}
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
                            className="text-gray-300 hover:text-amber-500 p-1 cursor-pointer"
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
                          <span>Confidence: {(confidence * 100).toFixed(0)}%</span>
                          <span className="text-emerald-600">QC score: {(voice.qc_rating * 100).toFixed(0)}%</span>
                        </div>

                        <div className="flex items-center gap-2 pt-2 border-t border-gray-100">
                          <button
                            onClick={() => playVoicePreview(voice.voice_id)}
                            className="flex-1 flex items-center justify-center gap-1.5 bg-gray-50 hover:bg-gray-100 text-gray-700 text-xs py-1.5 px-3 rounded-lg border border-gray-200 transition-all font-medium cursor-pointer"
                          >
                            <Play className={`w-3.5 h-3.5 ${previewingVoiceId === voice.voice_id ? 'text-blue-600 animate-pulse' : ''}`} />
                            {previewingVoiceId === voice.voice_id ? 'Playing...' : 'Preview Sample'}
                          </button>
                          <button
                            onClick={() => handleSelectVoiceAndOpen(voice.voice_id, voice.style)}
                            className={`flex-1 text-xs py-1.5 px-3 rounded-lg border transition-all font-medium cursor-pointer ${
                              isSelected
                                ? 'bg-blue-600 text-white border-blue-600'
                                : 'bg-white hover:bg-gray-50 text-gray-700 border-gray-200'
                            }`}
                          >
                            {isSelected ? 'Active in Studio ✓' : 'Select Voice'}
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

      {/* VOICE REPLACEMENT CONFIRMATION MODAL */}
      {voiceChangeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4 animate-in fade-in duration-150">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-gray-200 space-y-5 animate-in zoom-in-95 duration-150">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-purple-50 border border-purple-200 flex items-center justify-center text-purple-600">
                  <RefreshCw className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-gray-900">
                    Confirm Voiceover Change
                  </h3>
                  <p className="text-xs text-gray-500">
                    {voiceChangeModal.type === 'character'
                      ? `Replace voice for "${voiceChangeModal.characterName}"`
                      : "Replace voice for entire narration"}
                  </p>
                </div>
              </div>
              <button
                disabled={isReplacingVoice}
                onClick={() => setVoiceChangeModal(null)}
                className="text-gray-400 hover:text-gray-600 p-1 cursor-pointer disabled:opacity-50"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Voice Comparison Cards */}
            <div className="space-y-2.5 bg-gray-50 p-3.5 rounded-xl border border-gray-200 text-xs">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-gray-400 text-[11px] block">Current Voice:</span>
                  <span className="font-medium text-gray-700">
                    {voices.find(v => v.voice.voice_id === voiceChangeModal.currentVoiceId)?.voice.name || voiceChangeModal.currentVoiceId}
                  </span>
                </div>
                <button
                  onClick={() => playVoicePreview(voiceChangeModal.currentVoiceId)}
                  className="flex items-center gap-1 bg-white hover:bg-gray-100 text-gray-700 px-2 py-1 rounded border border-gray-200 cursor-pointer font-medium"
                >
                  <Play className={`w-3 h-3 ${previewingVoiceId === voiceChangeModal.currentVoiceId ? 'text-blue-600 animate-pulse' : 'text-gray-600'}`} />
                  Listen
                </button>
              </div>

              <div className="border-t border-gray-200 pt-2 flex items-center justify-between">
                <div>
                  <span className="text-purple-600 font-medium text-[11px] block">New Voiceover:</span>
                  <span className="font-semibold text-gray-900">
                    {voices.find(v => v.voice.voice_id === voiceChangeModal.newVoiceId)?.voice.name || voiceChangeModal.newVoiceId}
                  </span>
                </div>
                <button
                  onClick={() => playVoicePreview(voiceChangeModal.newVoiceId)}
                  className="flex items-center gap-1 bg-purple-50 hover:bg-purple-100 text-purple-700 px-2 py-1 rounded border border-purple-200 font-medium cursor-pointer"
                >
                  <Play className={`w-3 h-3 ${previewingVoiceId === voiceChangeModal.newVoiceId ? 'text-purple-600 animate-pulse' : 'text-purple-600'}`} />
                  Audition Sample
                </button>
              </div>
            </div>

            {/* Scope & Impact Info */}
            <div className="bg-purple-50/60 border border-purple-100 rounded-xl p-3 text-xs space-y-1 text-purple-950">
              <p className="font-semibold flex items-center gap-1.5 text-purple-900">
                <Sparkles className="w-3.5 h-3.5 text-purple-600" />
                <span>Autonomous Re-generation & Mastering</span>
              </p>
              <p className="text-[11px] text-purple-800 leading-relaxed">
                This will re-synthesize <strong>{voiceChangeModal.affectedLinesCount} dialogue {voiceChangeModal.affectedLinesCount === 1 ? 'line' : 'lines'}</strong> using the new voice, update timeline synchronicity, and re-master the final audio at -14 LUFS.
              </p>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center justify-end gap-2.5 pt-1">
              <button
                disabled={isReplacingVoice}
                onClick={() => setVoiceChangeModal(null)}
                className="px-3.5 py-2 text-xs font-medium text-gray-600 hover:text-gray-900 bg-white border border-gray-200 hover:bg-gray-50 rounded-xl transition-all cursor-pointer disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                disabled={isReplacingVoice}
                onClick={handleConfirmVoiceChange}
                className="flex items-center gap-2 px-4 py-2 text-xs font-medium text-white bg-purple-600 hover:bg-purple-700 rounded-xl transition-all cursor-pointer shadow-sm disabled:opacity-50"
              >
                {isReplacingVoice ? (
                  <>
                    <div className="w-3.5 h-3.5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                    <span>Replacing Voiceover...</span>
                  </>
                ) : (
                  <>
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span>Confirm & Change Voiceover</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* PROJECT VOICE REPLACEMENT SELECTOR MODAL */}
      {showProjectVoicePicker && activeProject && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-center z-50 p-4 animate-in fade-in duration-150">
          <div className="bg-white border border-gray-200 rounded-2xl max-w-xl w-full p-6 shadow-2xl space-y-4 max-h-[85vh] flex flex-col animate-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between border-b border-gray-100 pb-3">
              <div className="flex items-center gap-2">
                <RefreshCw className="w-4 h-4 text-purple-600" />
                <div>
                  <h3 className="font-semibold text-sm text-gray-900">Change Narration Voiceover</h3>
                  <p className="text-[11px] text-gray-500">Pick a new voice to replace the current voiceover for this recording.</p>
                </div>
              </div>
              <button
                onClick={() => setShowProjectVoicePicker(false)}
                className="text-gray-400 hover:text-gray-700 p-1 cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-2 pr-1">
              {voices.map(({ voice }) => {
                const isCur = (activeProject.voice_id || '') === voice.voice_id;
                return (
                  <div
                    key={voice.voice_id}
                    className={`flex items-center justify-between p-3 rounded-xl border transition-all ${
                      isCur ? 'bg-purple-50/50 border-purple-200' : 'bg-gray-50/50 hover:bg-gray-50 border-gray-200'
                    }`}
                  >
                    <div className="truncate flex-1 pr-3">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-xs text-gray-900">{voice.name}</span>
                        <span className="text-[10px] bg-white border border-gray-200 text-gray-600 px-1.5 py-0.2 rounded font-mono">
                          {voice.gender}
                        </span>
                        <span className="text-[10px] bg-purple-50 text-purple-700 px-1.5 py-0.2 rounded border border-purple-100">
                          {voice.style}
                        </span>
                      </div>
                      <p className="text-[11px] text-gray-500 truncate mt-0.5">{voice.description}</p>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        onClick={() => playVoicePreview(voice.voice_id)}
                        className="flex items-center gap-1 bg-white hover:bg-gray-100 text-gray-700 text-xs px-2.5 py-1.5 rounded-lg border border-gray-200 transition-all cursor-pointer font-medium"
                      >
                        <Play className={`w-3 h-3 ${previewingVoiceId === voice.voice_id ? 'text-blue-600 animate-pulse' : ''}`} />
                        <span>Preview</span>
                      </button>
                      <button
                        disabled={isCur}
                        onClick={() => requestProjectVoiceChange(voice.voice_id)}
                        className={`text-xs px-3 py-1.5 rounded-lg font-medium transition-all cursor-pointer ${
                          isCur
                            ? 'bg-gray-100 text-gray-400 border border-gray-200 cursor-not-allowed'
                            : 'bg-purple-600 hover:bg-purple-700 text-white shadow-xs'
                        }`}
                      >
                        {isCur ? 'Active Voice' : 'Select Voice'}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

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
