import visual_graph
import code_for_UEandSE
import kFastestPaths
import graph_DS
import time
import csv
import signal
import string
import matplotlib.pyplot as plt
import tqdm
import numpy as np
"""in dit document wordt er getest wat de invloed op onze situatie is wanneer de factor waarmee de paden worden berekend wordt afgenomen"""
def write():
    k = 6
    precisie = 2000
    factor = 10
    subt = 1
    with open('C:/Users/warre/PycharmProjects/VOP/output/test_factor2.csv', 'w', newline='') as file:
        with open('C:/Users/warre/PycharmProjects/VOP/output/test_factor_paths2.csv', 'a', newline='') as file2:
            writer = csv.writer(file)
            writer2=csv.writer(file2)
            while(factor >= 1):
                #k snelste paden berekenen
                superlist, G = kFastestPaths.input_data("C:/Users/warre/PycharmProjects/VOP/OD_data/data/test.csv", "C:/Users/warre/PycharmProjects/VOP/OD_data/data/Graph.graphml", k, factor=factor)

                #opslaan van het aantal keer dat een tak meer dan 1x voorkomt in snelste paden
                counter = [0 for i in range(k)]  # aantal takken die redundant gebruikt worden
                for OD in superlist:
                    edge_counter = [0 for i in range(k)]
                    edges = [[] for i in range(k)]
                    for path in OD[1]:
                        for edge in path:
                            yes = False
                            for i in range(k-2, -1, -1):
                                if edge in edges[i]:
                                    yes = True
                                    edge_counter[i+1] += 1
                                    edge_counter[i] -= 1
                                    edges[i+1].append(edge)
                                    break
                            if not yes:
                                edges[0].append(edge)
                                edge_counter[0] += 1
                    for i, element in enumerate(edge_counter):
                        counter[i] += element/(sum(edge_counter)*len(superlist))
                row = [factor]
                for element in counter:
                    row.append(element)
                writer2.writerow(row)

                #opslaan in csv bestanden van informatie over beide equilibria, namelijk per OD paar voor elke route: toegekende flow, reistijd, reistijd zonder flow
                UE, SE = code_for_UEandSE.linearapproxEQ(G, superlist, precisie, "UE"), code_for_UEandSE.linearapproxEQ(G, superlist, precisie, "SE")
                ue_tt, se_tt = code_for_UEandSE.get_total_travel_time(UE, G),  code_for_UEandSE.get_total_travel_time(SE, G)
                #user en system equilibria
                writer.writerow(["new", factor, ue_tt, se_tt])

                info = {(OD[0][0], OD[0][1]): {i: [0, 0, 0] for i in range(k)} for OD in superlist} #woordenboek die per OD paar aangeeft wat
                edge_tt = {edge: 0 for edge in G.edges}
                # aantal flows die route pakken opslaan + reistijd per route per voertuig
                uebar = tqdm.tqdm(total=len(UE) - 1)
                for i in range(1, len(UE)):
                    if UE[i][0][:2] == "fr":  # de flows van elke route hebben we ook nodig
                        first_index = UE[i][0].find('|')
                        second_index = UE[i][0].find('|', first_index + 1)
                        Origin, Destination, route = int(UE[i][0][2:first_index]), int(
                        UE[i][0][first_index + 1:second_index]), int(
                        UE[i][0][second_index + 1:])  # fr = "fr%s%s%s" %(listoflists[0][0], listoflists[0][1], i)
                        info[(Origin, Destination)][route][0] = UE[i][1]  # flow op route steken
                    elif UE[i][0][0] == "f":  # met de flow op een tak te maken
                        index = UE[i][0].find('|')  # splitsing tussen knoopnamen met '|'
                        edge = (int(UE[i][0][1:index]), int(UE[i][0][index + 1:]))  # tak die we aan het bekijken zijn
                        ta0 = 3.6 * G[edge[0]][edge[1]]['length'] / G[edge[0]][edge[1]]['speed_kph']  # de ta0 van een edge (=reistijd in s)
                        ca = G[edge[0]][edge[1]]['capacity']
                        edge_tt[edge] = ta0 * (1 + 0.15 * ((UE[i][1] / ca) ** 4))
                    uebar.update(1)

                for OD in superlist:  # elk OD paar bekijken
                    for j, route in enumerate(OD[1]):  # alle routes bekijken
                        for edge in route:  # elke tak beschouwen
                            info[(OD[0][0], OD[0][1])][j][1] += edge_tt[edge]  # wat is de reistijd per route
                            info[(OD[0][0], OD[0][1])][j][2] += 3.6 * G[edge[0]][edge[1]]['length'] / G[edge[0]][edge[1]][
                                'speed_kph']  # om te weten wat ta0 van deze route is (=hoe mensen route inschatten)

                # opslaan in csv bestand:
                for OD, paths in info.items():
                    writer.writerow([OD])
                    for path, value in paths.items():
                        writer.writerow([path, value[0], value[1], value[2]])
                uebar.close()
                # hetzelfde voor SE:
                writer.writerow(["System Equilibrium"])
                info = {(OD[0][0], OD[0][1]): {i: [0, 0, 0] for i in range(k)} for OD in superlist}
                edge_tt = {edge: 0 for edge in G.edges}
                # aantal flows die route pakken opslaan + reistijd per route per voertuig
                sebar = tqdm.tqdm(total=len(SE) - 1)
                for i in range(1, len(SE)):
                    if SE[i][0][:2] == "fr":  # de flows van elke route hebben we ook nodig
                        first_index = SE[i][0].find('|')
                        second_index = SE[i][0].find('|', first_index + 1)
                        Origin, Destination, route = int(SE[i][0][2:first_index]), int(SE[i][0][first_index + 1:second_index]), int(SE[i][0][second_index + 1:])  # fr = "fr%s%s%s" %(listoflists[0][0], listoflists[0][1], i)
                        info[(Origin, Destination)][route][0] = SE[i][1]  # flow op route steken
                    elif SE[i][0][0] == "f":  # met de flow op een tak te maken
                        index = SE[i][0].find('|')  # splitsing tussen knoopnamen met '|'
                        edge = (int(SE[i][0][1:index]), int(SE[i][0][index + 1:]))  # tak die we aan het bekijken zijn
                        ta0 = 3.6 * G[edge[0]][edge[1]]['length'] / G[edge[0]][edge[1]][
                            'speed_kph']  # de ta0 van een edge (=reistijd in s)
                        ca = G[edge[0]][edge[1]]['capacity']
                        edge_tt[edge] = ta0 * (1 + 0.15 * ((SE[i][1] / ca) ** 4))
                    sebar.update(1)

                for OD in superlist:  # elk OD paar bekijken
                    for j, route in enumerate(OD[1]):  # alle routes bekijken
                        for edge in route:  # elke tak beschouwen
                            info[(OD[0][0], OD[0][1])][j][1] += edge_tt[edge]
                            info[(OD[0][0], OD[0][1])][j][2] += 3.6 * G[edge[0]][edge[1]]['length'] / G[edge[0]][edge[1]][
                                'speed_kph']  # om te weten wat ta0 van deze route is (=hoe mensen route inschatten)
                sebar.close()
                # opslaan in csv bestand:
                for OD, paths in info.items():
                    writer.writerow([OD])
                    for path, value in paths.items():
                        writer.writerow([path, value[0], value[1], value[2]])

                if factor == 6:
                    subt = 0.5
                factor -= subt
def plot():
    """plot de totale reistijden in functie van de factor"""
    #uit document halen
    factor = []
    ue_tt = []
    se_tt = []
    UE = []
    SE = []
    curr_UE = {}
    curr_SE = {}
    curr_OD = None
    SE_ = False #weten of we met UE of SE info bezig zijn
    with open('C:/Users/warre/PycharmProjects/VOP/output/test_factor2.csv', 'r', newline='') as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] == "new": #nieuwe factor
                SE_ = False
                factor.append(float(row[1]))
                ue_tt.append(float(row[2]))
                se_tt.append(float(row[3]))
                if curr_SE:  # als het niet het begin is
                    SE.append(curr_SE)
                    curr_SE = {}
                if curr_UE:
                    UE.append(curr_UE)
                    curr_UE = {}
            elif len(row) == 3:
                continue #verkeerd opgeslagen oeps
            else:
                if row[0] == "System Equilibrium":  # hierna komt info over SE
                    SE_ = True
                elif len(row) == 1:  # nieuw OD paar
                    # (OD1, OD2)
                    index = row[0].find(',')
                    curr_OD = (int(row[0][1:index]), int(row[0][index + 2: -1]))  # node id's zijn int
                    if SE_:
                        curr_SE[curr_OD] = {}
                    else:
                        curr_UE[curr_OD] = {}
                elif SE_:  # nieuwe info over OD paar
                    curr_SE[curr_OD][int(row[0])] = (float(row[1]), float(row[2]), float(row[3]))  # flow, reistijd, ta0
                else:
                    curr_UE[curr_OD][int(row[0])] = (float(row[1]), float(row[2]), float(row[3]))
        SE.append(curr_SE)
        UE.append(curr_UE)

        #plotten:
        #omdraaien
        factor = factor[::-1]
        ue_tt = ue_tt[::-1]
        se_tt = se_tt[::-1]
        #reistijden
        plt.plot(factor, ue_tt)
        plt.xticks(factor)
        plt.plot(factor, se_tt)
        plt.xlabel("factor")
        plt.ylabel("totale reistijd (s)")
        plt.vlines(x= 2 , ymin=0, ymax= se_tt[2], linestyles='dotted', color='black')
        plt.vlines(x= 10 , ymin=0, ymax=se_tt[14], linestyles='dotted', color='black')
        plt.hlines(xmin= 0 ,xmax= 2, y=se_tt[2], linestyles='dotted', color='black')
        plt.hlines(xmin= 0 ,xmax= 10, y=se_tt[14], linestyles='dotted', color='black')
        plt.scatter(x=1, y=se_tt[0], s=5 ,color="0.1", zorder=2)
        plt.scatter(x=2, y=se_tt[2], s=5, color="0.1", zorder=2)
        plt.scatter(x=10, y=se_tt[14],s=5, color="0.1", zorder=2)
        diff = se_tt[9]-se_tt[1]
        plt.vlines(x= 1.4, ymin=se_tt[2], ymax=se_tt[-1], color='0.1')
        plt.text(0.5,(se_tt[2]+se_tt[-1]) / 2 , f"Verschil: {round(diff//3600)}u {round((diff%3600)//60)}m {round((diff%3600)%60)}s", ha='center', va='center')
        plt.ylim(1.75*1e7, 2.22*1e7)
        plt.title("Invloed van de factor op de totale reistijd bij $k_{factor}$=6")
        plt.show()
        #door minder verschillende takken wel duidelijk minder verschil tussen ue en se, bv. verschil tussen factor=2 en factor=10 (die helemaal op het einde staat opgeslagen)
        diff2 = ue_tt[2] - se_tt[2]
        diff3 = ue_tt[-1] - se_tt[-1]
        print(f"Verschil factor=2, k=6: {code_for_UEandSE.sec_to_str(diff2)}")
        print(f"Verchil factor=10,k=6: {code_for_UEandSE.sec_to_str(diff3)}")

def edge_usage():
    """deze functie maakt een scatter plot die per factor een punt zet op het percentage van takken die i (0 < i <= k) keer gebruikt worden in de k snelste paden van een OD paar,
    en uitgemiddeld over alle OD paren"""
    x= [i+1 for i in range(k)]
    factor = []
    usage = []
    with open('C:/Users/warre/PycharmProjects/VOP/output/test_factor_paths2.csv', 'r', newline='') as file:
        reader = csv.reader(file)
        i = 0
        row = reader.__next__()
        usage.append([])
        factor.append(float(row[0][3:]))
        for element in row[1:]:
            usage[i].append(float(element))
        i += 1
        for row in reader:
            usage.append([])
            factor.append(round(float(row[0]), 2))
            for element in row[1:]:
                usage[i].append(float(element))
            i += 1
        legend = []
        for i, element in enumerate(usage):
            plt.scatter(x, element)
            legend.append(str(factor[i]))
        legend = plt.legend(legend, title="gebruikte factor", loc="best")
        plt.xlim(0,)
        plt.xlabel("aantal paden n die de tak gebruikt")
        plt.ylabel("gemiddeld aantal takken (%)")
        plt.show()


if __name__=='__main__':
    k = 6
    precisie = 2000
    factor = 10
    subt = 1
    #write()
    #plot()
    edge_usage()