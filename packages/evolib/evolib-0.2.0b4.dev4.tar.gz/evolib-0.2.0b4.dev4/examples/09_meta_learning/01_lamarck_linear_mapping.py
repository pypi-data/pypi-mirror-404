from __future__ import annotations

import numpy as np

from evolib import Indiv, Pop


def synaptic_scaling_over_inputs(
    net,
    xs: np.ndarray,
    *,
    target_activity: float = 0.1,
    rate: float = 1e-3,
) -> None:
    """Homeostatic synaptic scaling based on mean absolute neuron activity over inputs."""
    neurons = net.get_all_neurons()

    # Accumulate mean absolute activity per neuron
    acc = np.zeros(len(neurons), dtype=float)

    for x in xs:
        net.reset(full=True)
        _ = net.calc([float(x), 1.0])
        for i, n in enumerate(neurons):
            acc[i] += abs(float(n.output))

    mean_a = acc / max(1, len(xs))

    # Apply scaling per neuron to all incoming weights
    eps = 1e-6
    for i, n in enumerate(neurons):
        a = float(mean_a[i]) + eps
        scale = target_activity / a
        scale = 1.0 + rate * (scale - 1.0)

        for c in n.incoming:
            c.weight *= float(scale)

# -----------------------------
# Task: stationary linear mapping
# -----------------------------


def target(x: float) -> float:
    """Stationary mapping used for every episode."""
    return float(x)  # y = x


# -----------------------------
# Online learning rule (weights only)
# -----------------------------


def apply_three_factor_error_plasticity(
    net, y_true: float, y_pred: float, eta: float, *, weight_clip: float = 3.0
) -> None:
    """
    Three-factor plasticity rule (stationary supervised setting):

        r = y_true - y_pred
        dw = eta * r * pre * post

    Notes:
    - r carries sign, so updates can increase or decrease weights.
    - No bias updates in this basic example (bias should be disabled in YAML).
    """
    r = float(y_true - y_pred)
    r = float(np.clip(r, -1.0, 1.0))  # stability

    for c in net.get_all_connections():
        pre = float(c.source.output)
        post = float(c.target.output)
        c.weight += float(eta) * r * pre * post
        c.weight = float(np.clip(c.weight, -weight_clip, weight_clip))


# -----------------------------
# Fitness evaluation (Lamarck)
# -----------------------------


def lamarck_linear_mapping_fitness(indiv: Indiv) -> None:
    """
    Lamarck evaluation:
    - Online learning modifies the individual's weights.
    - We do NOT restore weights afterwards.
    - Fitness is measured after training (generalization on x_test).

    This means:
    - Within a generation, individuals improve during evaluation.
    - Across generations, improved weights can be inherited (Lamarck).
    """
    net = indiv.para["nnet"].net

    # Fixed learning rate for the "learning basics" demo.
    # If you want, this can later become an evolvable vector module.
    eta = 0.01

    # Deterministic train/test points
    x_train = np.linspace(-1.0, 1.0, 32)
    x_test = np.linspace(-1.0, 1.0, 64)

    net.reset(full=True)

    # Train (online updates)
    for x in x_train:
        y_pred = float(net.calc([float(x), 1.0])[0])  # 2 inputs: x and constant 1.0
        y_true = target(float(x))
        apply_three_factor_error_plasticity(net, y_true=y_true, y_pred=y_pred, eta=eta)


    synaptic_scaling_over_inputs(net, x_train, target_activity=0.1, rate=1e-3)

    # Test (no learning)
    net.reset(full=True)
    preds = []
    trues = []
    for x in x_test:
        preds.append(float(net.calc([float(x), 1.0])[0]))
        trues.append(target(float(x)))

    preds_arr = np.asarray(preds, dtype=float)
    trues_arr = np.asarray(trues, dtype=float)
    mse = float(np.mean((preds_arr - trues_arr) ** 2))

    indiv.fitness = mse


# -----------------------------
# Run
# -----------------------------


def on_improvement(pop: Pop) -> None:
    best = pop.best()
    net = best.para["nnet"].net
    w = net.get_weights()
    print(f"  best fitness={best.fitness:.6g}, mean|w|={float(np.mean(np.abs(w))):.4g}")


def main() -> None:
    pop = Pop(
        config_path="configs/01_lamarck_linear_mapping.yaml",
        fitness_function=lamarck_linear_mapping_fitness,
    )
    pop.run(verbosity=1, on_improvement=on_improvement)


if __name__ == "__main__":
    main()

