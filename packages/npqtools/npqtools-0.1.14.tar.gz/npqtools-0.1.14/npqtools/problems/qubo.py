from dwave.samplers import SteepestDescentSampler, TabuSampler, SimulatedAnnealingSampler, PathIntegralAnnealingSampler
from gurobi_optimods.qubo import solve_qubo
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from numpy.matrixlib.defmatrix import matrix


class QUBO:
    """
    Родительский класс всех матриц QUBO


    :param matrix: Матрица QUBO.
    :param decomposition: Двумерный массив матриц - итоговая матрица QUBO вычисляется как сумма кронекеровых произведений каждой строки.
    :param min_energy: Минимальное значение QUBO.
    :param shape: Число бинарных переменных.
    :param raw_solution: Словарь длины self.shape с парами "номер бинарной переменной" : "0/1", на котором достигается минимум QUBO.
    :param solution: Решение, на котором достигается минимум QUBO.
    :param delta: Линейный коэффициент QUBO
    """

    def __init__(self, matrix=None):

        if not isinstance(matrix, np.ndarray) and matrix is not None:
            raise TypeError("QUBO must be nxn matrix or none type object!")
        if matrix is not None:
            if not matrix.dtype == np.int64:
                raise TypeError("QUBO matrix must contain only integer values!")
            if not len(matrix.shape) or not matrix.shape[0] == matrix.shape[1]:
                raise TypeError("QUBO matrix must be quadratic with only 2 dimensions!")

        self.matrix: np.array = matrix  # Матрица QUBO
        self.decomposition = None  # Двумерный массив матриц - итоговая матрица QUBO вычисляется как сумма кронекеровых произведений каждой строки.
        self.min_energy = None  # Минимальное значение QUBO
        self.shape = None if self.matrix is None else self.matrix.shape[0]  # Число бинарных переменных
        self.raw_solution = None  # Словарь длины self.shape с парами "номер бинарной переменной" : "0/1", на котором достигается минимум QUBO
        self.solution = None  # Решение, на котором достигается минимум QUBO
        self.delta = 0  # Линейный коэффициент QUBO

    def find_min_energy(self, num_reads=None, solver='SDS'):
        """
        Находит минимальное значение QUBO.

        :param num_reads: количество запусков поиска минимума.
        :param solver:
          * 'TS' - TabuSolver,
          * 'SDS' - SteepestDescentSolver,
          * 'SAS' - SimulatedAnnealingSolver,
          * 'SQAS' - PathIntegralAnnealingSampler,
          * 'GS' - GurobiSolver - необходимо наличие прав на использование.
        :return: Минимальное значение x.T @ Q @ x.
        """
        if self.matrix is None:
            if self.decomposition is None:
                assert "Matrix is empty!"
            else:
                self.matrix = self.matrix_from_decomposition()
        self.matrix = np.triu(self.matrix + self.matrix.T - np.diag(np.diag(self.matrix)))
        Q = self.matrix

        if solver == 'TS':
            sampler = TabuSampler()
            if num_reads is None:
                num_reads = 50000 // self.get_shape() + 1
        elif solver == 'SDS':
            sampler = SteepestDescentSampler()
            if num_reads is None:
                num_reads = max(1, 30000000000 // self.get_shape() ** 2)
        elif solver == 'SAS':
            sampler = SimulatedAnnealingSampler()
            if num_reads is None:
                num_reads = 1000000 // self.get_shape() ** 2 + 1
        elif solver == 'SQAS':
            sampler = PathIntegralAnnealingSampler()
            if num_reads is None:
                num_reads = 100
        elif solver == 'GS':
            result = solve_qubo(Q)
            self.min_energy = result.objective_value + self.delta
            raw_solution = dict()
            for i in range(len(result.solution)):
                raw_solution[i] = np.int8(1) if result.solution[i] == 1 else np.int8(0)
            self.raw_solution = raw_solution
            self.set_solution()
            return
        else:
            raise TypeError("Invalid Solver")
        sampleset = sampler.sample_qubo(Q, num_reads=num_reads)

        self.min_energy = sampleset.first.energy + self.delta
        self.raw_solution = sampleset.first.sample

        self.set_solution()
        return self.min_energy

    def min_energy(self):
        """
        :return: Минимум QUBO
        """
        return self.min_energy

    def get_shape(self):
        """
        :return: Число бинарных переменных, если матрица задана, None иначе
        """
        if self.shape is not None:
            return self.shape
        return None if self.matrix is None else self.matrix.shape[0]

    def matrix_from_decomposition(self):
        """
        Метод, составляющий матрицу QUBO из разложения на кронекеровы произведения.
        Перемножает (Кронекерово) все матрицы в строке self.decomposition, а результаты складывает.

        :return: Матрицу QUBO соответствующего разложения
        """

        def kron_prod(matrix_list):
            l = len(matrix_list)
            if l == 0:
                return 0
            elif l == 1:
                return matrix_list[0]
            else:
                ret = np.kron(matrix_list[0], matrix_list[1])
                for i in range(2, l):
                    ret = np.kron(ret, matrix_list[i])
                return ret

        if len(self.decomposition) == 0:
            return 0
        else:
            matrix = kron_prod(self.decomposition[0])
            for i in range(1, len(self.decomposition)):
                matrix += kron_prod(self.decomposition[i])
            return matrix

    def complication(self, dQ=None, dDelta=0):
        """
        Изменяет построенную матрицу QUBO на dQ и сдвигает минимум на dDelta.

        :param dQ: delta Q - дополнительное слагаемое в матрице QUBO, квадратная матрица совпадающая по размеру с матрицей QUBO.
        :param dDelta: delta Delta - дополнительный сдвиг - число.
        """
        if self.matrix is None:
            return TypeError("You must create QUBO matrix first!")
        if dQ is None:
            dQ = np.zeros((self.shape, self.shape))
        if not isinstance(dQ, np.ndarray):
            raise TypeError("dQ must be np.ndarray!")
        if not dQ.shape[0] == dQ.shape[1] == self.matrix.shape[0]:
            raise TypeError("dQ must be same size as self.matrix!")
        if not (isinstance(dDelta, int) or isinstance(dDelta, float)):
            raise TypeError("dDelta must be int or float!")
        self.matrix += dQ
        self.delta += dDelta

    def get_qubo_excel(self, file_path: str):
        """
        Создает файл npqtools_qubo.xlsx, содержащий матрицу qubo

        :param file_path: строка - место сохранения файла npqtools_qubo.xlsx
        """
        if self.matrix is None:
            if self.decomposition is None:
                raise TypeError("You should compute QUBO matrix first!")
            else:
                self.matrix_from_decomposition()

        df = pd.DataFrame(self.matrix)
        df.to_excel(file_path + "npqtools_qubo.xlsx", index=False, header=False)
