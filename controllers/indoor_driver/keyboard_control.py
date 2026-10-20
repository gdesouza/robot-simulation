"""Manual policy. Replace this policy with autonomous commands in the future."""
def wheel_commands(keys, keyboard, maximum):
    if ord(' ') in keys:
        return 0.0, 0.0
    forward = bool(keys & {ord('W'), ord('w'), keyboard.UP})
    reverse = bool(keys & {ord('S'), ord('s'), keyboard.DOWN})
    left = bool(keys & {ord('A'), ord('a'), keyboard.LEFT})
    right = bool(keys & {ord('D'), ord('d'), keyboard.RIGHT})
    drive = int(forward) - int(reverse)
    turn = 0.65 * (int(left) - int(right))
    a, b = drive - turn, drive + turn
    scale = maximum / max(1.0, abs(a), abs(b))
    return a * scale, b * scale


def read_keys(keyboard):
    keys = set()
    while (key := keyboard.getKey()) != -1:
        keys.add(key & keyboard.KEY)
    return keys
