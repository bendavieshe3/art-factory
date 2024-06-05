import os
import sys

from shared.work import perform_worker_task

# Ensure the shared module can be imported
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

if __name__ == "__main__":
    perform_worker_task()
