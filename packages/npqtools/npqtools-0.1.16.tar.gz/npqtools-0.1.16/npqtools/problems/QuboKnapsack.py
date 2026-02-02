from npqtools.problems.qubo import QUBO
import numpy as np


class QUBOKnapsack(QUBO):
    def __init__(self, objects_list, capability):
        """
        Класс для решения задачи о рюкзаке.
        Размер матрицы QUBO - K + [Log2(M)], где K - число предметов, M - вместительность рюкзака.

        :param objects_list: Numpy массив с двумя столбцами - цена объекта и его вес.
        :param capability: вместительность рюкзака.
        """

        if not isinstance(objects_list, np.ndarray):
            raise TypeError("Objects list must be np.ndarray!")
        if not objects_list.dtype == np.int64:
            raise TypeError("Objects weights and costs must be np.int64!")
        if not len(objects_list.shape) == 2 or not objects_list.shape[1] == 2:
            raise TypeError("Object list must be nx2 matrix!")


        super().__init__()
        self.objects_weights = objects_list[:, 1].reshape(-1, 1)
        self.objects_costs = objects_list[:, 0]
        self.capability = capability
        self.sum_weight = 0
        self.compute_qubo()

    def set_solution(self):
        self.solution = np.array([key for key, value in self.raw_solution.items() if value == np.int8(1)])
        self.solution = self.solution[self.solution < self.objects_weights.shape[0]]
        self.sum_weight = sum(map(lambda obj_numb: self.objects_weights[obj_numb], self.solution))[0]

    def _int_log(self, n: int) -> int:
        """
        :param n: Натуральное число.
        :return: M : 2^M <= n < 2^(M+1).
        """

        res_log = 0
        value = 1
        while value <= n:
            res_log += 1
            value *= 2
        return res_log - 1

    def compute_qubo(self):
        """
        Вычисляет матрицу QUBO по формуле (1)

        """

        A = self.objects_costs.sum()
        M = self._int_log(self.capability)
        self.shape = self.objects_weights.shape[0] + 1 + M

        # Разобьем первое слагаемое на 4 матрицы

        degs = np.hstack([2 ** np.arange(M), self.capability + 1 - 2 ** M]).reshape(-1, 1)
        matrix1 = self.objects_weights @ self.objects_weights.T
        matrix2 = -(self.objects_weights @ degs.T)
        matrix3 = -(degs @ self.objects_weights.T)
        matrix4 = degs @ degs.T

        self.matrix = A * np.vstack([np.hstack([matrix1, matrix2]), np.hstack([matrix3, matrix4])]) - np.diag(np.hstack([self.objects_costs, np.zeros(M + 1)])).astype(int)
        self.delta = 0

    def display_solution(self):
        """
        Выводит в командную строку максимальный суммарный вес и набор объектов, реализующих этот вес.

        """

        print(f"Наилучшая сумма: {-self.min_energy}")
        print(f"Суммарный вес: {self.sum_weight}")
        print("Товары с номерами:")
        print(self.solution)