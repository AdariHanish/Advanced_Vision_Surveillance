import time
import math

loiter_start_time = {}

LOITER_THRESHOLD = 5  # seconds
RUN_THRESHOLD = 50    # pixel distance


def check_loiter(person_id):
    current_time = time.time()

    if person_id not in loiter_start_time:
        loiter_start_time[person_id] = current_time
        return False

    if current_time - loiter_start_time[person_id] > LOITER_THRESHOLD:
        return True

    return False


def check_running(previous_center, current_center):
    distance = math.sqrt(
        (current_center[0] - previous_center[0]) ** 2 +
        (current_center[1] - previous_center[1]) ** 2
    )

    if distance > RUN_THRESHOLD:
        return True

    return False