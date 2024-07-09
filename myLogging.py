import queue
import threading
import time
logQueue = queue.Queue()
logLock = threading.Lock()
def log():
    while True:
        while not logQueue.empty():
            print(logQueue.get())
            logQueue.task_done()
        time.sleep(0.1)
