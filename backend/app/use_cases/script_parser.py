import re
from dataclasses import dataclass, field

from langdetect import DetectorFactory, detect

DetectorFactory.seed = 0

_SPEAKER_LINE = re.compile(r"^\[(?P<speaker>[^\]]+)\]\s*(\((?P<expression>[^)]*)\))?\s*:\s*(?P<text>.+)$")
_SCENE_LINE = re.compile(r"^SCENE:\s*(?P<desc>.+)$", re.IGNORECASE)
_CAMERA_LINE = re.compile(r"^CAMERA:\s*(?P<notes>.+)$", re.IGNORECASE)

_DEVANAGARI_RE = re.compile(r"[ऀ-ॿ]")
_HINDI_ROMAN_WORDS = {
    "hai", "hain", "nahi", "kya", "kaise", "kaisa", "acha", "accha", "yaar",
    "kyun", "kyu", "matlab", "bas", "bhi", "toh", "tum", "aap", "mujhe",
    "tumhe", "kar", "karo", "raha", "rahi", "rahe", "chal", "chalo", "haan",
}


@dataclass
class ParsedLine:
    order: int
    scene_order: int
    speaker_name: str | None
    text: str
    detected_language: str
    expression_tag: str | None


@dataclass
class ParsedScene:
    order: int
    description: str = ""
    background_prompt: str = ""
    camera_notes: str = ""


@dataclass
class ParseResult:
    scenes: list[ParsedScene] = field(default_factory=list)
    lines: list[ParsedLine] = field(default_factory=list)
    unmatched_speakers: set[str] = field(default_factory=set)


def detect_language(text: str) -> str:
    """Devanagari script -> hi. Romanized Hindi words mixed with Latin -> hinglish.
    Otherwise fall back to langdetect, defaulting to en on ambiguity."""
    if _DEVANAGARI_RE.search(text):
        return "hi"

    words = re.findall(r"[a-zA-Z']+", text.lower())
    hindi_hits = sum(1 for w in words if w in _HINDI_ROMAN_WORDS)
    if hindi_hits and hindi_hits < len(words):
        return "hinglish"
    if hindi_hits and hindi_hits == len(words):
        return "hi"

    try:
        code = detect(text)
    except Exception:
        return "en"
    return "en" if code == "en" else code


def parse_script(raw_text: str, known_character_names: set[str]) -> ParseResult:
    result = ParseResult()
    current_scene = ParsedScene(order=0)
    has_scene_content = False
    line_order = 0

    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        scene_match = _SCENE_LINE.match(line)
        if scene_match:
            if has_scene_content:
                result.scenes.append(current_scene)
                current_scene = ParsedScene(order=len(result.scenes))
                has_scene_content = False
            current_scene.description = scene_match.group("desc")
            current_scene.background_prompt = scene_match.group("desc")
            continue

        camera_match = _CAMERA_LINE.match(line)
        if camera_match:
            current_scene.camera_notes = camera_match.group("notes")
            continue

        speaker_match = _SPEAKER_LINE.match(line)
        if speaker_match:
            has_scene_content = True
            speaker_name = speaker_match.group("speaker").strip()
            if speaker_name not in known_character_names:
                result.unmatched_speakers.add(speaker_name)
            text = speaker_match.group("text").strip()
            result.lines.append(
                ParsedLine(
                    order=line_order,
                    scene_order=current_scene.order,
                    speaker_name=speaker_name,
                    text=text,
                    detected_language=detect_language(text),
                    expression_tag=speaker_match.group("expression"),
                )
            )
            line_order += 1
            continue

        # Plain narration/unlabeled line: treat as scene description continuation
        current_scene.description = f"{current_scene.description} {line}".strip()
        has_scene_content = True

    if has_scene_content or not result.scenes:
        result.scenes.append(current_scene)

    return result
