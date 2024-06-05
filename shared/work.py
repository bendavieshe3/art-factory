# shared/work.py
def get_test_message():
    return "This is a test message from shared code."


def perform_worker_task():
    message = get_test_message()
    print(f"Worker task: {message}")


def perform_foreman_task():
    print("Foreman task started.")
    # Implement the foreman task logic here
    print("Foreman task completed.")
