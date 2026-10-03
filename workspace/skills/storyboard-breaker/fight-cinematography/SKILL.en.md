---
name: fight-cinematography
description: High-speed fight cinematography handbook — position formulas, speed annotations, and prompt writing for fight/chase/climax segments
---

# High-Speed Fight Cinematography Handbook (fight / high-speed action segments only)

## When to apply (auto-detection)

When a segment or any sub-shot within it involves **fighting, charging, chasing, dodge-and-counter, flying kicks, heavy-strike bursts, knockback** or other high-speed action, pick the camera work from this handbook's "position formulas" and "speed annotations", taking priority over the base camera vocabulary; dialogue, setup, and transition segments do not use this handbook.

The core logic comes down to two words: **fast** and **anticipation** — manufacture speed, amplify speed. The camera serves three goals:
1. Let the audience follow the trajectory of the action
2. Amplify the impact along the attack direction
3. Use camera speed to create a sense of oppression

## Position formulas (10)

Each formula = camera/movement combo + suited moves + prompt writing (embed directly at the start of a 【镜头N】 in `description`):

| # | Formula | Suited moves | Prompt writing |
|---|---|---|---|
| 1 | Opening clash: low position + rapid push-in | Heavy punches, collisions, the first exchange | Camera at a 0.5 m low angle pushes in rapidly from below, capturing the dust and shockwave volume kicked up by the two fighters' high-speed collision; the LOW angle amplifies the oppression |
| 2 | Lateral tracking: orbit + focus switch | Combos, offense-defense transitions, dynamic exchanges | ORBIT half-surrounds from behind the attacker, focus locked on the struck fighter's hair and clothing hem, switching focus at the instant of impact |
| 3 | Ground-hugging follow: ground-level view + low tracking | Sweep kicks, ground rolls, low movements | Camera hugs the ground at a low angle following the leg sweep, debris rushing past the lens |
| 4 | Airborne follow: low-angle shot + rapid tilt-up | Flying kicks, roundhouse kicks, aerial combos | Low-angle shot, TILT UP rapidly following the fighter as they launch into the air, emphasizing hang time |
| 5 | Impact instant: sudden freeze + slight tremor | The landing blow, climax beat | Close-up at the instant of impact, 0.15 s of high-speed blur, afterimage on the struck body part, slight rebound shake on the camera |
| 6 | Knockback: rapid pull-back + tracking | Heavy strike sending the target flying, repel | Camera pulls back rapidly, tracking along the trail of the fighter being knocked away, the background tearing open in depth |
| 7 | Extreme closeness: tracking view + DOLLY push | Flurries, combination strikes | DOLLY pushes laterally, the camera pressed to the limit against the two grappling fighters, letting the audience feel the oppression of the fist wind |
| 8 | Dodge and counter: reverse push-in + focus switch | Dodges, defensive counters | Camera pushes in rapidly from behind the attacker, PAN whips sideways toward the counter direction, PUSH rushes in on the counter move, focus snapping from attacker to counter-attacker |
| 9 | Low-angle counter: upward angle + rapid pull-back | Rising counterattacks, leaping strikes | Starts on a low-angle upward shot, pulling back rapidly as the fighter leaps, expanding in an instant from a low-angle close-up into an aerial wide |
| 10 | Finishing pose: slow push-in + slow pull-back | Ending a combo, posing, charging the next strike | MCU slowly pushes in to lock the fighter's pose, then PULL slowly retreats defocusing the background, preserving the tension of the instant before the next burst |

## Speed annotations (4, layered onto the position formulas)

| Annotation | Used for | Effect | Writing |
|---|---|---|---|
| Swift fast tracking | Charges, rushes, pursuits, close-quarters movement | Tension, speed, strong rhythm | Rapid medium-shot push-pull; foreground elements streak past, the background smears with lateral motion blur |
| Whip pan | Turns, dodges, impact instants, sudden direction changes | Suddenness, burst | WHIP sweeps across at the instant of contact, focus snapping to the fighter who took the hit |
| Gentle slow pull-back | Suppression ending, dust settling, revealing the battlefield | Tension after the close | Camera pulls back slowly from the most intense point of the clash, focus locked on the character as the battlefield unfolds behind |
| Shock quake | Heavy blows, bursts, shattering, collapses | Deep impact | Camera shakes 0.3 s at the instant of impact, the frame trembling slightly, ground debris bursting outward along the shockwave |

## Writing rules (mapping to the storyboard fields)

- `movement`: pick a formula name or combo from the tables (e.g. "airborne follow (low-angle shot + rapid TILT UP)"), one primary move per sub-shot
- 【镜头N】 in `description`: start each sub-shot with a complete camera instruction = **position/angle + movement + speed adverb + shot size**; keep the numeric values (0.5 m, 0.15 s, 0.3 s) verbatim — video-prompt expands `description` segment by segment, and a lost number is a lost sense of speed
- Speed adverbs must be concrete: rapidly/steadily/slowly/fast-then-slow; never a bare "push-in" or "follow"
- One camera move per sub-shot, continuous within it; fight segments may hard-switch formulas between sub-shots, with cut points aligned to 【镜头N】
- **Fast-slow alternation**: after 2-3 consecutive rapid sub-shots, buffer with one Gentle slow pull-back or an impact freeze before the next burst; all-rapid smears into mush, all-slow loses the oppression
- Bullet time / slow motion remain accent techniques, capped at 1-2 per episode by the base rules, used only at impact instants or finishing poses

## Universal templates (apply directly)

- **High-speed opening**: formula 1 (low rapid push) + Swift
- **Combo segment**: formula 7 (extreme-close DOLLY) ↔ formula 2 (ORBIT focus switch), hard cuts between sub-shots
- **Dodge counter**: formula 8 (reverse push-in + focus switch) + Whip
- **Heavy-strike burst**: formula 5 (0.15 s impact blur) + Shock (0.3 s shake) → formula 6 (rapid pull-back trail)
- **Finishing pose**: formula 10 (slow MCU push-in → Gentle pull-back), charging the next exchange

## One-line summary

The essence of fight cinematography is "**always moving**" — convey speed and oppression through camera motion, alternating rapid bursts with brief freezes, and use the gaps between moves to gather and link.
