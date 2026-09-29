"""Signal-control policies. Each takes an Intersection and returns a road index."""
import numpy as np

from traffic_env import N_ROADS


def fixed_time(env):
    """Traditional signal: cycle N -> S -> E -> W regardless of traffic."""
    return env.cycle % N_ROADS


def priority_heuristic(env):
    """The original controller in traffic_controller.py: traffic + waiting * 0.7."""
    return int(np.argmax(env.queue_lengths() + env.waiting * 0.7))


def longest_queue(env):
    """Simple greedy baseline: serve whichever road has the most cars."""
    return int(np.argmax(env.queue_lengths()))


FEATURE_NAMES = [
    "bias", "queue", "queue (first 5 cars)", "head-of-queue wait", "already green",
    "already green x queue", "longest other queue", "total queue", "total queue^2",
]


def features(env):
    """One feature row per candidate road. The same weights score every road,
    so the agent learns a general rule rather than per-road preferences."""
    q = env.queue_lengths() / 10.0
    head = env.head_waits() / 30.0
    hold = np.array([1.0 if env.green == a else 0.0 for a in range(N_ROADS)])
    total = q.sum()
    longest_other = np.array([np.delete(q, a).max() for a in range(N_ROADS)])
    return np.stack([
        np.ones(N_ROADS), q, np.minimum(q, 0.5), head, hold, hold * q,
        longest_other, np.full(N_ROADS, total), np.full(N_ROADS, total ** 2),
    ], axis=1)


class LinearQAgent:
    """Q-learning with a linear value function: Q(s, road) = w . features(s, road).

    A lookup-table agent was tried first (see README) but had to bucket queue
    lengths, which threw away exactly the detail that matters here.
    """

    def __init__(self, lr=0.003, gamma=0.9, seed=0):
        self.w = np.zeros(len(FEATURE_NAMES))
        self.lr = lr
        self.gamma = gamma
        self.rng = np.random.default_rng(seed)

    def q_values(self, env):
        return features(env) @ self.w

    def act(self, env, epsilon=0.0):
        if self.rng.random() < epsilon:
            return int(self.rng.integers(N_ROADS))
        values = self.q_values(env)
        return int(self.rng.choice(np.flatnonzero(values == values.max())))

    def update(self, feats, road, reward, next_env, done):
        target = reward if done else reward + self.gamma * self.q_values(next_env).max()
        error = np.clip(target - feats[road] @ self.w, -10, 10)  # clip for stability
        self.w += self.lr * error * feats[road]

    def policy(self, env):
        return self.act(env)

    def save(self, path):
        np.save(path, self.w)

    @classmethod
    def load(cls, path):
        agent = cls()
        agent.w = np.load(path)
        return agent
