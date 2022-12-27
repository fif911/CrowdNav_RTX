# TODO(seasonality): Implement logic here ??
"""
We will have 1 experiment with will run for a long time with all the options
OR
We can have multiple experiments FOR EACH time step (e.g. we run 24 experiments with simulate 1 days in total)
I would suggest going to the second as it is easier to integrate
"""

from colorama import Fore

from rtxlib import info, error, current_milli_time
from rtxlib.execution import experimentFunction
from rtxlib.trafficprovider.TrafficParser import TrafficGenerator

import matplotlib.pyplot as plt


def start_seasonality_strategy(wf):
    """ Seasonality strategy

    executes all experiments from the definition file """
    info("> ExecStrategy   | Seasonality", Fore.CYAN)
    wf.totalExperiments = len(wf.execution_strategy["knobs"])
    info(f"Total experiments: {wf.totalExperiments}")
    sample_size = wf.execution_strategy["sample_size"]
    warmup_size = wf.execution_strategy["ignore_first_n_results"]
    for knobset in wf.execution_strategy["knobs"]:
        if "total_car_counter" not in knobset:
            knobset["total_car_counter"] = 600  # set default
        car_counter = knobset["total_car_counter"]
        exp_start_timestamp = current_milli_time()
        experimentFunction(
            wf,
            {
                "knobs": knobset,
                "ignore_first_n_results": warmup_size,
                "sample_size": sample_size,
            },
            TrafficGenerator(car_counter, minute_in_step=15, rescale_time=1 / (60 * 15))
        )
        print(f"Experiment took: {(current_milli_time() - exp_start_timestamp)/1000/60} minutes")
