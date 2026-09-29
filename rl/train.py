"""
Train one Q-learning agent per traffic scenario and save it to rl/models/.

    python rl/train.py

Training episodes use seeds 0..EPISODES-1; evaluate.py uses a disjoint seed
range, so the agent is always tested on traffic it has never seen.
"""
import os
import time

from policies import FEATURE_NAMES, LinearQAgent, features
from traffic_env import SCENARIOS, Intersection

EPISODES = 1000
EPS_START, EPS_END, EPS_DECAY_FRACTION = 1.0, 0.05, 0.5
REWARD_SCALE = 100.0  # keeps values in a comfortable numeric range

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")


def train(scenario, episodes=EPISODES, seed=0):
    agent = LinearQAgent(seed=seed)
    env = Intersection(scenario)
    decay_episodes = int(episodes * EPS_DECAY_FRACTION)
    for ep in range(episodes):
        epsilon = max(EPS_END, EPS_START - (EPS_START - EPS_END) * ep / decay_episodes)
        env.reset(seed=ep)
        while not env.done:
            feats = features(env)
            action = agent.act(env, epsilon)
            cost, executed = env.step(action)
            # Learn from the road that actually went green (differs on emergencies)
            agent.update(feats, executed, -cost / REWARD_SCALE, env, env.done)
    return agent


if __name__ == "__main__":
    os.makedirs(MODEL_DIR, exist_ok=True)
    for name in SCENARIOS:
        start = time.time()
        agent = train(name)
        agent.save(os.path.join(MODEL_DIR, f"weights_{name}.npy"))
        print(f"{name}: trained {EPISODES} episodes in {time.time() - start:.0f}s")
        for f, w in zip(FEATURE_NAMES, agent.w):
            print(f"  {f:24s} {w:+.2f}")
