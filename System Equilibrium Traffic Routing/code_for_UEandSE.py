#!/usr/bin/env python
# coding: utf-8
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
            total += Eq[i][1] *ta0 * (1 + 0.15 * ((Eq[i][1] / ca) ** 4))

    return total

# functie die de formules van UE en SE lineair benadert
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
        values.append(dw *ta0 * (1 + 0.15 * ((dw/ca)**4)))
    return [steps, values]  # return een lijst met daarin de lijst met x waarden en die met y waarden

def linearapproxEQ(G, superlist, precision, typeofeq):#, lin_manier='x'):
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

def sec_to_str(s): #x s -> ... uur ... minuten ... seconden
    return f"{round(s//3600)}u {round((s%3600)//60)}m {round((s%3600)%60)}s"

def save(inputgraph,inputcsv, k, precision, superlist=None):
    """opslaan van beide oplossingen in een csv bestand (k waarde en precisie, opnieuw eventueel nog factor)"""
    #print("input data...")
    if not superlist:
        begininput = time.time()
        superlist = kFastestPaths.load_fastestpaths(k, inputcsv, inputgraph)
        eindeinput = time.time()
    G = kFastestPaths.complete_graph(graph_DS.load_networkxgraph(inputgraph))
    #print("SE..")
    q = linearapproxEQ(G, superlist, precision, "SE")
    begin = time.time()
    #print("UE..")
    l = linearapproxEQ(G, superlist, precision, "UE")
    einde = time.time()
    #om te testen:
    index = inputcsv.rfind('/')
    id = inputcsv[index+1:]
    with open(f'C:/Users/warre/PycharmProjects/VOP/output/oplossingen/{id}/{k}k{precision}precsolution.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['user equilibrium', '', 'system equilibrium', ''])
            writer.writerow([l[0], '', q[0], ''])
            for i in range(1, len(l)):
                writer.writerow([l[i][0], l[i][1], q[i][0], q[i][1]])
    #print("Done!")
    #print("geschatte duurtijd (in seconden) voor het oplossen van het model: %f" % (einde - begin))
    #print("geschatte duurtijd (in seconden) voor het berekenen van de input data: %f" % (eindeinput - begininput))

def assign_flows(Eq, G):
    """functie die de flows berekend door een bepaald equilibrium toekent aan de graaf G"""
    for i in range(1, len(Eq)):
        if Eq[i][0][0] == "f" and Eq[i][0][1] != "r":
            index = Eq[i][0].find("|")
            u = int(Eq[i][0][1:index])
            v = int(Eq[i][0][index+1:])
            G[u][v]['flow'] = Eq[i][1]


def load(inputgraph,inputcsv, k, precision, superlist=None):
    """slaat equilibria op indien dit nog niet gebeurde, en laadt ze terug in lijsten in om ze te returnen"""
    index = inputcsv.rfind('/')
    id = inputcsv[index+1:]
    if not(os.path.exists(f'C:/Users/warre/PycharmProjects/VOP/output/oplossingen/{id}/{k}k{precision}precsolution.csv')):
        #als het nog niet bestaat opslaan van de uitkomst met bepaalde k waarde en precisie waarde
        save(inputgraph,inputcsv, k, precision, superlist)
    #terug eruit halen
    with open(f'C:/Users/warre/PycharmProjects/VOP/output/oplossingen/{id}/{k}k{precision}precsolution.csv', 'r', newline='') as file:
        UE = []
        SE = []
        reader = csv.reader(file)
        reader.__next__()  # skip first line
        first = next(reader)
        UE.append(float(first[0]))
        SE.append(float(first[2]))
        for row in reader:
            UE.append((row[0], float(row[1])))
            SE.append((row[2], float(row[3])))
    #indien nood aan superlist:
    #superlist, G = kFastestPaths.input_data("C:/Users/warre/PycharmProjects/VOP/OD_data/data/OD_Flows_1%.csv", "C:/Users/warre/PycharmProjects/VOP/OD_data/data/Graph.graphml", k, 10)
    #anders:
    G = graph_DS.load_networkxgraph("C:/Users/warre/PycharmProjects/VOP/OD_data/data/Graph.graphml")
    G = kFastestPaths.complete_graph(G)
    print("UE = %f" % get_total_travel_time(UE, G))
    print("SE = %f" % get_total_travel_time(SE, G))
    print("SE objective= %f" % (SE[0]))
    return UE, SE

