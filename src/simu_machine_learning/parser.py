import numpy as np


class DataParser:
    """
    Parses experimental data
    """

    @staticmethod
    def parse_experiences(
        experiences: list[list[tuple]],
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Parses a list of experiences into input and output arrays for training.

        Args:
            experiences (list[list[tuple]]): List of experiences, each a list of (t, x, y) tuples.

        Returns:
            tuple[np.ndarray, np.ndarray]: Arrays for inputs (times) and outputs (positions).
        """
        X = []
        Y = []

        for exp in experiences:
            for t, x, y in exp:
                X.append([t])  # entrée NN
                Y.append([x, y])  # sortie NN

        return np.array(X, dtype=np.float32), np.array(Y, dtype=np.float32)
