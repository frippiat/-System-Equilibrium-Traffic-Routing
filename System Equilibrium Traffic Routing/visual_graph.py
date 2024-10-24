#fancy_plot:
#Install windows package from: https://graphviz.gitlab.io/_pages/Download/Download_windows.html
#Install python graphviz package
#Add C:\Program Files (x86)\Graphviz2.38\bin to User path
#Add C:\Program Files (x86)\Graphviz2.38\bin\dot.exe to System Path
import copy
import csv
import code_for_UEandSE
import graphviz
import os
import networkx as nx
import numpy as np
import random
import matplotlib.pyplot as plt
import pylab
import random_test_data
import graph_DS
from shapely.geometry import LineString,Point
import osmnx as ox
import time
import kFastestPaths
import math
import tqdm
import plotly.graph_objects as go
import geopy
import plotly.express as px
"""file waarin ik heel heel hard heb geprutst met allerlei packages om uiteindelijk een mooie html visualisatie te kunnen maken, ik heb alle functies wel nog laten staan met 
commentaar bij"""
def fancy_graphviz_plot():
    """een voorbeeld hiervan werd op github toegevoegd met de naam "voorbeeld_graphviz_plot, de code is al wat aangepast sinds dat voorbeeld, maar uiteindelijk werd graphviz niet echt gebruikt"""
    #best enkel voor 1 OD paar aangezien dit niet de snelste is (tenzij je kan vinden hoe sfdp werkt als visualisatie engine, dat zou ook voor volledige grafen moeten schalen)
    ###############################################################
    #nodige initialisaties:
    outputpath = "C:/Users/warre/PycharmProjects/VOP/output/visualisation/OD"
    k = 3
    precisie = 2000
    factor = 3000 #is beetje raar bij graphviz ma die kan niet zo kleine coordinaatverschillen aan als plotly, dus moet het met een groot genoege factor vermenigvuldigd worden
    G = kFastestPaths.complete_graph(graph_DS.load_networkxgraph("C:/Users/warre/PycharmProjects/VOP/OD_data/data/Graph.graphml"))
    w, z = 1596398275, 300235023
    paths = kFastestPaths.k_fastest_paths(G, w, z, k, 10)
    superlist = [([w, z, 2500], paths)] # 1 OD paar
    #superlist = load...
    #graphviz.executable = 'C:/Program Files/Graphviz/bin/'
    #os.environ["PATH"] += os.pathsep + 'C:/Users/warre/PycharmProjects/VOP/Graphviz/bin/' # werkt enkel lokaal!!,dit voegt de folder waar graphviz executables zijn toe aan de path variabele zdat pad kan worden gevonden
    f = graphviz.Digraph(filename=outputpath, engine='fdp')
    f.graph_attr['overlap'] = 'false'
    ##############################################################
    #step 0: UE en SE berekenen
    UE, SE = code_for_UEandSE.linearapproxEQ(G, superlist, precisie, "UE"), code_for_UEandSE.linearapproxEQ(G, superlist, precisie, "SE")
    GSE = copy.deepcopy(G)
    #toekennen van de flows
    code_for_UEandSE.assign_flows(UE, G)
    code_for_UEandSE.assign_flows(SE, GSE)
    #flows per route
    fprue = flows_per_route(UE, superlist)
    fprse = flows_per_route(SE, superlist)
    #totale reistijden
    uett = code_for_UEandSE.get_total_travel_time(UE, G)
    sett = code_for_UEandSE.get_total_travel_time(SE, GSE)
    print(uett)
    print(sett)
    diff = uett-sett
    print(f"diff = {round(diff//2600)}u {round((diff%3600)//60)}m {round((diff%3600)%60)}s")
    ##############################################################
    #stap 1: alles plotten?
    #als paths is gespecifieerd enkel deze snelste paden plotten
    if paths:
        edges = {(element[0], element[1]): False for element in G.edges}
        nodes =  {t:False for t in G.nodes}
        for path in paths:
            for edge in path:
                edges[edge] = True
                nodes[edge[0]] = True
                nodes[edge[1]] = True
    else:
        edges = {(element[0], element[1]): True for element in G.edges}
        nodes =  {t:True for t in G.nodes}
    ##############################################################
    #stap 2: nodige toevoegen
    #takken
    colors = ["grey", "lightgreen", "limegreen", "green", "bisque", "orange", "darkorange", "lightcoral", "red"] #TODO: verschillende kleurtjes er in verwerken
    already_added = [] #om geen dubbelaars toe te voegen
    coordinates = {u:None for u in G.nodes}
    pbar = tqdm.tqdm(total = len(G.edges))
    for u, v, d in G.edges(data=True):
        if edges[(u,v)] == False:
            continue
        if 'geometry' in d:
            coord = d['geometry']
            coordinates[u] = coord.coords[0]
            coordinates[v] = coord.coords[-1]
        else: #schatten van de coordinaten
            cu = coordinates[u] if coordinates[u] else estimate_coords(G, u)
            cv = coordinates[v] if coordinates[v] else estimate_coords(G, v)
            if not cu or not cv:
                continue #stel dat er toch nog een coordinaat niet gekend is (komt normaal niet voor)
            coord = LineString([cu, cv])
        #u als nog niet toegevoegd
        if u not in already_added:
            coord_u = coord.coords[0]
            position_u = f'{coord_u[0] * factor},{coord_u[1] * factor}!' #dit is de manier waarop je hard coordinaten codeert met fdp engine
            if u == w or u == z:
                #f.node(str(v), label="", color="gold", pos=position_v, shape="star", height="2.5", width="2.5", style="filled")
                f.node(str(u), label="", image="C:/Users/warre/PycharmProjects/VOP/afbeeldingen/test_city.jpg", pos=position_v, fixedsize="True", shape="plaintext")
            else:
                f.node(str(u), label="", color="black", pos=position_u, penwidth="30")
            #layer3.append(go.Scatter(x=[coord_u[0]] , y=[coord_u[1]], mode='markers', marker=dict(size=4 if ODnodes[u] else 2, color="red" if ODnodes[u] else "black"), hovertemplate=text))
            already_added.append(u)
        #v als nog niet toegevoegd
        if v not in already_added:
            coord_v = coord.coords[-1]
            position_v = f'{coord_v[0] * factor},{coord_v[1] * factor}!'
            if v == w or v == z:
                #f.node(str(v), label="", color="gold", pos=position_v, shape="star", height="2.5", width="2.5", style="filled")
                f.node(str(v), label="", image="C:/Users/warre/PycharmProjects/VOP/afbeeldingen/test_city.jpg", pos=position_v, fixedsize="True", shape="plaintext")
            else:
                f.node(str(v), label="", color="black", pos=position_v, penwidth="30")
            # layer3.append(go.Scatter(x=[coord_u[0]] , y=[coord_u[1]], mode='markers', marker=dict(size=4 if ODnodes[u] else 2, color="red" if ODnodes[u] else "black"), hovertemplate=text))
            already_added.append(u)
        #edge
        #kleur
        diff = G[u][v]['flow'] - GSE[u][v]['flow']
        if diff > 0:  # yellow
            #r = 125+min(diff, 120) #boven de 100 blijven anders wordt het veel te donker
            #g = 125+min(diff, 120)
            #b  = 0
            color = "yellow"
        elif diff < 0:  # green als SE meer eraan toekent
            #r = b = 0
            #g = 125+min(abs(diff), 120)
            color = "green"
        else:
            #r=g=b=185
            color="gray"
        #color = f"rgb({r}, {g}, {b})"
        # edges vermooien: https://graphviz.org/docs/edges/ -> meer op wegen laten lijken
        f.edge(str(u), str(v), label=f"UE: {G[u][v]['flow']} SE: {GSE[u][v]['flow']}",fontsize='30', _attributes={'pos': ' '.join(f'{x*factor},{y*factor}!' for x, y in coord.coords), 'color':color, 'penwidth': "30"})
        pbar.update(1)
    pbar.close()
    ##############################################################################################
    #laatste stap: tonen
    f.view()


#ingebouwde functies van osmx gebruiken, maar heb je minder vrijheid mee dan bij graphviz, echter kan deze wel gigantische grafen aan...
# hierbij mag men niet filteren zoals in de functie complete_graph!
def osmx_plot(G,paths=None):
    colors = ['grey', 'lightgreen', 'limegreen', 'green', 'bisque', 'orange', 'darkorange', 'lightcoral', 'red']
    edge_colors = []
    for u, v, d in G.edges(data=True):
        if 'weight' in d:
            index = min(8, int(d['weight'] // (d['capacity'] / 9)))
            edge_colors.append(colors[index])
        else:
            edge_colors.append('white')
    #edge_labels=dict([((u,v,),d['weight']) for u,v,d in G.edges(data=True) if 'weight' in d else 0])

    ox.plot_graph(G, node_color='w', edge_color=edge_colors)

def estimate_coords(G, u, recursion_depth=0):
    """benadert de coordinaten van u door te kijken naar de coordinaten van de buren, houd wel nog geen rekening met hoe ver ze liggen"""
    #als je al 4x hebt moeten recursief zoeken om de coordinaat te kunnen benaderen, is dit omdat je itereert tussen u en v natuurlijk als je benadering voor buur v nodig hebt voor benadering u
    if recursion_depth > 4:
        return None
    x_coord = 0
    y_coord = 0
    number_of_neighbors = 0
    for v in G[u]: #bekijk alle buren
        if 'geometry' in G[u][v]: #coordinaat van de knoop zit dus toch in andere tak vertrekkend uit u opgeslagen
            coord = G[u][v]['geometry'].coords
            return coord[0][0], coord[0][1]

    for v in G[u]: #bekijk nogmaals de buren
        for w in G[v]: #om naar coord van v te zoeken
            if 'geometry' in G[v][w]:
                coord = G[v][w]['geometry'].coords
                if w == u: #stel er is enkel een tak van w naar u dan heb je nu toch de coordinaat van u gevonden
                    return coord[-1][0], coord[-1][1]
                #anders weet je gewoon de coordinaat van v
                x_coord += coord[0][0]
                y_coord += coord[0][1]
                number_of_neighbors+=1
                break #niet meer nodig om verder te lopen want je hebt coordinaat van deze buur
        #als hier komt dan is ook coordinaat van buur niet gekend dus moet deze benaderd worden, echter is dit een extra recursie op v om de coordinaat van u te zoeken
        appr = estimate_coords(G, v, recursion_depth=recursion_depth+1)
        if not appr:
            continue #deze knoop niet meerekenen voor de benadering
        x_coord += appr[0]
        y_coord += appr[1]
        number_of_neighbors+=1
    if number_of_neighbors == 0: #geen buren gevonden die kunnen helpen om coordinaten te benaderen
        return None
    return x_coord/number_of_neighbors, y_coord/number_of_neighbors #pas als de coordinaat echt nergens opgeslagen ligt dan benader je het door het gemiddelde van de omstaanden waarvan wel coordinaat is gekend

def flows_per_route(Eq, superlist):
    #hoeveel flows kent eq toe aan elke route tussen OD paar? deze functie maakt er een woordenboek van om gemakkelijk te kunnen opvragen voor te visualiseren dan
    ans = {}
    for OD in superlist:
        ans[(OD[0][0], OD[0][1])] = {}
    for i in range(1, len(Eq)):
        if Eq[i][0][:2] == "fr":
            first_index = Eq[i][0].find('|')
            second_index = Eq[i][0].find('|', first_index + 1)
            Origin, Destination, route = int(Eq[i][0][2:first_index]), int(Eq[i][0][first_index + 1:second_index]), int(Eq[i][0][second_index + 1:])  # fr = "fr%s%s%s" %(listoflists[0][0], listoflists[0][1], i)
            ans[(Origin, Destination)][route] = Eq[i][1]  # flow op route steken
    return ans

def plot_random_fastest_path():
    """om de k snelste paden tussen twee random knopen met een bepaalde factor te visualiseren, ook hiervan zijn er voorbeelden op de github aanwezig"""
    #########################parameters#####################################
    inputpath = "C:/Users/warre/PycharmProjects/VOP/OD_data/data/Graph.graphml"
    k = 4
    factor = 1.2
    #########################berekeningen##################################
    G = kFastestPaths.complete_graph(graph_DS.load_networkxgraph(inputpath))
    Gcopy = copy.deepcopy(G)
    origin, destination = random.choice(list(G.nodes())), random.choice(list(G.nodes()))
    superlist = kFastestPaths.k_fastest_paths(G, origin, destination, k, factor)
    edges = {edge:False for edge in G.edges}
    ########################visualisatie###################################
    fig = go.Figure()
    # knopen dubbel toevoegen vertraagt het interactieve
    already_added = []
    # opslaan van alle info op dan zeer gemakkelijk een hover tekst te kunnen toevoegen
    pbar = tqdm.tqdm(total=len(superlist))
    for path in superlist:
        for edge in path:
            edges[edge] = True
        pbar.update(1)
    pbar.close()
    pbar = tqdm.tqdm(total=len(G.edges))
    coordinates = {u: None for u in G.nodes}  # om niet telkens de coordinaat te moeten schatten als het niet nodig is
    #lagen
    layer1 = []
    layer2 = []
    layer3 = []
    layer4 = []
    # voeg knopen en takken toe
    for u, v, d in G.edges(data=True):
        if 'geometry' in d:
            coord = d['geometry']
            coordinates[u] = coord.coords[0]
            coordinates[v] = coord.coords[-1]
        else:  # schatten van de coordinaten
            cu = coordinates[u] if coordinates[u] else estimate_coords(G, u)
            cv = coordinates[v] if coordinates[v] else estimate_coords(G, v)
            if not cu or not cv:
                print("oei")
                continue  # stel dat er toch nog een coordinaat niet gekend is (komt normaal niet voor)
            coord = LineString([cu, cv]) #het wegsegment tussen u en v wordt voorgesteld als een rechte lijn tussen de twee
        # u als nog niet toegevoegd
        if u not in already_added:
            text = f"Node: {u}"
            coord_u = coord.coords[0]
            if u==origin or u == destination:
                layer4.append(go.Scatter(x=[coord_u[0]], y=[coord_u[1]], mode='markers', marker=dict(size=15, color= "gold", symbol='star'), hovertemplate=f"Node {u}"))
            else:
                layer3.append(go.Scatter(x=[coord_u[0]], y=[coord_u[1]], mode='markers', marker=dict(size=4, color= "rgb(120, 120, 120)"), hovertemplate=f"Node {u}"))
            already_added.append(u)
        # v als nog niet toegevoegd
        if v not in already_added:
            text = f"Node: {v}"
            coord_v = coord.coords[-1]
            if  v == origin or v == destination:
                layer4.append(go.Scatter(x=[coord_v[0]], y=[coord_v[1]], mode='markers', marker=dict(size=15, color="gold", symbol='star'), hovertemplate=f"Node {v}"))
            else:
                layer3.append(go.Scatter(x=[coord_v[0]], y=[coord_v[1]], mode='markers', marker=dict(size=4, color="rgb(120, 120, 120)"), hovertemplate=f"Node {v}"))
            already_added.append(v)
        #edge
        text = f"Deze tak stelt een wegsegment voor met: <br> - snelheidslimiet: {G[u][v]['speed_kph']} km/u <br> - {G[u][v]['lanes']} rijvakken"
        xs, ys = zip(*coord.coords)
        if edges[(u,v)]:
            layer2.append(go.Scatter(x=xs, y=ys, mode='lines', marker=dict(size=5, color="red"), hovertemplate=text))  # tak rood als in snelste paden, anders zwart
        else:
            layer1.append(go.Scatter(x=xs, y=ys, mode='lines', marker=dict(size=1, color="rgb(185, 185, 185)")))
        pbar.update(1)
    pbar.close()
    # legende maken om het te verduidelijken -> duurt suuuupeer lannggg TODO: fix, ook bij functie interactive_plot()
    # layout instellen
    fig.update_layout(
        title=f'{k} snelste paden berekend met factor {factor}',
        title_font_size=24,
        # legend_title_text='Legende:',
        showlegend=False,
        margin=dict(l=20, r=20, t=60, b=20),
        hovermode='closest',
        dragmode='pan',
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
    )
    for element in layer1:
        fig.add_trace(element)
    for element in layer2:
        fig.add_trace(element)
    for element in layer3:
        fig.add_trace(element)
    for element in layer4:
        fig.add_trace(element)
    # tonen + opslaan
    fig.show()
    fig.write_html(f'C:/Users/warre/PycharmProjects/VOP/output/visualisation/randomfastestpath{k}_{factor}.html')


def interactive_plot():
    """dit is de belangerijkste plot functie, die een interactieve plot maakt, ook hiervan zijn er voorbeelden op de github aanwezig"""
    ###########################parameters##################################
    #speel hier wat mee om uiteindelijk een superlist te krijgen van wat je wilt plotten
    inputpath = "C:/Users/warre/PycharmProjects/VOP/OD_data/data/Graph.graphml"
    inputpathcsv = "C:/Users/warre/PycharmProjects/VOP/OD_data/data/oneexample.csv"
    k = 5
    precisie = 2000
    factor = 10
    #load graph
    #superlist = kFastestPaths.load_fastestpaths(k, inputpathcsv, inputpath)
    #superlist, G =
    G = kFastestPaths.complete_graph(graph_DS.load_networkxgraph(inputpath))
    u, v = 269807842, 1477320374
    fastest = kFastestPaths.k_fastest_paths(G, u, v, k, factor=factor)
    print(len(fastest))
    superlist = [([u, v, 5000], fastest)]
    Gcopy = copy.deepcopy(G)
    ######################berekeningen#######################################
    #UE, SE = code_for_UEandSE.load(inputpath, inputpathcsv,k, precisie, superlist=superlist) #TODO: uncomment als dit al werd opgeslagen/je wilt dat dit wordt opgeslagen!!!! spaart je veel tijd
    UE, SE = code_for_UEandSE.linearapproxEQ(G, superlist, precisie, "UE"), code_for_UEandSE.linearapproxEQ(G, superlist, precisie, "SE")

    #flows toekennen + flows per route berekenen
    Gcopy = copy.deepcopy(G)
    code_for_UEandSE.assign_flows(UE, G)
    code_for_UEandSE.assign_flows(SE, Gcopy)
    fprue = flows_per_route(UE, superlist)
    fprse = flows_per_route(SE, superlist)
    #totale reistijden
    uett = code_for_UEandSE.get_total_travel_time(UE, G)
    sett = code_for_UEandSE.get_total_travel_time(SE, Gcopy)
    # create a Plotly figure
    fig = go.Figure()
    #knopen dubbel toevoegen vertraagt het interactieve
    already_added = []
    #opslaan van alle info op dan zeer gemakkelijk een hover tekst te kunnen toevoegen
    pbar = tqdm.tqdm(total=len(superlist))
    ODnodes = {u:False for u in G.nodes}
    edge_text = {edge:[[0, 0, 0] for i in range(k)] for edge in G.edges}
    layer1 = [] #under layer
    layer2 = [] #middle layer
    layer3 = [] #above layer
    for OD in superlist:
        ODnodes[OD[0][0]] = True
        ODnodes[OD[0][1]] = True
        total_flow = OD[0][2]
        for i, path in enumerate(OD[1]):
            flow_ue = fprue[(OD[0][0], OD[0][1])][i]
            flow_se = fprse[(OD[0][0], OD[0][1])][i]
            if flow_ue > 0 or flow_se > 0: #niet zo nuttig als er geen flows zijn toegekend
                for edge in path:
                    edge_text[edge][i][0] += 1
                    edge_text[edge][i][1] += flow_ue
                    edge_text[edge][i][2] += flow_se
        pbar.update(1)
    pbar.close()
    pbar = tqdm.tqdm(total=len(G.edges))
    coordinates = {u:None for u in G.nodes} #om niet telkens de coordinaat te moeten schatten als het niet nodig is
    #voeg knopen en takken toe
    for u, v, d in G.edges(data=True):
        if 'geometry' in d:
            coord = d['geometry']
            coordinates[u] = coord.coords[0]
            coordinates[v] = coord.coords[-1]
        else: #schatten van de coordinaten
            cu = coordinates[u] if coordinates[u] else estimate_coords(G, u)
            cv = coordinates[v] if coordinates[v] else estimate_coords(G, v)
            if not cu or not cv:
                continue #stel dat er toch nog een coordinaat niet gekend is (komt normaal niet voor)
            coord = LineString([cu, cv])
        #u als nog niet toegevoegd
        if u not in already_added:
            text = f"Node: {u}"
            coord_u = coord.coords[0]
            layer3.append(go.Scatter(x=[coord_u[0]] , y=[coord_u[1]], mode='markers', marker=dict(size=4 if ODnodes[u] else 2, color="red" if ODnodes[u] else "black"), hovertemplate=text))
            already_added.append(u)
        #v als nog niet toegevoegd
        if v not in already_added:
            text = f"Node: {v}"
            coord_v = coord.coords[-1]
            layer3.append(go.Scatter(x=[coord_v[0]] , y=[coord_v[1]], mode='markers', marker=dict(size=4 if ODnodes[v] else 2, color="red" if ODnodes[v] else "black"), hovertemplate=text))
            already_added.append(v)
        #edge
        text = f"totale toegekende flows->UE: {G[u][v]['flow']:.2f}, SE: {Gcopy[u][v]['flow']:.2f}"
        for i, element in enumerate(edge_text[(u, v)]):
            if element[0] > 0:
                text += f'<br>* deel van {i+1}{"de" if i > 0 else "ste"} snelste pad van {element[0]} OD-{"paar" if element[0] == 1 else "paren"}. (UE: {element[1]:.2f} en SE:{element[2]:.2f})'
        xs, ys = zip(*coord.coords)
        #kleur
        diff = math.floor(G[u][v]['flow'] - Gcopy[u][v]['flow'])
        if diff > 0:  # yellow
            r = 125+min(diff, 120) #boven de 100 blijven anders wordt het veel te donker
            g = 125+min(diff, 120)
            b  = 0
        elif diff < 0:  # green als SE meer eraan toekent
            r = b = 0
            g = 125+min(abs(diff), 120)
        else:
            r=g=b=185
        color = f"rgb({r}, {g}, {b})"
        if diff == 0:
            layer1.append(go.Scatter(x=xs, y=ys, mode='lines', marker=dict(size=int(d['lanes']), color=color),hovertemplate=text))
        else:
            layer2.append(go.Scatter(x=xs, y=ys, mode='lines', marker=dict(size=int(d['lanes']), color=color),hovertemplate=text))
        pbar.update(1)
    pbar.close()
    #legende maken om het te verduidelijken -> weet niet waarom dit niet werkt
    # Add a legend to explain the colors
    """fig.add_trace(go.Scatter(x=[],
                             y=[],
                             mode='markers',
                             marker=dict(size=10, color='yellow'),
                             name='UE flow > SE flow'))

    fig.add_trace(go.Scatter(x=[],
                             y=[],
                             mode='markers',
                             marker=dict(size=10, color='green'),
                             name='SE flow > UE flow'))

    fig.add_trace(go.Scatter(x=[],
                             y=[],
                             mode='markers',
                             marker=dict(size=10, color='black'),
                             name='UE flow = SE flow'))
    fig.add_trace(go.Scatter(x=[],
                             y=[],
                             mode='markers',
                             marker=dict(size=10, color='red'),
                             name='Origin/Destination'))"""
    #in juiste volgorde toevoegen
    for scatter in layer1:
        fig.add_trace(scatter)
    for scatter in layer2:
        fig.add_trace(scatter)
    for scatter in layer3:
        fig.add_trace(scatter)
    # layout instellen
    fig.update_layout(
        title=f'SE: {round(sett//3600)}u {round((sett%3600)//60)}m {round((sett%3600)%60)}s vs UE: {round(uett//3600)}u {round((uett%3600)//60)}m {round((uett%3600)%60)}s for k<sub>{factor}</sub>={k}',
        title_font_size=24,
        #legend_title_text='Legende:',
        showlegend=False,
        margin=dict(l=20, r=20, t=60, b=20),
        hovermode='closest',
        dragmode='pan',
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
    )

    # tonen + opslaan
    fig.show()
    #TODO: pas dit aan als je het op unieke locatie wilt opslaan en niet telkens wilt overschrijven!!!!!!!!!!!!!!!!
    fig.write_html('C:/Users/warre/PycharmProjects/VOP/output/visualisation/diff.html')

if __name__ == '__main__':
    plot_random_fastest_path()
    #interactive_plot()
    #fancy_graphviz_plot()
