import numpy as np


class Neural_network:
    """
    A feedforward neural network with two hidden layers using ReLU activation.
    """
    def __init__(self, input_dim, hidden_dim, output_dim, learning_rate) -> None:
        self.mu = learning_rate

        self.W1 = np.random.randn(hidden_dim, input_dim) * 0.1
        self.b1 = np.zeros(hidden_dim)

        self.W2 = np.random.randn(hidden_dim, hidden_dim) * 0.1
        self.b2 = np.zeros(hidden_dim)

        self.W3 = np.random.randn(output_dim, hidden_dim) * 0.1
        self.b3 = np.zeros(output_dim)

    def MSE(self, x: np.ndarray, y: np.ndarray) -> np.float32:
        """
        Mean Squared Error loss function.

        Args:
            x (np.ndarray): Predicted values
            y (np.ndarray): True values

        Returns:
            np.float32: Mean squared error between x and y
        """
        return np.mean((x - y) ** 2)

    def relu(self, x: np.ndarray) -> np.ndarray:
        """
        ReLU activation function.

        Args:
            x (np.ndarray): Input array

        Returns:
            np.ndarray: Output after applying ReLU activation
        """
        return np.maximum(0, x)

    def relu_derivative(self, x: np.ndarray) -> np.ndarray:
        """
        Derivative of the ReLU activation function.

        Args:
            x (np.ndarray): Input array

        Returns:
            np.ndarray: Output after applying the derivative of ReLU activation
        """
        return (x > 0).astype(float)

    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        Forward pass through the network.

        Args:
            x (np.ndarray): Input array of shape (1, )

        Returns:
            np.ndarray: Output array of shape (2, ) representing the predicted position (x, y)
        """
        self.x_1 = self.W1 @ x + self.b1
        self.x_hat = self.relu(self.x_1)

        self.x_2 = self.W2 @ self.x_hat + self.b2
        self.x_hat2 = self.relu(self.x_2)

        self.output = self.W3 @ self.x_hat2 + self.b3
        return self.output

    def backward(self, t: np.ndarray, target: np.ndarray) -> None:
        """
        Backward pass to update the network weights using gradient descent.

        Args:
            t (np.ndarray: shape (1, )): input time
            target (np.ndarray: shape (2, )): target position (x, y)
        """
        dL_output = 2 * (self.output - target) / target.size # dérivée MSE

        dW3 = np.outer(dL_output, self.x_hat2)
        db3 = dL_output

        d_x_hat2 = self.W3.T @ dL_output
        d_x_2 = d_x_hat2 * self.relu_derivative(self.x_2)

        dW2 = np.outer(d_x_2, self.x_hat)
        db2 = d_x_2

        d_x_hat1 = self.W2.T @ d_x_2
        d_x_1 = d_x_hat1 * self.relu_derivative(self.x_1)

        dW1 = np.outer(d_x_1, t)
        db1 = d_x_1

        self.W3 -= self.mu * dW3
        self.b3 -= self.mu * db3
        self.W2 -= self.mu * dW2
        self.b2 -= self.mu * db2
        self.W1 -= self.mu * dW1
        self.b1 -= self.mu * db1
