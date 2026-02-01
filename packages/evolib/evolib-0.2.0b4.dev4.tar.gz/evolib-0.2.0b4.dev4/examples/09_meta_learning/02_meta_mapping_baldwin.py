from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from evolib import Indiv, Pop

# -----------------------------
# Task definition
# -----------------------------


@dataclass(frozen=True)
class MappingTask:
    """Defines a family of episode-wise mappings y = f(x, episode_id)."""

    # Choose a small set of mappings that are "confusable" without adaptation.
    # The agent must infer which mapping is active via feedback.
    mapping_names: tuple[str, ...] = ("identity", "negation", "abs")

    def target(self, x: float, mapping_id: int) -> float:
        name = self.mapping_names[mapping_id % len(self.mapping_names)]
        if name == "identity":
            return x
        if name == "negation":
            return -x
        if name == "abs":
            return abs(x)
        raise ValueError(f"Unknown mapping: {name}")


TASK = MappingTask()


def zero_all_biases(net) -> None:
    for n in net.get_all_neurons():
        n.bias = 0.0


# -----------------------------
# Online learning rule
# -----------------------------


def apply_three_factor_error_plasticity(
    net, y_true: float, y_pred: float, lr: float
) -> None:
    """Three-factor plasticity: dw = lr * (y_true - y_pred) * pre * post."""
    r = float(y_true - y_pred)
    r = float(np.clip(r, -1.0, 1.0))  # stabilizer

    weight_clip = 3.0

    for c in net.get_all_connections():
        pre = float(c.source.output)
        post = float(c.target.output)
        c.weight += float(lr) * r * pre * post
        c.weight = float(np.clip(c.weight, -weight_clip, weight_clip))


# -----------------------------
# Fitness evaluation (Baldwin)
# -----------------------------


def meta_mapping_fitness(indiv: Indiv) -> None:
    """
    Evaluate one individual via multiple deterministic episodes.

    Structure:
    - For each episode:
        1) Save initial weights (genotype)
        2) Adapt for K steps with online updates (inner loop)
        3) Test for M steps with learning disabled (measure adaptation quality)
        4) Restore initial weights (Baldwin reset)
    - Fitness = mean test MSE over episodes (minimize).
    """

    # --- get modules ---
    # EvoNet module (as in your existing examples)
    evonet = indiv.para["nnet"].net

    learning_rate = float(np.asarray(indiv.para["meta_lr"].vector).ravel()[0])

    # Deterministic episode set (fixed x samples)
    x_train = np.linspace(-1.0, 1.0, 32)
    x_test = np.linspace(-1.0, 1.0, 64)

    # Inner-loop steps (adaptation) and outer evaluation
    num_episodes = 6  # small and cheap
    mse_per_episode: list[float] = []

    # Save genotype once per episode
    for episode_id in range(num_episodes):
        w0 = evonet.get_weights().copy()

        # Pick mapping deterministically by episode id
        mapping_id = episode_id % len(TASK.mapping_names)

        # -------------------------
        # Adaptation phase (learn)
        # -------------------------
        evonet.reset(full=True)

        for x in x_train:
            # input: x plus a constant bias feature helps learning in tiny nets
            y_pred = float(evonet.calc([float(x), 1.0])[0])
            y_true = float(TASK.target(float(x), mapping_id))

            apply_three_factor_error_plasticity(evonet, y_true, y_pred, learning_rate)

        # -------------------------
        # Test phase (no learning)
        # -------------------------
        evonet.reset(full=True)
        y_preds = []
        y_trues = []
        for x in x_test:
            y_pred = float(evonet.calc([float(x), 1.0])[0])
            y_true = float(TASK.target(float(x), mapping_id))
            y_preds.append(y_pred)
            y_trues.append(y_true)

        y_preds_arr = np.asarray(y_preds, dtype=float)
        y_trues_arr = np.asarray(y_trues, dtype=float)
        mse = float(np.mean((y_preds_arr - y_trues_arr) ** 2))
        mse_per_episode.append(mse)

        # -------------------------
        # Baldwin reset (critical)
        # -------------------------
        evonet.set_weights(w0)
        zero_all_biases(evonet)

    indiv.fitness = float(np.mean(mse_per_episode))


# -----------------------------
# Running the experiment
# -----------------------------


def on_improvement(pop: Pop) -> None:
    best = pop.best()
    lr = float(np.asarray(best.para["meta_lr"].vector).ravel()[0])
    print(f"  best meta: learning_rate={lr:.4g}, " f"fitness={best.fitness:.6g}")


def main() -> None:
    pop = Pop(
        config_path="configs/02_meta_mapping_baldwin.yaml",
        fitness_function=meta_mapping_fitness,
    )
    pop.run(verbosity=1, on_improvement=on_improvement)


if __name__ == "__main__":
    main()
