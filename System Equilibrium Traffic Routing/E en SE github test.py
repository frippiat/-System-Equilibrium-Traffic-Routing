import kFastestPaths
from gurobipy import GRB, Model
import graph_DS
import networkx as nx
import matplotlib.pyplot as pltw
import time
import csv
import os
import math


def get_total_travel_time(Eq, G):
    """geeft je de totale reistijd terug gebruik deze zeker bij beide, want anders krijg je bij inaccuraat aantal linearisatie intervallen een veel te hoge waarde voor de totale reistijd in het SE!! """
    total = 0
    for i in range(1, len(Eq)): #alle variabelen overlopen
        if (Eq[i][0][0] == "f" and Eq[i][0][1] != "r"): #als het een flow op een tak is, dit is van de vorm (f%s|%s)
            splits = Eq[i][0].find("|")
            first_edge = int(Eq[i][0][1:splits])
            second_edge = int(Eq[i][0][splits+1:])
            ta0 = 3.6*G[first_edge][second_edge]['length']/G[first_edge][second_edge]['speed_kph']  # de ta0 van een edge (=reistijd in s)
            ca = G[first_edge][second_edge]['capacity']
            total += Eq[i][1]*ta0 * (1 + 0.15 * ((Eq[i][1] / ca) ** 4))

    return total


# In[4]:


def getlineairapprox(G, edge, dw, precision, typeofeq):
    steps = []  # lijst waar de x waarden van de benaderde functie inkomen
    values = []  # lijst waar de y waarden van de benaderde functie inkomen
    ta0 = 3.6*G[edge[0]][edge[1]]['length']/G[edge[0]][edge[1]]['speed_kph']  # de ta0 van een edge (=reistijd in s)
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


# In[5]:


def linearapproxEQ(G, superlist, precision, typeofeq,procent):#, lin_manier='x'):
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
                max_dw[edge] += procent*OD[0][2]
        totaldw += procent*OD[0][2]
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
            myvars[fr] = optmod.addVar(name=fr, vtype=GRB.CONTINUOUS, lb=0, ub=procent*listoflists[0][2])  # toevoegen van de variabele die de flow op die route beschrijft aan de variabelen en tegelijk ook aan het gurobi model
            optmod.addConstr(myvars[fr] >= 0)
            constr_fr += myvars[fr]  # toevoegen van fr aan het voorheen vermelde constraint
            for edge in list:  # elke edge op de route bekijken
                currentconstr = "c%s|%s" % (edge[0], edge[1])  # currentconstr gelijk stellen aan het constraint op f van de tak dat hierboven geinitialiseerd werd
                myvars[currentconstr] += myvars[fr]  # toevoegen van fr aan het constraint van f van de tak
        #cfr = "cfrdw%s|%s" % (listoflists[0][0], listoflists[0][1])  # naam voor constraint die aan het model wordt toegevoegd
        optmod.addConstr(constr_fr == procent*listoflists[0][2])  # het constraint dat alle fr samen dw moeten zijn toevoegen aan het model (stond ook verkeerd uitgelijnd )
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


# In[6]:


def assign_flows(Eq, G):
    """functie die de flows berekend door een bepaald equilibrium toekent aan de graaf G"""
    for i in range(1, len(Eq)):
        if Eq[i][0][0] == "f" and Eq[i][0][1] != "r":
            index = Eq[i][0].find("|")
            u = int(Eq[i][0][1:index])
            v = int(Eq[i][0][index+1:])
            G[u][v]['flow'] = Eq[i][1]
# In[7]:


G=nx.DiGraph()
G.add_nodes_from([1,2,3,4,5,6,7])
G.add_edge(1, 2, capacity=1000,length = 5, speed_kph = 50)
G.add_edge(2, 4, capacity=1000,length = 5, speed_kph = 50)
G.add_edge(1, 3, capacity=1000,length = 5, speed_kph = 50)
G.add_edge(3, 4, capacity=1000,length = 5, speed_kph = 50)
G.add_edge(2, 5, capacity=1000,length = 5, speed_kph = 50)
G.add_edge(3, 6, capacity=1000,length = 5, speed_kph = 50)
G.add_edge(4, 7, capacity=1000,length = 5, speed_kph = 50)
G.add_edge(5, 7, capacity=1000,length = 5, speed_kph = 50)
G.add_edge(6, 7, capacity=1000,length = 5, speed_kph = 50)
listofroutes=[([1,4,1000],[[(1,2),(2,4)],[(1,3),(3,4)]]),([1,7,1000],[[(1,2),(2,4),(4,7)],[(1,3),(3,4),(4,7)],[(1,2),(2,5),(5,7)],[(1,3),(3,6),(6,7)]])]

listofroutes,G = kFastestPaths.input_data("C:/Users/warre/PycharmProjects/VOP/OD_data/data/OD_Flows_1%.csv","C:/Users/warre/PycharmProjects/VOP/OD_data/data/Graph.graphml", 4)


# In[9]:





# In[ ]:


import csv
with open ('midCorrectpercentageofflows.csv', mode='w', newline='') as file:
    # Create a CSV writer object
    writer = csv.writer(file)
    for i in range(4,7):
        percent =0.2*i
        writer.writerow([percent])
        l=linearapproxEQ(G,listofroutes,2200,"UE",percent)
        writer.writerow(["UE = %f" % l[0]])
        writer.writerow(["traveltime = %f" % get_total_travel_time(l, G)])
        q=linearapproxEQ(G,listofroutes,2200,"SE",percent)
        writer.writerow(["SE = %f" % q[0]])
        writer.writerow(["traveltime = %f" % get_total_travel_time(q, G)])
with open ('lowCorrectpercentageofflows.csv', mode='w', newline='') as file:
    # Create a CSV writer object
    writer = csv.writer(file)
    for i in range(1,4):
        percent =0.2*i
        writer.writerow([percent])
        l=linearapproxEQ(G,listofroutes,2200,"UE",percent)
        writer.writerow(["UE = %f" % l[0]])
        writer.writerow(["traveltime = %f" % get_total_travel_time(l, G)])
        q=linearapproxEQ(G,listofroutes,2200,"SE",percent)
        writer.writerow(["SE = %f" % q[0]])
        writer.writerow(["traveltime = %f" % get_total_travel_time(q, G)])
with open ('highCorrectpercentageofflows.csv', mode='w', newline='') as file:
    # Create a CSV writer object
    writer = csv.writer(file)
    for i in range(7,10):
        percent =0.2*i
        writer.writerow([percent])
        l=linearapproxEQ(G,listofroutes,2200,"UE",percent)
        writer.writerow(["UE = %f" % l[0]])
        writer.writerow(["traveltime = %f" % get_total_travel_time(l, G)])
        q=linearapproxEQ(G,listofroutes,2200,"SE",percent)
        writer.writerow(["SE = %f" % q[0]])
        writer.writerow(["traveltime = %f" % get_total_travel_time(q, G)])
