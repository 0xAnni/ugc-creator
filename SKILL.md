---
name: ugc-creator
description: >-
  Turns Claude into a hyper-realistic AI UGC influencer studio. Use this whenever
  the user wants to create, manage, or scale a synthetic/AI influencer or AI UGC
  creator: building a consistent character, writing image or video generation
  prompts for an AI model (Flux, Midjourney, Kling, Sora, Veo, etc.), producing
  TikTok/Reels/Shorts-style content, product/testimonial/UGC clips, or "shot on
  iPhone" lifestyle photos of a recurring synthetic person. Trigger it even when
  the user doesn't say "skill": e.g. "make my AI model look the same in every
  post", "generate a week of UGC for my AI girl", "why does my AI influencer
  change face every time", "write a Kling video prompt", or "I need a consistent
  AI avatar for ads". The skill treats a character as DATA (a JSON identity card)
  plus a deterministic 6-layer prompt assembler, so the same person comes out
  every time instead of drifting between generations.
---

# ugc-creator

Build AI UGC influencers that stay **the same person** across every shot, scene,
and video, and generate a whole content calendar from one-line briefs.

The core idea: **don't prompt a character, compile one.** A character is not a
saved image you keep re-uploading and praying the face holds. It's a **JSON
identity card** (the single source of truth) plus a deterministic **6-layer
prompt assembler**. Identity lives in data, so consistency stops being luck and
becomes a property of the system.

## When you're invoked, figure out which job this is

1. **Create an actor**: the user wants a new synthetic person. → Go to
   *Workflow A*.
2. **Generate a shot (or a batch)**: the user has an actor and wants
   image/video prompts. → Go to *Workflow B*.
3. **Animate a shot to video**: turn a still into a Kling 3.0 clip via fal.ai.
   → Go to *Workflow C*.
4. **Fix drift / lock consistency**: "she looks different every time." →
   Two layers: the identity card + consistency protocol
   (`references/prompt-layers.md`) kills prompt-side variance; the reference
   lock (`references/reference-lock.md`) kills sampler-side variance. For
   recurring content, use both.

If the user just describes a vibe ("a Swedish beach girl"), assume they want
Workflow A first, then B.

## The mental model (state this to the user once, briefly)

- **Identity = data, not a vibe.** A re-uploaded image with a begging paragraph
  is a soft suggestion the model reinterprets every time → drift. A JSON card
  with an exact skin hex (`#F8C4AE`, not "fair skin") and pinned asymmetry keeps
  every prompt aiming at the same person.
- **Two kinds of drift, two locks.** The card kills the drift *you* cause
  (prompt variance). The sampler still re-rolls within what's left, and that is
  killed by reference conditioning: a face pack generated from the card, then
  cref / PuLID / InstantID for stills and Kling v3 `elements` for video. Card =
  spec, references = latch. See `references/reference-lock.md`.
- **Realism = imperfection, not beauty.** AI images fail because they're *too
  clean*. We inject flaws on purpose (the 10 anchors).
- **Shots = assembled, not authored.** Every prompt is 6 ordered layers, with
  the character lock always first so nothing downstream can renegotiate the face.
- **The skill is the asset.** Built once, reused forever, forked into a roster.

---

## Workflow A: Create an actor (the identity card)

The identity card is the heart of everything. Get it right before generating
anything, because every later step inherits from it.

1. **Gather traits.** Ask the user for, or propose, each field. If they give you
   reference images, describe each separately and let the user pick which trait
   comes from which (hair from one, eyes from another). You're mixing traits
   into a *new* synthetic person, not copying a real one.
2. **Pin the hard-to-keep fields with precision.** These are the ones models love
   to "fix," so they must be exact:
   - `skin_tone_hex`: an actual hex value, never a phrase.
   - `eyes`, `jawline`: include a deliberate, specific **asymmetry**
     ("left eye 2% smaller", "left jaw a touch softer"). Consistent asymmetry is
     what reads as a real individual.
   - `distinguishing_marks`: a mole/scar/freckle pinned to specific real estate.
   - `prompt_seed`: a fixed integer to anchor generation.
3. **Write the card** to `assets/actors/<actor_id>.json` following the schema in
   `assets/actor-card.schema.json`. Use `assets/actors/lila.json` as the worked
   example.
4. **Validate the base portrait.** Generate one straight-on portrait first (a
   neutral build: studio or simple background, the actor at rest). Do not move on
   until the face is right: every later shot inherits from it.
5. **Build the face pack.** From the validated portrait, generate the 4-6
   canonical reference shots (frontal, three-quarters, profile, expression,
   full body) per `references/reference-lock.md`, and store them in
   `assets/actors/<actor_id>/facepack/`. The pack is the identity latch for
   every batch and every video; it is a build output of the card, never a
   source of truth.

Full field-by-field guidance: **`references/identity-card.md`**.

---

## Workflow B: Generate a shot from a one-line brief

This is the payoff. The user gives one line; you assemble a full, production-ready
prompt. Example brief:

> `Lila, just out of the sea, wet hair, golden hour`

**Steps:**

1. **Load the actor card** named in the brief (`assets/actors/<name>.json`).
2. **Pick the shot type** (one of 7) and the **camera profile** (one of 4) that
   fit the brief. If the brief implies them, choose silently; otherwise ask.
   See `references/shot-types.md` and `references/camera-profiles.md`.
3. **Assemble the 6 layers**: this is the deterministic core. Read
   `references/prompt-layers.md` for the exact assembly spec. In short:
   1. **Character lock**: every card field, verbatim. Always first.
   2. **Scenario**: what she's doing + its physical consequences (wet skin,
      goosebumps, flushed cheeks).
   3. **Environment**: place + the lighting physics it implies.
   4. **Camera**: the chosen iPhone profile, framing, distance.
   5. **Realism injection**: all 10 anchors (`references/realism-anchors.md`).
   6. **Negative prompt**: everything we refuse (plastic skin, symmetry,
      beauty-filter smoothing, extra fingers, CGI sheen).
4. **Output** the final positive prompt and the negative prompt as separate
   blocks the user can paste into their image model (Flux / Midjourney / fal.ai)
   — or render it directly with `scripts/generate_image.py` (LivePair, needs an
   `LP_KEY`; pass the face-pack frontal as `--anchor` to run the identity-locked
   i2i edit).
5. **Attach the reference lock** whenever the shot is part of recurring content:
   the face-pack frontal via `--cref` (Midjourney), PuLID / InstantID (Flux,
   SDXL), or as the edit input (gpt-image). Weights and failure modes:
   `references/reference-lock.md`.
6. **For a batch** (a content calendar), repeat per brief but hold the
   **consistency protocol**: Layer 1 is byte-identical across all shots, the
   asymmetry/marks/skin-hex never move, and the same face-pack reference rides
   on every generation. Never let the scenario rewrite the face.

A week of content is just seven one-line briefs. The marginal cost of a new shot
is one sentence.

---

## Workflow C: Animate a shot to video (Kling 3.0 via fal.ai)

Stills get a feed; video gets a creator. Motion is where most AI influencers
break (warping faces, melting hands), so we direct the model with restraint.

1. **Write the motion prompt** following the director rules in
   `references/video-kling.md`. The non-negotiables:
   - **One main action per clip.** Not "waves, turns, smiles, sips". Pick one.
   - **Say "static camera" twice** when you want a locked frame (models ignore it
     said once).
   - **Small, human motion**: blinks, micro head tilts, a breath, natural lip
     sync. Big motion detonates identity.
   - **Vertical 9:16.**
2. **Lock identity with an element.** Kling v3 takes the character as a
   first-class `elements` input (face-pack frontal + reference angles) and you
   address her in the prompt as `@Element1`. This is the video-side identity
   latch; use it on every clip of a recurring actor.
3. **Generate** with `scripts/generate_video.py` (image→video on Kling 3.0 via
   fal.ai). It needs a `FAL_KEY` env var, the start image, and optionally
   `--element-frontal` / `--element-ref` for the identity element. Run
   `python scripts/generate_video.py --help` for usage.

---

## Reference files (read the one you need, when you need it)

| File | Read it when |
|------|-------------|
| `references/identity-card.md` | Creating or editing an actor (field-by-field guidance) |
| `references/prompt-layers.md` | Assembling any shot prompt; fixing drift; batch consistency |
| `references/realism-anchors.md` | You need the 10 anchors and how to phrase each |
| `references/camera-profiles.md` | Choosing/writing the camera layer (4 iPhone profiles) |
| `references/shot-types.md` | Choosing the shot type (7 UGC formats) |
| `references/video-kling.md` | Writing motion prompts / running the fal.ai script |
| `references/reference-lock.md` | Latching identity beyond the card: face pack, cref/PuLID/InstantID, Kling v3 elements, LoRA |

## Assets

- `assets/actor-card.schema.json`: the JSON Schema for identity cards.
- `assets/actors/lila.json`: a complete worked example actor.

## Hard rules (the few things that are actually non-negotiable)

These earn their rigidity because breaking them is exactly how the system fails:

- **Layer 1 (character lock) is always first and always complete.** If you drop a
  field, that field drifts.
- **`skin_tone_hex` is a hex, never a phrase.** A phrase is re-interpretable; a
  hex is not.
- **Preserve the asymmetry and marks as features, not noise.** The model's
  instinct is to "beautify" them away: that's the drift.
- **One main action per video clip.**
- **Recurring content always carries a reference.** The card alone pins the
  spec, not the sampler. Face pack on stills, `elements` on video. If a
  reference disagrees with the card, regenerate the reference from the card.

Everything else is guidance you can adapt to the brief.
