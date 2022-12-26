# TODO(seasonality): Implement logic here ??
"""
We will have 1 experiment with will run for a long time with all the options
OR
We can have multiple experiments FOR EACH time step (e.g. we run 24 experiments with simulate 1 days in total)
I would suggest going to the second as it is easier to integrate
"""
from pprint import pprint

from colorama import Fore

from rtxlib import info, error
from rtxlib.execution import experimentFunction
from rtxlib.trafficprovider.TrafficParser import TrafficGenerator

import matplotlib.pyplot as plt

def start_seasonality_strategy(wf):
    """ executes all experiments from the definition file """
    info("> ExecStrategy   | Seasonality", Fore.CYAN)
    wf.totalExperiments = len(wf.execution_strategy["knobs"])
    info(f"Total experiments: {wf.totalExperiments}")
    sample_size = wf.execution_strategy["sample_size"]
    warmup_size = wf.execution_strategy["ignore_first_n_results"]
    if "total_car_counter" not in wf.execution_strategy["knobs"]:
        wf.execution_strategy["knobs"]["total_car_counter"] = 600
        pop_size = wf.execution_strategy["knobs"]["total_car_counter"]
    pop_size = wf.execution_strategy["knobs"]["total_car_counter"]
    kn = wf.execution_strategy["knobs"]
    #Warm-Up
    res = experimentFunction(wf, {
        "knobs": kn,
        "ignore_first_n_results": warmup_size,
        "sample_size": 2*warmup_size,
    })
    res = experimentFunction(wf, {
        "knobs": kn,
        "ignore_first_n_results": warmup_size,
        "sample_size": sample_size,},
        TrafficGenerator(pop_size,minute_in_step=15,time_scale = 1/15)
        )