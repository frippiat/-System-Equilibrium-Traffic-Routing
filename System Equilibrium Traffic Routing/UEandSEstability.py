


import kFastestPaths
from gurobipy import GRB, Model
import graph_DS
import networkx as nx
import matplotlib.pyplot as pltw
import time




def getlineairapprox(edge, dw, precision, typeofeq):
    steps = []  # lijst waar de x waarden van de benaderde functie inkomen
    values = []  # lijst waar de y waarden van de benaderde functie inkomen
    ta0 = 3.6*G[edge[0]][edge[1]]['length']/G[edge[0]][edge[1]]['speed_kph']  # de ta0 van een edge (=reistijd in s)
    ca = G[edge[0]][edge[1]]['capacity']  # de ca van een edge
    step = 0.75 * dw / precision + (1 if precision > 1000 else precision / 1000) * 0.25 * dw / precision  # formule die de stapgrootte bepaald van de lineaire opdeling. fa kan max dw zijn maar zal wss nooit zo groot zijn, daarom heb ik een formule gebruikt die voor kleine precisie de linearisatie vooral conentreert op het eerste deel van de functie,maar als de precisie groot genoeg is (hier 100) dan zal de functie wel mooi in gelijke delen verdeeld worden
    if (typeofeq == "UE"):  # vult de x en y waarden aan voor UE
        for i in range(precision):
            steps.append(i * step)
            values.append(ta0 * (i * step+G[edge[0]][edge[1]]['flow']) + (0.15 * ta0 * ((i * step+G[edge[0]][edge[1]]['flow']) ** 5)) / ((ca ** 4) * 5))
        steps.append(dw)
        values.append(ta0 * (dw+G[edge[0]][edge[1]]['flow']) + (0.15 * ta0 * ((G[edge[0]][edge[1]]['flow']+dw) ** 5)) / ((ca ** 4) * 5))
    elif (typeofeq == "SE"):  # vult de x en y waarden aan voor SE
        for i in range(precision):
            steps.append(i * step)
            values.append((step * i+G[edge[0]][edge[1]]['flow']) *ta0 * (1 + 0.15 * (((step * i+G[edge[0]][edge[1]]['flow']) / ca) ** 4)))
        steps.append(dw)
        values.append( (G[edge[0]][edge[1]]['flow']+dw) * ta0 * (1 + 0.15 * (((G[edge[0]][edge[1]]['flow']+dw)/ca)**4)))
    return [steps, values]  # return een lijst met daarin de lijst met x waarden en die met y waarden



def linearapproxEQ(G, superlist, precision, typeofeq,UEpercentage):
    totaldw = 0
    for i in superlist:
        totaldw += UEpercentage*i[0][2]
    optmod = Model(name=f"lineair approx {typeofeq}")  # aanmaken van een gurobi module
    #optmod.setParam('NodefileStart', 0) # vanaf gurobi meer dan 0 MB (0GB) aan RAM gebruikt zal het zoveel mogelijk proberen om dingen "uit te swappen" naar een eigen file op de disk, de 'NodeFile' -> dus hoe lager hoe sneller gurobi zal proberen zoveel mogelijk op de disk te zetten, maar dus logischerwijze ook hoe trager
    #optmod.setParam('NumericFocus', 3) #om snelheid niet belangerijk te maken, 0= full snelheid -> 3=full numeric accuracy #model wordt unfeasible plots hierdoor???
    #optmod.setParam('Threads', 1) #aantal threads instellen
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
    for edge in Gf.edges():
        a = "f%s|%s" % (edge[0], edge[1])  # de naam van de variabele voor de flow op de tak bv.:f12

        ya = "yf%s|%s" % (edge[0], edge[1])  # de naam van de variabele voor de y waarden van de lineaire approximatie voor de flow op de tak bv.:yf12. deze variabele heb je nodig om later de lineare functie van deze f bij de algehele functie op te tellen
        cya = "cyf%s|%s" % (edge[0], edge[1])  # de naam van de variabele voor de constraint die zal aangeven hoe f12 en yf12 samenhangen (namelijk via de lineaire functie, hier kan men zeggen dat yf12= f(f12) met f dan de lineair geaproximeerde functie). het is een beetje raar dat dit via een constraint moet maar dit is nu eenmaal hoe gurobi werkt
        myvars[a] = optmod.addVar(name=a, vtype=GRB.CONTINUOUS,lb=0)  # het toevoegen van de variabele (bv f12 aan het gurobi model)
        myvars[ya] = optmod.addVar(name=ya, vtype=GRB.CONTINUOUS,lb=0)  # het toevoegen van de variabele (bv yf12 aan het gurobi model)
        constr = "c%s|%s" % (edge[0], edge[1])  # het aanmaken van een constraint voor f12 dit is het constraint die zegt dat f12 de som is van alle fr die door de tak 1-2 stromen (zie constraints op curusblad dat warre had doorgestuurd)
        myvars[constr] = 0  # het toevoegen van deze constraint aan de vairabelen
        linaprox = getlineairapprox(edge, totaldw, precision, typeofeq)  # het oproepen van de functie die de lineare approximatie teruggeeft
        myvars[cya] = optmod.addGenConstrPWL(myvars[a], myvars[ya], linaprox[0], linaprox[1], "myconstr")  # toevoegen van het constraint dat f12 aan zijn lineaire functie yf12 koppelt (voor meer info zie https://www.gurobi.com/documentation/current/refman/py_model_agc_pwl.html)
        function += myvars[ya]  # het toevoegen van de lineaire approx functie aan de algehele functie zodat we uiteindelijk de som bekomen bij het beeindigen van de for loop)
    optmod.setObjective(function, sense=GRB.MINIMIZE)  # functie toevoegen aan het gurobi model
    for e, listoflists in enumerate(superlist):
        constr_fr = 0  # initialiseren van het constraint dat zegt dat de som van alle fr gelijk is aan dw, dit is per OD paar te beschouwen (aanpassing met code voordien)
        for i, list in enumerate(listoflists[1]):  # elke route bekijken

            fr = "fr%s|%s|%s" % (listoflists[0][0], listoflists[0][1], i)  # aanmaken van de variabele die de flow op die route beschrijft
            myvars[fr] = optmod.addVar(name=fr, vtype=GRB.CONTINUOUS, lb=0, ub=UEpercentage*listoflists[0][2])  # toevoegen van de variabele die de flow op die route beschrijft aan de variabelen en tegelijk ook aan het gurobi model
            constr_fr += myvars[fr]  # toevoegen van fr aan het voorheen vermelde constraint
            for edge in list:  # elke edge op de route bekijken
                currentconstr = "c%s|%s" % (edge[0], edge[1])  # currentconstr gelijk stellen aan het constraint op f van de tak dat hierboven geinitialiseerd werd
                myvars[currentconstr] += myvars[fr]  # toevoegen van fr aan het constraint van f van de tak
        cfr = "cfrdw%s|%s" % (listoflists[0][0], listoflists[0][1])  # naam voor constraint die aan het model wordt toegevoegd
        myvars[cfr] = optmod.addConstr(constr_fr == UEpercentage*listoflists[0][2],name=cfr)  # het constraint dat alle fr samen dw moeten zijn toevoegen aan het model (stond ook verkeerd uitgelijnd )
    for edge in Gf.edges():  # elke tak bekijken om de constraint dat alle fr van routes die edge gebruiken moet gelijk zijn aan flow op die tak
        a = "f%s|%s" % (edge[0], edge[1])
        currentconstr = "c%s|%s" % (edge[0], edge[1])  # de som van alle fr die door f van de tak gaan (zie ook hierboven telkens bv c12 genaamd (bekijk dus de lines met c%s%s))
        constroff = "cstr%s|%s" % (edge[0], edge[1])  # een variabele aanmaken voor de constraint die aan het model wordt toegevoegd
        myvars[constroff] = optmod.addConstr(myvars[a] == myvars[currentconstr], name=constroff)  # het constraint aan het model toevoegen
    optmod.optimize()  # model uitreknen
    l = []
    l.append(optmod.ObjVal)  # de uitgerekende waarde aan de lijst toevoegen (dus UE of SE)

    #for v in optmod.getVars():
        #l.append((v.varName, v.x))  # alle variabelen in het model toevoegen aan de lijst
    for edge in G.edges():
        a = "f%s|%s" % (edge[0], edge[1])
        l.append((a,myvars[a].x+G[edge[0]][edge[1]]["flow"]))
        G[edge[0]][edge[1]]["flow"] = myvars[a].x
    optmod.dispose() #close the model
    return l  # de lijst teruggeven






def stabilityofEQ(G,listofroutes,precision,UEpercentage,aantal_iterations):
    if aantal_iterations%2==0:
        aantal_iterations += 1 ; #anders geef je het UE terug nbij even aantal iteraties

    for edge in G.edges():
        G[edge[0]][edge[1]]["flow"] = 0
    EQ = "UE"
    percentage = UEpercentage
    if percentage != 0:

        l = linearapproxEQ(G, listofroutes, precision, EQ, percentage)
    if percentage != 1:
        for i in range(aantal_iterations):
            EQ = "SE" if EQ == "UE" else "UE"
            percentage = 1 - UEpercentage if EQ == "SE" else UEpercentage
            l = linearapproxEQ(G, listofroutes, precision, EQ, percentage)

    return l
        
        


        

        
        
        
        
        
def get_total_travel_time(Eq, G): #functie om de totale reistijd van een equilibrium te berekenen
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



#testcode:
get_total_travel_time(qe,G)

listofroutes,G = kFastestPaths.input_data("OD_Flows_10%.csv","Graph.graphml",7) 

import csv
import time
checktime = time.time();
with open ('stability.csv', mode='w', newline='') as file:
    # Create a CSV writer object
    writer = csv.writer(file)

    # Write the header row
    for i in range(11):
        qe=stabilityofEQ(G,listofroutes,2200,i/10,1)
        traveltime=get_total_travel_time(qe,G)
        writer.writerow([i/10])
        writer.writerow([traveltime])
        writer.writerow([time.time()-checktime])
        checktime = time.time()


    # Write the header row
    for i in range(11):
        qe = stabilityofEQ(G, listofroutes, 2200, i / 10, 1)
        traveltime = get_total_travel_time(qe, G)
        writer.writerow([i / 10])
        writer.writerow([traveltime])
        writer.writerow([time.time() - checktime])
        checktime = time.time()