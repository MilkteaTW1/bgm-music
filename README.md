# bgm-music

Tell it what kind of video you are making; it composes matching background music, attacks its own result, fixes what was attacked, and hands you the best take. No music theory needed.

你只要說影片類型(教學、Vlog、科技、遊戲實況…),它就套用那類影片的配樂規則自動作曲,自己挑毛病、自己修,最後交出最好的一版。不需要懂樂理。

## Use

```bash
pip install numpy scipy        # and ffmpeg on your PATH
python -m bgm_music --list     # video types and why each sounds the way it does
python -m bgm_music --video vlog --duration 45
python -m bgm_music --video 教學 --duration 90 --loop
```

Output: `out/<type>_<seconds>s.mp3` plus a `.review.json` with every draft's score and what the critic complained about.

## How it works

1. **Rules per video type** (`profiles.py`): tempo, mode, chords, drums, brightness, loudness. Videos with a voice-over get no busy melody, a dip around the voice band and a quieter level.
2. **Compose** (`compose.py`): chords, bass, arpeggio, optional melody and drums, synthesised from maths with numpy. No samples, so nothing third-party ships with the music.
3. **Critic** (`review.py`): measures clipping, rumble, harshness, space for a voice, pacing, repetition, loop seams and endings.
4. **Adversarial loop** (`adversary.py`): every complaint maps to a concrete repair; only the better draft of each lineage survives each round.

## Honest limits

- The score is the critic's opinion, written by the same author as the composer. It rewards what it measures, so a high score is not proof the music is beautiful. **Your ears are the final judge.**
- The sound is synthesised, so it is thinner than recorded instruments.
- Planned: an independent critic (a learned quality model such as Meta's Audiobox Aesthetics, CC-BY-4.0) and feedback in plain words ("too loud", "too plain") that tunes the rules.

MIT licensed. See `NOTICE.md` for what it touches.
