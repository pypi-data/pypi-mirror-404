from npqtools.problems.qubo import QUBO
import numpy as np
from npqtools.problems.PrintGraph import PrintTiling2Dim


class QUBOTiling2Dim(QUBO):
    """
    Класс для решения задачи плотного замощения
    Размер матрицы QUBO - K(D1D2+D1+D2), где K - число прямоугольников, D1, D2 - размер заполняемого большогоо прямоугольника

    :param objects_shapes: матрица Numpy - размеры прямоугольников
    :param separations: массив кортежей, состоящих из 2х кортежей - координаты раздеялемых клеток
    :param banned: массив кортежей из 2х элеметов - координыты запрещенных для покрытия клеток

    """
    def __init__(self, objects_shapes: np.array, x: int, y: int, separations=None, banned=None):
        super().__init__()
        self.objects_shape_1 = objects_shapes[:, 0]
        self.objects_shape_2 = objects_shapes[:, 1]
        self.separations = separations
        self.banned = banned
        self.x = x
        self.y = y
        self.k = self.objects_shape_1.shape[0]
        self.sum_weight = 0
        self.compute_qubo()
        self.delta = 0

    def set_solution(self):
        self.solution = [
            [sum([(k + 1) * self.raw_solution[j * self.x * self.k + i * self.k + k] for k in range(self.k)]) for j in
             range(self.y)] for i in range(self.x)]

    def display_solution(self):
        """
        Рисует таблицу - заполняемый прямоугольник с нарисовааными прямоугольниками + все ограничения

        """
        PrintTiling2Dim(np.array(self.solution), self.k, banned=self.banned, separations=self.separations)
        for i in self.solution:
            print(*i)

    def compute_qubo(self):
        """
        Вычисляет матрицу QUBO

        """
        C = self.x * self.y * self.k
        B = C * self.x * self.y * self.x * self.y
        A = 2 * B
        matrix1 = np.diag([1 for _i in range(self.x * self.y)] + [0 for _i in range(self.x + self.y)])
        self.matrix = A * np.kron(matrix1, np.ones((self.k, self.k)) - np.eye(self.k))
        for k in range(self.k):
            matrix1 = np.array([[1 for _j in range(self.y)] + [-self.objects_shape_1[k]]])
            matrix1 = matrix1.T @ matrix1
            for i in range(self.x):
                self.matrix += A * np.pad(
                    np.kron(matrix1, np.diag([0 if t != i * self.k + k else 1 for t in range(self.x * self.k)])),
                    ((0, self.y * self.k), (0, self.y * self.k)), constant_values=0)
        for k in range(self.k):
            matrix1 = np.array([[1 for _i in range(self.x)] + [-self.objects_shape_2[k]]])
            matrix1 = matrix1.T @ matrix1
            for j in range(self.y):
                matrix2 = np.kron(matrix1, np.diag([0 if k_ != k else 1 for k_ in range(self.k)]))
                matrix2 = np.insert(matrix2, self.x * self.k,
                                    [[0] for _i in range(self.x * (self.y - j) * self.k + self.k * j)], axis=1)
                matrix2 = np.insert(matrix2, self.x * self.k,
                                    [[0] for _i in range(self.x * (self.y - j) * self.k + self.k * j)], axis=0)
                self.matrix += A * np.pad(matrix2, (
                    (j * self.k * self.x, self.k * (self.y - j - 1)), (j * self.k * self.x, self.k * (self.y - j - 1))))
        self.matrix += B * np.diag([2 if t < self.x * self.y * self.k else -1 for t in range(self.matrix.shape[0])])
        self.matrix += B * np.pad(np.diag([-1 for _i in range(self.x * (self.y - 1) * self.k)], k=self.x * self.k),
                                  ((0, self.x * self.k + self.y * self.k), (0, self.x * self.k + self.y * self.k)))
        self.matrix += B * np.pad(np.diag(
            [-1 if t % (self.k * self.x) < self.k * (self.x - 1) else 0 for t in range((self.x * self.y - 1) * self.k)],
            k=self.k), ((0, self.x * self.k + self.y * self.k), (0, self.x * self.k + self.y * self.k)))
        self.matrix += np.diag([-1 if t < self.x * self.y * self.k else 0 for t in range(self.matrix.shape[0])])
        self.matrix += C * np.pad(np.kron(np.eye(self.x * self.y), np.diag(
            [(-self.objects_shape_1[k] * self.objects_shape_2[k]) for k in range(self.k)])),
                                  ((0, self.x * self.k + self.y * self.k), (0, self.x * self.k + self.y * self.k)))
        self.matrix += C * np.pad(np.kron(np.ones((self.x * self.y, self.x * self.y)), np.eye(self.k)),
                                  ((0, self.x * self.k + self.y * self.k), (0, self.x * self.k + self.y * self.k)))
        if self.banned is not None:
            for cell in self.banned:
                matrix1 = np.zeros((self.x * self.y, self.x * self.y))
                matrix1[cell[1] * self.x + cell[0]][cell[1] * self.x + cell[0]] = 1

                self.matrix += A * np.pad(np.kron(matrix1, np.eye(self.k)), (
                    (0, self.k * self.x + self.k * self.y), (0, self.k * self.x + self.k * self.y)))
        if self.separations is not None:
            for sep in self.separations:
                x1, y1, x2, y2 = sep[0][0], sep[0][1], sep[1][0], sep[1][1]
                matrix1 = np.zeros((self.x * self.y, self.x * self.y))
                matrix1[y1 * self.x + x1][y2 * self.x + x2] = 1
                self.matrix += A * np.pad(np.kron(matrix1, np.eye(self.k)), (
                    (0, self.k * self.x + self.k * self.y), (0, self.k * self.x + self.k * self.y)))
