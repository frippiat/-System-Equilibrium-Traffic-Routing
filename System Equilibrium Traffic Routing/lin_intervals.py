import csv
import signal
import visual_graph
import code_for_UEandSE
import kFastestPaths
import graph_DS
import matplotlib.pyplot as plt
import os
import time
import numpy as np
def handler(signum, frame): #hiermee ga ik zorgen dat het genereren van data stopt na bepaalde precisie en niet er tijdens
    global should_stop
    should_stop = True


def write_data(k, step):
    """opslaan van de berekentijd, totale reistijd en linearisatiefout ifv het aantal intervallen bij een vaste k-waarde"""
    global should_stop
    with open(f'C:/Users/warre/PycharmProjects/VOP/output/aantal linearisatie intervallen/{k}_linearisatie_{step}.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        precision = 1
        G = kFastestPaths.complete_graph(graph_DS.load_networkxgraph("C:/Users/warre/PycharmProjects/VOP/OD_data/data/Graph.graphml"))
        superlist = kFastestPaths.load_fastestpaths(k, "C:/Users/warre/PycharmProjects/VOP/OD_data/data/OD_Flows_1%.csv", "C:/Users/warre/PycharmProjects/VOP/OD_data/data/Graph.graphml" )
        while(True):        #zoeken soort "optimale" waarde voor de parameter k, hoeveel waardes moeten we beschouwen, ga gewoon eens nachtje laten runnen en dan data uit csv bekijken,hopende dat ik al het nodige heb opgeslagen
            if should_stop: #als er signaal is geweest om af te breken
                break
            print(f'start simulatie met precisie {precision}...')
            start_time = time.time() #om te berekentijd te kunnen plotten
            #equilibriums uitrekenen
            UE=code_for_UEandSE.linearapproxEQ(G,superlist, precision, "UE") #bereken UE
            SE=code_for_UEandSE.linearapproxEQ(G,superlist, precision, "SE") #bereken SE
            #stop de timer
            end_time = time.time()
            berekentijd = end_time - start_time  #berekentijd in seconden voor input data + beide equilibriums
            #totale reistijden
            UE_totaltime = code_for_UEandSE.get_total_travel_time(UE, G)
            SE_totaltime = code_for_UEandSE.get_total_travel_time(SE, G)
            SE_objective = SE[0]
            writer.writerow([precision ,berekentijd, UE_totaltime, SE_totaltime, SE_objective])
            precision += step
def plot_data(k, step):
    with open(f'C:/Users/warre/PycharmProjects/VOP/output/aantal linearisatie intervallen/{k}_linearisatie_{step}.csv', 'r', newline='') as file:
        reader = csv.reader(file)
        precision = [] #precisie om te plotten
        berekentijd = [] #duurtijd van de berekening voor beide equilibriums
        diff = [] #verschil in totale reistijd in seconden
        objective_diff = []
        for row in reader:
            precision.append(int(row[0]))
            berekentijd.append(float(row[1]))
            diff.append(float(row[2])-float(row[3]))
            objective_diff.append(float(row[4])-float(row[3]))

        # aangezien het in csv is opgeslagen kan je nu mooi aanpassen tot het mooie plot is)
        helpx = np.array(precision)
        helpy = np.array(berekentijd)
        p = np.polyfit(helpx, helpy, 1)
        y_reg = np.polyval(p, helpx)
        plt.plot(precision , berekentijd, label="berekentijd(s)")
        plt.plot(precision, y_reg, label='Regression line')
        plt.legend(["waargenomen berekentijd","regressie lijn"], loc="best")
        plt.xlabel('Aantal linearisatie intervallen')
        plt.ylabel('berekentijd (s)')
        plt.title('berekentijd in functie van de precisie voor k$_\mathrm{10}$=10')
        plt.show()
        plt.close()

        #nieuwe plot: verschil in totale reistijd
        plt.plot(precision, diff, label="diff_UE_SE(s)")
        plt.xlabel('precisie')
        plt.ylabel('Verschil (s)')
        plt.title("Verschil in totale reistijd in functie van de precisie, voor k$_\mathrm{10}$=10")
        plt.ylim(600000,)
        #display the plot
        plt.show()
        plt.close()

        #nieuwe plot: verschil tussen objective functie en totale reistijd berekend via de "precieze" functie en de toegekende flows.
        plt.plot(precision, objective_diff, label="diff_UE_SE(s)")
        plt.xlabel('precisie')
        plt.ylabel('fout (s)')
        plt.xlim(450, )
        plt.ylim(0, 6*1e3)
        plt.title("Fout geintroduceerd door de lineaire benadering op de totale reistijd van het SE, k$_\mathrm{10}$=10")
        plt.show()

if __name__ == '__main__':
    k = 10 #k=12 omdat ik dit al had opgeslagen
    step = 50

    #als test nog niet bestaat met bepaalde k en step
    #signal.signal(signal.SIGINT, handler)                          #als er een interrupt komt dan zal deze opgevangen worden door de functie handler
    #should_stop = False                                     #should stop flag op vals zetten
    #write_data(k, step)                     #beginnen met data schrijven

    #uncomment als je de data ook wilt laten plotten:
    plot_data(k ,step)



"""def getlineairapprox_variant(G, edge, dw, precision, typeofeq, lin_manier='x'):
    values = []  # lijst waar de y waarden van de benaderde functie inkomen
    ta0 = 3.6*G[edge[0]][edge[1]]['length']/G[edge[0]][edge[1]]['speed_kph']  # de ta0 van een edge (=reistijd in s)
    ca = G[edge[0]][edge[1]]['capacity']  # de ca van een edge
    appr_max = 3*ca
    firststeps = math.ceil(0.9*precision)
    secondsteps = math.floor(0.1*precision)
    secondsteps += (secondsteps==0)
    if lin_manier == 'x': #gewoon verdelen volgens x-as:
        steps = [i * appr_max/firststeps for i in range(firststeps+1)] # lijst waar de x waarden van de benaderde functie inkomen
        complete_steps = [(appr_max + i * (dw-appr_max)/secondsteps) for i in range(1 , secondsteps+1)]
        steps.extend(complete_steps)
    else: #verdelen volgens de y-as

    if (typeofeq == "UE"):  # vult de x en y waarden aan voor UE
        for step in steps:
            if lin_manier == 'x':
                values.append(ta0 * step + (0.15 * ta0 * ((step) ** 5)) / ((ca ** 4) * 5))
            else:
                #via y-as lineariseren
    elif (typeofeq == "SE"):  # vult de x en y waarden aan voor SE
        for step in steps:
            if lin_manier == 'x':
                values.append(step *ta0 * (1 + 0.15 * (((step) / ca) ** 4)))
            else:
                None
    if lin_manier == 'x':
        ans = [steps, values]
    else:
        ans = [values, steps] #x en y waarden zitten natuurlijk in de verkeerde lijst bij de benadering via de y-waarde
    return ans"""