import random
import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np

#genereren van een random connected graaf met n knopen en m takken
#ook hier heb ik veel te veel werk ingestoken, dacht dat het langer ging duren om echte grafen in te laden..
#mag dus op zich genegeerd worden ook, heeft spijtig genoeg niet veel bijgedragen aan het project
#is echt wel random nu, maar denk voldoende voor eerste testen
def generate_random_connected(n, m, nodes=None):
    #als geen lijst met knoopnamen werd doorgegeven
    if (nodes==None):
        nodes = []
        for i in range(n):
            nodes.append(i)
    if (len(nodes) != n):
        raise Exception('Aantal knopen moet gelijk zijn aan m!')
    if (m<n or n<=0):
        raise Exception('onmogelijk om geconnecteerde graaf te maken!')

    #creeren van een minimale opspannende boom
    S, visited = set(nodes), set()

    #neem random knoop
    current_node = random.sample(S, 1).pop()
    S.remove(current_node)
    visited.add(current_node)

    #graaf opstellen
    G = nx.DiGraph()

    #voor random weginformatie
    snelheden = [5.56, 8.33, 13.89, 19.44, 25, 33.33]
    while S:
        #bezoek random knoop
        neighbor = random.sample(nodes, 1).pop()
        #als deze nog niet was bezocht, markeer als bezocht en verbind met current_node
        if neighbor not in visited:
            n = random.randint(1, 4)   #random_aantal_rijvakken
            capaciteit = 1000*n
            lengte = random.randint(500, 3000) #random afstand in m, ook niet echt een idee hoe je dat randomized
            snelheidslimiet = snelheden[random.randint(0,5)] #random snelheidslimiet
            gewicht = random.randint(0, capaciteit) #tijdelijke flow voor te kunnen plotten
            G.add_edge(current_node, neighbor, weight=gewicht, max_speed=snelheidslimiet, capacity=capaciteit, width=n, length=lengte)
            S.remove(neighbor)
            visited.add(neighbor)
        #nieuwe te onderzoeken node
        current_node = neighbor

    #nu hebben we geconnecteerde graaf dus kunnen we gewoon takken bijvoegen tot we gewenste aantal hebben
    if (G.number_of_edges() < m):
        for i in range(m-G.number_of_edges()):
            u, v = random.sample(nodes,1).pop(), random.sample(nodes,1).pop()
            #geen wegen tussen eenzelfde knoop, en ook geen takken die er al waren
            while (u==v or ((u,v) in G.edges)):
                v = random.sample(nodes,1).pop()
            n = random.randint(1, 4)  # random_aantal_rijvakken
            lengte = random.randint(500, 3000) #random afstand in m, ook niet echt een idee hoe je dat randomized
            capaciteit = 1000 * n
            snelheidslimiet = snelheden[random.randint(0, 5)]  # random snelheidslimiet
            gewicht = random.randint(0, capaciteit)  # tijdelijke flow voor te kunnen plotten
            G.add_edge(u,v , weight=gewicht, max_speed=snelheidslimiet, capacity=capaciteit, width=n, length=lengte)
    return G

#genereert random flows en OD-paren
def generate_random_flows(G, nOD = 0):
    flows = {}
    if (nOD<=0):
        nOD = random.randint(G.number_of_nodes()//4, G.number_of_nodes()//2)
    for i in range(nOD):
        u, v = random.sample(G.nodes, 1).pop(), random.sample(G.nodes, 1).pop()
        # geen wegen tussen eenzelfde knoop
        while (u == v):
            v = random.sample(G.nodes, 1).pop()
        flows[(u,v)] = random.randint(500, 4000) #TODO: weet niet goed hoe je die flows goed kan randomizen..
    return flows



