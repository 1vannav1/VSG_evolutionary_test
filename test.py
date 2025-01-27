#Чтобы работала программа нужно разделить 2 цикла
#один цикл глобальный, который считает программу для каждого индивидуума
#2 цикл должен подгружать индивидуума из популяции, его значения 
#смотри строка 91
from deap import base, algorithms
from deap import creator
from deap import tools

import mhi.pscad
import os
import matplotlib.pyplot as plt
import pandas as pd
import random
import numpy as np
from threading import Thread

# константы генетического алгоритма
MAX_GENERATIONS = 5     # максимальное количество поколений
ONE_MAX_LENGTH = 400    #длина одного экземпляра соответсвующей 2 секундам работы
POPULATION_SIZE = 10    # количество индивидуумов в популяции
P_CROSSOVER = 0.9       # вероятность скрещивания
P_MUTATION = 0.1        # вероятность мутации индивидуума

#переменные определяющие рабочий файл в PSCAD
file_path = os.path.abspath('') + "\\"  
file_name = 'Dtl_VSM_T'





#___________________________________________________________________________________________________________________________________________#
#ГЛОБАЛЬНЫЙ ЦИКЛ
for i in range(MAX_GENERATIONS*POPULATION_SIZE):
    with mhi.pscad.application() as pscad:                          
        pscad.load(file_path + file_name + '.pscx')
        dtl_vsm_t = pscad.project(file_name)
        dtl_vsm_t.parameters(time_duration="10.0")
        dtl_vsm_t.parameters(PlotType="1", output_filename="H_VSM%s" %(i))
        dtl_vsm_t.run()

#Чтение файлов загруженных после расчета
        temp = pd.read_csv(file_path + file_name + '.gf81\\' + 'H_VSM%s_05.out'%(i), delimiter='\s+', header=None, index_col=None,skiprows=1) 
        frequencyVSG = temp.iloc[601:,7]
        frequencyVSG = list(frequencyVSG)
        time = temp.iloc[601:,0]
        time = list(time)

    #________________________________________________________________________________________________________________________________________#
    # ГЕНЕТИЧЕСКИЙ АЛГОРИТМ: НАЧАЛО

    #Формирование генетического алгоритма 
    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))         #список Тj оперделяющая уменьшение суммы интегралла
    creator.create("Individual", list, fitness=creator.FitnessMin)      #Список индивидуума состоящий из тj


    #расчет приспособленности индивидуума
    def oneMinFitness(individual):
        individual = [abs(0.01*((1 - a) + (1 - b)))/2 for a, b in zip(frequencyVSG[1:], frequencyVSG)]
        return sum(individual), 

    toolbox = base.Toolbox()
    toolbox.register("randomTj", random.randint, 1, 20)
    toolbox.register("individualCreator", tools.initRepeat, creator.Individual, toolbox.randomTj, ONE_MAX_LENGTH)
    toolbox.register("populationCreator", tools.initRepeat, list, toolbox.individualCreator)

    population = toolbox.populationCreator(n=POPULATION_SIZE)

    toolbox.register("select", tools.selTournament, tournsize=3)
    toolbox.register("mate", tools.cxOnePoint)
    toolbox.register("mutate", tools.mutFlipBit, indpb=1.0/ONE_MAX_LENGTH)
    toolbox.register("evaluate", oneMinFitness)

    def select(population, n_pop):
        return population

    #сбор данных
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("max", np.max)
    stats.register("avg", np.mean)
    stats.register("values", np.array)

    #запускаем генетический алгоритм
    population, logbook = algorithms.eaSimple(population, toolbox,
                                            cxpb=P_CROSSOVER,
                                            mutpb=P_MUTATION,
                                            ngen=MAX_GENERATIONS,
                                            stats=stats,
                                            verbose=False)

    minFitnessValues, meanFitnessValues, vals = logbook.select("max", "avg", "values")

#ГЕНЕТИЧЕСКИЙ АЛГОРИТМ: КОНЕЦ
#___________________________________________________________________________________________________________________________________________#

# подгружаем данные в текстовый файл для чтения пискадом 
       
    f = 0
    n = 0
    
    if i <= 9:
        f = i
    else:
        n = i // 10 % 10
        f = i - n * 10

        individum = population[f]

        with open("hello.txt", "w") as file:
            for z in range(len(individum)):                 # Проходим по каждому элементу списка и записываем в файл
                file.write(f"{individum[z]}\n")  # Преобразуем число в строку и добавляем перевод строки
                
    plt.plot(minFitnessValues, color='red')
    plt.plot(meanFitnessValues, color='green')
    plt.xlabel('Поколение')
    plt.ylabel('Макс/средняя приспособленность')
    plt.title('Зависимость максимальной и средней приспособленности от поколения')

"""
plt.figure(1)
for i in range(MAX_GENERATIONS):
    temp = pd.read_csv(file_path + file_name + '.gf81\\' + 'H_VSM%s_05.out' %(i+1), delimiter='\s+', header=None, index_col=None,skiprows=1) #Чтение файлов загруженных после расчета
    frequencyVSG = temp.iloc[:,7]
    time = temp.iloc[:,0]
    plt.plot(time, frequencyVSG)
plt.show()
"""














