# Third-party notes

Everything in this repository is MIT. What it touches:

| Piece | Licence | How it is used |
|---|---|---|
| numpy, scipy | BSD-3-Clause | required Python dependencies |
| FFmpeg | LGPL/GPL (depends on the build) | called as an external program, not bundled or linked |
| Audiobox Aesthetics (Meta) | CC-BY-4.0 | optional extra critic, installed by the user; credit Meta if you redistribute its scores or model |

Deliberately left out: Essentia (AGPL-3.0, and its mood models are CC BY-NC-SA, non-commercial), and any SoundFont or sample
pack with unclear terms. The music is synthesised from maths in `compose.py`, so no recorded audio is shipped, and the
tracks it produces carry no third-party rights.
