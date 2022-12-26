# Simple sequantial run of knob values
from pprint import pprint

name = "CrowdNav-Seasonality"
execution_strategy = {
    "ignore_first_n_results": 10,  # SETTING TIME
    # "sample_size": 60*24*7*4,
    "sample_size": 2 * 60 * 24 * 7,  # how much eval steps we want. Eval is 30 secs in legoland
    "type": "seasonality",
    "knobs": [
        # {
        #     "total_car_counter": 0,
        #     "car_counter_is_initial": True
        # },
        # {
        #     "total_car_counter": 1,
        #     "car_counter_is_initial": False
        # },
        {"total_car_counter": 700,
         "car_counter_is_initial": True,
         },
        # "car_migration_ticks_amount": 500,  # e.g. setting time. pass it to CrowdNav so we can adjust our
        # increase/decrease algorithm
        # },
        # {"total_car_counter": 400,
        #  "car_counter_is_initial": False},
        # {"total_car_counter": 1500,
        #  "car_counter_is_initial": False},
        # {"total_car_counter": 100,
        #  "car_counter_is_initial": False},
        # {"total_car_counter": 2000,
        #  "car_counter_is_initial": False}
    ]
}


def primary_data_reducer(state, newData, wf):
    # print(f"state: {state}")
    # print(f"newData: {newData}")
    cnt = state["count"]
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
    state['average_speeds'].append(newData['smart_cars_average_speed'])
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
    return resultState["avg_overhead"]


def state_initializer(state, wf):
    state["count"] = 0
    state["avg_overhead"] = 0
    state['ticks'] = []
    state['traffic_volumes'] = []
    state['traffic_targets'] = []
    state['average_speeds'] = []
    return state
