import numpy as np

from npqtools.problems.qubo import QUBO
from npqtools.problems.PrintGraph import PaintVertexSetInNonWeightedGraph


class QUBOClique(QUBO) :
    """
    Класс для решения задачи о поиске максимальной клики.
    Размер матрицы QUBO - |V|, где V - множество вершин

    :param adjastensy_matrix: матрица смежности. Квадратная матрица Numpy с бинарными переменными
    :param adjacency_matrix_size: сторона матрицы смежности.
    """
    def __init__ (self, adjacency_matrix : np.array):
        if not isinstance(adjacency_matrix, np.ndarray):
            raise TypeError("Adjacency matrix must be ndarray!")
        if not len(adjacency_matrix.shape) or not adjacency_matrix.shape[0] == adjacency_matrix.shape[1]:
            raise TypeError("Adjacency matrix must be quadratic with only 2 dimensions!")
        
        super().__init__()
        self.adjacency_matrix = adjacency_matrix
        self.adjacency_matrix_size = adjacency_matrix.shape[0]
        self.compute_qubo()

    def change_adjstency_matrix(self) -> None :
        """
        Преобразует матрицу смежности взвешенного графа в матрицу с бинарными переменными.

        """
        for i in range(self.adjacency_matrix_size) :
            for j in range(self.adjacency_matrix_size) :
                if self.adjacency_matrix[i][j] :
                    self.adjacency_matrix[i][j] = 1
                if i == j :
                    self.adjacency_matrix[i][j] = 0

    def compute_qubo(self, change_mat=True) -> None:
        """
        Вычисляет матрицу QUBO

        """

        if change_mat:
            self.change_adjstency_matrix()
        self.shape = self.adjacency_matrix_size
        self.matrix = self.shape * (np.ones((self.shape, self.shape)) - np.eye(self.shape) - self.adjacency_matrix) - 2 * np.eye(self.shape)

    def set_solution(self) -> None:
        """
        Устанавливает поле solution в масиив номеров вершин, содержащихся в наибольшей клике

        """
        self.solution = np.array([key for key, value in self.raw_solution.items() if value])

    def display_solution(self) -> None:
        """
        Рисует визуальное представление графа с отмечеными ребрами клики.

        """
        PaintVertexSetInNonWeightedGraph(self.adjacency_matrix, self.solution)

