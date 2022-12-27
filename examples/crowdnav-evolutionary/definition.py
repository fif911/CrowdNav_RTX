"""
Evolutionary search for knob values

By far these are the best values for Router for 500 cars we were able to get:
    'route_random_sigma': 0.23,
    'exploration_percentage': 0.17,
    'max_speed_and_length_factor': 1.95,
    'average_edge_duration_factor': 1.36,
    'freshness_update_factor': 16,
    'freshness_cut_off_value': 696,
    're_route_every_ticks': 54
"""
name = "CrowdNav-Evolutionary"

execution_strategy = {
    "parallel_execution_of_individuals": False,  # if this is True,
    # CrowdNav should be run with 'python parallel.py <no>'
    "ignore_first_n_results": 50,  # 10000,
    "sample_size": 200,  # 10000,
    "type": "evolutionary",
    "optimizer_method": "GA",
    "optimizer_iterations": 10,  # number of generations
    "population_size": 5,  # number of individuals in the population
    "crossover_probability": 0.5,
    "mutation_probability": 0.2,
    "knobs": {
        "route_random_sigma": (0.0, 0.3),
        "exploration_percentage": (0.0, 0.3),
        "max_speed_and_length_factor": (1, 2.5),
        "average_edge_duration_factor": (1, 2.5),
        "freshness_update_factor": (5, 20),
        "freshness_cut_off_value": (100, 700),
        "re_route_every_ticks": (10, 70)
    }
}


def primary_data_reducer(state, newData, wf):
    cnt = state["count"]
    state["avg_overhead"] = (state["avg_overhead"] * cnt + newData["overhead"]) / (cnt + 1)
    state["count"] = cnt + 1
    return state


primary_data_provider = {
    "type": "kafka_consumer",
    "kafka_uri": "localhost:9092",
    "topic": "crowd-nav-trips",
    "serializer": "JSON",
    "data_reducer": primary_data_reducer
}

change_provider = {
    "type": "kafka_producer",
    "kafka_uri": "localhost:9092",
    "topic": "crowd-nav-commands",
    "serializer": "JSON",
}


# defines what the experimentFunction returns
def evaluator(resultState, wf):
    # avg overhead computed by primary_data_reducer
    return resultState["avg_overhead"]


def state_initializer(state, wf):
    state["count"] = 0
    state["avg_overhead"] = 0
    return state
