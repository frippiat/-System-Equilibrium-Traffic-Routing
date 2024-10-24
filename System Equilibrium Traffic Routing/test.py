import graph_DS
import kFastestPaths
import networkx as nx
import random
import tqdm
"""
#vlugge testfile, niet relevant
# gechecket dat er zeker geen randomness zit in shortest paths 
G = graph_DS.load_networkxgraph("C:/Users/warre/PycharmProjects/VOP/OD_data/data/Graph.graphml")

allemaal = []
cbar = tqdm.tqdm(total=1000)
for i in range(1000):
    random_nodes = random.sample(list(G.nodes()), 2)
    node1 = random_nodes[0]
    node2 = random_nodes[1]
    while not (nx.has_path(G, node1, node2)):
        random_nodes = random.sample(list(G.nodes()), 2)
        node1 = random_nodes[0]
        node2 = random_nodes[1]
    first = nx.shortest_path(G, source=node1, target=node2, weight='travel_time')

    for i in range(50):
        second = nx.shortest_path(G, source=node1, target=node2, weight='travel_time')
        if second != first:
            print('pfff, dit dus')
    cbar.update(1)

cbar.close()"""
#superlist, G = kFastestPaths.input_data("C:/Users/warre/PycharmProjects/VOP/OD_data/data/OD_Flows_1%.csv","C:/Users/warre/PycharmProjects/VOP/OD_data/data/Graph.graphml", 1, 10)
G = kFastestPaths.complete_graph(graph_DS.load_networkxgraph("C:/Users/warre/PycharmProjects/VOP/OD_data/data/Graph.graphml"))
