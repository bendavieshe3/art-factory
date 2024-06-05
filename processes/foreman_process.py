import os
import sys

# Ensure the shared module can be imported
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)
from shared.work import perform_foreman_task

if __name__ == "__main__":
    perform_foreman_task()
