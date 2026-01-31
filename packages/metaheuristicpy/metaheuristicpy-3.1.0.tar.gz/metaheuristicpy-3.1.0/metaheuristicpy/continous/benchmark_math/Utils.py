import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

class Utils:
    def __init__(self):
        pass
    
    def _plot_fitness(
        self, 
        list_fitness_values, 
        plot_configuration={
            "figsize": (10,8)
        }, 
        plot_description={
            'title': "List of Best Fitness Values",
            "x-axis": "Iteration",
            "y-axis": "Fitness"
        }):
        plt.figure(figsize=plot_configuration['figsize'])
        plt.plot(list_fitness_values)
        plt.title(plot_description['title'])
        plt.xlabel(plot_description['x-axis'])
        plt.ylabel(plot_description['y-axis'])
        plt.show()