
import random

def sample_network_delay(agent_id) -> int:
    """Simulates network delay in microseconds."""
    return random.randint(100, 1000)
