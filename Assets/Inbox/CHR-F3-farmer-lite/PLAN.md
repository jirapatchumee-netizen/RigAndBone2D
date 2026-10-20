# Rig plan: char_farmer (pack CHR-F3-farmer-lite)
reference: `Assets/Source/chr_f1_farmer/v001/parts/char_farmer_hero_v01.png`; units_per_px 0.26; generation scale vs reference = **1.18x** (bigger = sharper parts); sheet 1536x1024, gutter 6%

| part | parent | reference bbox | painted box (with overlap) | draw size px | pivot (ref px) | height units | layer |
|---|---|---|---|---|---|---|---|
| body | root | [185, 425, 545, 872] | [185, 413, 545, 872] | 425x542 | [345, 640] | 119.34 | 20 |
| arm_r | body | [118, 488, 272, 705] | [118, 454, 282, 705] | 194x296 | [245, 520] | 65.26 | 17 |
| arm_l | body | [465, 478, 580, 685] | [455, 444, 580, 685] | 148x284 | [482, 505] | 62.66 | 27 |
| hat | head | [0, 0, 626, 378] | [0, 0, 626, 378] | 739x446 | [310, 300] | 98.28 | 50 |

Sprites to generate: **4** (+ heads/expressions reused from the approved pack if listed in the spec).
Nothing here is generated; Codex draws exactly these pieces in ONE edit of the approved reference.
