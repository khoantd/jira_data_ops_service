

from status_cr import it_status_and_operation


def initiation_phase_accum(x):
    return x + 1


def analysis_phase_accum(x):
    return x + 1


def in_queue_dev_phase_accum(x):
    return x + 1


def in_dev_phase_accum(x):
    return x + 1


def uat_phase_accum(x):
    return x + 1


def hold_phase_accum(x):
    return x + 1


def done_phase_accum(x):
    return 1


def invalid_status(x):
    raise Exception("Invalid operation")

# The better way:


def perform_operation(x, chosen_operation="initiation_phase"):

    ops = {
        "initiation_phase": initiation_phase_accum,
        "analysis_phase": analysis_phase_accum,
        "in_queue_dev": in_queue_dev_phase_accum,
        "in_dev": in_dev_phase_accum,
        "uat": uat_phase_accum,
        "hold": hold_phase_accum,
        "done": done_phase_accum
    }

    chosen_operation_function = ops.get(chosen_operation, invalid_status)

    # print(chosen_operation_function)

    return chosen_operation_function(x)


# if __name__ == "__main___":
phase = it_status_and_operation("0. New/Open")
nbr = perform_operation(0, phase)
print("Hello")
print(nbr)
