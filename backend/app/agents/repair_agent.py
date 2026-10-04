import os
from typing import Dict, Any, Optional
from ..models.schemas import ChunkPlan
from ..providers.base import BaseTTSProvider
from .audio_processor import AudioProcessorAgent
from .qc_agent import AutonomousQCAgent

class AutonomousRepairAgent:
    """
    Module 15 & 16: Autonomous Repair Agent & Multi-Attempt Intelligence
    Executes surgical chunk regeneration with adaptive parameters.
    Ensures that when Chunk 07 fails, ONLY Chunk 07 is repaired rather than the entire project.
    """

    def __init__(
        self,
        tts_provider: BaseTTSProvider,
        audio_processor: AudioProcessorAgent,
        qc_agent: AutonomousQCAgent
    ):
        self.tts_provider = tts_provider
        self.audio_processor = audio_processor
        self.qc_agent = qc_agent

    async def repair_single_chunk(
        self,
        chunk: ChunkPlan,
        voice_id: str,
        failure_reason: str,
        override_rate: Optional[str] = None,
        override_pitch: Optional[str] = None
    ) -> ChunkPlan:
        """
        Executes targeted regeneration with strategy adaptation.
        """
        chunk.attempt_count += 1
        
        # Strategy selection based on attempt & failure reason
        applied_rate = override_rate or chunk.rate
        applied_pitch = override_pitch or chunk.pitch

        if "rushed" in failure_reason.lower():
            # Slow down slightly
            applied_rate = "-10%"
        elif "silence" in failure_reason.lower() or "stagnation" in failure_reason.lower():
            # Speed up slightly
            applied_rate = "+5%"
        elif chunk.attempt_count > 1:
            # Fallback safe neutral cadence
            applied_rate = "+0%"
            applied_pitch = "+0Hz"

        chunk.rate = applied_rate
        chunk.pitch = applied_pitch

        # Re-synthesize
        res = await self.tts_provider.synthesize_chunk(
            text=chunk.normalized_text,
            voice_id=voice_id,
            rate=applied_rate,
            pitch=applied_pitch,
            output_path=chunk.audio_file
        )

        if res["success"]:
            chunk.duration = self.audio_processor.get_audio_duration(chunk.audio_file)
            passed, msg = self.qc_agent.analyze_chunk_quality(chunk)
            chunk.qc_pass = passed
            chunk.qc_message = msg
        else:
            chunk.qc_pass = False
            chunk.qc_message = f"Repair synthesis failed: {res.get('error')}"

        return chunk
