import time

def get_current_time_milli():
    return int(round(time.time() * 10000))

def debouncer(callback, throttle_time_limit=1000):

    last_millis = get_current_time_milli()  

    def throttle():
        nonlocal last_millis
        curr_millis = get_current_time_milli()
        print("Throttle Called.................", curr_millis, last_millis, throttle_time_limit)
        if (curr_millis - last_millis) > throttle_time_limit:
            last_millis = get_current_time_milli()
            callback()

    return throttle    


def slugify(text: str):
    return text.lower().replace(" ", "_")
