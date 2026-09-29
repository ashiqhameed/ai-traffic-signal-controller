"""Sanity checks for the simulator. Run: python -m pytest rl"""
import numpy as np

from policies import FEATURE_NAMES, fixed_time, features, priority_heuristic
from traffic_env import N_ROADS, Intersection


def run(policy, seed=7, scenario="balanced"):
    env = Intersection(scenario)
    env.reset(seed=seed)
    while not env.done:
        env.step(policy(env))
    return env


def test_no_cars_created_or_lost():
    env = run(priority_heuristic)
    assert env.arrived == len(env.waits) + env.queue_lengths().sum()


def test_same_seed_same_traffic_for_every_policy():
    a, b = run(fixed_time), run(priority_heuristic)
    assert a.arrived == b.arrived
    assert np.array_equal(a.arrivals, b.arrivals)


def test_switching_costs_lost_time_but_holding_does_not():
    env = Intersection()
    env.reset(seed=1)
    env.emergency[:] = -1
    env.queues[0].extend([0] * 50)
    env.discharge[:] = 1
    env.step(0)  # switch from no green -> North: 1 lost second, 4 cars
    served_after_switch = len(env.waits)
    env.step(0)  # hold North: 5 cars
    assert served_after_switch == 4
    assert len(env.waits) - served_after_switch == 5


def test_emergency_overrides_the_chosen_road():
    env = Intersection()
    env.reset(seed=1)
    env.emergency[0] = 2
    _, executed = env.step(0)
    assert executed == 2


def test_features_one_row_per_road_and_finite():
    env = Intersection("rush_hour")
    env.reset(seed=3)
    while not env.done:
        f = features(env)
        assert f.shape == (N_ROADS, len(FEATURE_NAMES))
        assert np.isfinite(f).all()
        env.step(fixed_time(env))
