"""Messages passed from the decode worker to the audio output pump."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PcmChunk:
    generation: int
    payload: bytes


@dataclass(frozen=True)
class DecodeFinished:
    generation: int


@dataclass(frozen=True)
class DecodeFailed:
    generation: int
    message: str


@dataclass(frozen=True)
class StreamMetadataChanged:
    generation: int
    title: str


PipelineMessage = PcmChunk | DecodeFinished | DecodeFailed | StreamMetadataChanged
