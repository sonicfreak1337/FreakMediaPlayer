"""Parametric equalizer models and presets."""

from __future__ import annotations

from dataclasses import dataclass

EQUALIZER_FREQUENCIES_HZ = (31, 62, 125, 250, 500, 1000, 2000, 4000, 8000, 16000)
MIN_FREQUENCY_HZ = 20
MAX_FREQUENCY_HZ = 20_000
MIN_GAIN_DB = -12.0
MAX_GAIN_DB = 12.0
MIN_Q = 0.2
MAX_Q = 12.0
DEFAULT_Q = 1.0
MIN_PREAMP_DB = -18.0
MAX_PREAMP_DB = 6.0
EQUALIZER_REFERENCE_SAMPLE_RATE = 48_000


@dataclass(frozen=True)
class EqualizerBand:
    frequency_hz: int
    gain_db: float
    q: float = DEFAULT_Q
    enabled: bool = True


@dataclass(frozen=True)
class EqualizerPreset:
    preset_id: str
    name: str
    bands: tuple[EqualizerBand, ...]
    preamp_db: float = 0.0
    genre: str = "General"


def make_preset(
    preset_id: str,
    name: str,
    gains_db: tuple[float, ...],
    *,
    q_values: tuple[float, ...] | None = None,
    preamp_db: float = 0.0,
    genre: str = "General",
) -> EqualizerPreset:
    if len(gains_db) != len(EQUALIZER_FREQUENCIES_HZ):
        raise ValueError("Equalizer preset must define one gain per frequency band.")
    resolved_q_values = q_values or (DEFAULT_Q,) * len(EQUALIZER_FREQUENCIES_HZ)
    if len(resolved_q_values) != len(EQUALIZER_FREQUENCIES_HZ):
        raise ValueError("Equalizer preset must define one Q value per frequency band.")
    return EqualizerPreset(
        preset_id=preset_id,
        name=name,
        bands=tuple(
            EqualizerBand(
                frequency_hz=frequency,
                gain_db=clamp_gain(gain),
                q=clamp_q(q),
            )
            for frequency, gain, q in zip(
                EQUALIZER_FREQUENCIES_HZ,
                gains_db,
                resolved_q_values,
                strict=True,
            )
        ),
        preamp_db=clamp_preamp(preamp_db),
        genre=genre,
    )


def clamp_frequency(frequency_hz: int) -> int:
    return min(MAX_FREQUENCY_HZ, max(MIN_FREQUENCY_HZ, frequency_hz))


def clamp_gain(gain_db: float) -> float:
    return min(MAX_GAIN_DB, max(MIN_GAIN_DB, gain_db))


def clamp_q(q: float) -> float:
    return min(MAX_Q, max(MIN_Q, q))


def clamp_preamp(preamp_db: float) -> float:
    return min(MAX_PREAMP_DB, max(MIN_PREAMP_DB, preamp_db))


def _genre_preset(
    genre: str,
    preset_id: str,
    name: str,
    gains_db: tuple[float, ...],
) -> EqualizerPreset:
    """Build a broad musical curve with conservative output headroom."""
    peak_boost = max(0.0, *gains_db)
    preamp_db = -min(6.0, peak_boost + (0.5 if peak_boost else 0.0))
    return make_preset(
        preset_id,
        name,
        gains_db,
        q_values=(1.1,) * len(EQUALIZER_FREQUENCIES_HZ),
        preamp_db=preamp_db,
        genre=genre,
    )


# The curves are deliberately broad and moderate. They describe a useful tonal
# starting point for a style; they are not a claim that every recording in that
# style needs the same corrective EQ.
_PRESET_DEFINITIONS = (
    # General listening
    ("General", "flat", "Flat", (0, 0, 0, 0, 0, 0, 0, 0, 0, 0)),
    ("General", "balanced", "Balanced", (0, 0.3, 0.5, 0.2, -0.3, 0, 0.4, 0.6, 0.5, 0.2)),
    ("General", "bass-boost", "Bass Boost", (2.5, 3, 2, 0.5, -0.5, -0.5, 0, 0.3, 0.2, 0)),
    (
        "General",
        "vocal-clarity",
        "Vocal Clarity",
        (-1, -0.8, -0.5, -0.3, 0.5, 1.5, 2.2, 1.8, 0.5, 0),
    ),
    ("General", "warm", "Warm", (0.5, 1, 1.5, 1.2, 0.6, 0, -0.5, -0.8, -0.5, -0.3)),
    ("General", "bright", "Bright", (-0.5, -0.4, -0.3, -0.2, 0, 0.4, 1, 1.8, 2, 1.5)),
    ("General", "late-night", "Late Night", (-1.5, -1, -0.3, 0.4, 0.8, 1, 0.8, 0.3, -0.5, -1)),
    # Pop
    ("Pop", "pop", "Pop", (0.8, 1.2, 0.5, -0.4, -0.5, 0.4, 1.3, 1.5, 1.2, 0.8)),
    ("Pop", "dance-pop", "Dance Pop", (1.5, 2.2, 1, -0.8, -0.8, 0, 1, 1.8, 1.5, 0.5)),
    ("Pop", "electropop", "Electropop", (1.2, 2, 0.8, -1, -0.7, 0.2, 1, 1.7, 1.7, 0.8)),
    ("Pop", "synthpop", "Synthpop", (1, 1.5, 0.5, -0.5, 0, 0.5, 1, 1.4, 1.8, 1.2)),
    ("Pop", "indie-pop", "Indie Pop", (0.3, 0.7, 0.8, 0.3, -0.2, 0.4, 1.2, 1.2, 0.7, 0.3)),
    ("Pop", "dream-pop", "Dream Pop", (0.5, 1, 1.2, 0.7, 0.2, -0.3, 0.2, 0.8, 1.5, 1.2)),
    ("Pop", "k-pop", "K-Pop", (1.2, 2, 0.7, -0.8, -0.7, 0.2, 1.4, 2, 1.8, 1)),
    ("Pop", "j-pop", "J-Pop", (0.7, 1.2, 0.5, -0.4, -0.2, 0.6, 1.5, 1.8, 1.7, 1)),
    ("Pop", "city-pop", "City Pop", (0.8, 1.3, 1, 0.3, -0.2, 0.3, 1, 1.5, 1.4, 0.8)),
    ("Pop", "power-pop", "Power Pop", (0.5, 1.2, 1, -0.3, -0.4, 0.6, 1.5, 1.8, 1.2, 0.5)),
    # Rock and alternative
    ("Rock & Alternative", "rock", "Rock", (0.7, 1.3, 1, -0.7, -0.5, 0.6, 1.5, 1.7, 1.2, 0.5)),
    (
        "Rock & Alternative",
        "classic-rock",
        "Classic Rock",
        (0.7, 1.2, 1.3, 0.2, -0.4, 0.5, 1.2, 1.3, 0.7, 0.2),
    ),
    (
        "Rock & Alternative",
        "alternative-rock",
        "Alternative Rock",
        (0.5, 1.1, 0.8, -0.5, -0.5, 0.5, 1.4, 1.8, 1.2, 0.5),
    ),
    (
        "Rock & Alternative",
        "indie-rock",
        "Indie Rock",
        (0.2, 0.7, 1, 0.4, -0.2, 0.5, 1.3, 1.5, 0.8, 0.3),
    ),
    ("Rock & Alternative", "hard-rock", "Hard Rock", (1, 1.8, 1, -1, -0.8, 0.7, 1.8, 2, 1.2, 0.4)),
    ("Rock & Alternative", "punk-rock", "Punk Rock", (0.2, 0.8, 0.5, -0.6, 0, 1, 2, 2.2, 1.2, 0.2)),
    (
        "Rock & Alternative",
        "grunge",
        "Grunge",
        (0.8, 1.5, 1.3, 0.2, -0.5, 0.4, 1.2, 1.5, 0.6, -0.2),
    ),
    (
        "Rock & Alternative",
        "progressive-rock",
        "Progressive Rock",
        (0.4, 0.8, 0.8, -0.3, -0.2, 0.5, 1.2, 1.3, 1, 0.6),
    ),
    (
        "Rock & Alternative",
        "psychedelic-rock",
        "Psychedelic Rock",
        (0.7, 1, 1.2, 0.6, 0, -0.2, 0.4, 1, 1.4, 1),
    ),
    (
        "Rock & Alternative",
        "shoegaze",
        "Shoegaze",
        (0.7, 1.2, 1.3, 0.8, 0.2, -0.5, -0.2, 0.5, 1.2, 1),
    ),
    ("Rock & Alternative", "post-rock", "Post-Rock", (0.5, 1, 1.1, 0.5, 0, -0.2, 0.3, 1, 1.3, 0.8)),
    (
        "Rock & Alternative",
        "rockabilly",
        "Rockabilly",
        (-0.3, 0.3, 1.1, 1, 0.2, 0.6, 1.3, 1.4, 0.6, 0),
    ),
    # Metal (legacy ids and curves remain available)
    ("Metal", "metal", "Metal", (1.5, 2.5, 1.5, -2, -1.5, 0.5, 1.5, 1, 2, 1)),
    ("Metal", "heavy-metal", "Heavy Metal", (1, 2, 1.2, -1.2, -0.8, 0.8, 1.8, 2, 1.5, 0.7)),
    ("Metal", "metalcore", "Metalcore", (2, 3, 1, -2.5, -2, 0.5, 2.5, 1.5, 1, 0.5)),
    ("Metal", "death-metal", "Death Metal", (1, 2, 1, -1.5, -0.8, 0.5, 1.5, 2, 1, 0)),
    ("Metal", "deathcore", "Deathcore", (1.5, 2.5, 1, -2, -1, 0.8, 2, 2.5, 1, 0)),
    ("Metal", "black-metal", "Black Metal", (-1, -0.5, 0, -0.5, 0.5, 1.5, 2, 2.5, 2, 1)),
    ("Metal", "doom-metal", "Doom Metal", (2, 2.5, 2, 1.5, 0.5, 0, -0.5, -1, -1, -1.5)),
    ("Metal", "thrash-metal", "Thrash Metal", (0.5, 1.5, 0.5, -1.5, -0.5, 1, 2, 2.5, 1.5, 0.5)),
    ("Metal", "djent", "Djent", (0.5, 1, 0, -2.5, -1.5, 1, 2.5, 2, 0.5, -0.5)),
    (
        "Metal",
        "progressive-metal",
        "Progressive Metal",
        (0.5, 1, 0.5, -1, -0.5, 0.8, 1.5, 1.5, 1, 0.5),
    ),
    ("Metal", "power-metal", "Power Metal", (0.7, 1.5, 0.7, -1, -0.5, 1, 2, 2.2, 1.5, 0.8)),
    (
        "Metal",
        "symphonic-metal",
        "Symphonic Metal",
        (0.8, 1.3, 0.8, -0.8, -0.2, 0.8, 1.8, 2, 1.7, 1),
    ),
    ("Metal", "nu-metal", "Nu Metal", (1.8, 2.7, 1.5, -1.7, -1.2, 0.5, 1.7, 2, 1, 0)),
    (
        "Metal",
        "industrial-metal",
        "Industrial Metal",
        (1, 2, 0.5, -1.5, -0.7, 0.8, 2, 2.2, 1.5, 0.5),
    ),
    ("Metal", "folk-metal", "Folk Metal", (0.8, 1.5, 1.2, -0.5, 0.2, 0.8, 1.5, 1.7, 1.2, 0.5)),
    ("Metal", "stoner-metal", "Stoner Metal", (1.8, 2.3, 2, 1.2, 0.3, -0.3, -0.5, -0.3, 0, -0.5)),
    # Dance and electronic music
    ("Electronic", "electronic", "Electronic", (1.2, 2, 0.7, -0.8, -0.5, 0.2, 0.8, 1.5, 1.5, 0.8)),
    ("Electronic", "house", "House", (1.5, 2.5, 1, -1, -0.8, 0, 0.7, 1.3, 1.2, 0.3)),
    ("Electronic", "deep-house", "Deep House", (1.8, 2.7, 1.5, -0.2, -0.6, -0.3, 0.3, 0.8, 0.7, 0)),
    (
        "Electronic",
        "tech-house",
        "Tech House",
        (1.5, 2.5, 0.8, -1.2, -0.7, 0.2, 0.8, 1.4, 1.2, 0.2),
    ),
    ("Electronic", "techno", "Techno", (1.8, 2.8, 0.8, -1.3, -0.8, 0.2, 1, 1.5, 1.3, 0.3)),
    ("Electronic", "trance", "Trance", (1.2, 2.2, 0.8, -1, -0.5, 0.5, 1.2, 1.8, 1.7, 0.8)),
    ("Electronic", "drum-and-bass", "Drum & Bass", (2, 3, 1, -1.5, -1, 0.2, 1.2, 1.8, 1.5, 0.5)),
    ("Electronic", "dubstep", "Dubstep", (2.5, 3, 1.2, -1.5, -1, 0.3, 1.5, 2, 1.3, 0.2)),
    ("Electronic", "hardstyle", "Hardstyle", (2, 3, 1, -1.8, -1.2, 0.5, 1.5, 2, 1.5, 0.4)),
    ("Electronic", "ambient", "Ambient", (0.8, 1.2, 1, 0.5, 0, -0.2, 0.2, 0.8, 1.5, 1.5)),
    ("Electronic", "idm", "IDM", (1, 1.5, 0.5, -0.5, -0.3, 0.4, 1, 1.5, 1.7, 1)),
    ("Electronic", "synthwave", "Synthwave", (1.5, 2.2, 1.2, 0, -0.4, 0.3, 0.8, 1.4, 1.7, 1)),
    ("Electronic", "disco", "Disco", (1, 1.8, 1.2, 0.2, -0.3, 0.5, 1.2, 1.6, 1.3, 0.5)),
    ("Electronic", "chillout", "Chillout", (1, 1.5, 1.2, 0.5, 0, -0.2, 0.2, 0.8, 1.1, 0.7)),
    # Hip-hop, R&B and groove-based styles
    ("Hip-Hop & R&B", "hip-hop", "Hip-Hop", (1.8, 2.8, 1.5, -0.8, -1, 0.3, 1.3, 1.5, 0.8, 0)),
    ("Hip-Hop & R&B", "boom-bap", "Boom Bap", (1.2, 2, 1.8, 0.5, -0.7, 0.3, 1.2, 1.3, 0.5, -0.2)),
    ("Hip-Hop & R&B", "trap", "Trap", (2.5, 3, 1, -1.2, -1, 0.5, 1.7, 2, 1.2, 0.2)),
    ("Hip-Hop & R&B", "drill", "Drill", (2.5, 3, 1.2, -1, -0.8, 0.3, 1.5, 1.8, 0.8, -0.2)),
    (
        "Hip-Hop & R&B",
        "lo-fi-hip-hop",
        "Lo-Fi Hip-Hop",
        (0.5, 1.3, 1.7, 1, 0.2, -0.2, -0.5, -0.8, -1.5, -2),
    ),
    (
        "Hip-Hop & R&B",
        "conscious-hip-hop",
        "Conscious Hip-Hop",
        (1, 1.8, 1.2, -0.3, -0.4, 0.7, 1.7, 1.5, 0.6, 0),
    ),
    ("Hip-Hop & R&B", "r-and-b", "R&B", (1.3, 2, 1.5, 0.3, -0.3, 0.5, 1.3, 1.5, 1, 0.4)),
    ("Hip-Hop & R&B", "neo-soul", "Neo Soul", (0.8, 1.5, 1.8, 1, 0.3, 0.4, 1, 1.2, 0.7, 0.2)),
    ("Hip-Hop & R&B", "soul", "Soul", (0.5, 1.2, 1.7, 1.2, 0.5, 0.6, 1.3, 1.5, 0.8, 0.2)),
    ("Hip-Hop & R&B", "funk", "Funk", (0.7, 1.7, 1.8, 0.4, -0.5, 0.5, 1.5, 1.8, 1, 0.2)),
    # Jazz and blues
    ("Jazz & Blues", "jazz", "Jazz", (0.2, 0.7, 1.2, 1, 0.3, 0.4, 1, 1.3, 0.8, 0.3)),
    ("Jazz & Blues", "vocal-jazz", "Vocal Jazz", (-0.3, 0.2, 0.8, 0.8, 0.5, 1, 1.6, 1.4, 0.5, 0)),
    ("Jazz & Blues", "bebop", "Bebop", (-0.2, 0.3, 0.8, 0.6, 0.2, 0.8, 1.5, 1.7, 1, 0.3)),
    ("Jazz & Blues", "cool-jazz", "Cool Jazz", (0.2, 0.6, 1, 0.8, 0.3, 0.4, 0.8, 1, 0.6, 0.2)),
    (
        "Jazz & Blues",
        "jazz-fusion",
        "Jazz Fusion",
        (0.8, 1.5, 1.2, 0, -0.4, 0.5, 1.3, 1.6, 1.1, 0.4),
    ),
    ("Jazz & Blues", "big-band", "Big Band", (0, 0.5, 1, 0.7, 0, 0.7, 1.5, 1.7, 1, 0.2)),
    (
        "Jazz & Blues",
        "smooth-jazz",
        "Smooth Jazz",
        (0.5, 1, 1.3, 0.8, 0.2, 0.3, 0.8, 1.1, 0.8, 0.4),
    ),
    ("Jazz & Blues", "blues", "Blues", (0.4, 1, 1.5, 1.2, 0.3, 0.6, 1.4, 1.6, 0.8, 0.1)),
    (
        "Jazz & Blues",
        "delta-blues",
        "Delta Blues",
        (-0.5, 0, 1, 1.5, 0.8, 0.8, 1.5, 1.4, 0.5, -0.2),
    ),
    (
        "Jazz & Blues",
        "electric-blues",
        "Electric Blues",
        (0.3, 1, 1.4, 0.7, -0.2, 0.7, 1.7, 1.9, 0.8, 0),
    ),
    # Classical and acoustic ensembles
    ("Classical", "classical", "Classical", (-0.3, 0.2, 0.7, 0.5, 0, 0.3, 0.8, 1.2, 1.3, 0.8)),
    ("Classical", "orchestral", "Orchestral", (0.2, 0.7, 1, 0.5, -0.2, 0.2, 0.8, 1.2, 1.2, 0.7)),
    (
        "Classical",
        "chamber-music",
        "Chamber Music",
        (-0.3, 0.1, 0.7, 0.7, 0.2, 0.5, 1, 1.2, 0.8, 0.3),
    ),
    ("Classical", "baroque", "Baroque", (-0.5, -0.2, 0.4, 0.6, 0.3, 0.6, 1.2, 1.5, 1, 0.3)),
    ("Classical", "romantic-classical", "Romantic", (0.5, 1, 1.2, 0.8, 0.2, 0.2, 0.7, 1.1, 1, 0.5)),
    ("Classical", "opera", "Opera", (-0.3, 0.2, 0.7, 0.4, 0.3, 0.9, 1.6, 1.5, 0.8, 0.3)),
    ("Classical", "solo-piano", "Solo Piano", (-0.5, 0, 0.7, 1, 0.5, 0.4, 0.9, 1.3, 1, 0.4)),
    ("Classical", "choral", "Choral", (-0.7, -0.3, 0.3, 0.5, 0.5, 1, 1.5, 1.4, 0.7, 0.2)),
    # Country, folk and acoustic roots
    ("Country & Folk", "country", "Country", (-0.2, 0.4, 1.2, 1, 0, 0.7, 1.5, 1.7, 1, 0.2)),
    (
        "Country & Folk",
        "contemporary-country",
        "Contemporary Country",
        (0.5, 1.2, 1.2, 0, -0.4, 0.7, 1.5, 1.8, 1.1, 0.3),
    ),
    ("Country & Folk", "bluegrass", "Bluegrass", (-0.8, -0.2, 0.8, 1, 0.3, 0.9, 1.7, 2, 1.2, 0.3)),
    ("Country & Folk", "americana", "Americana", (0, 0.5, 1.2, 1.1, 0.3, 0.6, 1.3, 1.5, 0.8, 0.2)),
    ("Country & Folk", "folk", "Folk", (-0.5, 0, 0.8, 1, 0.5, 0.7, 1.3, 1.5, 0.8, 0.2)),
    (
        "Country & Folk",
        "indie-folk",
        "Indie Folk",
        (-0.2, 0.3, 1, 1.2, 0.5, 0.6, 1.2, 1.4, 0.7, 0.2),
    ),
    (
        "Country & Folk",
        "singer-songwriter",
        "Singer-Songwriter",
        (-0.7, -0.2, 0.6, 0.9, 0.6, 1, 1.6, 1.5, 0.6, 0),
    ),
    ("Country & Folk", "celtic", "Celtic", (-0.5, 0, 0.8, 0.8, 0.2, 0.8, 1.5, 1.8, 1.1, 0.4)),
    ("Country & Folk", "acoustic", "Acoustic", (-0.7, -0.2, 0.8, 1.1, 0.5, 0.8, 1.5, 1.7, 1, 0.3)),
    # Reggae and Caribbean music
    ("Reggae & Caribbean", "reggae", "Reggae", (1.2, 2, 1.7, 0.2, -0.7, 0.3, 1.2, 1.4, 0.7, 0)),
    (
        "Reggae & Caribbean",
        "roots-reggae",
        "Roots Reggae",
        (1.5, 2.3, 2, 0.7, -0.5, 0.2, 1, 1.2, 0.5, -0.2),
    ),
    ("Reggae & Caribbean", "dub", "Dub", (2, 2.8, 2, 0.5, -0.8, -0.3, 0.4, 0.8, 0.5, -0.3)),
    (
        "Reggae & Caribbean",
        "dancehall",
        "Dancehall",
        (2, 2.8, 1.2, -0.8, -0.7, 0.5, 1.5, 1.8, 1, 0.1),
    ),
    ("Reggae & Caribbean", "ska", "Ska", (0.3, 1, 1.2, 0, -0.4, 0.8, 1.8, 2, 1, 0.1)),
    (
        "Reggae & Caribbean",
        "rocksteady",
        "Rocksteady",
        (1, 1.8, 1.8, 0.8, -0.3, 0.4, 1.2, 1.4, 0.6, 0),
    ),
    ("Reggae & Caribbean", "soca", "Soca", (1.2, 2, 1, -0.3, -0.5, 0.5, 1.4, 1.8, 1.3, 0.4)),
    # Latin, African and global styles
    ("Latin & Global", "latin-pop", "Latin Pop", (1.2, 2, 1, -0.5, -0.6, 0.5, 1.4, 1.8, 1.3, 0.4)),
    ("Latin & Global", "reggaeton", "Reggaeton", (2, 2.8, 1.2, -1, -0.8, 0.5, 1.5, 1.8, 1, 0)),
    ("Latin & Global", "salsa", "Salsa", (0.5, 1.2, 1.1, 0.2, -0.2, 0.8, 1.8, 2, 1.2, 0.2)),
    ("Latin & Global", "bachata", "Bachata", (0.7, 1.4, 1.3, 0.4, -0.2, 0.7, 1.5, 1.7, 1, 0.2)),
    ("Latin & Global", "bossa-nova", "Bossa Nova", (0, 0.5, 1.2, 1, 0.3, 0.6, 1.2, 1.4, 0.7, 0.2)),
    ("Latin & Global", "flamenco", "Flamenco", (-0.8, -0.3, 0.5, 0.8, 0.5, 1, 1.8, 2, 1.2, 0.3)),
    ("Latin & Global", "afrobeat", "Afrobeat", (1, 2, 1.8, 0.4, -0.4, 0.5, 1.5, 1.7, 1, 0.2)),
    (
        "Latin & Global",
        "afrobeats",
        "Afrobeats",
        (1.8, 2.6, 1.2, -0.6, -0.7, 0.5, 1.5, 1.8, 1, 0.1),
    ),
    ("Latin & Global", "amapiano", "Amapiano", (2, 3, 1.8, 0, -0.8, -0.3, 0.5, 1, 0.8, 0)),
    (
        "Latin & Global",
        "world-fusion",
        "World Fusion",
        (0.7, 1.3, 1.2, 0.4, 0, 0.6, 1.3, 1.5, 1, 0.4),
    ),
    # Music for picture, games and speech
    (
        "Soundtrack & Spoken",
        "cinematic",
        "Cinematic",
        (1.2, 2, 1.5, 0.5, -0.3, 0.2, 0.8, 1.4, 1.5, 1),
    ),
    (
        "Soundtrack & Spoken",
        "epic-orchestral",
        "Epic Orchestral",
        (1.5, 2.5, 1.3, -0.3, -0.5, 0.4, 1.2, 1.8, 1.7, 0.8),
    ),
    (
        "Soundtrack & Spoken",
        "film-score",
        "Film Score",
        (0.8, 1.5, 1.2, 0.4, -0.2, 0.3, 0.9, 1.4, 1.3, 0.7),
    ),
    (
        "Soundtrack & Spoken",
        "game-soundtrack",
        "Game Soundtrack",
        (1.2, 2, 1, -0.5, -0.4, 0.5, 1.3, 1.7, 1.5, 0.6),
    ),
    (
        "Soundtrack & Spoken",
        "anime-soundtrack",
        "Anime Soundtrack",
        (0.8, 1.5, 0.7, -0.5, -0.2, 0.8, 1.7, 2, 1.6, 0.7),
    ),
    ("Soundtrack & Spoken", "chiptune", "Chiptune", (-1, -0.5, 0, 0.5, 1, 1.3, 1.7, 2, 1.5, 0.5)),
    ("Soundtrack & Spoken", "podcast", "Podcast", (-2, -1.5, -1, -0.5, 0.7, 1.8, 2.5, 1.7, 0, -1)),
    (
        "Soundtrack & Spoken",
        "audiobook",
        "Audiobook",
        (-2.5, -2, -1.2, -0.3, 1, 2, 2.3, 1.2, -0.5, -1.5),
    ),
)


EQUALIZER_PRESETS = tuple(_genre_preset(*definition) for definition in _PRESET_DEFINITIONS)
EQUALIZER_GENRES = tuple(dict.fromkeys(preset.genre for preset in EQUALIZER_PRESETS))
