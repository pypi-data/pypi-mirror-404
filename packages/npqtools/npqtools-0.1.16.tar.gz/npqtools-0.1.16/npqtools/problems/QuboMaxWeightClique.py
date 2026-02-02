import numpy as np

from npqtools.problems.qubo import QUBO
from npqtools.problems.PrintGraph import PaintVertexSetInWeightedGraph

class QUBOMaxWeightClique(QUBO) :
    """
        Класс для решения задачи о поиске клики с максимальной суммой весов ребер.
        Размер матрицы QUBO - |V|, где V - множество вершин

        :param adjastensy_matrix: матрица смежности. Квадратная матрица Numpy переменными
        :param adjacency_matrix_size: сторона матрицы смежности.
        """
    def __init__(self, adjacency_matrix : np.array):

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

    def change_adjacency_matrix(self) :
        """
        Ставит на главной диагонали матрицы смежности 0
        """
        self.adjacency_matrix -= np.diag(np.diag(self.adjacency_matrix))

    def generate_mask(self) -> np.array :
        new_m = self.adjacency_matrix.copy()
        new_m[new_m > 0] = 1
        return new_m

    def compute_qubo(self):
        """
        Вычисляет матрицу QUBO

        """
        self.shape = self.adjacency_matrix_size
        self.change_adjacency_matrix()
        self.matrix = - self.adjacency_matrix
        mask = self.generate_mask()
        self.matrix += self.adjacency_matrix.sum() * (np.ones(self.matrix.shape) - mask - np.eye(self.matrix.shape[0])).astype(int)
    

    def set_solution(self) -> None:
        """
        Устанавливает self.solution в массив номеров вершин в максимальной клике

        """
        self.solution = np.array([key for key, value in self.raw_solution.items() if value])

    
    def display_solution(self) -> None :
        """
        Рисует заданный граф, выделяя ребра максимальной клики

        """
        PaintVertexSetInWeightedGraph(self.adjacency_matrix, self.solution)
