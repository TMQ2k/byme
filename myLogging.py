import queue
import threading
import time
logQueue = queue.Queue()
logLock = threading.Lock()
logEvent = threading.Event()

printLock = threading.Lock()
def log():
    while not logEvent.set():
        try:
            while not logQueue.empty() and not logEvent.set():
                with printLock:
                    msg = logQueue.get()
                    if type(msg) is not tuple:
                        print(msg)
                    else:
                        print(msg[0], end=msg[1])
                logQueue.task_done()
        except Exception:
            break
        time.sleep(0.1)

def wait():
    while printLock.locked():
        time.sleep(0.01)
    printLock.acquire()
