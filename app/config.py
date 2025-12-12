import os
import random

def get_config():
    process_id = os.getenv("PROCESS_ID")
    if not process_id:
        hostname = os.getenv("HOSTNAME", "q1-app-0")
        try:
            process_id = hostname.split("-")[-1]
        except Exception:
            process_id = "0"

    peers_raw = os.getenv("PEERS", "")
    peers = [p.strip() for p in peers_raw.split(",") if p.strip()]

    delay_message_id = os.getenv("DELAY_MESSAGE_ID", "")
    delay_ms = int(os.getenv("DELAY_MS", "0"))
    initial_clock = int(os.getenv("INITIAL_CLOCK", str(random.randint(0, 10))))
    num_processes = int(os.getenv("NUM_PROCESSES", "3"))

    return {
        "process_id": process_id,
        "peers": peers,
        "delay_message_id": delay_message_id,
        "delay_ms": delay_ms,
        "initial_clock": initial_clock,
        "num_processes": num_processes,
    }
