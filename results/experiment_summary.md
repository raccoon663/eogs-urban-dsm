# Experiment summary

All primary rows are single-seed RTX 5080 runs evaluated on the same 260,610-pixel mask.

| Views | MAE (m) | RMSE (m) | Median AE (m) | P90 AE (m) | Runtime (s) | Peak allocated VRAM (MiB) | Gaussians |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 4 | 2.451348 | 3.202577 | 2.129531 | 5.037973 | 267.890 | 901.131 | 86,134 |
| 8 | 1.372550 | 2.363790 | 0.504714 | 4.037796 | 215.282 | 700.156 | 39,219 |
| 9 | 1.330521 | 2.305070 | 0.599343 | 3.893315 | 213.834 | 675.853 | 32,827 |

Four to eight views reduces MAE by 44.01%. Eight to nine reduces it by 3.06%. The latter is a small change in one scene and is not evidence of a universal saturation point.

The independently reproduced RTX 4060 nine-view baseline reports MAE 1.354606 m and RMSE 2.318913 m on its original 261,121-pixel mask. The comparable RTX 5080 nine-view per-run values are 1.332051 m and 2.307607 m on 261,121 pixels. Software stacks differ, so this close agreement is reproducibility evidence rather than a GPU comparison.
