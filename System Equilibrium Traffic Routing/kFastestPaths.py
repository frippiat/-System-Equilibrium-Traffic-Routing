import code_for_UEandSE
import visual_graph
import random
import osmnx as ox
import networkx as nx
import graph_DS
import csv
import copy
import os
import tqdm

# tijdverspilling, want gebruik uiteindelijk ingebouwde functie van networkx (was op zich wel te verwachten dat die er ging zijn)
def fastest_path(G, u, v):
    # begin en eindknoop dezelfde
    if (u == v):
        return None

    # geen pad tussen begin en eindknoop
    if (nx.has_path(G, u, v) == False):
        raise Exception("No path between u en v in this graph")

    # begin en eindknoop verschillend en er is een pad dus zeker ook een kortste pad
    distances = {node: float('inf') for node in G.nodes}
    paths = {node: None for node in G.nodes}
    distances[u] = 0
    visited_nodes = set()
    next_nodes = [(u, neighbor) for neighbor in list(G[u].keys())]
    while (next_nodes):
        previous, current = next_nodes.pop()
        if distances[previous] + G[previous][current]['travel_time'] > distances[current]:
            continue

        distances[current] = distances[previous] + G[previous][current]['travel_time']
        paths[current] = previous
        # checken of er eventueel snellere paden via deze naar de buren zijn
        for neighbor in G[current].keys():
            if distances[neighbor] > distances[current] + G[previous][current]['travel_time']:
                next_nodes.append((current, neighbor))

    # pad reconstrueren
    shortest_path = []
    current = v
    while (paths[current] != None):
        shortest_path.append((paths[current], current))
        current = paths[current]
    shortest_path = shortest_path.reverse()
    return shortest_path


def k_fastest_paths(G, u, v, k, factor, filter=None):
    """functie die de k zo verschillend mogelijke kortste paden van u naar v teruggeeft,
    de factor is de factor waarmee de reistijd van de takken wordt verhoogt elke keer het gebruikt wordt,
    de filter kan worden ingesteld als een maximaal percentage dat de routes mogen verschillen van de snelste (bv. 10 voor 10%)"""
    # begin en eindknoop gelijk
    if (u == v):
        return None
    # geen pad tussen begin en eindknoop
    if (nx.has_path(G, u, v) == False):
        # raise Exception("No path between u en v in this graph")
        return None
    # vindt de k "snelste maar verschillende" paden
    P = []
    # "nul"reistijd snelste route
    fastest = nx.shortest_path_length(G, source=u, target=v, weight='travel_time')
    for i in range(k):
        #als er filter aanwezig is moet er gechecket worden of de ta0 van deze route al niet te hoog ligt, anders kunnen we returnen aangezien volgende paden ook hoger zullen liggen
        if filter:
            tt = nx.shortest_path_length(G, source=u, target=v, weight='travel_time')
            if ((tt-fastest)/fastest) > (filter/100):
                for path in P:
                    for edge in path:
                        G[edge[0]][edge[1]]['travel_time'] = 3.6 * G[edge[0]][edge[1]]['length'] / G[edge[0]][edge[1]]['speed_kph']
                return P
        # snelste pad toevoegen
        path = nx.shortest_path(G, source=u, target=v, weight='travel_time')
        # herorganiseren voor juist te kunnen doorgeven aan functie Ward
        path_reorganised = []
        # aanpassen van de graaf om de takken minder waarschijnlijk te maken
        for i in range(len(path) - 1):
            path_reorganised.append((path[i], path[i + 1]))
            G[path[i]][path[i + 1]]['travel_time'] *= factor
        P.append(path_reorganised)
    #terug travel time terugbrengen
    for path in P:
        for edge in path:
            G[edge[0]][edge[1]]['travel_time'] = 3.6*G[edge[0]][edge[1]]['length']/G[edge[0]][edge[1]]['speed_kph']
    return P


# functie om alle nodige ontbrekende waarden van de data te benaderen (behalve de coordinaten, heb dat bij visualisatie gestoken aangezien dat enkel daar nodig is)
def complete_graph(G, flows=None):
    """functie die de attributen van de graaf zo goed mogelijk aanvult"""
    G = ox.add_edge_speeds(G)  ##https: // osmnx.readthedocs.io / en / stable / osmnx.html  # osmnx.speed.add_edge_speeds, voegt speed toe via gemiddelde van alle maxspeeds van elk highway type
    for u, v, d in G.edges(data=True):
        if 'maxspeed' not in d:
            d['maxspeed'] = d['speed_kph']
        elif str(d['maxspeed']).isdigit():
            d['speed_kph'] = float(d['maxspeed'])  # juist instellen
        # ga enkel speed_kph aanpassen, en in maxspeed de origele waarden laten staan, eventueel gaan we deze nog nodig hebben
        elif type(d['maxspeed']) == list:  # maximum van de verschillende waardne nemen, want gaat dan over mindere maxsnelheid bij speciale gevallen
            d['speed_kph'] = [item for item in d['maxspeed'] if str(item).isdigit()]  # filteren van elementen die niet kunnen worden omgezet naar een getal
            d['speed_kph'] = max(list(map(float, d['speed_kph'])))  # pakken het maximum van alle verschillende waarden die nog overschieten
        if 'lanes' not in d:
            d['lanes'] = 1
        if type(d['lanes']) == list:  # meerdere aantallen rijvakken gedefinieerd?
            d['lanes'] = str(min(list(map(int, d['lanes'])))) #extra rijvakken is gewoon omdat er onderbaan een oprit is of even een verbreding bij voorsorteren, echter dient dit niet in rekening te worden gebracht
        if (d['lanes'] == '0'):  # weet niet hoe er 0 in kan komen ma bon
            d['lanes'] = '1'
        if 'oneway' in d and not d['oneway'] and int(d['lanes']) > 1:
            d['lanes'] = str(int(d['lanes'])//2) #als het een two way weg is dan is het aantal rijvakken gelijk aan het aantal rijvakken van beide richtingen, en voor beide richtingen is er zo een tak, als het aantal rijvakken dan oneven is dan is het  omdat er een tussenstrook is of even een busstrook ofzo, is het 1 dan is dit een kleine weg
        d['capacity'] = 1000 * float(d['lanes'])  # capaciteit toevoegen, soms een aantal lanes van 1.5 enz, i guess dat dit het gemiddelde is (eerst 2 dan 1 bv.), dus kunnen we dat nog altijd gebruiken i guess
        if flows == "random":
            d['flow'] = random.randint(0, d['capacity'])  # random flows toekennen
        else:
            d['flow'] = 0 #flow 0 toekennen, zodanig dat je bij code UE en SE een lower bound vna d['weight'] krijgt (handig voor stabiliteit bv)
        if 'length' not in d:
            print('oei') #geen oei's dus komt niet voor normaal -> als je hier toch problemen mee hebt kan je eens bij visualisatie kijken om coordinaten te bepalen en zo de lengte te berekenen
            d['length'] = '1'
        d['travel_time'] = 3.6 * d['length'] / d['speed_kph'] #travel time in s

    #enkel nodige attributen overhouden + omzetten naar digraph
    GDi = G.to_directed()
    #de verschillende attributen: ['osmid', 'name', 'highway', 'maxspeed', 'oneway', 'length', 'geometry', 'lanes', 'ref', 'access', 'bridge', 'junction', 'width', 'area', 'tunnel']
    attributes_to_keep = ['osmid', 'flow', 'length', 'lanes', 'speed_kph', 'capacity', 'travel_time', 'crs', 'geometry']
    GDi = nx.DiGraph(((u, v, {k: d[k] for k in attributes_to_keep if k in d}) for u, v, d in GDi.edges(data=True)))
    return GDi


def OD_Data(input_path):
    """haalt OD_data uit het csv bestand opgeslagen op input_path"""
    ans = []
    with open(input_path, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        reader.__next__()  # skip first line
        for row in reader:
            ans.append(list(map(int, row))) #todo: moet ik hier geen float van maken voor de OD (is teovallig overal geheel in de documenten peisk)
    return ans

def save_fastestpaths(k, input_path_csv, input_path_graph):
    """om de snelste paden op te slaan in csv bestand via od-csv bestand en de k waarde (eventueel factor toevoegen!)"""
    index = input_path_csv.rfind('/')
    id = input_path_csv[index+1:]
    with open(f"C:/Users/warre/PycharmProjects/VOP/output/fastest paths/{id}/{k}.csv", 'a', newline='') as file:
        writer = csv.writer(file)
        listoflists, G = input_data(input_path_csv, input_path_graph, k)
        for OD in listoflists:
            writer.writerow([OD[0][0], OD[0][1], OD[0][2]])
            for path in OD[1]:
                writer.writerow(["new"])
                for edge in path:
                    writer.writerow([edge[0], edge[1]])


def load_fastestpaths(k, input_path_csv, input_path_graph):
    """deze functie slaat de snelste paden op indien de file nog niet bestaat, anders laadt het het snel in en returned het de superlist"""
    index = input_path_csv.rfind('/')
    id = input_path_csv[index+1:]
    if not(os.path.exists(f'C:/Users/warre/PycharmProjects/VOP/output/fastest paths/{id}/{k}.csv')): #opnieuw sorry da ik alles zo lokaal doe, maakt het een stuk makkelijker, maar is snel aan te passen ook
        #als het nog niet bestaat opslaan van de uitkomst met bepaalde k waarde en precisie waarde
        save_fastestpaths(k, input_path_csv, input_path_graph)
    with open(f"C:/Users/warre/PycharmProjects/VOP/output/fastest paths/{id}/{k}.csv", 'r', newline='') as file:
        reader = csv.reader(file)
        ans = []
        curr = None
        curr_path = None
        for row in reader:
            if len(row) == 3: #header
                if curr_path :
                    curr[1].append(curr_path)
                if curr:
                    ans.append(tuple(curr))
                curr = []
                curr_path = None
                curr.append([int(row[0]), int(row[1]), float(row[2])])
                curr.append([])
            elif row[0] == "new": #nieuw path
                if curr_path:
                    curr[1].append(curr_path)
                curr_path = []
            else:
                curr_path.append((int(row[0]), int(row[1])))
        curr[1].append(curr_path)
        ans.append(tuple(curr))
    return ans

def input_data(input_path_csv, input_path_graph, k, factor=10, filter=None):
    """geeft de input data weer in de volgende vorm [([u,v,dw], [k_fastest_paths]),([u2,v2,dw2], [k_fastest_paths2]),...,([un,vn,dwn], [k_fastest_pathsn])], G"""
    ans = []
    OD_data = OD_Data(input_path_csv)  # OD data ophalen
    G = graph_DS.load_networkxgraph(input_path_graph) #graaf ophalen
    G = complete_graph(G) #data aanvullen
    cbar = tqdm.tqdm(total=len(OD_data))
    #voor elk OD paar de k snelste paden berekenen
    for OD in OD_data:
        kfastest = k_fastest_paths(G, OD[0], OD[1], k, factor=factor, filter=filter)
        if kfastest:  # als het niet None is (dus als u != v)
            ans.append((OD, kfastest))
        cbar.update(1)
    cbar.close()
    return ans, G

if __name__ == "__main__":
    """tests omdat er even problemen waren met de snelste paden, mag genegeerd worden"""
    for i in range(1, 13):
        print('----------------------new-----------------------------')
        G = complete_graph(graph_DS.load_networkxgraph("C:/Users/warre/PycharmProjects/VOP/OD_data/data/Graph.graphml"))
        superlist = load_fastestpaths(i, "C:/Users/warre/PycharmProjects/VOP/OD_data/data/OD_Flows_1%.csv", "C:/Users/warre/PycharmProjects/VOP/OD_data/data/Graph.graphml")
        UE, SE = code_for_UEandSE.load("C:/Users/warre/PycharmProjects/VOP/OD_data/data/Graph.graphml", "C:/Users/warre/PycharmProjects/VOP/OD_data/data/OD_Flows_1%.csv", i, 2000, superlist=superlist)
        uett = code_for_UEandSE.get_total_travel_time(UE, G)
        sett = code_for_UEandSE.get_total_travel_time(SE, G)
        if uett < sett:
            print('UE < SE ')
            continue
        totalflow = 0
        for OD in superlist:
            totalflow += OD[0][2]
            for path in OD[1]:
                if path[0][0] != OD[0][0]:
                    print('probleem met snelste paden')
                if path[-1][1] != OD[0][1]:
                    print('probleem met snelste paden')
                for i in range(0, len(path)-1):
                    if path[i][1] != path[i+1][0]:
                        print('probleem met snelste paden')

        print(f"totalflow={totalflow}")

        if len(UE) != len(SE):
            print('lengtes niet gelijk')
        uetotalflow = 0
        setotalflow = 0
        for i in range(1, len(UE)):
            if UE[i][0][0] == "f" and UE[i][0][1] != "r":
                uetotalflow += float(UE[i][1])
                if float(UE[i][1]) < 0:
                    print(float(SE[i][1]))
        for i in range(1, len(SE)):
            if SE[i][0][0] == "f" and SE[i][0][1] != "r":
                if float(SE[i][1]) < 0:
                    print(float(SE[i][1]))
                setotalflow += float(SE[i][1])

        print(uetotalflow)
        print(setotalflow)  # corrected indentation

    """ okej = True
        for i in range(len(superlist)):
            firstk = superlist[i][1]
            for j in range(len(superlist2)):
                if superlist[i][0] == superlist2[j][0]:
                    secondk = superlist2[j][1]
                    count = 0
                    for path in secondk:
                        inofnie = False
                        for path2 in firstk:
                            if path == path2:
                                inofnie = True
                                break
                        if not(inofnie):
                            count += 1
                    if count > 1:
                        print(count)
                        okej = False
                    break
        superlist = superlist2
        print(okej)"""
    """
    G = complete_graph(graph_DS.load_networkxgraph("C:/Users/warre/PycharmProjects/VOP/OD_data/data/Graph.graphml"))
    k = 2
    listoflists = [([10017948126,250415698,74], k_fastest_paths(G,10017948126, 250415698, 19, factor=10))]
    print('---------------fastest paths---------------')
    print(listoflists)
    print('----------------saving---------------------')
    with open(f"C:/Users/warre/PycharmProjects/VOP/output/fastest paths/test.csv", 'w', newline='') as file:
        writer = csv.writer(file)
        for OD in listoflists:
            print([OD[0][0], OD[0][1], OD[0][2]])
            writer.writerow([OD[0][0], OD[0][1], OD[0][2]])
            for path in OD[1]:
                writer.writerow(["new"])
                for edge in path:
                    writer.writerow([edge[0], edge[1]])
    print('----------------loading---------------------')
    with open(f"C:/Users/warre/PycharmProjects/VOP/output/fastest paths/test.csv", 'r', newline='') as file:
        reader = csv.reader(file)
        ans = []
        curr = None
        curr_path = None
        for row in reader:
            if len(row) == 3: #header
                if curr_path:
                    curr[1].append(curr_path)
                if curr:
                    ans.append(tuple(curr))
                curr = []
                curr_path = None
                curr.append([int(row[0]), int(row[1]), float(row[2])])
                curr.append([])
            elif row[0] == "new": #nieuw path
                if curr_path:
                    curr[1].append(curr_path)
                curr_path = []
            else:
                curr_path.append((int(row[0]), int(row[1])))
        curr[1].append(curr_path)
        ans.append(tuple(curr))
    print('---------------fastest paths---------------')
    print(ans)
    print(ans==listoflists)"""
