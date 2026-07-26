from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import Character, Scene, Script, ScriptLine
from app.use_cases.script_parser import parse_script


async def parse_and_link_script(db: AsyncSession, script: Script) -> None:
    """Re-parses script.raw_text and replaces its Scene/ScriptLine rows,
    resolving speaker names against existing Character rows by name."""
    result = await db.execute(select(Character))
    characters_by_name = {c.name: c for c in result.scalars().all()}

    parsed = parse_script(script.raw_text, set(characters_by_name.keys()))

    existing_lines = (
        await db.execute(select(ScriptLine).where(ScriptLine.script_id == script.id))
    ).scalars().all()
    for line in existing_lines:
        await db.delete(line)
    existing_scenes = (
        await db.execute(select(Scene).where(Scene.script_id == script.id))
    ).scalars().all()
    for scene in existing_scenes:
        await db.delete(scene)
    await db.flush()

    scene_rows: dict[int, Scene] = {}
    for parsed_scene in parsed.scenes:
        scene_row = Scene(
            script_id=script.id,
            order=parsed_scene.order,
            description=parsed_scene.description,
            background_prompt=parsed_scene.background_prompt,
            camera_notes=parsed_scene.camera_notes,
        )
        db.add(scene_row)
        scene_rows[parsed_scene.order] = scene_row
    await db.flush()

    for parsed_line in parsed.lines:
        speaker = characters_by_name.get(parsed_line.speaker_name) if parsed_line.speaker_name else None
        db.add(
            ScriptLine(
                script_id=script.id,
                scene_id=scene_rows[parsed_line.scene_order].id,
                order=parsed_line.order,
                speaker_character_id=speaker.id if speaker else None,
                text=parsed_line.text,
                detected_language=parsed_line.detected_language,
                expression_tag=parsed_line.expression_tag,
            )
        )
    await db.commit()
