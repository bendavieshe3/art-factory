# Standard Library
import os
import sys

# Ensure the shared module can be imported
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

# First Party
from shared.work import perform_worker_task

if __name__ == "__main__":
    perform_worker_task()
