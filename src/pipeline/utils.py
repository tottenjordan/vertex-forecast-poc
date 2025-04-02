def format_state(state):
    if state in ['PIPELINE_STATE_SUCCEEDED', 'SUCCEEDED']:
        return f'\033[92m[{state}]\x1b[0m'
    if state in ['PIPELINE_STATE_RUNNING', 'PENDING', 'RUNNING']:
        return f'\033[94m[{state}]\x1b[0m'
    return f'\033[91m[{state}]\x1b[0m'