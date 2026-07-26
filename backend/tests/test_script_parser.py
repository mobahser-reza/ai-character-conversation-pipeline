from app.use_cases.script_parser import detect_language, parse_script

SAMPLE = """SCENE: A cozy modern living room, warm lighting
[Aryan] (smiling, leaning forward): Hey, kaise ho aap?
[Meera] (curious): I'm good yaar, just thinking about our next trip.
CAMERA: slow zoom in
[Aryan] (laughing): Trip? Let's plan it right now!
"""


def test_parses_scenes_and_lines():
    result = parse_script(SAMPLE, known_character_names={"Aryan", "Meera"})

    assert len(result.scenes) == 1
    assert result.scenes[0].description == "A cozy modern living room, warm lighting"
    assert result.scenes[0].camera_notes == "slow zoom in"

    assert len(result.lines) == 3
    assert result.lines[0].speaker_name == "Aryan"
    assert result.lines[0].expression_tag == "smiling, leaning forward"
    assert result.lines[1].speaker_name == "Meera"
    assert not result.unmatched_speakers


def test_flags_unmatched_speaker():
    result = parse_script("[Unknown]: hello there", known_character_names={"Aryan"})
    assert result.unmatched_speakers == {"Unknown"}


def test_detects_hindi_devanagari():
    assert detect_language("नमस्ते आप कैसे हैं") == "hi"


def test_detects_hinglish():
    assert detect_language("Hey yaar, kaise ho aap today?") == "hinglish"


def test_detects_english():
    assert detect_language("Hello, how are you doing today?") == "en"


def test_multiple_scenes_split_on_scene_marker():
    script = (
        "SCENE: Kitchen\n"
        "[Aryan]: Coffee?\n"
        "SCENE: Garden\n"
        "[Meera]: Sure, let's go outside.\n"
    )
    result = parse_script(script, known_character_names={"Aryan", "Meera"})
    assert len(result.scenes) == 2
    assert result.scenes[0].description == "Kitchen"
    assert result.scenes[1].description == "Garden"
    assert result.lines[0].scene_order == 0
    assert result.lines[1].scene_order == 1
