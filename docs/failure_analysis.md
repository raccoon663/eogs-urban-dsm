# Failure analysis

## Vegetation

Vegetation is the largest remaining error source in all three configurations. On the common valid mask, vegetation MAE is 2.999 m for four views, 3.135 m for eight, and 3.192 m for nine, compared with sub-meter building and ground MAE in the eight- and nine-view runs.

The selected crop in `figures/vegetation_failure.png` shows a consistent geometric failure: irregular reference canopies become smooth surfaces, adjacent crowns merge, and crown boundaries spread into nearby pixels. The 4-view crop has a smaller mean height bias in this one component, but it also loses canopy detail. Its lower vegetation MAE does not support the claim that fewer views reconstruct vegetation better.

## Buildings and transitions

Four views produce low roofs, blurred edges, and leakage into surrounding surfaces. Added coverage restores much of the roof height and outline. Local errors remain at roof edges, building/tree boundaries, the waterfront, and other sharp surface transitions.

## Interpretation limits

- One 256 m × 256 m scene was evaluated.
- Each configuration was run once with seed 0.
- Only one nested 4/8-view selection was tested.
- View count also changes image composition and acquisition dates.
- Satellite and LiDAR dates may differ, and vegetation changes over time.
- No independent DTM was available, so the analysis concerns DSM surface height rather than canopy height above ground.
- The reference vertical datum and exact LiDAR acquisition date were not verified.

The results support the narrow conclusion that four views were insufficient for rigid surfaces in this experiment, while vegetation remained difficult at every tested coverage level. They should not be generalized city-wide or to forest canopy reconstruction.
