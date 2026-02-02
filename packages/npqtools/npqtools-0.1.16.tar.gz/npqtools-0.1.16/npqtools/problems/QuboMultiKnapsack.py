from npqtools.problems.qubo import QUBO
import numpy as np


class QUBOMultiKnapsack(QUBO):
    """
        Класс для решения задачи о рюкзаке.
        Размер матрицы QUBO - K + ∑[Log2(M_i)], где K - число предметов, M_i - i-я размерность рюкзака.

        :param objects_list: Numpy массив с d + 1 столбцами - его цена и его размерности.
        :param capability: Numpy вектор c d элементами - вместительность рюкзака.
        """
    def __init__(self, objects_list, capabilities):
        assert type(objects_list) == np.ndarray, "Invalid input"
        assert objects_list.dtype == np.int64, "Invalid types!"
        super().__init__()
        self.objects_costs = objects_list[:, 0]
        self.objects_weights = objects_list[:, 1:]
        self.capabilities = capabilities
        self.quantity = objects_list.shape[1] - 1
        self.sum_weight = 0
        self.compute_qubo()

    def set_solution(self):
        self.solution = np.array([key + 1 for key, value in self.raw_solution.items() if
                                  value == np.int8(1) and key < self.objects_weights.shape[0]])

    def display_solution(self):
        """
        Выводит в командную строку решение задачи
        """
        print(f"Наилучшая сумма: {-self.min_energy}")
        print("Товары с номерами:")
        print(self.solution)

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
        Вычисляет матрицу QUBO

        """
        A = self.objects_costs.sum() + 1
        M = np.array([self._int_log(i) for i in self.capabilities])
        self.shape = self.objects_weights.shape[0] + 1 + M.sum()
        degs = [np.hstack([2 ** np.arange(M[i]), self.capabilities[i] + 1 - 2 ** M[i]]).reshape(-1, 1) for i in
                range(self.capabilities.shape[0])]
        matrix1 = - np.diag(self.objects_costs)
        for i in range(self.quantity):
            matrix1 += A * np.array([self.objects_weights[:, i]]).T @ np.array([self.objects_weights[:, i]])
        for i in range(self.quantity):
            matrix1 = np.hstack([matrix1, - A * (np.array([self.objects_weights[:, i]]).T @ degs[i].T)])
        for i in range(self.quantity):
            matrix2 = -(degs[i] @ np.array([self.objects_weights[:, i]]))
            for j in range(self.quantity):
                if j == i:
                    matrix2 = np.hstack([matrix2, degs[i] @ degs[i].T])
                else:
                    matrix2 = np.hstack([matrix2, np.zeros([matrix2.shape[0], M[i] + 1])])
            matrix1 = np.vstack([matrix1, A * matrix2])
        self.delta = 0
        self.matrix = matrix1
