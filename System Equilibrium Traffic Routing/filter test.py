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
import pandas as pd

"""in deze file test ik wat er foor k_2 = 6 en k_10 = 6 gebeurt wanneer ik er een filter van 25% op zet, en hoeveel routes er dan worden genegeerd, en of het wel nog de moeite is dan om 
het door te voeren"""

k = [] #om tabel duidelijk te maken (bv. k_2_filtered)
nrroutes = [] #absoluut aantal routes
ue = [] #ue totale reistijd
se = [] #se totale reistijd
diff = [] # verschil tussen de twee
gemroutes = [] #gemiddeld aantal routes per OD paar

#Wanneer de k snelste paden worden berekend via factor= 2 met een filter van 25%
superlist, G = kFastestPaths.input_data("C:/Users/warre/PycharmProjects/VOP/OD_data/data/OD_Flows_1%.csv", "C:/Users/warre/PycharmProjects/VOP/OD_data/data/Graph.graphml", 6, 2, 25)
total = 0
gem = 0
for OD in superlist:
    total += len(OD[1])
    gem += len(OD[1])/len(superlist)
nrroutes.append(total)
gemroutes.append(gem)
uet, set = code_for_UEandSE.linearapproxEQ(G, superlist, 2000, "UE"), code_for_UEandSE.linearapproxEQ(G, superlist, 2000, "SE")
uett, sett = code_for_UEandSE.get_total_travel_time(uet, G), code_for_UEandSE.get_total_travel_time(set, G)
difft = uett-sett
ue.append(code_for_UEandSE.sec_to_str(uett))
se.append(code_for_UEandSE.sec_to_str(sett))
diff.append(code_for_UEandSE.sec_to_str(difft))
k.append("k2, filtered")

#Wanneer de k snelste paden worden berekend via factor= 2 zonder filter
superlist, G = kFastestPaths.input_data("C:/Users/warre/PycharmProjects/VOP/OD_data/data/OD_Flows_1%.csv", "C:/Users/warre/PycharmProjects/VOP/OD_data/data/Graph.graphml", 6, 2)
total = 0
gem = 0
for OD in superlist:
    total += len(OD[1])
    gem += len(OD[1])/len(superlist)
nrroutes.append(total)
gemroutes.append(gem)
uet, set = code_for_UEandSE.linearapproxEQ(G, superlist, 2000, "UE"), code_for_UEandSE.linearapproxEQ(G, superlist, 2000, "SE")
uett, sett = code_for_UEandSE.get_total_travel_time(uet, G), code_for_UEandSE.get_total_travel_time(set, G)
difft = uett-sett
ue.append(code_for_UEandSE.sec_to_str(uett))
se.append(code_for_UEandSE.sec_to_str(sett))
diff.append(code_for_UEandSE.sec_to_str(difft))
k.append("k2")

#Wanneer de k snelste paden worden berekend via factor=10 zonder filter
superlist, G = kFastestPaths.input_data("C:/Users/warre/PycharmProjects/VOP/OD_data/data/OD_Flows_1%.csv", "C:/Users/warre/PycharmProjects/VOP/OD_data/data/Graph.graphml", 6, 10)
total = 0
gem = 0
for OD in superlist:
    total += len(OD[1])
    gem += len(OD[1])/len(superlist)
nrroutes.append(total)
gemroutes.append(gem)
uet, set = code_for_UEandSE.linearapproxEQ(G, superlist, 2000, "UE"), code_for_UEandSE.linearapproxEQ(G, superlist, 2000, "SE")
uett, sett = code_for_UEandSE.get_total_travel_time(uet, G), code_for_UEandSE.get_total_travel_time(set, G)
difft = uett-sett
ue.append(code_for_UEandSE.sec_to_str(uett))
se.append(code_for_UEandSE.sec_to_str(sett))
diff.append(code_for_UEandSE.sec_to_str(difft))
k.append("k10")

#Wanneer de k snelste paden worden berekend via factor=10 met een filter van 25%
superlist, G = kFastestPaths.input_data("C:/Users/warre/PycharmProjects/VOP/OD_data/data/OD_Flows_1%.csv", "C:/Users/warre/PycharmProjects/VOP/OD_data/data/Graph.graphml", 6, 10, 25)
total = 0
gem = 0
for OD in superlist:
    total += len(OD[1])
    gem += len(OD[1])/len(superlist)
nrroutes.append(total)
gemroutes.append(gem)
uet, set = code_for_UEandSE.linearapproxEQ(G, superlist, 2000, "UE"), code_for_UEandSE.linearapproxEQ(G, superlist, 2000, "SE")
uett, sett = code_for_UEandSE.get_total_travel_time(uet, G), code_for_UEandSE.get_total_travel_time(set, G)
difft = uett-sett
ue.append(code_for_UEandSE.sec_to_str(uett))
se.append(code_for_UEandSE.sec_to_str(sett))
diff.append(code_for_UEandSE.sec_to_str(difft))
k.append("k10, filtered")


#uitprinten om het dan ook in het verslag te kunnen zetten
print(k)
print(nrroutes)
print(ue)
print(se)
print(diff)
print(gemroutes)
#tabel
df = pd.DataFrame({'k': k,
                   'nrroutes': nrroutes,
                   'ue': ue,
                   'se': se,
                   'diff': diff,
                   'gemroutes': gemroutes})
print(df)