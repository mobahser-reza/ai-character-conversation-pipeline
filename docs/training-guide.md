# Training Guide — Running the Pipeline Yourself

This is the walkthrough for going from "empty dashboard" to "finished video," and
for producing every future video after handover. No coding required for any of this.

## 0. First-time setup

1. Install Docker Desktop.
2. In the project root: `cp .env.example .env`, then fill in:
   - `JWT_SECRET_KEY` — any random string (command to generate one is in the file's comment)
   - `ENCRYPTION_MASTER_KEY` — a Fernet key (command to generate one is in the file's comment)
   - `ADMIN_USERNAME` / `ADMIN_PASSWORD` — your dashboard login
3. `docker compose up --build`
4. Open `http://localhost:3000`, log in with the admin credentials from `.env`.

At this point every pipeline stage runs in **stub mode** — the pipeline works
end-to-end and produces a real (if placeholder-looking) video with zero API cost.
Use this to learn the workflow before spending money on real providers.

## 1. Add your API keys (once real vendors are ready)

Go to **API Keys** in the dashboard.
1. Paste your ElevenLabs / HeyGen / Runway (or others) key, save.
2. Under "Active provider per capability," switch `tts` → `elevenlabs`,
   `avatar` → `heygen`, `video_gen` → `runway` (or whichever combination you're using).
   Leave any capability on `local_stub` if you don't have that vendor yet — the
   pipeline still runs, that stage just renders a placeholder.

## 2. Create your two permanent characters

Go to **Characters** → fill in name, personality/description, and a reference
image URL (a hosted photo/art of the character HeyGen or your avatar provider
will animate). Save.

Then, on the same character card, add a **voice**:
- Provider: `elevenlabs` (or your TTS vendor)
- Provider voice id: the voice ID from your ElevenLabs voice library (clone your
  own voice there first if you want a custom one, then copy its ID here)
- Language: `en`, `hi`, or `hinglish` — add one voice profile per language you'll
  use for that character; the pipeline picks the character's assigned default
  voice regardless of language today, so for true multi-voice-per-language you'd
  extend `run_pipeline.py`'s voice selection (see architecture.md)

Repeat for your second character. Do this once — it's permanent.

## 3. Write a script

Go to **Scripts**. The only input format you ever need:

```
SCENE: A cozy modern living room, warm lighting, medium shot
[Aryan] (smiling, leaning forward): Hey, kaise ho aap?
[Meera] (curious, arms crossed): I'm good yaar, just thinking about our next trip.
CAMERA: slow zoom in
[Aryan] (laughing): Trip? Let's plan it right now!
```

- `[Name]` must exactly match a character name you created in step 2.
- `(...)` is optional — describes expression/body language for that line.
- `SCENE:` starts a new background; `CAMERA:` sets that scene's camera movement.
- Mix English, Hindi (Devanagari or Latin script), and Hinglish freely, line by line.

Click **Preview speakers/languages** before saving — it flags any character name
that doesn't match one you've created, and shows you the detected language per
line, so you can catch typos before spending on generation.

Click **Save script**.

## 4. Generate the video

From the Scripts list, click **Generate video →** next to your saved script.
Pick the aspect ratio (9:16 for Reels/Shorts/TikTok, 1:1 for feed posts, 16:9 for
YouTube), click **Start pipeline**. You're dropped onto the job page, which shows
live progress through all six stages: tts → avatar → background → composite →
subtitles → export. When it finishes, the final video plays right there and is
also listed under **Jobs**.

## 5. Iterate

If a line reads wrong or a scene prompt needs tweaking, go back to **Scripts**,
edit the raw text, save (it re-parses automatically), and generate again from
step 4. Each generation is a new independent job — nothing about your characters
or previous videos is touched.

## Troubleshooting

- **Unmatched speaker warning**: the `[Name]` in your script doesn't exactly
  match a character name (case-sensitive). Fix the script or the character name.
- **Job fails at a stage**: check that stage's provider has an active API key
  under **API Keys**. The job's error message names the failing stage.
- **Video looks like placeholder graphics**: that capability is still set to
  `local_stub` — switch it to your real provider under **API Keys**.
