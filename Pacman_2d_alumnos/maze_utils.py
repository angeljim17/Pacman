import math


ANGLE_TO_VECTOR = {
    0.0: (1.0, 0.0),
    90.0: (0.0, 1.0),
    180.0: (-1.0, 0.0),
    270.0: (0.0, -1.0),
}


def angle_to_vector(angle):
    return ANGLE_TO_VECTOR.get(float(angle) % 360.0, (1.0, 0.0))


def find_middle_tunnel_rows(mapa):
    rows, _ = mapa.shape
    open_rows = [r for r in range(rows) if mapa[r, 0] == 0 and mapa[r, -1] == 0]
    if not open_rows:
        return tuple()

    groups = []
    start = prev = open_rows[0]
    for row in open_rows[1:]:
        if row == prev + 1:
            prev = row
            continue
        groups.append((start, prev))
        start = prev = row
    groups.append((start, prev))

    mid_row = (rows - 1) * 0.5
    best_start, best_end = min(groups, key=lambda item: abs(((item[0] + item[1]) * 0.5) - mid_row))
    return tuple(range(best_start, best_end + 1))


def shortest_wrapped_delta(delta, period):
    if period <= 0:
        return delta
    if abs(delta) <= period * 0.5:
        return delta
    return delta - math.copysign(period, delta)
