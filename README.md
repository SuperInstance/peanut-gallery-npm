# peanut-gallery

> **The peanut gallery for AI outputs.** Multiple models comment, grade, and one-up each other in a GAN game for many uses.

The "peanut gallery" is a concept from vaudeville — a vocal, opinionated audience that heckles from the cheap seats. In AI, this becomes:

**Multiple models watch the same output, then try to outperform each other by finding edges and breaking each other's paradigms.**

## The pattern

```
[Target output] → Model A produces v1
                → Model B critiques v1, produces v2
                → Model C critiques v2, produces v3
                → ...
                → JEV + JEPA vote on which version is best
                → Winners are canon, losers are archived
```

## The substrate cell is the unit

Each round of the gallery is a substrate cell:
- `cell_id`: unique
- `prev_hash`: chain to previous round
- `producer`: which model made it
- `critic_feedback`: what the gallery said
- `jev_score`: how JEV scored it
- `jepa_score`: how JEPA scored it

## Use cases

- **Creative writing**: models compete to write the best poem
- **Code review**: models find bugs in each other's code
- **Image description**: models describe images better than each other (extends JEV-Diffusion)
- **Strategy games**: models play each other at games
- **Math proofs**: models find errors in each other's proofs

## Files (coming)

- `gallery.py` — the main loop
- `models.py` — model registry
- `critic.py` — what the gallery says
- `voting.py` — JEV + JEPA voting
- `examples/` — pre-run competitions
