from stem_api.audio import classify_stem, pick_clean_stem


def test_classify_stem_detects_echo_and_dry() -> None:
    assert classify_stem("voice_no_echo.wav") == "dry"
    assert classify_stem("my_echo_track.wav") == "echo"


def test_pick_clean_stem_prefers_dry(tmp_path) -> None:
    dry = tmp_path / "dry.wav"
    wet = tmp_path / "wet.wav"
    dry.touch()
    wet.touch()

    stems = {"reverb": wet, "dry": dry}
    selected = pick_clean_stem(stems)
    assert selected == dry


def test_pick_clean_stem_falls_back_to_first_item(tmp_path) -> None:
    alt = tmp_path / "alt.wav"
    alt.touch()
    stems = {"unknown": alt}
    selected = pick_clean_stem(stems)
    assert selected == alt
