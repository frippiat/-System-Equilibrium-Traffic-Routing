import csv
import time
import kFastestPaths
import code_for_UEandSE
import graph_DS
import random
import numpy as np
import pandas as pd
from gurobipy import GRB, Model
import networkx as nx
"""best wel veel tijd ingestoken voor niets, dus is niet zo belangerijk om te herlezen, in deze file heb ik een poging gedaan om te zien hoeveel procent er 
aan elke route wordt toegekend, maar zoals eigenlijk te verwachten was hangt dit gigantisch af van de situatie, en dus helpt het niet zo hard om startwaardes door
te geven aan gurobi."""

# functie die de formules van UE en SE lineair benadert (gekopieerd)
def getlineairapprox(G, edge, dw, precision, typeofeq):
    steps = []  # lijst waar de x waarden van de benaderde functie inkomen
    values = []  # lijst waar de y waarden van de benaderde functie inkomen
    ta0 = G[edge[0]][edge[1]]['travel_time']  # de ta0 van een edge (=reistijd in s)
    ca = G[edge[0]][edge[1]]['capacity']  # de ca van een edge
    step = 0.75 * dw / precision + (1 if precision > 100 else precision / 100) * 0.25 * dw / precision  # formule die de stapgrootte bepaald van de lineaire opdeling. fa kan max dw zijn maar zal wss nooit zo groot zijn, daarom heb ik een formule gebruikt die voor kleine precisie de linearisatie vooral conentreert op het eerste deel van de functie,maar als de precisie groot genoeg is (hier 100) dan zal de functie wel mooi in gelijke delen verdeeld worden
    if (typeofeq == "UE"):  # vult de x en y waarden aan voor UE
        for i in range(precision):
            steps.append(i * step)
            values.append(ta0 * (i * step) + (0.15 * ta0 * ((i * step) ** 5)) / ((ca ** 4) * 5))
        steps.append(dw)
        values.append(ta0 * dw + (0.15 * ta0 * (dw ** 5)) / ((ca ** 4) * 5))
    elif (typeofeq == "SE"):  # vult de x en y waarden aan voor SE
        for i in range(precision):
            steps.append(i * step)
            values.append((step * i) *ta0 * (1 + 0.15 * (((step * i) / ca) ** 4)))
        steps.append(dw)
        values.append(dw * ta0 * (1 + 0.15 * ((dw/ca)**4)))
    return [steps, values]  # return een lijst met daarin de lijst met x waarden en die met y waarden

# functie die de variabelen en constraints aanmaakt en het module minimaliseert (en dus uitrekent) (kleine aanpassing, namelijk de gok, om het duidelijker te maken aangeduid met TODO)
def linearapproxEQ(G, superlist, precision, typeofeq, startvalues=None):#, lin_manier='x'):
    """startvalues moet van de vorm fr%s|%s zijn voor de eenvoud"""
    optmod = Model(name=f"lineair approx {typeofeq}")  # aanmaken van een gurobi module
    #optmod.setParam('NodefileStart', 0) # vanaf gurobi meer dan 0 MB (0GB) aan RAM gebruikt zal het zoveel mogelijk proberen om dingen "uit te swappen" naar een eigen file op de disk, de 'NodeFile' -> dus hoe lager hoe sneller gurobi zal proberen zoveel mogelijk op de disk te zetten, maar dus logischerwijze ook hoe trager
    #optmod.setParam('NumericFocus', 3) #om snelheid niet belangerijk te maken, 0= full snelheid -> 3=full numeric accuracy, helpt lijk wel nie echt..
    function = 0  # initialiseren van de functie die we gaan gebruiken
    myvars = vars()  # vars() is een woordenboek met alle variabelen in, wordt later gebruikt
    #ging ervan uit dat het beter was om de graaf te filteren zodat we met minder variabelen zitten, dus beschouw nieuwe graaf met enkel takken uit de paden
    Gf = nx.DiGraph()
    for OD in superlist:
        for path in OD[1]:
            for node_pair in path:
                Gf.add_node(node_pair[0])
                Gf.add_node(node_pair[1])
                edge_attrs = G.get_edge_data(*node_pair)
                Gf.add_edge(*node_pair, **edge_attrs)
    max_dw = {edge:0 for edge in Gf.edges()}
    totaldw = 0
    for OD in superlist:
        for route in OD[1]:
            for edge in route:
                max_dw[edge] += OD[0][2]
        totaldw += OD[0][2]
    for edge in Gf.edges():
        a = "f%s|%s" % (edge[0], edge[1])  # de naam van de variabele voor de flow op de tak bv.:f12
        ya = "yf%s|%s" % (edge[0], edge[1])  # de naam van de variabele voor de y waarden van de lineaire approximatie voor de flow op de tak bv.:yf12. deze variabele heb je nodig om later de lineare functie van deze f bij de algehele functie op te tellen
        #cya = "cyf%s|%s" % (edge[0], edge[1])
        myvars[a] = optmod.addVar(name=a, vtype=GRB.CONTINUOUS, lb=0, ub=max_dw[edge])  # het toevoegen van de variabele (bv f12 aan het gurobi model), pas de weight van de tak al aan bij bijvoorbeeld zeker wilt zijn dat er een minimale flow van weight wordt toegekend
        optmod.addConstr(myvars[a] >= 0)
        myvars[ya] = optmod.addVar(name=ya, vtype=GRB.CONTINUOUS, lb=0)  # het toevoegen van de variabele (bv yf12 aan het gurobi model)
        optmod.addConstr(myvars[ya] >= 0)
        constr = "c%s|%s" % (edge[0], edge[1])  # het aanmaken van een constraint voor f12 dit is het constraint die zegt dat f12 de som is van alle fr die door de tak 1-2 stromen (zie constraints op curusblad dat warre had doorgestuurd)
        myvars[constr] = 0  # het toevoegen van deze constraint aan de vairabelen
        linaprox = getlineairapprox(G, edge, totaldw, precision, typeofeq)  # het oproepen van de functie die de lineare approximatie teruggeeft
        optmod.addGenConstrPWL(myvars[a], myvars[ya], linaprox[0], linaprox[1])  # toevoegen van het constraint dat f12 aan zijn lineaire functie yf12 koppelt (voor meer info zie https://www.gurobi.com/documentation/current/refman/py_model_agc_pwl.html)
        function += myvars[ya]  # het toevoegen van de lineaire approx functie aan de algehele functie zodat we uiteindelijk de som bekomen bij het beeindigen van de for loop)
    optmod.setObjective(function, sense=GRB.MINIMIZE)  # functie toevoegen aan het gurobi model
    for e, listoflists in enumerate(superlist):
        constr_fr = 0  # initialiseren van het constraint dat zegt dat de som van alle fr gelijk is aan dw, dit is per OD paar te beschouwen (aanpassing met code voordien)
        for i, list in enumerate(listoflists[1]):  # elke route bekijken
            fr = "fr%s|%s|%s" % (listoflists[0][0], listoflists[0][1], i)  # aanmaken van de variabele die de flow op die route beschrijft
            myvars[fr] = optmod.addVar(name=fr, vtype=GRB.CONTINUOUS, lb=0, ub=listoflists[0][2])  # toevoegen van de variabele die de flow op die route beschrijft aan de variabelen en tegelijk ook aan het gurobi model
            if startvalues: #TODO
                myvars[fr].Start = startvalues[i]*listoflists[0][2]  # meegeven van initiele toekenning flows
            optmod.addConstr(myvars[fr] >= 0)
            constr_fr += myvars[fr]  # toevoegen van fr aan het voorheen vermelde constraint
            for edge in list:  # elke edge op de route bekijken
                currentconstr = "c%s|%s" % (edge[0], edge[1])  # currentconstr gelijk stellen aan het constraint op f van de tak dat hierboven geinitialiseerd werd
                myvars[currentconstr] += myvars[fr]  # toevoegen van fr aan het constraint van f van de tak
        #cfr = "cfrdw%s|%s" % (listoflists[0][0], listoflists[0][1])  # naam voor constraint die aan het model wordt toegevoegd
        optmod.addConstr(constr_fr == listoflists[0][2])  # het constraint dat alle fr samen dw moeten zijn toevoegen aan het model (stond ook verkeerd uitgelijnd )
    for edge in Gf.edges():  # elke tak bekijken om de constraint dat alle fr van routes die edge gebruiken moet gelijk zijn aan flow op die tak
        a = "f%s|%s" % (edge[0], edge[1])
        currentconstr = "c%s|%s" % (edge[0], edge[1])  # de som van alle fr die door f van de tak gaan (zie ook hierboven telkens bv c12 genaamd (bekijk dus de lines met c%s%s))
        #constroff = "cstr%s|%s" % (edge[0], edge[1])  # een variabele aanmaken voor de constraint die aan het model wordt toegevoegd
        optmod.addConstr(myvars[a] == myvars[currentconstr])  # het constraint aan het model toevoegen
    optmod.optimize()  # model uitreknen
    l = []
    l.append(optmod.ObjVal)  # de uitgerekende waarde aan de lijst toevoegen (dus UE of SE)
    for v in optmod.getVars():
        l.append((v.varName, v.x))  # alle variabelen in het model toevoegen aan de lijst
    optmod.dispose() #close the model
    return l  # de lijst teruggeven

def generate_random_superlist(G, total_flow, k, OD_pairs="low", factor=10):
    """functie die random OD-paren genereert gegeven de flow en gewenste hoeveelheid od paren (hoog/laag)"""
    #total_flow is een indicatie van de gewenste flow, ik doe dit niet exact omdat dit toch niet echt uitmaakt, anders moet je gwn nog een minimum functie toevoegen
    assert OD_pairs in ["low", "high"], "keyword OD_pairs must have a value of low or high"
    assigned_flow = 0
    ans = []
    nodes = list(G.nodes())
    probs = np.array([1 / i for i in range(1, 101)])
    probs /= probs.sum()  # normalize probabilities so they sum up to 1
    while (assigned_flow < total_flow):
        OD = random.sample(nodes, 2)
        kfastest = kFastestPaths.k_fastest_paths(G, OD[0], OD[1], k, factor=factor)
        if kfastest:  # als het niet None is (dus als u != v en er een pad is tussen u en v)
            min_capacity = 10000 #zeker geen 10 rijvakken
            fastest_path = kfastest[0]
            for edge in fastest_path: #capaciteit van snelste pad is belangerijkst aangezien vooral dit bepaald in welke mate de flow wordt "opgesplitst"
                if G[edge[0]][edge[1]]['capacity'] < min_capacity:
                    min_capacity = G[edge[0]][edge[1]]['capacity']
            flow = np.random.choice(range(1, 101), p=probs) if OD_pairs == "high" else random.randint(min_capacity/2, min_capacity*2)
            assigned_flow += flow
            ans.append(([OD[0], OD[1], flow], kfastest))
    return ans

def write(k):
    """functie die gebruik van routes per od paar wegschrijft naar csv bestand om later dan er terug uit te halen"""
    G = kFastestPaths.complete_graph(graph_DS.load_networkxgraph("C:/Users/warre/PycharmProjects/VOP/OD_data/data/Graph.graphml"))
    for i in range(20):
        # laag:
        superlist = generate_random_superlist(G, random.randint(10000, 40000), k)
        UE, SE = code_for_UEandSE.linearapproxEQ(G, superlist, 2000, 'UE'), code_for_UEandSE.linearapproxEQ(G, superlist, 2000, 'SE')
        # makkelijk totale flow bijhouden + nummer van OD paar
        ODflows = {}  # makkelijk aan de flows van de OD paren geraken
        OD_nr = {}
        for i, OD in enumerate(superlist):
            ODflows[(OD[0][0], OD[0][1])] = OD[0][2]
            OD_nr[(OD[0][0], OD[0][1])] = i

        # bijhouden van alle resultaten
        total_ODs = len(superlist)
        UE_low = np.zeros((total_ODs, k))
        SE_low = np.zeros((total_ODs, k))

        for i in range(1, len(UE)):
            if UE[i][0][:2] == "fr":
                index1 = UE[i][0].find("|")
                index2 = UE[i][0].find("|", index1 + 1)
                OD0 = int(UE[i][0][2:index1])
                OD1 = int(UE[i][0][index1 + 1:index2])
                route = int(UE[i][0][index2 + 1:])
                UE_low[OD_nr[(OD0, OD1)]][route] = float(UE[i][1]) / ODflows[(OD0, OD1)]

        for i in range(1, len(SE)):
            if SE[i][0][:2] == "fr":
                index1 = SE[i][0].find("|")
                index2 = SE[i][0].find("|", index1 + 1)
                OD0 = int(UE[i][0][2:index1])
                OD1 = int(UE[i][0][index1 + 1:index2])
                route = int(UE[i][0][index2 + 1:])
                SE_low[OD_nr[(OD0, OD1)]][route] = float(SE[i][1]) / ODflows[(OD0, OD1)]

        with open('C:/Users/warre/PycharmProjects/VOP/output/guesseslow.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["new", code_for_UEandSE.get_total_travel_time(UE, G)])
            for element in UE_low:
                writer.writerow(list(element))
            writer.writerow(["SE", code_for_UEandSE.get_total_travel_time(SE, G)])
            for element in SE_low:
                writer.writerow(list(element))

        # high
        superlist = generate_random_superlist(G, random.randint(20000, 50000), k, "high")
        UE, SE = code_for_UEandSE.linearapproxEQ(G, superlist, 2000, 'UE'), code_for_UEandSE.linearapproxEQ(G, superlist, 2000, 'SE')
        # makkelijk totale flow bijhouden + nummer van OD paar
        ODflows = {}  # makkelijk aan de flows van de OD paren geraken
        OD_nr = {}
        for i, OD in enumerate(superlist):
            ODflows[(OD[0][0], OD[0][1])] = OD[0][2]
            OD_nr[(OD[0][0], OD[0][1])] = i

        # bijhouden van alle resultaten
        total_ODs = len(superlist)
        UE_high = np.zeros((total_ODs, k))
        SE_high = np.zeros((total_ODs, k))

        for i in range(1, len(UE)):
            if UE[i][0][:2] == "fr":
                index1 = UE[i][0].find("|")
                index2 = UE[i][0].find("|", index1 + 1)
                OD0 = int(UE[i][0][2:index1])
                OD1 = int(UE[i][0][index1 + 1:index2])
                route = int(UE[i][0][index2 + 1:])
                UE_high[OD_nr[(OD0, OD1)]][route] = float(UE[i][1]) / ODflows[(OD0, OD1)]

        for i in range(1, len(SE)):
            if SE[i][0][:2] == "fr":
                index1 = SE[i][0].find("|")
                index2 = SE[i][0].find("|", index1 + 1)
                OD0 = int(UE[i][0][2:index1])
                OD1 = int(UE[i][0][index1 + 1:index2])
                route = int(UE[i][0][index2 + 1:])
                SE_high[OD_nr[(OD0, OD1)]][route] = float(SE[i][1]) / ODflows[(OD0, OD1)]

        with open('C:/Users/warre/PycharmProjects/VOP/output/guesseshigh.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["new", code_for_UEandSE.get_total_travel_time(SE, G)])
            for element in UE_high:
                writer.writerow(list(element))
            writer.writerow(["SE", code_for_UEandSE.get_total_travel_time(SE, G)])
            for element in SE_high:
                writer.writerow(list(element))

def test(k):
    """test of het effectief sneller is via het egemiddelde van alle in write geschreven waarden"""
    with open('C:/Users/warre/PycharmProjects/VOP/output/guesseshigh.csv', 'r', newline='') as file:
        with open('C:/Users/warre/PycharmProjects/VOP/output/guesseslow.csv', 'r', newline='') as file2:
            readerhigh = csv.reader(file)
            readerlow = csv.reader(file2)
            average_procent_UE_low = [[] for i in  range(k)]
            average_procent_SE_low = [[] for i in  range(k)]
            average_procent_SE_high = [[] for i in  range(k)]
            average_procent_UE_high = [[] for i in  range(k)]
            #samen want uiteindelijk is het niet te voorspellen..
            average_procent_SE = [[] for i in  range(k)]
            average_procent_UE = [[] for i in  range(k)]
            SE = False
            for row in readerlow:
                if row[0] == "new" or row[0] == "n":
                    SE = False
                elif row[0] == "SE" or row[0] == "S":
                    SE = True
                else:
                    for i, element in enumerate(row):
                        if SE:
                            average_procent_SE_low[i].append(float(element))
                            average_procent_SE[i].append(float(element))
                        else:
                            average_procent_UE_low[i].append(float(element))
                            average_procent_UE[i].append(float(element))
            for row in readerhigh:
                if row[0] == "new" or row[0] == "n":
                    SE = False
                elif row[0] == "SE" or row[0] == "S":
                    SE = True
                else:
                    for i, element in enumerate(row):
                        if SE:
                            average_procent_SE_high[i].append(float(element))
                            average_procent_SE[i].append(float(element))
                        else:
                            average_procent_UE_high[i].append(float(element))
                            average_procent_UE[i].append(float(element))
            """
            print("UE low:")
            # Calculate mean and standard deviation for each inner array
            mean_values = [pd.Series(data).mean() for data in average_procent_UE_low]
            std_values = [pd.Series(data).std() for data in average_procent_UE_low]
            # Create a DataFrame with the desired columns
            df = pd.DataFrame({'i': range(len(average_procent_UE_low)),
                               'mean_procent': mean_values,
                               'standard_deviation': std_values})

            # Print the table
            print(df)
            print("SE low:")
            # Calculate mean and standard deviation for each inner array
            mean_values = [pd.Series(data).mean() for data in average_procent_SE_low]
            std_values = [pd.Series(data).std() for data in average_procent_SE_low]
            # Create a DataFrame with the desired columns
            df = pd.DataFrame({'i': range(len(average_procent_SE_low)),
                               'mean_procent': mean_values,
                               'standard_deviation': std_values})

            # Print the table
            print(df)
            print("UE high:")
            # Calculate mean and standard deviation for each inner array
            mean_values = [pd.Series(data).mean() for data in average_procent_UE_high]
            std_values = [pd.Series(data).std() for data in average_procent_UE_high]
            # Create a DataFrame with the desired columns
            df = pd.DataFrame({'i': range(len(average_procent_UE_high)),
                               'mean_procent': mean_values,
                               'standard_deviation': std_values})

            # Print the table
            print(df)
            print("SE high:")
            # Calculate mean and standard deviation for each inner array
            mean_values = [pd.Series(data).mean() for data in average_procent_SE_high]
            std_values = [pd.Series(data).std() for data in average_procent_SE_high]
            # Create a DataFrame with the desired columns
            df = pd.DataFrame({'i': range(len(average_procent_SE_high)),
                               'mean_procent': mean_values,
                               'standard_deviation': std_values})

            # Print the table
            print(df)"""

            print("SE:")
            # Calculate mean and standard deviation for each inner array
            mean_valuesse = [pd.Series(data).mean() for data in average_procent_SE]
            std_valuesse = [pd.Series(data).std() for data in average_procent_SE]
            # Create a DataFrame with the desired columns
            df = pd.DataFrame({'i': range(len(average_procent_SE)),
                               'mean_procent': mean_valuesse,
                               'standard_deviation': std_valuesse})

            # Print the table
            print(df)
            print("UE:")
            # Calculate mean and standard deviation for each inner array
            mean_valuesue = [pd.Series(data).mean() for data in average_procent_UE]
            std_valuesue = [pd.Series(data).std() for data in average_procent_UE]
            # Create a DataFrame with the desired columns
            df = pd.DataFrame({'i': range(len(average_procent_UE)),
                               'mean_procent': mean_valuesue,
                               'standard_deviation': std_valuesue})

            # Print the table
            print(df)
            G = kFastestPaths.complete_graph(graph_DS.load_networkxgraph("C:/Users/warre/PycharmProjects/VOP/OD_data/data/Graph.graphml"))
            #best wel nog met volledig andere flows
            superlist = kFastestPaths.load_fastestpaths(9, "C:/Users/warre/PycharmProjects/VOP/OD_data/data/OD_Flows_1%.csv", "C:/Users/warre/PycharmProjects/VOP/OD_data/data/Graph.graphml")
            start = time.time()
            UE = linearapproxEQ(G,superlist, 2000, "UE", startvalues=mean_valuesue)
            end = time.time()
            print(f"UE new time: {end-start}")
            start = time.time()
            UE = linearapproxEQ(G,superlist, 2000, "UE")
            end = time.time()
            print(f"UE normal time: {end-start}")
            start = time.time()
            UE = linearapproxEQ(G,superlist, 2000, "SE")
            end = time.time()
            print(f"SE normal time: {end-start}")
            start = time.time()
            UE = linearapproxEQ(G,superlist, 2000, "SE", startvalues=mean_valuesse)
            end = time.time()
            print(f"SE new time: {end-start}")

            #is het nu zo dat het ook beter werkt bij lagere factoren, gewoon door dat we doorgeven dat de snelste routes meest dienen te worden gebruikt
            superlist, G = kFastestPaths.input_data("C:/Users/warre/PycharmProjects/VOP/OD_data/data/OD_Flows_1%.csv", "C:/Users/warre/PycharmProjects/VOP/OD_data/data/Graph.graphml", 9, 2)
            start = time.time()
            UE = linearapproxEQ(G, superlist, 2000, "UE", startvalues=mean_valuesue)
            end = time.time()
            print(f"UE new time: {end - start}")
            start = time.time()
            UE = linearapproxEQ(G, superlist, 2000, "UE")
            end = time.time()
            print(f"UE normal time: {end - start}")
            start = time.time()
            UE = linearapproxEQ(G, superlist, 2000, "SE")
            end = time.time()
            print(f"SE normal time: {end - start}")
            start = time.time()
            UE = linearapproxEQ(G, superlist, 2000, "SE", startvalues=mean_valuesse)
            end = time.time()
            print(f"SE new time: {end - start}")
def ue_route_guesses():
    """laatmaar, werkt niet"""
    return [0.93506, 0.04908, 0.00668, 0.00161, 0.00161, 0.0009, 0.00124, 0.00083, 0.00111, 0.00089, 0.00076, 0.00057, 0.0012, 0.00087, 0.00088]

def se_route_guesses():
    """laatmaar, werkt niet"""
    return [0.83676, 0.11299, 0.03033, 0.00703, 0.00419, 0.00173, 0.00199, 0.00112, 0.00139, 0.00141, 0.001, 0.00079, 0.00147, 0.00111, 0.00119]

if __name__=='__main__':
    #write(15)
    #test(15)
    pass
    #niet echt verschil