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


# _______________________________________КОНСТАНТЫ ГЕНЕТИЧЕСКОГО АЛГОРИТМА
MAX_GENERATIONS = 20    # максимальное количество поколений
ONE_MAX_LENGTH = 400    #длина одного экземпляра соответсвующей 2 секундам работы
POPULATION_SIZE = 3   # количество индивидуумов в популяции
P_CROSSOVER = 0.9       # вероятность скрещивания
P_MUTATION = 0.1        # вероятность мутации индивидуума
t = 0.01                # временной шаг
generationCounter = 0   # счетчик поколений


#_______________________________________рабочий файл в PSCAD
file_path = os.path.abspath('') + "\\"  
file_name = 'Dtl_VSM_T'



#_______________________________________КЛАССЫ ЗАДАЧИ
    #класс индивидуум, содержащий 
class Individual(list):
    def __init__(self, *args):
        super().__init__(*args)
        self.fitness = FitnessMin()

    #класс оценок индивидуумов
class FitnessMin():
    def __init__(self):
        self.values = [0]



#_______________________________________ФУНКЦИИ ЗАДАЧИ
    #создание отдельного индивидуума
def individualCreator():
    return Individual([random.randint(2, 24) for i in range(ONE_MAX_LENGTH)])
    
    #клонирование индивидуума
def clone(value):
    ind = Individual(value[:])
    ind.fitness.values[0] = value.fitness.values[0]
    return ind

    #турнирный отбор 3х самых лучших экземпляров
def selTournament(population, p_len):
    offspring = []
    for n in range(p_len):
        i1 = i2 = i3 = 0
        while i1 == i2 or i1 == i3 or i2 == i3:
            i1, i2, i3 = random.randint(0, p_len-1), random.randint(0, p_len-1), random.randint(0, p_len-1)
        offspring.append(min([population[i1], population[i2], population[i3]], key=lambda ind: ind.fitness.values[0]))
    return offspring

    #одноточечный кроссинговер
def cxOnePoint(child1, child2):
    s = random.randint(2, len(child1)-3)
    child1[s:], child2[s:] = child2[s:], child1[s:]
   
    #мутации отдельного гена (нужно переписать так как тут инверсия битов происходит)
def mutFlipBit(mutant, indpb=0.01):
    for indx in range(len(mutant)):
        if random.random() < indpb:
            mutant[indx] == random.randint(2, 24)

    #создание популяции индивидуумов
def populationCreator(n = 0):
    return list([individualCreator() for i in range(n)])
                
    #функция расчета интегралла 
def oneMinFitness(individual):
    individual = [abs(t*((1 - a) + (1 - b)))/2 for a, b in zip(frequencyVSG[1:], frequencyVSG)]
    return sum(individual)



#_______________________________________НАЧАЛО РАБОТЫ
    #создание популяции при призыве функции + счетчик поколений
population = populationCreator(n=POPULATION_SIZE)
    
    #переменные для статичстики
minFitnessValues = []
meanFitnessValues = []



            #____________________________________ОСНОВНОЙ ГЕНЕТИЧЕСКИЙ АЛГОРИТМ____________________________________

    #___________________________________________________РАСЧЕТ "ПОКОЛЕНИЯ"__________________________________________________
while  generationCounter < MAX_GENERATIONS:                 #min(fitnessValues) > 0 and
    generationCounter += 1
   
        #_____________________РАСЧЕТ "ИНДИВИДУУМЫ"_____________________
    for i in range(POPULATION_SIZE):
        
            #подгрузка значений в PSCAD
        individual = population[i]

        with open("hello.txt", "w") as file:
            for z in range(len(individual)):         # Проходим по каждому элементу списка и записываем в файл
                file.write(f"{individual[z]}\n")     # Преобразуем число в строку и добавляем перевод строки

            #запуск PSCAD
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

            #расчет приспособленности (нужно ее ставить тогда, когда посчитаны все индивидуумы или после каждого расчета PSCAD)
        fitnessValues = list(map(oneMinFitness, population[i]))
        #_____________________РАСЧЕТ "ИНДИВИДУУМЫ"_____________________


        #соединение двух списков. В популяции каждому индивуидууму присуждается оценка.
    for individual, fitnessValue in zip(population, fitnessValues):
        individual.fitness.values = fitnessValue

        #спсиок приспособленностей 
    fitnessValues = [ind.fitness.values[0] for ind in population]


        #проведение турнироного отбора
    offspring = selTournament(population, len(population))
    offspring = list(map(clone, offspring))

        #создание детей от четных и нечетных родителей
    for child1, child2 in zip(offspring[::2], offspring[1::2]):
        if random.random() < P_CROSSOVER:
            cxOnePoint(child1, child2)

        #мутация отдельных генов
    for mutant in offspring:
        if random.random() < P_MUTATION:
            mutFlipBit(mutant, indpb=1.0/ONE_MAX_LENGTH)

        #обновление оценок для оффспринг
    freshFitnessValues = list(map(oneMinFitness, offspring))
    for individual, fitnessValue in zip(offspring, freshFitnessValues):
        individual.fitness.values = fitnessValue
        
        #перерасчет оценок для популяции
    fitnessValues = [ind.fitness.values[0] for ind in population]

        #присуждение популяции списка оффспринг
    population[:] = offspring

        #ведем статистику
    minFitness = min(fitnessValues)
    meanFitness = sum(fitnessValues) / len(population)
    minFitnessValues.append(minFitness)
    meanFitnessValues.append(meanFitness)
    print(f"Поколение {generationCounter}: Макс приспособ. = {minFitness}, Средняя приспособ.= {meanFitness}")

    best_index = fitnessValues.index(min(fitnessValues))
    print("Лучший индивидуум = ", *population[best_index], "\n")
    #___________________________________________________РАСЧЕТ "ПОКОЛЕНИЯ"__________________________________________________


plt.plot(minFitnessValues, color='red')
plt.plot(meanFitnessValues, color='green')
plt.xlabel('Поколение')
plt.ylabel('Макс/средняя приспособленность')
plt.title('Зависимость максимальной и средней приспособленности от поколения')
plt.show()  