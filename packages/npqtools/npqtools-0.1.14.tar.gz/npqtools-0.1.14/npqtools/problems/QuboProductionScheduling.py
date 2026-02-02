from npqtools.problems.qubo import QUBO
import numpy as np


class QUBOProductionScheduling(QUBO):
    """
    Класс для решения задачи о Распределении планировании производства
    Размер матрицы QUBO - MJ^2, где M - число машин, J - число работ

    :param jobs_completion_time_matrix: матрица, В клетке (i, j) стоит время работы j на машине i - целое число
    :param setup_times_matrix: матрица, строки - работы, столбцы - работы. В клетке (i, j) стоит время перенастройки машины с работы i на работу j - целое число
    :param jobs_value_matrix: матрица, В клетке (i, j) стоит вклад работы j на машине i - целое число
    :param B: коэффициент, отвечающий за значимость минимизации суммарного времени простоя машин
    :param C: коэффициент, отвечающий за значимость равномерного использования машин
    :param D: коэффициент, отвечающий за значимость максимизации вклада работ на машинах

    """
    def __init__(self, jobs_completion_time_matrix, setup_times_matrix, jobs_value_matrix, B=1, C=1, D=1):
        assert isinstance(jobs_value_matrix, np.ndarray) and \
               isinstance(jobs_completion_time_matrix, np.ndarray) and \
               isinstance(setup_times_matrix, np.ndarray), \
            TypeError("All matrices should be ndarray!")
        assert isinstance(D, int) and \
               isinstance(B, int) and \
               isinstance(C, int), \
            TypeError("All coefficients must be integers!")
        assert jobs_completion_time_matrix.shape[0] == jobs_value_matrix.shape[0], \
            TypeError("Mismatch in machines quantity!")
        assert (jobs_completion_time_matrix.shape[1] == jobs_value_matrix.shape[1]
                == setup_times_matrix.shape[0] == setup_times_matrix.shape[1]), \
            TypeError("Mismatch in jobs quantity!")

        super().__init__()
        self.jobs_q = jobs_completion_time_matrix.shape[1]
        self.machines_q = jobs_completion_time_matrix.shape[0]
        self.setup_times_matrix = setup_times_matrix
        self.jobs_completion_time_matrix = jobs_completion_time_matrix
        self.jobs_value_matrix = jobs_value_matrix
        self.max_capacity = self.jobs_q
        self.B = B
        self.C = C
        self.D = D
        self.compute_decomposition()

    def set_solution(self):
        """
        Устанавливает поле self.solution как матрицу со строками - списком работ, выполняемых на соответсвенной машине

        """
        solution_list = [key for key, value in self.raw_solution.items() if value == np.int8(1)]
        solution_list.sort(key=lambda x: x % self.jobs_q)

        self.solution = [[] for _ in range(self.machines_q)]

        for el in solution_list:
            self.solution[el // self.jobs_q ** 2].append(el // self.jobs_q % self.jobs_q)

    def compute_decomposition(self):
        """
        Вычисляет декомпозицию на Кронекерывы произведения

        """
        # Порядок m, j, t
        m = self.machines_q
        j = self.jobs_q
        t = self.jobs_q

        A = (self.B * self.setup_times_matrix.max() * j ** 3 * m +
             self.C * self.jobs_completion_time_matrix.max() ** 2 * j ** 4 * m +
             self.D * self.jobs_value_matrix.max() * j ** 2 * m)
        self.delta = A * j

        eye_m = np.eye(m)
        ones_m = np.ones((m, m))
        eye_j = np.eye(j)
        ones_j = np.ones((j, j))
        eye_t = np.eye(t)
        ones_t = np.ones((t, t))


        eye_t1 = eye_t.copy()
        eye_t1[0, 0] = 0

        P = np.zeros((m * j, m * j))
        row_indices = np.arange(m)[:, None, None] * j + np.arange(j)[None, :, None]
        col_indices = np.arange(m)[:, None, None] * j + np.arange(j)[None, None, :]
        P[row_indices, col_indices] = np.einsum('ij,ik->ijk', self.jobs_completion_time_matrix,
                                                self.jobs_completion_time_matrix)
        self.decomposition = [
            [A * ones_m, eye_j, ones_t],  # 1
            [-2 * A * eye_m, eye_j, eye_t],  # 1
            [A * eye_m, ones_j, eye_t],  # 2
            [-A * eye_m, eye_j, eye_t],  # 2
            [A * eye_m, ones_j, eye_t1],  # 3
            [-A * eye_m, ones_j, np.roll(eye_t1, -1, axis=1)],  # 3
            [-A * eye_m, ones_j, np.roll(eye_t1, -1, axis=0)],  # 3
            [A * eye_m, eye_j, eye_t1],  # 3
            [A * eye_m, ones_j, np.rot90(eye_t1, k=2)],  # 3
            [-A * eye_m, eye_j, np.rot90(eye_t1, k=2)],  # 3
            [self.B * eye_m, self.setup_times_matrix, np.roll(eye_t1, -1, axis=0)],  # 4
            [self.C * P, ones_t],  # 5
            [-self.D * np.eye(m * j) * np.reshape(self.jobs_value_matrix, (m * j,), order='C'), eye_t]  # 6
        ]

    def display_solution(self):
        """
        Выводит результат в командную строку

        """
        print("Наилучшее расписание производства:")
        for m in range(len(self.solution)):
            print(f"Последовательность работ для машины {m + 1}:", end=' ')
            for job in self.solution[m]:
                print(job + 1, end=' ')
            print()
