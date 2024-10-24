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
"""file waarin ik tests doe voor een in onze situatie (!) optimale waarde van k"""
def handler(signum, frame): #hiermee ga ik zorgen dat de functie stopt bij een nieuwe k en niet wanneer er nog data wordt weggeschreven
    global should_stop
    should_stop = True

def write_data(factor): #schrijft alle nodige info naar het volgens de factor gepaste csv bestand
    global should_stop
    with open(f'C:/Users/warre/PycharmProjects/VOP/output/k_values{factor}.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        pbar = tqdm.tqdm(total=30)
        G = kFastestPaths.complete_graph(graph_DS.load_networkxgraph("C:/Users/warre/PycharmProjects/VOP/OD_data/data/Graph.graphml"))
        pbar.update(1)
        for k in range(1 ,30):        #30 paden is zeker meeeeeer dan voldoende want bij 22 merkte ik al dat het gigantisch lang duurde en er veel paden niet werden gebruikt
            if should_stop: #als er signaal is geweest om af te breken, breek af
                break
            print(f'start simulatie met k-waarde {k}...')
            start_time = time.time() #om de berekentijd te kunnen plotten
            #berekenen van de k snelste paden
            #deselecteer als je ook de snelste paden in csv bestanden wilt opslaan (duurt stuk langer):
            #listofroutes = kFastestPaths.load_fastestpaths(k, "C:/Users/warre/PycharmProjects/VOP/OD_data/data/OD_Flows_1%.csv", "C:/Users/warre/PycharmProjects/VOP/OD_data/data/Graph.graphml")
            #deselcteer als je enkel hier de snelste paden gaat gebruiken en deze dus niet hoeven opgeslagen te worden
            listofroutes, G = kFastestPaths.input_data("C:/Users/warre/PycharmProjects/VOP/OD_data/data/OD_Flows_1%.csv", "C:/Users/warre/PycharmProjects/VOP/OD_data/data/Graph.graphml",k, factor=factor)
            #equilibriums uitrekenen
            #deselecteer als je ook de oplossingen in csv bestanden wilt opslaan (duurt stuk langer):
            #UE, SE = code_for_UEandSE.load("C:/Users/warre/PycharmProjects/VOP/OD_data/data/Graph.graphml", "C:/Users/warre/PycharmProjects/VOP/OD_data/data/OD_Flows_1%.csv", k,  2000, listofroutes)
            #deselecteer als je gwn de oplossing hier nodig hebt:
            UE, SE = code_for_UEandSE.linearapproxEQ(G, listofroutes, 2000, "UE"), code_for_UEandSE.linearapproxEQ(G, listofroutes, 2000, "SE")
            #stop de timer
            end_time = time.time()
            berekentijd = end_time - start_time  # berekentijd in seconden voor input data + beide equilibriums

            #totale reistijden opvragen via andere functies
            UE_totaltime = code_for_UEandSE.get_total_travel_time(UE, G)
            SE_totaltime = code_for_UEandSE.get_total_travel_time(SE, G)

            #opslaan in csv bestand als soort header
            writer.writerow("volgende waarde: {}".format(k))
            writer.writerow([berekentijd, UE_totaltime, SE_totaltime])
            #bekijken van het verschil tussen de individuele reistijden van het UE en het SE
            #opslaan van dictionary die OD-route afbeeldt op (flow, reistijd gegeven de flows, reistijd zonder flows)
            writer.writerow(["User Equilibrium"])
            info = {(OD[0][0], OD[0][1]): {i:[0, 0, 0] for i in range(k)} for OD in listofroutes}
            edge_tt = {edge:0 for edge in G.edges}
            # aantal flows die route pakken opslaan + reistijd per route per voertuig
            uebar = tqdm.tqdm(total=len(UE)-1)
            for i in range(1, len(UE)):
                if UE[i][0][:2] == "fr": #de flows van elke route hebben we ook nodig
                    first_index = UE[i][0].find('|')
                    second_index = UE[i][0].find('|', first_index + 1)
                    Origin, Destination, route = int(UE[i][0][2:first_index]), int(UE[i][0][first_index+1:second_index]), int(UE[i][0][second_index+1:]) #fr = "fr%s%s%s" %(listoflists[0][0], listoflists[0][1], i)
                    info[(Origin, Destination)][route][0] = UE[i][1] #flow op route steken
                elif UE[i][0][0] == "f" :  #met de flow op een tak te maken
                    index = UE[i][0].find('|')  # splitsing tussen knoopnamen met '|'
                    edge = (int(UE[i][0][1:index]), int(UE[i][0][index+1:]))  # tak die we aan het bekijken zijn
                    ta0 = 3.6 * G[edge[0]][edge[1]]['length'] / G[edge[0]][edge[1]]['speed_kph']  # de ta0 van een edge (=reistijd in s)
                    ca = G[edge[0]][edge[1]]['capacity']
                    edge_tt[edge] = ta0 * (1 + 0.15 * ((UE[i][1] / ca) ** 4))
                uebar.update(1)

            for OD in listofroutes: #elk OD paar bekijken
                for j, route in enumerate(OD[1]): #alle routes bekijken
                    for edge in route: #elke tak beschouwen
                        info[(OD[0][0], OD[0][1])][j][1]  += edge_tt[edge] #wat is de reistijd per route
                        info[(OD[0][0], OD[0][1])][j][2] +=  3.6 * G[edge[0]][edge[1]]['length'] / G[edge[0]][edge[1]]['speed_kph'] #om te weten wat ta0 van deze route is (=hoe mensen route inschatten)

            #opslaan in csv bestand:
            for OD, paths in info.items():
                writer.writerow([OD])
                for path, value in paths.items():
                    writer.writerow([path, value[0], value[1], value[2]])
            print(f"UE met k-waarde {k} opgeslagen")
            #uebar.close()
            #hetzelfde voor SE:
            writer.writerow(["System Equilibrium"])
            info = {(OD[0][0], OD[0][1]): {i:[0, 0, 0] for i in range(k)} for OD in listofroutes}
            edge_tt = {edge:0 for edge in G.edges}
            # aantal flows die route pakken opslaan + reistijd per route per voertuig
            uebar = tqdm.tqdm(total=len(SE)-1)
            for i in range(1, len(SE)):
                if SE[i][0][:2] == "fr": #de flows van elke route hebben we ook nodig
                    first_index = SE[i][0].find('|')
                    second_index = SE[i][0].find('|', first_index + 1)
                    Origin, Destination, route = int(SE[i][0][2:first_index]), int(SE[i][0][first_index+1:second_index]), int(SE[i][0][second_index+1:]) #fr = "fr%s%s%s" %(listoflists[0][0], listoflists[0][1], i)
                    info[(Origin, Destination)][route][0] = SE[i][1] #flow op route steken
                elif SE[i][0][0] == "f" :  #met de flow op een tak te maken
                    index = SE[i][0].find('|')  # splitsing tussen knoopnamen met '|'
                    edge = (int(SE[i][0][1:index]), int(SE[i][0][index+1:]))  # tak die we aan het bekijken zijn
                    ta0 = 3.6 * G[edge[0]][edge[1]]['length'] / G[edge[0]][edge[1]]['speed_kph']  # de ta0 van een edge (=reistijd in s)
                    ca = G[edge[0]][edge[1]]['capacity']
                    edge_tt[edge] = ta0 * (1 + 0.15 * ((SE[i][1] / ca) ** 4))
                uebar.update(1)

            for OD in listofroutes: #elk OD paar bekijken
                for j, route in enumerate(OD[1]): #alle routes bekijken
                    for edge in route: #elke tak beschouwen
                        info[(OD[0][0], OD[0][1])][j][1]  += edge_tt[edge]
                        info[(OD[0][0], OD[0][1])][j][2] +=  3.6 * G[edge[0]][edge[1]]['length'] / G[edge[0]][edge[1]]['speed_kph'] #om te weten wat ta0 van deze route is (=hoe mensen route inschatten)
            #sebar.close()
            #opslaan in csv bestand:
            for OD, paths in info.items():
                writer.writerow([OD])
                for path, value in paths.items():
                    writer.writerow([path, value[0], value[1], value[2]])
            print(f"SE met k-waarde {k} opgeslagen")
            pbar.update(1)
        pbar.close()

if __name__ == '__main__':
    #opslaan van de data:
    #signal.signal(signal.SIGINT, handler)   #als er een interrupt komt dan zal deze opgevangen worden door de functie handler
    #should_stop = False                     #should stop flag op vals zetten
    #conform met test_factor eens kijken naar factor=10 en factor=2
    #write_data(10)                            #beginnen met data schrijven voor factor 10
    #write_data(2)                            #ook voor factor 2
    #nodige info eruithalen:
    factor = 2 #10
    k = [0]
    berekentijd = [] #verschillende berekentijden in functie van k waarde terug opslaan
    UE_totaltime = [] #totale reistijden in functie van k waarde
    SE_totaltime = []
    UE = []  #de verschillende info woordenboeken (per OD per route de flow, reistijd en reistijd zonder flow) per k waarde
    SE = []
    diff = [] #verschil in reistijd
    factor = 2 #10
    with open(f'C:/Users/warre/PycharmProjects/VOP/output/k_values{factor}.csv', 'r', newline='') as file:
        reader = csv.reader(file)
        curr_UE = {}
        curr_SE = {}
        curr_OD = None
        algemene_info = False #weten of de volgende lijn algemene info is
        SE_ = False #weten of we met UE of SE info bezig zijn
        for row in reader:
            if row[0]=="v" and row[1] == "o": #nieuwe k-waarde
                k.append(k[-1]+1)
                algemene_info = True #aangeven dat volgende lijn algemene info bevat (berekentijd, ...)
                if curr_SE: #als het niet het begin hebben we een woordenboek van een bepaalde k waarde dus slaan we die op
                    SE.append(curr_SE)
                    curr_SE = {}
                if curr_UE:
                    UE.append(curr_UE)
                    curr_UE = {}
            elif algemene_info: #rij met berekentijd, ...
                berekentijd.append(float(row[0])) #berekentijd is float die seconden voorstelt
                UE_totaltime.append(float(row[1]))
                SE_totaltime.append(float(row[2]))
                diff.append(float(row[1]) - float(row[2]))
                algemene_info = False #hierna komt de info van OD paren en paden enzo
            else:
                if row[0] == "System Equilibrium": #hierna komt info over SE
                    SE_ = True
                elif row[0] == "User Equilibrium": #hierna komt info over UE
                    SE_ = False
                elif len(row) == 1: #nieuw OD paar
                    # (OD1, OD2)
                    index = row[0].find(',')
                    curr_OD = (int(row[0][1:index]), int(row[0][index+2: -1])) #node id's zijn int
                    if SE_:
                        curr_SE[curr_OD] = {}
                    else:
                        curr_UE[curr_OD] = {}
                elif SE_: #nieuwe info over OD paar
                    curr_SE[curr_OD][int(row[0])] = (float(row[1]), float(row[2]), float(row[3])) #flow, reistijd, ta0
                else:
                    curr_UE[curr_OD][int(row[0])]= (float(row[1]), float(row[2]), float(row[3]))
        SE.append(curr_SE)
        UE.append(curr_UE)
    k = k[1:]
    print(code_for_UEandSE.sec_to_str(UE_totaltime[5]))
    print(code_for_UEandSE.sec_to_str(SE_totaltime[5]))
    diff3 =UE_totaltime[5] - SE_totaltime[5]
    print(code_for_UEandSE.sec_to_str(diff3))
    #verwerken + visualiseren:
    #1 visualisatie van berekentijd ifv k
    plt.plot(k, berekentijd, label="berekentijd(s)")
    plt.plot(k, berekentijd, '-o', label="berekentijd(s)", linestyle='dotted')
    plt.xticks(k)
    plt.xlabel('k')
    plt.ylabel('berekentijd')
    plt.title(f"berekentijd in functie van aantal snelste paden")
    plt.xlabel('k$_\mathrm{10}$')
    plt.ylabel('berekentijd(s)')
    plt.title(f"Totale berekentijd in functie van aantal snelste paden")
    plt.show()
    plt.close()
    # 2 visualisatie van beide totale reistijden ifv k
    plt.plot(k, UE_totaltime)
    plt.plot(k, SE_totaltime)
    plt.xlabel('k')
    plt.ylabel('totale reistijd')
    plt.title(f"Totale reistijd in functie van ")
    plt.legend(['UE', 'SE'], loc='upper right')
    plt.ylim(1.82*1e7, 1.93*1e7)
    plt.xticks(k)
    plt.xlabel('k$_\mathrm{10}$')
    diff  = UE_totaltime[6] - SE_totaltime[6]
    plt.semilogy([7, 7], [SE_totaltime[6], UE_totaltime[6]], color='black')
    plt.annotate(f'Verschil: {round(diff//3600)}u {round((diff%3600)//60)}m {round(((diff%3600)%60))}s = gemiddeld {round(diff/33406.0)}s per weggebruiker/uur', xy=(7.1, (UE_totaltime[6] + SE_totaltime[6]) / 2), rotation=0)
    plt.ylabel('totale reistijd (s)')
    plt.title("Som van alle reistijden bij k$_\mathrm{10}$ beschouwde snelste paden")
    plt.legend(['UE', 'SE'], loc='best')
    plt.ylim(1.82*1e7, 2*1e7)
    plt.show()
    plt.close()

    # 3 visualisatie van se totale reistijd ingezoomed
    plt.plot(k, SE_totaltime)
    plt.xlabel('k$_\mathrm{10}$')
    plt.ylabel('totale reistijd (s)')
    plt.title("SE totale reistijd")
    plt.xticks(k)
    plt.yticks([SE_totaltime[5],SE_totaltime[10]], labels=[f"{round(SE_totaltime[5]//3600)}u {round((SE_totaltime[5]%3600)//60)}m {round(((SE_totaltime[5]%3600)%60))}s",f"{round(SE_totaltime[10]//3600)}u {round((SE_totaltime[10]%3600)//60)}m {round(((SE_totaltime[10]%3600)%60))}s" ])
    plt.vlines(6, 0,SE_totaltime[5] , linestyles='dotted', color="black")
    plt.vlines(11, 0,SE_totaltime[10] , linestyles='dotted', color="black")
    plt.hlines(SE_totaltime[5], 0, 6, linestyles='dotted', color="black")
    plt.hlines(SE_totaltime[10], 0, 11, linestyles='dotted', color="black")
    plt.ylim(1.8443*1e7,1.847*1e7)
    plt.xlim(3.5, 15)
    plt.show()
    plt.close()

    #4 visualisatie van ue ingezoomed
    plt.plot(k, UE_totaltime)
    plt.ylabel('totale reistijd')
    plt.xlabel('k$_\mathrm{10}$')
    plt.ylabel(' (s)')
    plt.title("UE totale reistjd")
    plt.xticks(k)
    plt.yticks([UE_totaltime[5],UE_totaltime[10]], labels=[f"{round(UE_totaltime[5]//3600)}u {round((UE_totaltime[5]%3600)//60)}m {round(((UE_totaltime[5]%3600)%60))}s",f"{round(UE_totaltime[10]//3600)}u {round((UE_totaltime[10]%3600)//60)}m {round(((UE_totaltime[10]%3600)%60))}s" ])
    plt.vlines(6, 0,UE_totaltime[5] , linestyles='dotted', color="black")
    plt.vlines(11, 0,UE_totaltime[10] , linestyles='dotted', color="black")
    plt.hlines(UE_totaltime[5], 0, 6, linestyles='dotted', color="black")
    plt.hlines(UE_totaltime[10], 0, 11, linestyles='dotted', color="black")
    plt.xlim(3.5, 15)
    plt.ylim(1.912*1e7,1.923*1e7)
    plt.show()
    plt.close()

    #plotten wat er gemiddeld qua flow aan het extra pad wordt toegekend (staat niet in het verslag)
    k = k[:-1] #probleem met waarden laatste k waarde (paar laatste niet goed opgeslagen)
    UE = UE[:-1]
    SE = SE[:-1]
    diff = []
    UE_used = [0 for i in range(len(UE))]
    SE_used = [0 for i in range(len(SE))]
    for i in range(len(UE)):
        curr_UE = UE[i]
        curr_SE = SE[i]
        curr_diff = np.zeros((len(curr_UE)))
        for j, OD in enumerate(curr_UE):
            UE_used[i] += curr_UE[OD][i][0]/len(curr_UE)
            curr_diff[j] = (curr_UE[OD][i][2]-curr_UE[OD][0][2])/curr_UE[OD][0][2]
        for OD in curr_SE:
            SE_used[i] += curr_SE[OD][i][0]/len(curr_SE)
        diff.append((np.mean(curr_diff), np.std(curr_diff)))
    print('gemiddeld percentage extra reistijd (ta0) van extra route ivm snelste')
    for i in range(len(diff)):
        print(f"{i}: mean -> {diff[i][0]}% and standaardafwijking -> {diff[i][1]}%")
        #voor makkelijk te kunnen kopiern
        print(f"{i} & {round(diff[i][0], 4)} & {round(diff[i][1], 4)}")
    plt.plot(k, UE_used)
    plt.plot(k, SE_used)
    plt.xlabel('k')
    plt.ylabel('flow')
    plt.title("gemiddelde flow toegekend aan extra pad")
    plt.legend(["UE", "SE"], loc='best')
    plt.ylim(0, 0.3)
    #plt.plot(k, UE_used)
    #plt.plot(k, SE_used)
    plt.xlabel('k$_\mathrm{10}$$^{de}$ snelste pad')
    plt.ylabel('verschil in reistijd')
    plt.title("gemiddelde verschil in reistijd met snelste pad")
    #plt.legend(["UE", "SE"], loc='best')
    #plt.ylim(0, 0.3)
    plt.show()


