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


def start_seasonality_strategy(wf):
    """ executes all experiments from the definition file """
    info("> ExecStrategy   | Seasonality", Fore.CYAN)
    wf.totalExperiments = len(wf.execution_strategy["knobs"])
    info(f"Total experiments: {wf.totalExperiments}")

    # knob gener


    for exp_num, kn in enumerate(wf.execution_strategy["knobs"]):
        info(f"Total experiments: {wf.totalExperiments}")
        info(f"Running experiment: {exp_num + 1}/{wf.totalExperiments}")
        print("Setting for current experiment:")
        pprint(kn)
        experimentFunction(wf, {
            "knobs": kn,
            "ignore_first_n_results": wf.execution_strategy["ignore_first_n_results"],
            "sample_size": wf.execution_strategy["sample_size"],
        })
