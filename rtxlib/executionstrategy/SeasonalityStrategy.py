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

    # knob gener
    # tg = TrafficGenerator(0)
    tg = TrafficGenerator(600, minute_in_step = 15, rescale_time = 1/(30*15))

    wf.secondary_data_providers[0]['instance'].reset()
    new_data = wf.secondary_data_providers[0]["instance"].returnData()
    base_tick = new_data['tick']

    dates = []
    targets = []
    reals = []
    plt.ion()
    while True:
        # read kafka
        wf.secondary_data_providers[0]['instance'].reset()
        new_data = wf.secondary_data_providers[0]["instance"].returnData()
        print(new_data)

        tick,target,real = (new_data[field]
                            for field
                            in ["tick","traffic_target","traffic_volume"])
        dates.append(tg.date(tick))
        targets.append(target)
        reals.append(real)
        plt.plot(dates, target)
        plt.plot(dates, real)
        plt.draw()

        c_tick = new_data['tick']
        traffic_volume = tg(c_tick-base_tick)

        msg = {
            "total_car_counter": traffic_volume,
            "car_counter_is_initial": False
        }

        # apply changes to system
        try:
            wf.change_provider["instance"].applyChange(msg)
        except:
            error("apply changes did not work")

        # for exp_num, kn in enumerate(wf.execution_strategy["knobs"]):
        #     info(f"Total experiments: {wf.totalExperiments}")
        #     info(f"Running experiment: {exp_num + 1}/{wf.totalExperiments}")
        #     print("Setting for current experiment:")
        #     pprint(kn)
        # res = experimentFunction(wf, {
        #     "knobs": kn,
        #     "ignore_first_n_results": wf.execution_strategy["ignore_first_n_results"],
        #     "sample_size": wf.execution_strategy["sample_size"],
        # })