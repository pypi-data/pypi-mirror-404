from random import randint

import numpy as np
import time


class Tester:
    def __init__(self, problem_name, matrix=None, name=None):
        self.matrix = matrix
        self.test_name = name
        self.problem_name = problem_name
        print(f"Tester for {self.problem_name} problem was created!\n\n\n")

    def random_binary_matrix(self, vertex_cnt=10, density=0.8):
        self.matrix = np.array(
            [[min(randint(0, int(density * 100 // 10)), 1) for _ in range(vertex_cnt)] for _ in range(vertex_cnt)])

    def random_matrix(self, vertex_cnt=10, max_weight=10, density=0.8, width=None, height=None):
        self.matrix = np.array(
            [[min(randint(0, int(density * 100 // 10)), 1) * randint(0, max_weight) for _ in
              range(vertex_cnt if width == height else width)] for _ in
             range(vertex_cnt if width == height else height)])

    def __display_matrix(self, display_arglist=False, arglist=None):
        if arglist is None:
            arglist = []
        for row in self.matrix:
            for el in row:
                print(el, end=' ')
            print('')
        if display_arglist:
            for el in arglist:
                print(el)

    def tester_function(self, arglist):
        exit("Tester function is not implemented!")

    def test(self, display=False, num_reads=100, arglist=None, display_arglist=False):
        if arglist is None:
            arglist = []
        print(f"{self.test_name if self.test_name is not None else ''}")
        print(f"Testing {self.problem_name} problem!\nDisplay mode is {'on' if display else 'off'}\n")
        if self.matrix is None:
            print("Empty matrix!\n")
            return
        if display:
            self.__display_matrix(display_arglist, arglist)
        start_time = time.time()
        res = self.tester_function(arglist)
        res.find_min_energy(num_reads)
        print(
            f"Testing is completed!\nStart time - {start_time}\nFinish time - {time.time()}\nDuration - {-start_time + time.time()}\n")
        if display:
            res.display_solution()
        try:
            print(f"Solution: {list(map(int, res.solution))}")
        except Exception:
            print(f"Solution: {res.solution}")
        print(f"Minimal energy - {res.min_energy}")
