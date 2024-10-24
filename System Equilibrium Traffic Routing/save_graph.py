import graph_DS
import osmnx as ox
import networkx as nx
"""mag worden genegeerd, was om wat grafen al op te slaan indien we ze ooit nodig hadden"""
if __name__ == '__main__':
    #noord, zuid, oost, west
    #opslaan van Regio Gent
    #graph_DS.store_networkxgraph(graph_DS.graph_from_box_coordinates(51.093176,50.999308, 3.651296, 3.832376),'C:/Users/warre/PycharmProjects/VOP/output/RegioGent.csv')

    #opslaan van Vlaanderen
    #graph_DS.store_networkxgraph(graph_DS.graph_from_box_coordinates(51.505612,50.707094, 2.502955, 5.863131),'C:/Users/warre/PycharmProjects/VOP/output/Vlaanderen.csv')
    G = graph_DS.load_networkxgraph('C:/Users/warre/PycharmProjects/VOP/output/Vlaanderen.csv')
    #ox.plot_graph(G)

    #opslaan van Belgie
    #save_networkxgraph(graph_DS.graph_from_box_coordinates(51.505612,50.707094, ...),'C:/Users/warre/PycharmProjects/VOP/output/Vlaanderen.csv')


