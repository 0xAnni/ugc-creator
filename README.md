# ugc-creator

A Claude Code **skill** that turns Claude into a hyper-realistic AI UGC influencer
studio. Built by [@0x_Anni](https://x.com/0x_Anni); the full system, the economics,
and the story behind it are in [the article](https://x.com/0x_Anni/status/2067776249485791496).

If this saves you time, star the repo. It helps more builders find it. It treats a synthetic influencer as **data** (a JSON identity card) plus a
deterministic **6-layer prompt assembler**, so the same person comes out in every
shot instead of drifting between generations.

> Don't prompt an AI influencer. **Compile one.**

## What's inside

```
ugc-creator/
├── SKILL.md                      # the skill: workflows + rules (this is what Claude reads)
├── README.md                     # you are here
├── assets/
│   ├── actor-card.schema.json    # JSON schema for an actor identity card
│   └── actors/
│       └── lila.json             # a complete worked-example actor
├── references/
│   ├── identity-card.md          # how to build a consistent actor card
│   ├── prompt-layers.md          # the 6-layer prompt assembler (the engine)
│   ├── realism-anchors.md        # the 10 "imperfection" anchors that kill the AI look
│   ├── camera-profiles.md        # 4 iPhone camera simulation profiles
│   ├── shot-types.md             # 7 reusable UGC shot formats
│   ├── video-kling.md            # Kling 3.0 motion rules + fal.ai pipeline
│   └── reference-lock.md         # v2: the identity latch (face pack, cref/PuLID, Kling elements, LoRA)
└── scripts/
    ├── generate_image.py         # prompt->still via LivePair (t2i + anchor-locked i2i)
    └── generate_video.py         # image->video via Kling 3.0 on fal.ai (v3 elements)
```

**v2:** adds the reference-lock layer. The card kills prompt-side drift; the
face pack + reference conditioning (cref / PuLID / InstantID for stills, Kling
v3 `elements` for video, LoRA for permanent rosters) kills sampler-side drift.
The script now targets Kling 3.0 and takes the face pack via `--element-frontal`.

## Install

One command, into your global Claude Code skills directory:

**macOS / Linux:**
```bash
git clone https://github.com/0xAnni/ugc-creator.git ~/.claude/skills/ugc-creator
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/0xAnni/ugc-creator.git $env:USERPROFILE\.claude\skills\ugc-creator
```

Or install per-project instead: clone (or copy the folder) into
`<your-project>/.claude/skills/ugc-creator/`.

No git? Download the zip: **Code → Download ZIP**, unzip, and put the
`ugc-creator` folder in the same path.

Claude Code auto-discovers it. The skill triggers on requests like *"make my AI
influencer consistent,"* *"generate a week of UGC for my AI girl,"* or *"write a
Kling video prompt."*

## Quickstart

1. **Create an actor**: "Build me a UGC actor: Swedish, early 20s, beachy." Claude
   writes an identity card to `assets/actors/`.
2. **Generate a shot**: give a one-line brief:
   `Lila, just out of the sea, wet hair, golden hour`
   Claude returns a full positive + negative prompt — feed it to
   `scripts/generate_image.py` (needs an `LP_KEY` from
   https://livepairai.com/settings; `--anchor` keeps her face across
   scenes via i2i) or paste into your image model of choice.
3. **Generate a week**: give seven one-liners; the consistency protocol keeps her
   the same person in every frame.
4. **Animate**: feed a still + a motion prompt to `scripts/generate_video.py`
   (needs `pip install fal-client` and a `FAL_KEY`).

## The idea in one line

Identity is a JSON schema, not a re-uploaded image, so consistency is
deterministic instead of hopeful. Build the engine once; generate forever.
