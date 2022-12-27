# Simple sequantial run of knob values
from pprint import pprint

name = "CrowdNav-Seasonality"
execution_strategy = {
    "ignore_first_n_results": 10,  # SETTLING TIME
    # "sample_size": 60*24*7*4,
    # "sample_size": 60 * 24,  # how much eval steps we want. Eval is 30 secs in legoland
    "sample_size": 2 * 60 * 24 * 7,  # how much eval steps we want. Eval step is 30 secs in legoland
    "type": "seasonality",
    "knobs": [
        {
            "total_car_counter": 500,
            "car_counter_is_initial": True,

            'route_random_sigma': 0.18,
            'exploration_percentage': 0.21,
            'max_speed_and_length_factor': 1.95,
            'average_edge_duration_factor': 1.97,
            'freshness_update_factor': 14,
            'freshness_cut_off_value': 334,
            're_route_every_ticks': 57,
        },
    ]
}


def primary_data_reducer(state, newData, wf):
    # print(f"state: {state}")
    # print(f"newData: {newData}")
    cnt = state["count"]
    state["overheads"].append(newData["overhead"])
    state["avg_overhead"] = (state["avg_overhead"] * cnt + newData["overhead"]) / (cnt + 1)
    state["count"] = cnt + 1
    return state


def performance_data_reducer(state, newData, wf):
    cnt = state["duration_count"]
    state["duration_avg"] = (state["duration_avg"] * cnt + newData["duration"]) / (cnt + 1)
    state["duration_count"] = cnt + 1
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

kafkaTopicTick = "crowd-nav-tick_updates"


def ticks_data_reducer(state, newData, wf):
    # print(f"state: {state}")
    # print(f"newData: {newData}")
    state['ticks'].append(newData['tick'])
    state['traffic_volumes'].append(newData['traffic_volume'])
    state['traffic_targets'].append(newData['traffic_target'])
    state['smart_average_speeds_a'].append(newData['smart_average_speed_a'])
    state['smart_average_speeds_h'].append(newData['smart_average_speed_h'])
    state['average_speeds_h'].append(newData['average_speed_h'])
    state['average_speeds_a'].append(newData['average_speed_a'])
    return state


secondary_data_providers = [
    {
        "type": "kafka_consumer",
        "kafka_uri": "localhost:9092",
        "topic": kafkaTopicTick,
        "serializer": "JSON",
        "data_reducer": ticks_data_reducer
    }
]


def evaluator(resultState, wf):
    """Function to evaluate goodness of the knobs in the experiment
    Not applicable for seasonality strategy # TODO: Augustin maybe we will want to use it somehow
    """
    return 1
    # return resultState["avg_overhead"]


def state_initializer(state, wf):
    state["count"] = 0
    state["avg_overhead"] = 0
    # We flood our memory with arrays data
    state["overheads"] = []
    state['ticks'] = []
    state['traffic_volumes'] = []
    state['traffic_targets'] = []
    state['smart_average_speeds_a'] = []
    state['smart_average_speeds_h'] = []
    state['average_speeds_h'] = []
    state['average_speeds_a'] = []
    return state
