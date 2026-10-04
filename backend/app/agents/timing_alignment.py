import json
from typing import List, Dict, Any
from ..models.schemas import ChunkPlan

class TimingAlignmentAgent:
    """
    Module 13 & 17: Timing, Subtitles & Alignment Engine
    Calculates exact start/end time offsets and formats SRT, VTT, and JSON timings.
    """

    def compute_timeline(self, chunks: List[ChunkPlan]) -> List[ChunkPlan]:
        """Calculates running timeline with pauses."""
        current_time = 0.0
        for chunk in chunks:
            # pause before
            current_time += (chunk.pause_before_ms / 1000.0)
            chunk.start_time = round(current_time, 3)
            current_time += chunk.duration
            chunk.end_time = round(current_time, 3)
            # pause after
            current_time += (chunk.pause_after_ms / 1000.0)
        return chunks

    def generate_srt(self, chunks: List[ChunkPlan]) -> str:
        """Outputs standard SubRip (.srt) caption file."""
        lines = []
        for i, chunk in enumerate(chunks, 1):
            start_str = self._format_timestamp_srt(chunk.start_time)
            end_str = self._format_timestamp_srt(chunk.end_time)
            lines.append(f"{i}")
            lines.append(f"{start_str} --> {end_str}")
            lines.append(chunk.text)
            lines.append("")
        return "\n".join(lines)

    def generate_vtt(self, chunks: List[ChunkPlan]) -> str:
        """Outputs WebVTT (.vtt) caption file."""
        lines = ["WEBVTT", ""]
        for i, chunk in enumerate(chunks, 1):
            start_str = self._format_timestamp_vtt(chunk.start_time)
            end_str = self._format_timestamp_vtt(chunk.end_time)
            lines.append(f"{i}")
            lines.append(f"{start_str} --> {end_str}")
            lines.append(chunk.text)
            lines.append("")
        return "\n".join(lines)

    def generate_timings_json(self, chunks: List[ChunkPlan], total_duration: float) -> str:
        """Outputs CapCut / Premiere / After Effects compatible timing JSON."""
        data = {
            "total_duration_seconds": round(total_duration, 3),
            "chunks_count": len(chunks),
            "timeline": [
                {
                    "index": c.chunk_index,
                    "text": c.text,
                    "spoken_normalized": c.normalized_text,
                    "start": c.start_time,
                    "end": c.end_time,
                    "duration": round(c.duration, 3),
                    "emotion": c.emotion,
                    "speed": c.speed
                }
                for c in chunks
            ]
        }
        return json.dumps(data, indent=2)

    def _format_timestamp_srt(self, seconds: float) -> str:
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

    def _format_timestamp_vtt(self, seconds: float) -> str:
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hrs:02d}:{mins:02d}:{secs:02d}.{millis:03d}"
