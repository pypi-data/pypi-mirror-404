import numpy as np

from QuboClique import QUBOClique
import matplotlib.pyplot as plt
from time import time
from pandas import read_excel

correct_answers_files = [68, 27, 36, 44, 44]
data_files = ["../../../../Downloads/Новая таблица-30.xlsx","../../../../Downloads/Новая таблица-34.xlsx",  "../../../../Downloads/Новая таблица-32.xlsx", "../../../../Downloads/Новая таблица-31.xlsx", "../../../../Downloads/Новая таблица-33.xlsx"]

assert len(data_files) == len(correct_answers_files)
N = len(data_files)
comp_qubo_times = []
solv_times = []
data_sizes = [1000, 776, 300, 250, 200]
best_results = [1e9 for i in range(N)]
results = []
deltas = []

def e_to_m(e, n):
    res = np.zeros((n, n))
    for el in e:
        res[el[0] -1 , el[1]-1] = 1
        res[el[1]-1, el[0]-1] = 1
    return res

for i in range(N):
    print(f'Test {i}')
    print("_______________________________________")
    file_path = data_files[i]
    matrix = e_to_m(read_excel(file_path, header=None).to_numpy(), data_sizes[i])

    time_start_computing_qubo = time()

    mean_time = 0
    mean_res = 0

    sal = QUBOClique(matrix)

    comp_qubo_times.append(time() - time_start_computing_qubo)

    print(f'Test {i}')
    time_start_computing_qubo = time()

    time_start_solving = time()

    sal.find_min_energy(solver='SQAS')

    mean_time += time() - time_start_solving

    res = sal.min_energy

    results.append(res)
    solv_times.append(mean_time)

    real_res = 0

    deltas.append(max(.0,float(correct_answers_files[i] / (abs(results[-1])//2)-1)))

print(f"Computation QUBO times - {comp_qubo_times}")
print(f"Data sizes - {data_sizes}")
print(f"Solving times - {solv_times}")
print(f"Results - {results}")
print(f"Answer - {correct_answers_files}")

print(f"Deltas - {deltas}")

plt.figure(figsize=(8, 6))
plt.plot(data_sizes, deltas, marker='o', linestyle='-', color='b', label='SDS')
plt.title("Относительная ошибка")
plt.xlabel("Размер входных данных")
plt.ylabel("Относительная ошибка")
plt.grid(True)
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








