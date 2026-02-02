import networkx as nx
import matplotlib.pyplot as plt
import numpy as np


def PaintNonOrientatedGraphWithWay(matrix: np.array, way: np.array) -> None:
    G = nx.Graph()
    G.add_nodes_from(list(range(1, matrix.shape[0] + 1)))
    for i in range(matrix.shape[0]):
        for j in range(i, matrix.shape[0]):
            if matrix[i][j]:
                G.add_weighted_edges_from([(i + 1, j + 1, matrix[i][j])])
    Positions = nx.spring_layout(G)
    nx.draw_networkx_nodes(G, Positions, node_color="black", node_size=20)
    Labels = {node: f"{node}" for node in G.nodes}
    nx.draw_networkx_labels(G, Positions, labels=Labels, font_color="crimson", horizontalalignment="left",
                            verticalalignment="bottom", font_weight="black")
    nx.draw_networkx_edges(G, Positions, width=2, alpha=0.3, edge_color="gray")
    HighlightedEdges = []
    for i in range(1, way.size):
        HighlightedEdges.append((way[i - 1] + 1, way[i] + 1))
    nx.draw_networkx_edges(G, Positions, edgelist=HighlightedEdges, edge_color="blue", width=3, alpha=0.5,
                           label="Ребра пути")
    plt.legend(fontsize=10)
    plt.title("Salesman Graph")
    plt.axis("off")
    plt.show()
    return


def PaintNonOrientatedGraphWithCycle(matrix: np.array, way: np.array) -> None:
    G = nx.Graph()
    G.add_nodes_from(list(range(1, matrix.shape[0] + 1)))
    for i in range(matrix.shape[0]):
        for j in range(i, matrix.shape[0]):
            if matrix[i][j] > 0:
                G.add_weighted_edges_from([(i + 1, j + 1, matrix[i][j])])
    Positions = nx.spring_layout(G)
    nx.draw_networkx_nodes(G, Positions, node_color="black", node_size=20)
    Labels = {node: f"{node}" for node in G.nodes}
    nx.draw_networkx_labels(G, Positions, labels=Labels, font_color="crimson", horizontalalignment="left",
                            verticalalignment="bottom", font_weight="black")
    nx.draw_networkx_edges(G, Positions, width=2, alpha=0.3, edge_color="gray")
    HighlightedEdges = []
    for i in range(1, way.size + 1):
        HighlightedEdges.append((way[i - 1] + 1, way[i % way.size] + 1))
    nx.draw_networkx_edges(G, Positions, edgelist=HighlightedEdges, edge_color="blue", width=2, alpha=0.5,
                           label="Ребра пути")
    plt.legend(fontsize=10)
    plt.title("Salesman Graph")
    plt.axis("off")
    plt.show()
    return


def PaintVertexSetInNonWeightedGraph(matrix: np.array, vertex_list: np.array) -> None:
    G = nx.Graph()
    G.add_nodes_from(list(range(1, matrix.shape[0] + 1)))
    for i in range(matrix.shape[0]):
        for j in range(i + 1, matrix.shape[0]):
            if matrix[i][j]:
                G.add_weighted_edges_from([(i + 1, j + 1, matrix[i][j])])
    Positions = nx.spring_layout(G)
    for i in range(vertex_list.size):
        vertex_list[i] += 1
    nx.draw_networkx_nodes(G, Positions, node_color="black", node_size=10)
    Labels = {node: f"{node}" for node in G.nodes}
    nx.draw_networkx_nodes(G, Positions, node_color="navy", node_size=20, nodelist=vertex_list)
    nx.draw_networkx_edges(G, Positions, width=1, alpha=0.3, edge_color="gray")
    HighlightedEdges = []
    for i in range(vertex_list.size):
        for j in range(i + 1, vertex_list.size):
            HighlightedEdges.append((vertex_list[i], vertex_list[j]))
    nx.draw_networkx_edges(G, Positions, edgelist=HighlightedEdges, edge_color="blue", width=2, alpha=0.5,
                           label="Ребра клики")
    nx.draw_networkx_labels(G, Positions, labels=Labels, font_color="crimson", horizontalalignment="left",
                            verticalalignment="bottom", font_weight="black", font_size=10)
    plt.legend(fontsize=10)
    plt.title("Max Clique")
    plt.axis("off")
    plt.show()
    return


def PaintVertexSetInWeightedGraph(matrix: np.array, vertex_list: np.array) -> None:
    G = nx.Graph()
    G.add_nodes_from(list(range(1, matrix.shape[0] + 1)))
    for i in range(matrix.shape[0]):
        for j in range(i, matrix.shape[0]):
            if matrix[i][j]:
                G.add_weighted_edges_from([(i + 1, j + 1, matrix[i][j])])
    Positions = nx.spring_layout(G)
    for i in range(vertex_list.size):
        vertex_list[i] += 1
    nx.draw_networkx_nodes(G, Positions, node_color="black", node_size=10)
    nx.draw_networkx_nodes(G, Positions, node_color="navy", node_size=20, nodelist=vertex_list)
    Labels = {node: f"{node}" for node in G.nodes}
    nx.draw_networkx_labels(G, Positions, labels=Labels, font_color="crimson", horizontalalignment="left",
                            verticalalignment="bottom", font_weight="black", font_size=10)
    nx.draw_networkx_edges(G, Positions, width=1, alpha=0.3, edge_color="gray")
    HighlightedEdges = []
    for i in range(vertex_list.size):
        for j in range(i + 1, vertex_list.size):
            HighlightedEdges.append((vertex_list[i], vertex_list[j]))
    nx.draw_networkx_edges(G, Positions, edgelist=HighlightedEdges, edge_color="blue", width=2, alpha=0.5,
                           label="Ребра клики")
    plt.legend(fontsize=10)
    plt.title("Max Clique")
    plt.axis("off")
    plt.show()
    return


# vertexes[i][j] - j - я координата i - й вершины (0 - x, 1 - y), way - последовательность вершин (нумерация с 0).
def PrintGraphWithVertexCoordinatesAndWay(vertexes: np.array, way: np.array):
    plt.figure()
    for i in range(vertexes.shape[0]):
        for j in range(i + 1, vertexes.shape[0]):
            plt.plot([vertexes[i][0], vertexes[j][0]], [vertexes[i][1], vertexes[j][1]], color='gray', alpha=0.3)
    for i in range(1, way.shape[0]):
        if i == 1:
            plt.plot([vertexes[way[i - 1]][0], vertexes[way[i]][0]], [vertexes[way[i - 1]][1], vertexes[way[i]][1]],
                     color='blue', alpha=0.5, label="Ребра пути")
            continue
        plt.plot([vertexes[way[i - 1]][0], vertexes[way[i]][0]], [vertexes[way[i - 1]][1], vertexes[way[i]][1]],
                 color='blue', alpha=0.5)
    for i in range(vertexes.shape[0]):
        plt.text(vertexes[i][0], vertexes[i][1], str(i + 1), ha='left', va='bottom', color='crimson', weight='black')
    plt.title("Salesman Graph")
    plt.legend(fontsize=10)
    plt.axis('on')
    plt.show()


def PrintTiling2Dim(squares: np.array, q, banned=None, separations=None):
    x, y = squares.shape[0], squares.shape[1]
    for i in range(x):
        for j in range(y):
            if separations is not None:
                if ((i, j), (i, j + 1)) in separations or ((i, j + 1), (i, j)) in separations:
                    plt.plot([i, i + 1], [j + 1, j + 1], color='black', linewidth=10)
            if separations is not None:
                if ((i, j), (i + 1, j)) in separations or ((i + 1, j), (i, j)) in separations:
                    plt.plot([i + 1, i + 1], [j + 1, j], color='black', linewidth=10)
            plt.plot([i, i], [j, j + 1], color='black')
            plt.plot([i, i + 1], [j, j], color='black')
            plt.plot([i + 1, i + 1], [j, j + 1], color='black')
            plt.plot([i, i + 1], [j + 1, j + 1], color='black')
            if banned is not None:
                if (i, j) in banned:
                    plt.fill([i, i + 1, i + 1, i], [j, j, j + 1, j + 1], color='black')
            if squares[i][j] != 0:
                try:
                    plt.fill([i, i + 1, i + 1, i], [j, j, j + 1, j + 1],
                             color=(squares[i, j] / (q + 1), 1.0 - squares[i, j] / (q + 1),
                                    0.5 + 0.5 * squares[i, j] / (q + 1) * (- 1) ** squares[i, j]), alpha=0.75)
                except Exception:
                    print(squares[i, j] / (q + 1), 1.0 - squares[i, j] / (q + 1),
                          0.5 + 0.5 * squares[i, j] / (q + 1) * (- 1) ** squares[i, j], ' is not RGB')
                plt.text(i + 0.5, j + 0.5, str(squares[i][j]), color='black', ha='center', va='center')
    plt.title("Rectangle Tiling")
    plt.axis('off')
    plt.show()

