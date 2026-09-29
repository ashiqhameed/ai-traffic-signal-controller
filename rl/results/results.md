# Results

300 evaluation episodes x 200 cycles (~17 simulated minutes each) per policy, on traffic the agent never saw in training. ± is a 95% confidence interval.

## Balanced — Original demo traffic: 0-3 new cars per road per cycle

| Policy | Mean wait / car (s) | 95th pct wait (s) | vs. original heuristic |
|---|---|---|---|
| Fixed-time | 17.03 ± 0.25 | 44.3 ± 1.2 | +33.0% ± 1.8% |
| Priority heuristic (original) | 12.81 ± 0.10 | 26.7 ± 0.3 | — |
| Longest queue first | 11.35 ± 0.08 | 26.5 ± 0.3 | -11.3% ± 0.4% |
| Q-learning agent | 11.23 ± 0.07 | 25.5 ± 0.2 | -12.2% ± 0.4% |

## Rush Hour — Same total demand, concentrated on North-South

| Policy | Mean wait / car (s) | 95th pct wait (s) | vs. original heuristic |
|---|---|---|---|
| Fixed-time | 98.21 ± 1.99 | 231.2 ± 4.8 | +635.4% ± 13.4% |
| Priority heuristic (original) | 13.35 ± 0.11 | 28.1 ± 0.3 | — |
| Longest queue first | 10.93 ± 0.09 | 36.9 ± 0.4 | -18.0% ± 0.4% |
| Q-learning agent | 10.56 ± 0.07 | 31.5 ± 0.3 | -20.7% ± 0.3% |
