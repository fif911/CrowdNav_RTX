"""
Crowd Nav Seasonality simulation
"""

name = "CrowdNav-Seasonality"
execution_strategy = {
    "ignore_first_n_results": 10,  # SETTLING TIME
    "sample_size": 2 * 60 * 24,  # how much eval steps we want. Eval step is 30 secs in legoland
    "type": "seasonality",
    "knobs": [
        {
            "total_car_counter": 500,
            "car_counter_is_initial": True,

            # Uses the latest version of knobs from Evolutionary strategy for 500 cars
            'route_random_sigma': 0.23,
            'exploration_percentage': 0.17,
            'max_speed_and_length_factor': 1.95,
            'average_edge_duration_factor': 1.36,
            'freshness_update_factor': 16,
            'freshness_cut_off_value': 696,
            're_route_every_ticks': 54
        },
    ]
}


def primary_data_reducer(state, newData, wf):
    """Processes data sent when smart car arrives"""
    cnt = state["count"]
    state["overheads"].append(newData["overhead"])
    state["avg_overhead"] = (state["avg_overhead"] * cnt + newData["overhead"]) / (cnt + 1)
    state["count"] = cnt + 1
    return state


def ticks_data_reducer(state, newData, wf):
    """Processes data sent on every evaluation (30 ticks in CrowdNav by default)"""
    state['ticks'].append(newData['tick'])
    state['traffic_volumes'].append(newData['traffic_volume'])
    state['traffic_targets'].append(newData['traffic_target'])
    state['smart_average_speeds_a'].append(newData['smart_average_speed_a'])
    state['smart_average_speeds_h'].append(newData['smart_average_speed_h'])
    state['average_speeds_h'].append(newData['average_speed_h'])
    state['average_speeds_a'].append(newData['average_speed_a'])
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
    """Function to evaluate goodness of the knobs in the experiment"""
    return resultState["avg_overhead"]


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
