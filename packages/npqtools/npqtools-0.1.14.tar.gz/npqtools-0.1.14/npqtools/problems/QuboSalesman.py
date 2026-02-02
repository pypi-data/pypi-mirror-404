from npqtools.problems.qubo import QUBO

from npqtools.problems.PrintGraph import *
import numpy as np


class QUBOSalesman(QUBO):
    """
    Класс для решения задачи Коммивояжера
    Размер матрицы QUBO - |V|^2, где V - множество вершин

        :param adjacency_matrix: матрица смежности графа
        :param coord_matrix: матрица с координатами матрицы
        Не менее одного из пары adjacency_matrix и coord_matrix должен быть не пустым
        """
    def __init__(self, adjacency_matrix=None, coord_matrix=None):
        if not isinstance(adjacency_matrix, np.ndarray):
            if not isinstance(coord_matrix, np.ndarray):
                raise TypeError("Coordinates matrix must be ndarray!")
            if not len(coord_matrix.shape) == 2 or not coord_matrix.shape[1] == 2:
                raise TypeError("Coordinates matrix must be nx2 matrix!")
            self.is_from_coords = True
            self.coord_matrix = coord_matrix
            adjacency_matrix = np.sqrt(((coord_matrix[:, 0][:, None] - coord_matrix[:, 0][:, None].T) ** 2 + (
                    coord_matrix[:, 1][:, None] - coord_matrix[:, 1][:, None].T) ** 2))

        else:
            if not isinstance(adjacency_matrix, np.ndarray):
                raise TypeError("Adjacency matrix must be ndarray!")
            if not adjacency_matrix.dtype == np.int64:
                raise TypeError("Adjacency matrix must contain only int64 values!")
            if not len(adjacency_matrix.shape) or not adjacency_matrix.shape[0] == adjacency_matrix.shape[1]:
                raise TypeError("Adjacency matrix must be quadratic with only 2 dimensions!")
            self.is_from_coords = False

        super().__init__()
        self.adjacency_matrix = adjacency_matrix
        self.adjacency_matrix_size = adjacency_matrix.shape[0]
        self.compute_decomposition()

    def set_solution(self):
        solution = np.array([(key % self.adjacency_matrix_size, key // self.adjacency_matrix_size) for key, value in
                             self.raw_solution.items() if value == np.int8(1)])
        solution = solution[solution[:, 0].argsort()][:, 1]
        self.solution = solution if solution.shape[0] == self.adjacency_matrix_size else None

    def compute_decomposition(self):
        """
        Вычисляет декомпозицию на Кронекерывы произведения

        """
        A = self.adjacency_matrix.max() * self.adjacency_matrix_size
        self.delta = 2 * self.adjacency_matrix_size * A
        side = self.adjacency_matrix_size

        normal_adjacency_matrix = self.adjacency_matrix.copy()
        normal_adjacency_matrix[normal_adjacency_matrix == 0] = A
        self.decomposition = [
            [A * np.ones((side, side)), np.eye(side)],
            [-2 * A * np.eye(side), np.eye(side)],
            [np.eye(side), A * np.ones((side, side))],
            [np.eye(side), -2 * A * np.eye(side)],
            [normal_adjacency_matrix, np.roll(np.eye(side), 1, axis=1)]
        ]


    def display_solution(self):
        """
        Рисует исходный граф, отмечая ребрами кратчайший путь коммивояжера

        """
        if not self.is_from_coords:
            PaintNonOrientatedGraphWithCycle(self.adjacency_matrix,
                                             self.solution) if self.solution is not None else print("Nothing to show!")
        else:
            tmp_solution = np.append(self.solution, self.solution[0])
            PrintGraphWithVertexCoordinatesAndWay(self.coord_matrix,
                                                  tmp_solution) if self.solution is not None else print(
                "Nothing to show!")

    def compute_qubo(self):
        A = self.adjacency_matrix.max() * self.adjacency_matrix_size
        self.delta = 2 * self.adjacency_matrix_size * A
        B = 1
        QUBOMatrixSize = self.adjacency_matrix_size ** 2
        MatrixSize = self.adjacency_matrix_size
        Indices = np.arange(QUBOMatrixSize).reshape(-1, 1)

        Mask1 = ((Indices // MatrixSize) == (Indices.T // MatrixSize)).astype(int) - 2 * np.eye(
            QUBOMatrixSize)  # Первое слагаемое
        Mask2 = ((Indices % MatrixSize) == (Indices.T % MatrixSize)).astype(int) - 2 * np.eye(
            QUBOMatrixSize)  # Второе слагаемое
        Mask3 = ((self.adjacency_matrix[Indices // MatrixSize, Indices.T // MatrixSize] == 0) & (
                (Indices % MatrixSize - Indices.T % MatrixSize + 1) % MatrixSize == 0)).astype(int)  # Третье слагаемое
        Mask4 = self.adjacency_matrix[Indices // MatrixSize, Indices.T // MatrixSize] * (
                (Indices % MatrixSize - Indices.T % MatrixSize + 1) % MatrixSize == 0).astype(int)  # Четвертое слагаемое
        self.matrix = A * (Mask1 + Mask2 + Mask3) + B * Mask4


