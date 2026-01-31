import numpy as np


class BenchmarkMathematicFormulas:

    def __init__(self):
        pass

    # Define the benchmark functions
    @staticmethod
    def sphere(x):
        return np.sum(x**2)

    @staticmethod
    def rastrigin(x):
        d = len(x)
        return 10*d + np.sum(x**2 - 10*np.cos(2*np.pi*x))

    @staticmethod
    def griewank(x):
        d = len(x)
        s = np.sum(x**2)
        p = np.prod(np.cos(x / np.sqrt(np.arange(1, d+1))))
        return 1 + s/4000 - p
    
    @staticmethod
    def ackley_function(x, a=20, b=0.2, c=2 * np.pi):
        """
        Ackley Function as fitness function.

        Parameters:
        - x : array-like, the input array of points.
        - a, b, c : constants, typically set to a=20, b=0.2, c=2π.

        Returns:
        - f(x) : The value of the Ackley function at point x.
        """
        n = len(x)
        sum1 = np.sum(x ** 2)
        sum2 = np.sum(np.cos(c * x))

        term1 = -a * np.exp(-b * np.sqrt(sum1 / n))
        term2 = -np.exp(sum2 / n)

        return term1 + term2 + a + np.e
    
    @staticmethod
    def rosenbrock_function(x):
        return sum(100 * (x[1:] - x[:-1]**2)**2 + (x[:-1] - 1)**2)
    
    @staticmethod
    def schwefel_function(x):
        return 418.9829 * len(x) - sum(x * np.sin(np.sqrt(np.abs(x))))
    
    @staticmethod
    def levi_function(x):
        term1 = np.sin(3 * np.pi * x[0]) ** 2
        term2 = sum((x[:-1] - 1) ** 2 * (1 + np.sin(3 * np.pi * x[1:]) ** 2))
        term3 = (x[-1] - 1) ** 2 * (1 + np.sin(2 * np.pi * x[-1]) ** 2)
        return term1 + term2 + term3
    
    @staticmethod
    def zakharov_function(x):
        sum1 = sum(x**2)
        sum2 = sum(0.5 * (i + 1) * x[i] for i in range(len(x)))
        return sum1 + sum2**2 + sum2**4
    
    @staticmethod
    def sum_of_different_powers_function(x):
        return sum(np.abs(x[i]) ** (i + 2) for i in range(len(x)))
    
    @staticmethod
    def michalewicz_function(x, m=10):
        return -sum(np.sin(x[i]) * (np.sin((i + 1) * x[i] ** 2 / np.pi)) ** (2 * m) for i in range(len(x)))
    
    @staticmethod
    def easom_function(x):
        return -np.cos(x[0]) * np.cos(x[1]) * np.exp(-((x[0] - np.pi)**2 + (x[1] - np.pi)**2))
    
    @staticmethod
    def six_hump_camel_function(x):
        x1, x2 = x[0], x[1]
        return (4 - 2.1 * x1**2 + (x1**4) / 3) * x1**2 + x1 * x2 + (-4 + 4 * x2**2) * x2**2
    
    @staticmethod
    def beale_function(x):
        x1, x2 = x[0], x[1]
        return (1.5 - x1 + x1 * x2)**2 + (2.25 - x1 + x1 * x2**2)**2 + (2.625 - x1 + x1 * x2**3)**2
    