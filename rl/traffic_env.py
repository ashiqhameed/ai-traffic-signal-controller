"""
Discrete-time simulation of the four-way intersection in traffic_controller.py,
used to train and fairly compare signal-control policies.

Modelled on the original demo:
- every 5-second cycle, each road gets 0-3 new cars (per-scenario maximum)
- 10% of cycles are emergency overrides: a random road is forced green
- a green road clears 1-3 cars per second
- `waiting` follows the same update rules the original heuristic relies on

One deliberate addition: switching the green road costs SWITCH_LOST_SECONDS of
yellow/all-red time with no cars moving, while holding the same green does
not. This "lost time" is standard in real signal timing and gives a policy
something non-trivial to learn (when switching is worth it).

All randomness (arrivals, emergencies, discharge rates) is drawn up front from
the episode seed, so every policy evaluated on the same seed faces exactly the
same traffic.
"""
from collections import deque

import numpy as np

ROADS = ["North", "South", "East", "West"]
N_ROADS = len(ROADS)
CYCLE_SECONDS = 5
SWITCH_LOST_SECONDS = 1

SCENARIOS = {
    "balanced": {
        "max_arrivals": (3, 3, 3, 3),
        "description": "Original demo traffic: 0-3 new cars per road per cycle",
    },
    "rush_hour": {
        "max_arrivals": (5, 5, 1, 1),
        "description": "Same total demand, concentrated on North-South",
    },
}


class Intersection:
    def __init__(self, scenario="balanced", cycles=200, emergency_prob=0.1):
        self.max_arrivals = np.array(SCENARIOS[scenario]["max_arrivals"])
        self.cycles = cycles
        self.emergency_prob = emergency_prob

    def reset(self, seed):
        rng = np.random.default_rng(seed)
        self.arrivals = rng.integers(0, self.max_arrivals + 1, size=(self.cycles, N_ROADS))
        emergency_road = rng.integers(0, N_ROADS, size=self.cycles)
        self.emergency = np.where(rng.random(self.cycles) < self.emergency_prob, emergency_road, -1)
        self.discharge = rng.integers(1, 4, size=(self.cycles, CYCLE_SECONDS))

        # Each queue holds the arrival time (in seconds) of every waiting car
        self.queues = [deque([0] * n) for n in rng.integers(5, 16, size=N_ROADS)]
        self.waiting = rng.uniform(1, 5, size=N_ROADS)
        self.green = None
        self.cycle = 0
        self.clock = 0
        self.arrived = sum(len(q) for q in self.queues)
        self.waits = []  # completed per-car waits, in seconds
        self._add_arrivals()

    @property
    def done(self):
        return self.cycle >= self.cycles

    def queue_lengths(self):
        return np.array([len(q) for q in self.queues])

    def head_waits(self):
        """How long the first car in each queue has been waiting (0 if empty)."""
        return np.array([self.clock - q[0] if q else 0 for q in self.queues])

    def step(self, action):
        """Run one 5-second cycle. Returns (cost, executed_road).

        cost is the vehicle-seconds of queueing during the cycle (the sum of all
        queue lengths, each second) — minimising it minimises average delay.
        executed_road differs from action when an emergency override fires.
        """
        road = int(self.emergency[self.cycle]) if self.emergency[self.cycle] >= 0 else int(action)
        switched = road != self.green
        cost = 0
        for s in range(CYCLE_SECONDS):
            if not (switched and s < SWITCH_LOST_SECONDS):
                q = self.queues[road]
                for _ in range(min(int(self.discharge[self.cycle, s]), len(q))):
                    self.waits.append(self.clock - q.popleft())
            # Same waiting-signal update as traffic_controller.py
            for r in range(N_ROADS):
                if r == road:
                    self.waiting[r] = max(self.waiting[r] - 0.5, 0) if self.queues[r] else 0
                else:
                    self.waiting[r] += 1
            self.clock += 1
            cost += sum(len(q) for q in self.queues)
        self.green = road
        self.cycle += 1
        if not self.done:
            self._add_arrivals()
        return cost, road

    def _add_arrivals(self):
        for r, n in enumerate(self.arrivals[self.cycle]):
            self.queues[r].extend([self.clock] * int(n))
            self.arrived += int(n)

    def episode_metrics(self):
        """Per-car wait stats. Cars still queued at the end count with their
        wait so far, so a policy can't look good by starving a road."""
        still_waiting = [self.clock - t for q in self.queues for t in q]
        all_waits = np.array(self.waits + still_waiting, dtype=float)
        return {
            "mean_wait": all_waits.mean(),
            "p95_wait": np.percentile(all_waits, 95),
            "served": len(self.waits),
            "left_in_queue": len(still_waiting),
        }
