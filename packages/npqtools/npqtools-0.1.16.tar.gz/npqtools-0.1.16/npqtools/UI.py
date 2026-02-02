from npqtools.problems.QuboProductionScheduling import QUBOProductionScheduling
from npqtools.problems.QuboSalesman import QUBOSalesman
from npqtools.problems.QuboKnapsack import QUBOKnapsack
from npqtools.problems.QuboClique import QUBOClique
from npqtools.problems.QuboMaxWeightClique import QUBOMaxWeightClique

import numpy as np
from pandas import read_excel


def exel_to_nparray(file_path):
    """

    :param file_path: путь к Excel таблице с входными данными
    :return: Numpy матрицу - входные данные
    """
    return read_excel(file_path, header=None).to_numpy()


def salesman():
    """
    Пользовательский интерфейс для задачи Коммивояжера

    """
    print("---------------------------")
    print("*some short information*")
    print("To see examples type - Examples\n")
    print("Which type of datasets you want to use?")
    print("1 - Adjacency matrix")
    print("2 - Coordinates matrix")
    print("---------------------------")

    inp = input().strip().lower()
    print("Enter path to your dataset (.xlsx format)")

    if inp == '1':
        tmp = QUBOSalesman(adjacency_matrix=exel_to_nparray(input()))
        tmp.find_min_energy()
        tmp.display_solution()
        try:
            print(f"Solution: {list(map(int, tmp.solution))}")
        except Exception:
            print(f"Solution: {tmp.solution}")
    elif inp == '2':
        tmp = QUBOSalesman(coord_matrix=100 * exel_to_nparray(input()))
        tmp.find_min_energy()
        tmp.display_solution()
        tmp.get_qubo_excel(input("Где сохранить файл?"))
        try:
            print(f"Solution: {list(map(int, tmp.solution))}")
        except Exception:
            print(f"Solution: {tmp.solution}")
    elif inp == 'examples':
        print("*some examples*")
    else:
        print("Invalid input.")
        salesman()


def knapsack():
    """
    Пользовательский интерфейс для задачи о рюкзаке

    """
    print("---------------------------")
    print("*some short information*")
    print("To see examples type - Examples\n")

    inp = input().strip()
    print("Enter path to your dataset (.xlsx format)")

    if inp.lower() == 'examples':
        print("*some examples*")
    elif inp.endswith(".xlsx"):
        print("Enter integer capability")
        cap = input()
        if inp.isdecimal():
            tmp = QUBOKnapsack(exel_to_nparray(inp), cap)
            tmp.find_min_energy()
            tmp.display_solution()
        else:
            print("Invalid input.")
            knapsack()
    else:
        print("Invalid input.")
        knapsack()


def clique():
    """
    Пользовательский интерфейс для задачи о поиске максимальной клики и клики максимального веса

    """
    print("---------------------------")
    print("*some short information*")
    print("To see examples type - Examples\n")
    print("Which type of problem you want to solve?")
    print("1 - Clique with maximum summary weight")
    print("2 - Clique with maximum vertex quantity")
    print("---------------------------")

    inp = input().strip().lower()
    print("Enter path to your dataset (.xlsx format)")

    if inp == '1':
        tmp = QUBOMaxWeightClique(exel_to_nparray(input()))
        tmp.find_min_energy()
        tmp.display_solution()
        try:
            print(f"Solution: {list(map(int, tmp.solution))}")
        except Exception:
            print(f"Solution: {tmp.solution}")
    elif inp == '2':
        tmp_mat = exel_to_nparray(input())
        print(tmp_mat)
        N = np.max(tmp_mat)

# Создаём нулевую матрицу смежности N×N
        adj_matrix = np.zeros((N, N), dtype=int)

    # Заполняем матрицу (для неориентированного графа)
        adj_matrix[tmp_mat[:, 0] - 1, tmp_mat[:, 1] - 1] = 1
        adj_matrix[tmp_mat[:, 1] - 1, tmp_mat[:, 0] - 1] = 1
        tmp = QUBOClique(adj_matrix)
        tmp.find_min_energy()
        print(tmp.min_energy)
        #tmp.display_solution()
        try:
            print(f"Solution: {list(map(int, tmp.solution))}")
        except Exception:
            print(f"Solution: {tmp.solution}")
    elif inp == 'examples':
        print("*some examples*")
    else:
        print("Invalid input.")
        clique()


def prod():
    """
    Пользовательский интерфейс для задачи о распределении и планировании производства

    """
    print("---------------------------")
    print("*some short information*")
    print("To see examples type - Examples\n")
    print("---------------------------")

    print("Enter path to your dataset of jobs completion types (.xlsx format)")
    inp1 = input()
    if inp1.lower() == 'examples':
        print("*some examples*")
    elif inp1.endswith(".xlsx"):
        print("Great! Now enter path to your dataset of machines setup times(.xlsx format)")
        inp2 = input()
        if inp2.endswith(".xlsx"):
            print("Great! Now enter path to your dataset of impact of completion jobs on machines (.xlsx format)")
            inp3 = input()
            if inp3.endswith(".xlsx"):
                tmp = QUBOProductionScheduling(exel_to_nparray(inp1), exel_to_nparray(inp2), exel_to_nparray(inp3))
                tmp.find_min_energy()
                tmp.display_solution()

    else:
        print("Invalid input.")
        prod()


def start():
    """
    Запускается из файла UI.exe Представляет интерфейс для выбора задачи

    """
    print(
        "Hi! \n You are using npqtools - quantum tool for solving hard computation problems. \n Which problem would you like to solve?")
    print("Type 1 - Salesman problem")
    print("Type 2 - Knapsack problem")
    print("Type 3 - Max weight clique problem")
    print("Type 4 - Production scheduling problem")
    print("Type 0 - exit")
    print("Type info - to get more information about our project")

    cont = True
    while cont:
        inp = input().strip().lower()

        if inp == '1':
            cont = False
            salesman()
        elif inp == '2':
            cont = False
            knapsack()
        elif inp == '3':
            cont = False
            clique()
        elif inp == '4':
            cont = False
            prod()
        elif inp == 'info':
            cont = False
            print("More information about the project can be found at ____")
        elif inp == '0':
            print("Goodbye!")
            return
        else:
            print("Invalid input. Please try again.")


if __name__ == '__main__':
    start()

