import numpy as np

from QuboSalesman import QUBOSalesman
import matplotlib.pyplot as plt
from time import time
from pandas import read_excel

correct_answers_files = ["../../../../Downloads/Новая таблица-18.xlsx", "../../../../Downloads/Новая таблица-21.xlsx", "../../../../Downloads/Новая таблица-27.xlsx", "../../../../Downloads/Новая таблица-23.xlsx", "../../../../Downloads/Новая таблица-25.xlsx"]
data_files = ["../../../../Downloads/Новая таблица-19.xlsx", "../../../../Downloads/Новая таблица-20.xlsx", "../../../../Downloads/Новая таблица-26.xlsx", "../../../../Downloads/Новая таблица-22.xlsx", "../../../../Downloads/Новая таблица-24.xlsx"]

assert len(data_files) == len(correct_answers_files)
N = len(data_files)
comp_qubo_times = []
solv_times = []
real_results = []
data_sizes = []
best_results = [1e9 for i in range(N)]
results = []
deltas = []

for i in range(0, 5):
    print(f'Test {i}')
    print("_______________________________________")
    file_path = data_files[i]
    matrix = read_excel(file_path, header=None).to_numpy()

    data_sizes.append(matrix.shape[0])

    time_start_computing_qubo = time()

    mean_time = 0
    mean_res = 0

    sal = QUBOSalesman(coord_matrix=matrix)

    comp_qubo_times.append(time() - time_start_computing_qubo)

    print(f'Test {i}')
    time_start_computing_qubo = time()

    time_start_solving = time()

    sal.find_min_energy(solver='SQAS', num_reads=1)

    mean_time += time() - time_start_solving

    res = sal.min_energy

    results.append(res)
    solv_times.append(mean_time)

    real_res = 0


    real = read_excel(correct_answers_files[i], header=None).to_numpy().T[0].T
    for k in range((matrix.shape[0])):
        real_res += sal.adjacency_matrix[real[k]-1, real[(k+1)%(matrix.shape[0])]-1]

    deltas.append(max(.0,float((results[-1] / real_res - 1))))
    real_results.append(real_res)

print(f"Computation QUBO times - {comp_qubo_times}")
print(f"Data sizes - {data_sizes}")
print(f"Solving times - {solv_times}")
print(f"Results - {results}")
print(f"Answer - {real_results}")

print(f"Deltas - {deltas}")

plt.figure(figsize=(8, 6))
plt.plot(data_sizes, deltas, marker='o', linestyle='-', color='b', label='SQAS')
plt.title("Относительная ошибка")
plt.xlabel("Размер входных данных")
plt.ylabel("Относительная ошибка")
plt.grid(True)
plt.legend()
plt.show()


plt.figure(figsize=(8, 6))
plt.plot(data_sizes, solv_times, marker='o', linestyle='-', color='r', label='время')
plt.title("Время решения")
plt.xlabel("Размер входных данных")
plt.ylabel("Время решения (сек)")
plt.grid(True)
plt.show()

plt.figure(figsize=(8, 6))
plt.plot(data_sizes, comp_qubo_times, marker='o', linestyle='-', color='g', label='время')
plt.title("Время составления матрицы QUBO")
plt.xlabel("Размер входных данных")
plt.ylabel("Время составления (сек)")
plt.grid(True)
plt.show()








