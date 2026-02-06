from parser import DataParser
import numpy as np
from neural_network import Neural_network
import matplotlib.pyplot as plt
from tqdm import tqdm


def generate_experiences(
    n_experiences=50, n_steps=50, dt=0.1, noise_std=0.02
) -> list[list[tuple]]:
    """
    Generates synthetic experimental experiences of projectile motion with noise.

    Args:
        n_experiences (int, optional): The number of experiences to generate. Defaults to 50.
        n_steps (int, optional): The number of steps in each experience. Defaults to 50.
        dt (float, optional): The time interval between steps. Defaults to 0.1.
        noise_std (float, optional): The standard deviation of the noise added to the positions. Defaults to 0.02.

    Returns:
        list[list[tuple]]: A list of experiences, each a list of (t, x, y) tuples representing the trajectory with noise.
    """
    experiences = []

    for _ in range(n_experiences):
        x, y = np.random.uniform(-0.2, 0.2), np.random.uniform(0.8, 1.2)
        vx, vy = np.random.uniform(0.8, 1.2), np.random.uniform(0.0, 0.2)

        ax, ay = 0.0, -1.0  # pseudo-gravité

        traj = []
        t = 0.0

        for _ in range(n_steps):
            # Ajout bruit
            x_noisy = x + np.random.normal(0, noise_std)
            y_noisy = y + np.random.normal(0, noise_std)

            traj.append((t, x_noisy, y_noisy))

            vx += ax * dt
            vy += ay * dt
            x += vx * dt
            y += vy * dt
            t += dt

        experiences.append(traj)

    return experiences


def plot_results(experiences: list[list[tuple]], nn: Neural_network, t_max: float, n_points: int = 200) -> None:
    """
    Plots the experimental trajectories and the trajectory learned by the neural network.

    Args:
        experiences (list[list[tuple]]): A list of experiences, each a list of (t, x, y) tuples representing the trajectory with noise.
        nn (Neural_network): The neural network used to predict the trajectory.
        t_max (float): The maximum time value for the trajectory.
        n_points (int, optional): The number of points to plot for the predicted trajectory. Defaults to 200.
    """

    # Trajectoires réelles
    for exp in experiences:
        xs = [p[1] for p in exp]
        ys = [p[2] for p in exp]
        plt.plot(xs, ys, color="gray", alpha=0.3)

    # Trajectoire apprise
    t_vals = np.linspace(0, t_max, n_points)
    traj_pred = np.array([nn.forward(np.array([t])) for t in t_vals])

    plt.plot(
        traj_pred[:, 0],
        traj_pred[:, 1],
        color="red",
        linewidth=3,
        label="Trajectoire apprise (NN)",
    )

    plt.xlabel("x")
    plt.ylabel("y")
    plt.legend()
    plt.title("Trajectoires expérimentales vs trajectoire apprise")
    plt.grid()
    plt.show()


if __name__ == "__main__":
    experiences = generate_experiences()
    X, Y = DataParser.parse_experiences(experiences)

    nn = Neural_network(input_dim=1, hidden_dim=32, output_dim=2, learning_rate=1e-3)
    # Entraînement avec barre de progression
    pbar = tqdm(range(2000), desc="Entraînement", unit="epoch", ncols=80)
    for epoch in pbar:
        loss = 0.0
        for t, pos in zip(X, Y):
            t = np.array(t)
            pos = np.array(pos)
            pred = nn.forward(t)
            loss += nn.MSE(pred, pos)
            nn.backward(t, pos)
        avg_loss = loss / len(X)
        pbar.set_postfix(loss=f"{avg_loss:.6f}")

    plot_results(experiences, nn, t_max=X.max())
