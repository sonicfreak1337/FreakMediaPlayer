from __future__ import annotations

import queue
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import av
import numpy as np
import pytest

from freak_media_player.models.equalizer import EQUALIZER_PRESETS
from freak_media_player.player.decode_worker import AudioDecodeWorker
from freak_media_player.player.dsp.parametric_equalizer import ParametricEqualizerProcessor
from freak_media_player.player.pipeline_messages import PipelineMessage
from freak_media_player.player.stream_probe import probe_stream_url
from freak_media_player.player.stream_resolver import NetworkStreamResolver
from freak_media_player.player.streaming_decoder import PyAVStreamingDecoder
from freak_media_player.plugins.internet_radio.logo_cache import StationLogoCache


class RadioTestHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        base = f"http://127.0.0.1:{self.server.server_address[1]}"
        audio_payloads: dict[str, tuple[bytes, str]] = getattr(
            self.server, "audio_payloads", {}
        )
        icy_payloads: dict[str, bytes] = getattr(self.server, "icy_payloads", {})
        if self.path in icy_payloads:
            payload = icy_payloads[self.path]
            self.send_response(200)
            self.send_header("Content-Type", "audio/mpeg")
            self.send_header("icy-metaint", "512")
            self.send_header("icy-name", "Local ICY Radio")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        if self.path in audio_payloads:
            payload, content_type = audio_payloads[self.path]
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        if self.path == "/redirect.pls":
            self.send_response(302)
            self.send_header("Location", "/station.pls")
            self.end_headers()
        elif self.path == "/station.pls":
            payload = f"[playlist]\nFile1={base}/live.mp3\n".encode()
            self.send_response(200)
            self.send_header("Content-Type", "audio/x-scpls")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        elif self.path == "/logo.png":
            payload = b"local-test-image"
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        elif self.path == "/live.mp3":
            payload = b"ID3" + bytes(2048)
            self.send_response(200)
            self.send_header("Content-Type", "audio/mpeg")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        elif self.path == "/live.m3u8":
            payload = (
                b"#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:1\n"
                b"#EXTINF:0.1,\nsegment.ts\n#EXT-X-ENDLIST\n"
            )
            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.apple.mpegurl")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        elif self.path == "/stall.mp3":
            self.send_response(200)
            self.send_header("Content-Type", "audio/mpeg")
            self.send_header("Content-Length", "4096")
            self.end_headers()
            self.wfile.flush()
            time.sleep(4)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, _format: str, *_args: object) -> None:
        pass


@contextmanager
def local_radio_server(
    audio_payloads: dict[str, tuple[bytes, str]] | None = None,
    icy_payloads: dict[str, bytes] | None = None,
) -> Iterator[str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), RadioTestHandler)
    server.audio_payloads = audio_payloads or {}
    server.icy_payloads = icy_payloads or {}
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_local_server_playlist_redirect_and_logo_cache(tmp_path) -> None:
    with local_radio_server() as base:
        resolved = NetworkStreamResolver().resolve(f"{base}/redirect.pls")
        logo = StationLogoCache(tmp_path / "logos").get(f"{base}/logo.png")

    assert resolved == f"{base}/live.mp3"
    assert logo is not None
    assert logo.read_bytes() == b"local-test-image"


def test_local_server_manual_stream_probe_follows_playlist() -> None:
    with local_radio_server() as base:
        result = probe_stream_url(f"{base}/station.pls")

    assert result.resolved_url == f"{base}/live.mp3"
    assert result.content_type == "audio/mpeg"


def encode_test_audio(path: Path, codec: str, container_format: str) -> bytes:
    sample_rate = 48_000
    sample_count = 4_800
    timeline = np.arange(sample_count, dtype=np.float32) / sample_rate
    signal = 0.15 * np.sin(2 * np.pi * 440 * timeline)
    samples = np.stack((signal, signal)).astype(np.float32)
    with av.open(str(path), "w", format=container_format) as container:
        stream = container.add_stream(codec, rate=sample_rate)
        stream.layout = "stereo"
        if codec == "vorbis":
            stream.codec_context.options = {"strict": "experimental"}
        frame = av.AudioFrame.from_ndarray(samples, format="fltp", layout="stereo")
        frame.sample_rate = sample_rate
        for packet in stream.encode(frame):
            container.mux(packet)
        for packet in stream.encode(None):
            container.mux(packet)
    return path.read_bytes()


@pytest.mark.parametrize(
    ("codec", "container_format", "route", "content_type"),
    (
        ("mp3", "mp3", "/encoded.mp3", "audio/mpeg"),
        ("aac", "adts", "/encoded.aac", "audio/aac"),
        ("vorbis", "ogg", "/encoded.ogg", "audio/ogg"),
        ("libopus", "ogg", "/encoded.opus", "audio/ogg"),
    ),
)
def test_decoder_reads_real_supported_formats_over_local_http(
    tmp_path: Path,
    codec: str,
    container_format: str,
    route: str,
    content_type: str,
) -> None:
    payload = encode_test_audio(tmp_path / f"test-{codec}", codec, container_format)

    with local_radio_server({route: (payload, content_type)}) as base:
        chunks = list(
            PyAVStreamingDecoder().decode(
                f"{base}{route}", 0, threading.Event()
            )
        )

    assert chunks
    assert chunks[0].shape[0] == 2


def test_decoder_reads_real_hls_audio_over_local_http(tmp_path: Path) -> None:
    segment = encode_test_audio(tmp_path / "segment.ts", "aac", "mpegts")

    with local_radio_server({"/segment.ts": (segment, "video/mp2t")}) as base:
        chunks = list(
            PyAVStreamingDecoder().decode(
                f"{base}/live.m3u8", 0, threading.Event()
            )
        )

    assert chunks
    assert chunks[0].shape[0] == 2


def test_ffmpeg_aac_decoder_is_available_for_aac_and_aac_plus_profiles() -> None:
    decoder = av.Codec("aac", "r")

    assert decoder.is_decoder is True
    assert decoder.type == "audio"


def icy_stream(audio: bytes, titles: list[str], metaint: int = 512) -> bytes:
    output = bytearray()
    for block_index, offset in enumerate(range(0, len(audio), metaint)):
        chunk = audio[offset : offset + metaint]
        output.extend(chunk)
        if len(chunk) == metaint:
            title = titles[min(block_index, len(titles) - 1)]
            metadata = f"StreamTitle='{title}';".encode()
            block_count = (len(metadata) + 15) // 16
            padded = metadata.ljust(block_count * 16, b"\0")
            output.append(block_count)
            output.extend(padded)
    return bytes(output)


def test_decoder_extracts_real_icy_stream_title(tmp_path: Path) -> None:
    audio = encode_test_audio(tmp_path / "icy.mp3", "mp3", "mp3")
    payload = icy_stream(
        audio,
        ["First Artist - First Song", "Dark Artist - Night Song"],
    )
    decoder = PyAVStreamingDecoder()

    with local_radio_server(icy_payloads={"/icy.mp3": payload}) as base:
        chunks = list(decoder.decode(f"{base}/icy.mp3", 0, threading.Event()))

    assert chunks
    assert decoder.stream_title() == "Dark Artist - Night Song"


def test_stalled_network_decoder_is_bounded_after_stop() -> None:
    messages: queue.Queue[PipelineMessage] = queue.Queue(maxsize=16)
    worker = AudioDecodeWorker(
        PyAVStreamingDecoder(),
        ParametricEqualizerProcessor(EQUALIZER_PRESETS[0]),
        messages,
    )

    with local_radio_server() as base:
        worker.start(1, f"{base}/stall.mp3", 0)
        time.sleep(0.1)
        started = time.monotonic()
        worker.stop()
        stop_elapsed = time.monotonic() - started
        deadline = time.monotonic() + 5
        while worker.live_thread_count() and time.monotonic() < deadline:
            time.sleep(0.05)

    assert stop_elapsed < 1.0
    assert worker.live_thread_count() == 0
