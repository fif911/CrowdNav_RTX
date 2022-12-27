"""
Seasonality strategy

Runs experiments in Knobs (default 1) for set number of sample_size
Gathers data in 2 CSVs and saves them to examples/crowdnav-seasonality/ folder
"""

from colorama import Fore

from rtxlib import info, current_milli_time
from rtxlib.execution import experimentFunction
from rtxlib.trafficprovider.TrafficParser import TrafficGenerator


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
            TrafficGenerator(car_counter, minute_in_step=15,
                             rescale_time=1 / (60 * 15))
        )
        print(
            f"Experiment took: {(current_milli_time() - exp_start_timestamp) / 1000 / 60} minutes")
