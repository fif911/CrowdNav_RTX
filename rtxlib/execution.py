import copy

from rtxlib import info, error, warn, direct_print, process, log_results, current_milli_time


def _defaultChangeProvider(variables, wf):
    """ by default we just forword the message to the change provider """
    return variables


def warmup(wf, exp):
    """ignore the first data sets"""
    to_ignore = exp["ignore_first_n_results"]
    if to_ignore > 0:
        i = 0
        while i < to_ignore:
            new_data = wf.primary_data_provider["instance"].returnData()
            if new_data is not None:
                i += 1
                process("IgnoreSamples  | ", i, to_ignore)
        print("")
    # print("Ignoring finished. Started to collect data")


def initExperiment(wf, exp):
    """Load change event creator or use a default"""
    change_creator = _defaultChangeProvider
    if hasattr(wf, "change_event_creator"): change_creator = change_creator

    # start
    info("Experiment started>")
    info("> KnobValues for this experiment     | " + str(exp["knobs"]))
    info(f"Change creator: {change_creator(exp['knobs'], wf)}")
    # create new state
    exp["state"] = wf.state_initializer(dict(), wf)

    # apply changes to system
    try:
        wf.change_provider["instance"].applyChange(change_creator(exp["knobs"], wf))
    except:
        error("apply changes did not work")


def primaryUpdate(wf, exp, blocking=False):
    """we start with the primary data provider using blocking returnData"""
    if blocking:
        new_data = wf.primary_data_provider["instance"].returnData()
    else:
        new_data = wf.primary_data_provider["instance"].returnDataListNonBlocking()
        new_data = new_data[0] if new_data else None
    if new_data:
        try:
            exp["state"] = wf.primary_data_provider["data_reducer"](exp["state"], new_data, wf)
        except StopIteration:
            raise StopIteration()  # just fwd
        except RuntimeError:
            raise RuntimeError()  # just fwd
        except Exception as e:
            raise e
            error("could not reducing data set: " + str(new_data))
        return


def trafficUpdate(wf, exp, tgen, new_data):
    """Compose message for CrowdNav to update traffic volume and send it"""
    c_tick = new_data['tick']
    if tgen.base_tick is None:
        tgen.base_tick = c_tick
    traffic_volume = tgen(c_tick - tgen.base_tick)
    msg = {
        "total_car_counter": traffic_volume,
        "car_counter_is_initial": False
    }
    try:
        wf.change_provider["instance"].applyChange(msg)  # message to kafka
    except:
        error("apply changes did not work")


def secondaryUpdate(wf, exp, tgen):
    """Receive the data data from secondary_data_providers and process it"""
    for cp in wf.secondary_data_providers:
        # If message sent from CrowdNav in tick_updates topic - it's time for another evaluation step
        if tgen is not None and cp["topic"] == "crowd-nav-tick_updates":
            new_data = cp["instance"].returnData()
            if new_data:
                trafficUpdate(wf, exp, tgen, new_data)
                new_data = [new_data]
            else:
                print("Missing Data")
                new_data = []
        else:
            new_data = cp["instance"].returnDataListNonBlocking()
        for nd in new_data:
            try:
                exp["state"] = cp["data_reducer"](exp["state"], nd, wf)
            except StopIteration:
                raise StopIteration()  # just
            except RuntimeError:
                raise RuntimeError()  # just fwd
            except:
                error("could not reducing data set: " + str(nd))


def logResults(wf, exp, start_time, result):
    """Log the counter of this experiment in the workflow and log results to files"""
    if hasattr(wf, "experimentCounter"):
        wf.experimentCounter += 1
    else:
        wf.experimentCounter = 1
    # print the results
    duration = current_milli_time() - start_time
    # do not show stats for forever strategy
    if wf.totalExperiments > 0:
        info("> Statistics     | " + str(wf.experimentCounter) + "/" + str(wf.totalExperiments)
             + " took " + str(duration) + "ms" + " - remaining ~" + str(
            (wf.totalExperiments - wf.experimentCounter) * duration / 1000) + "sec")
    info("> FullState      | " + str(exp["state"]))
    info("> ResultValue    | " + str(result))

    # log the result values into a csv file
    # prepare for logging
    seasonality_details_plot: dict = copy.deepcopy(exp["state"])
    del seasonality_details_plot['count']
    del seasonality_details_plot['avg_overhead']
    seasonality_details_plot.pop('overheads', None)  # not the size of other arrays !!!

    # log seasonality_details.csv
    if seasonality_details_plot:  # check if there is relevant data to plot
        log_results(wf.folder, list(seasonality_details_plot.keys()), csv_name="seasonality_details.csv", append=False)
        for d in zip(*seasonality_details_plot.values()):
            log_results(wf.folder, d, csv_name="seasonality_details.csv", append=True)

    # log results.csv
    log_results(wf.folder, list(exp["knobs"].values()) + [result], append=True)


def experimentFunction(wf, exp, tgen=None):
    """ executes a given experiment="""
    start_time = current_milli_time()
    wf.primary_data_provider["instance"].reset()  # remove all old data from the queues
    initExperiment(wf, exp)
    warmup(wf, exp)
    sample_size = exp["sample_size"]
    i = 0
    try:
        # print("Before collecting samples")
        while i < sample_size:
            primaryUpdate(wf, exp, tgen is None)
            i += 1
            if i % 10 == 0:
                print(
                    f"Progress: {i} out of {sample_size}")  # as collect samples progress bar does not work for me |_o_|
            process("CollectSamples | ", i, sample_size, start=start_time)
            # now we use returnDataListNonBlocking on all secondary data providers
            if hasattr(wf, "secondary_data_providers"):
                secondaryUpdate(wf, exp, tgen)
            # if tgen is not None:
            #    trafficUpdate(wf,exp,tgen)
        print("")
    except StopIteration:
        # this iteration should stop asap
        error("This experiment got stopped as requested by a StopIteration exception")
    try:
        result = wf.evaluator(exp["state"], wf)
    except Exception as e:
        print(e)
        result = 0
        error("evaluator failed")
    logResults(wf, exp, start_time, result)
    # return the result value of the evaluator
    return result
