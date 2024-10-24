import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import random

def graph_from_box_coordinates(north_lat,south_lat,east_lon,west_lon):
    """Creëert een graaf op basis van de opgegeven bounding box-coördinaten"""
    polygon = ox.graph_from_bbox(north_lat,south_lat,east_lon,west_lon,network_type='drive')
    return polygon
    
def graph_from_explicit_location(city,country):
    """Creëert een graaf van het wegennetwerk van de opgegeven stad (en land)"""
    graph_from_place = ox.graph_from_place('{}, {}'.format(city, country), network_type='drive')
    return graph_from_place
    
def plot_mutlidigraph_osmx(graph):
    """Geeft de plot van een MultiDiGraph met behulp van de OSMnx-bibliotheek"""
    ox.plot_graph(graph)
    return

def plot_multidigraph_nx(graph):
    """Geeft de plot van een MultiDiGraph met behulp van de NetworkX-bibliotheek"""
    nx.draw(graph, with_labels=True)
    plt.show()
    return

def successors(graph, node_ID):
    """Geeft een lijst van alle successors (knopen aan takken waarnaar deze knoopt wijst) van de opgegeven knoop terug"""
    return graph.successors(node_ID)

def predecessors(graph, node_ID):
    """Geeft een lijst van alle predecessors (knopen aan takken die naar deze knoop wijzen) van de opgegeven knoop terug"""
    return graph.predecessors(node_ID)

def find_ID_from_coordinates(graph,x,y):
    """Vindt de knoop van de opgegeven graaf die de opgegeven coördinaten heeft"""
    for node_key, node_attrs in graph.nodes(data=True):
        if x==node_attrs['x']:
            if y==node_attrs['y']:
                return node_key
    return 0


def determine_coordinates_from_adress(adress):
    """Geeft de coördinaten van het opgegeven adres"""
    return ox.geocode(adress)
    
def get_value_from_node(graph,node_ID,attribute_name):
    """Geeft de waarde in van het opgegeven attribuut in de opgegeven knoop"""
    return graph.nodes[node_ID][attribute_name]

def set_value_in_node(graph,node_ID,attribute_name,value):
    """Stelt de waarde in van het opgegeven attribuut in de opgegeven knoop"""
    graph.nodes[node_ID][attribute_name]=value
    return

def set_value_in_edge(graph, u,v,attribute_name,value):
    """Stelt de waarde in van het opgegeven attribuut in de opgegeven tak"""
    graph[u][v][attribute_name]=value
    
def get_value_in_edge(graph, u,v,attribute_name):
    """Geeft de waarde van het opgegeven attribuut in de opgegeven tak"""
    return graph[u][v][attribute_name]    

def set_default_value_for_edge(graph, attribute_name, default_value):
    """Stelt een defaultwaarde in voor het opgegeven attribuut in alle takken van de graaf"""
    for u, v, k, data in graph.edges(keys=True, data=True):
        if attribute_name not in list(data):
            graph[u][v][attribute_name]=default_value

def store_networkxgraph(graph, output_path):
    """Slaat de NetworkX-graaf op in het opgegeven uitvoerpad"""
    ox.save_graphml(graph, filepath=output_path)

def load_networkxgraph(input_path):
    """Laadt de NetworkX-graaf uit het opgegeven invoerpad op"""
    return ox.load_graphml(filepath=input_path)


def find_two_close_nodes(G, max_distance):
    """Vindt twee knopen in de graaf die dichter of even ver van elkaar zijn als de opgegeven maximale afstand """
    nodes = list(G.nodes())
    while True:
        # Choose two random nodes
        u, v = random.sample(nodes, 2)
        # Calculate shortest path length between them
        distance = nx.shortest_path_length(G, u, v)
        if distance <= max_distance:
            return u, v