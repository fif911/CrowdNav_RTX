# Simple sequantial run of knob values
name = "CrowdNav-Seasonality"

execution_strategy = {
    "ignore_first_n_results": 10,  # TODO(seasonality): THIS IS OUR SETTING TIME (car_migration_ticks_amount)
    "sample_size": 100,  # TODO(seasonality): THIS IS OUR LENGTH OF AN HOUR. SHOULD BE CONVERTED TO TICKS TIME
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
        {"total_car_counter": 800,
         "car_counter_is_initial": True,
         "car_migration_ticks_amount": 500,  # e.g. setting time. pass it to CrowdNav so we can adjust our
         # increase/decrease algorithm
         },
        {"total_car_counter": 400,
         "car_counter_is_initial": False},
        {"total_car_counter": 1500,
         "car_counter_is_initial": False},
        {"total_car_counter": 100,
         "car_counter_is_initial": False},
        {"total_car_counter": 2000,
         "car_counter_is_initial": False}
    ]
}


def primary_data_reducer(state, newData, wf):
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

secondary_data_providers = [
    {
        "type": "kafka_consumer",
        "kafka_uri": "localhost:9092",
        "topic": kafkaTopicTick,
        "serializer": "JSON",
        "data_reducer": lambda x, y, z: x
    }
]


def evaluator(resultState, wf):
    return resultState["avg_overhead"]


def state_initializer(state, wf):
    state["count"] = 0
    state["avg_overhead"] = 0
    return state
