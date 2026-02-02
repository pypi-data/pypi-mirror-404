from npqtools.problems.qubo import QUBO
from npqtools.problems.PrintGraph import PaintNonOrientatedGraphWithCycle
import numpy as np


class QUBOHam(QUBO):
    def __init__(self, adjacency_matrix):
        """
        adjacency_matrix is a nxn matrix 
        dtype = int64
        """

        if not isinstance(adjacency_matrix, np.ndarray):
            raise TypeError("Adjacency matrix must be ndarray!")
        if not adjacency_matrix.dtype == np.int64:
            raise TypeError("Adjacency matrix must contain only int64 values!")
        if not len(adjacency_matrix.shape) or not adjacency_matrix.shape[0] == adjacency_matrix.shape[1]:
            raise TypeError("Adjacency matrix must be quadratic with only 2 dimensions!")
        
        
        super().__init__()
        self.adjacency_matrix = adjacency_matrix
        self.adjacency_matrix_size = adjacency_matrix.shape[0]
        self.compute_qubo()

    #Возвращает гамильтонов путь
    def set_solution(self):
        solution = np.array([(key % self.adjacency_matrix_size, key // self.adjacency_matrix_size) for key, value in self.raw_solution.items() if value == np.int8(1)])
        solution = solution[solution[:, 0].argsort()][:, 1]
        self.solution = solution if solution.shape[0] == self.adjacency_matrix_size else None

    def compute_qubo(self):
        self.shape = self.adjacency_matrix_size ** 2

        indices = np.arange(self.shape).reshape(-1, 1)

        mask1 = ((indices // self.adjacency_matrix_size) == (indices.T // self.adjacency_matrix_size)).astype(int) - 2 * np.eye(
            self.shape)
        mask2 = ((indices % self.adjacency_matrix_size) == (indices.T % self.adjacency_matrix_size)).astype(int) - 2 * np.eye(
            self.shape)
        mask3 = ((self.adjacency_matrix[indices // self.adjacency_matrix_size, indices.T // self.adjacency_matrix_size] == 0) & ((
            indices % self.adjacency_matrix_size - indices.T % self.adjacency_matrix_size + 1) % self.adjacency_matrix_size == 0)).astype(
            int)

        self.matrix = mask1 + mask2 + mask3
        self.delta = 2 * self.adjacency_matrix_size

    def display_solution(self):
        PaintNonOrientatedGraphWithCycle(self.adjacency_matrix, self.solution) if self.solution is not None else print("Nothing to show!")

    
