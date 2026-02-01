import time

def retry(func, retries=3, delay=0.3):
    for i in range(retries):
        try:
            if callable(func):
                return func()
            return func
        except Exception as e:
            if i == retries - 1:
                raise e
            time.sleep(delay)