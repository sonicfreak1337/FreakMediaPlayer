from freak_media_player.models.equalizer import EQUALIZER_PRESETS
from freak_media_player.player.audio_backend import NullAudioBackend
from freak_media_player.services.equalizer_service import EqualizerService


def test_equalizer_presets_have_matching_band_counts() -> None:
    band_count = len(EQUALIZER_PRESETS[0].bands)

    assert all(len(preset.bands) == band_count for preset in EQUALIZER_PRESETS)


def test_equalizer_includes_metal_subgenre_presets_with_headroom() -> None:
    presets = {preset.preset_id: preset for preset in EQUALIZER_PRESETS}

    assert {
        "death-metal",
        "deathcore",
        "black-metal",
        "doom-metal",
        "thrash-metal",
        "djent",
        "progressive-metal",
    } <= presets.keys()
    assert all(preset.preamp_db <= 0 for preset in presets.values())


def test_equalizer_service_selects_preset() -> None:
    backend = NullAudioBackend()
    service = EqualizerService(audio_backend=backend)

    selected = service.select_preset("metalcore")

    assert selected.preset_id == "metalcore"
    assert service.current_preset().preset_id == "metalcore"
    assert backend.equalizer_preset().preset_id == "metalcore"


def test_equalizer_service_stores_custom_gains() -> None:
    backend = NullAudioBackend()
    service = EqualizerService(audio_backend=backend)
    gains = (1.0, 0.5, 0.0, -1.0, -2.0, 0.0, 1.5, 2.0, 1.0, 0.5)

    selected = service.set_custom_gains(gains)

    assert selected.preset_id == "custom"
    assert tuple(band.gain_db for band in selected.bands) == gains


def test_equalizer_service_notifies_persistence_after_changes() -> None:
    saved_presets = []
    service = EqualizerService(
        audio_backend=NullAudioBackend(),
        preset_changed=saved_presets.append,
    )

    selected = service.select_preset("metalcore")

    assert saved_presets == [selected]
