import time

def benchmark(func):
    '''
    Prints `func` name and its benchmark time.
    '''
    def wrapped(*args, **kwargs):
        start = time.perf_counter()
        value = func(*args, **kwargs)
        end = time.perf_counter()
        elapsed = round(end-start, 2)
        print(f'{func.__name__} Completion Time: {elapsed}')
        return value
    return wrapped
