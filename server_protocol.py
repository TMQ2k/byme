import queue
# import socket
import threading
import os
import time
import signal
import myLogging
from messCore import *

# get server ip
SERVER_IP = socket.gethostbyname(socket.gethostname())
# setup server parameter
PORT = 5050
ADDR = (SERVER_IP, PORT)
# initialize server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)
server.listen()
# stop event
stop_event = threading.Event()


# get path
def read_list_file(filename):
    file_list = {}
    with open(filename, 'r') as f:
        for line in f:
            data = line.split(',')
            data[1] = data[1].strip("\n")
            file_list[data[0]] = data[1]
    return file_list


path = os.getcwd()  # path to the files
files = read_list_file("listOfFile.txt")  # list of files in the path
order_request = ["Critical", "High", "Normal"]  # order request list
# clients list
clients = []


def to_str(n, max_):
    str_n = str(n)
    return '0' * (max_ - len(str_n)) + str_n


def send_default_mes(client):
    send_data(client, "*Intro*")
    send_data(client, f"{len(files)}")
    for index, file in enumerate(files):
        filename = os.path.basename(file)
        msg = f"{filename}|{files[file]}"
        send_data(client, msg)


# send message to all current client when one client connected ???? =))))
def broadcast():
    for client in clients:
        send_default_mes(client)


# make_chunk_ function create chunk for sending
# the function read in a file in the form (file_name, pos) and the number of chunk to put on the queue
# return True if the file has not been fully read
# return False if the file has been fully read
def make_chunk_(file_name, chunks, chunk_data, number_of_chunk):
    data_max_len = MESS_LEN - 18 - 1 - 3
    filename = os.path.basename(file_name[0])
    filename = path + '\\' + filename

    count_chunk = 0
    with open(filename, "rb") as f:
        pos = file_name[1]
        f.seek(pos)
        file_data = f.read(data_max_len)
        data_len = len(file_data)
        while data_len == data_max_len and count_chunk < number_of_chunk:
            chunk_metadata = {
                # "filename": file_name[0],
                "size_of_chunk": to_str(data_len, 18),
                "end_file": 0  # False
            }
            chunks.put((file_data, chunk_metadata))
            file_data = f.read(data_max_len)
            data_len = len(file_data)
            count_chunk += 1

        if count_chunk < number_of_chunk or data_len < data_max_len:
            if data_len > 0:
                file_data = file_data + bytes('\0' * (data_max_len - data_len), FORMAT)
                chunk_metadata = {
                    # "filename": file_name[0],
                    "size_of_chunk": to_str(data_len, 18),
                    "end_file": 1  # True
                }
                chunks.put((file_data, chunk_metadata))
                # chunks.put((parse_message("EOF").encode(FORMAT), chunk_metadata))
                # chunks.put((parse_message(str(data_len)).encode(FORMAT), chunk_metadata))
                chunk_data.put([file_name[0], count_chunk + 1])
            else:
                chunk_metadata = {
                    # "filename": file_name[0],
                    "size_of_chunk": to_str(0, 18),
                    "end_file": 1  # True
                }
                file_data = file_data + bytes('\0' * data_max_len, FORMAT)
                chunks.put((file_data, chunk_metadata))
                # chunks.put((parse_message("EOF").encode(FORMAT), chunk_metadata))
                # chunks.put((parse_message(str(data_max_len)).encode(FORMAT), chunk_metadata))
                chunk_data.put([file_name[0], count_chunk + 1])
            return False
        else:
            chunk_data.put([file_name[0], number_of_chunk])
            file_name[1] += number_of_chunk * data_max_len
            return True


# def make_chunk(is_there_file, c_lock, c_files,
#                h_lock, h_files, n_lock, n_files, chunks, chunk_data, client_close):
#     # pass
#     # To do:
#     #   check if the user has sent something
#     #   if there isn't any then don't do anything
#     #   if there is then segment the file(s) to chunk by using the function make_chunk_
#     #   and if the file has been fully read then remove the file from the corresponding list
#     #   the max_chunks variable is used to only put in the queue that many chunk
#     #   make sure use lock to always read and write correctly

#     while not client_close.is_set():
#         try:
#             while not is_there_file.is_set() and not client_close.is_set() and not chunks.empty():
#                 myLogging.logQueue.put("Here 3")
#                 time.sleep(0.01)

#             if client_close.is_set():
#                 break
#             # Iterate over the files in user_input. Assuming user_input is a list of tuples (filename, position)
#             user_input = [c_files, h_files, n_files]
#             for file_list in user_input:
#                 if file_list is c_files:
#                     # file_list = c_files
#                     chunk_len = 10
#                     lock = c_lock
#                 elif file_list is h_files:
#                     # file_list = h_files
#                     chunk_len = 4
#                     lock = h_lock
#                 elif file_list is n_files:
#                     # file_list = n_files
#                     chunk_len = 1
#                     lock = n_lock
#                 else:
#                     # If the file isn't in any list, skip to the next file
#                     continue
#                 if client_close.is_set():
#                     break
#                 # myLogging.logQueue.put(f"{time.time()} here 5")
#                 # Use make_chunk_ to segment the file into chunks

#                 with lock:
#                     # try:
#                     for file in file_list:
#                         # lock.acquire()
#                         # file = file_list[i]
#                         # pre_size = chunks.qsize()
#                         file_has_ended = make_chunk_(file, chunks, chunk_data, chunk_len)

#                         # If the file has been fully read, remove it from its corresponding list
#                         if not file_has_ended:
#                             file_list.remove(file)

#                             # If there isn't any file to send next
#                             lock.release()
#                             with c_lock:
#                                 with h_lock:
#                                     with n_lock:
#                                         if len(c_files) + len(h_files) + len(n_files) == 0:
#                                             is_there_file.clear()
#                                 lock.acquire()
#                             lock.release()
#                             yield
#                             lock.acquire()
#                         # myLogging.logQueue.put(f"Here 2 {client_close.is_set()}")
#                     # except GeneratorExit:
#                     #    lock.acquire()

#             yield
#         except GeneratorExit:
#             pass

def make_chunk(is_there_file, c_lock, c_files,
               h_lock, h_files, n_lock, n_files, chunks, chunk_data, client_close):
    try:
        while not client_close.is_set():
            while not is_there_file.is_set() and not client_close.is_set() and chunks.empty():
                # myLogging.logQueue.put("Waiting for files to process")
                time.sleep(0.01)

            if client_close.is_set():
                break

            # Iterate over the files in user_input
            user_input = [c_files, h_files, n_files]
            for file_list in user_input:
                if file_list is c_files:
                    chunk_len = 10
                    lock = c_lock
                elif file_list is h_files:
                    chunk_len = 4
                    lock = h_lock
                elif file_list is n_files:
                    chunk_len = 1
                    lock = n_lock
                else:
                    continue

                if client_close.is_set():
                    break

                lock.acquire()
                for file in file_list:
                    if not lock.locked():
                        lock.aquire()
                    file_has_ended = make_chunk_(file, chunks, chunk_data, chunk_len)

                    if not file_has_ended:
                        file_list.remove(file)
                        lock.release()
                        with c_lock, h_lock, n_lock:
                            if len(c_files) + len(h_files) + len(n_files) == 0:
                                is_there_file.clear()
                        lock.acquire()
                    lock.release()
                    yield
                    lock.acquire()
                if lock.locked():
                    lock.release()
        yield
    except GeneratorExit:
        pass


# def update_last_chunk_in_queue(chunks):
#     temp_list = []

#     while not chunks.empty():
#         temp_list.append(chunks.get())

#     if temp_list:
#         last_chunk_data, last_chunk_metadata = temp_list[-1]
#         last_chunk_metadata["end_file"] = True
#         temp_list[-1] = (last_chunk_data, last_chunk_metadata)

#         for item in temp_list:
#             chunks.put(item)


def send_chunk(client, data, chunk_metadata):
    metadata = f"{chunk_metadata['size_of_chunk']}|{chunk_metadata['end_file']}"
    send_data_raw(client, metadata.encode(FORMAT) + b'||' + data)

    # client.sendall(metadata.encode() + b'|' + data)


# send file
def send_file(client, addr, aux_data, chunks, chunk_data, client_close):
    global path
    # * aux_data is expanded to is_there_file, c_lock, c_files, h_lock, h_files, n_lock, n_files
    make = make_chunk(*aux_data, chunks, chunk_data, client_close)
    next(make)

    try:
        # Check if client has disconnected. If client hasn't then keep sending data
        # Otherwise, return to main function
        while not client_close.is_set():
            header = chunk_data.get()
            # send the amount of chunk
            send_data(client, header[0] + '|' + str(header[1]))
            while header[1] > 0:
                data, chunk_metadata = chunks.get()

                if chunk_metadata["end_file"] == 1:
                    myLogging.logQueue.put(f"[{addr}] File \"{header[0]}\" has been sent")
                # send data here
                send_chunk(client, data, chunk_metadata)
                chunks.task_done()
                # myLogging.logQueue.put(f"Gui chunk")
                header[1] -= 1

            chunk_data.task_done()

            next(make)
        # myLogging.logQueue.put("Here 1")

    except ConnectionResetError:
        # myLogging.logQueue.put("A client has disconnected without a file")
        # raise ConnectionResetError
        pass
    # is_there_file, c_lock, c_files, h_lock, h_files, n_lock, n_files = aux_data
    # if is_there_file.is_set():
    # myLogging.logQueue.put("A client has disconnected without a file")


def handle_client(client, addr):
    myLogging.logQueue.put(f"Connection from {addr} has been established!")
    connected = True
    sending = False

    c_files = []
    c_lock = threading.Lock()
    h_files = []
    h_lock = threading.Lock()
    n_files = []
    n_lock = threading.Lock()

    chunks = queue.Queue()
    chunk_data = queue.Queue()

    send_event = threading.Event()
    close_event = threading.Event()
    send_thread = None
    while connected and not stop_event.is_set():
        try:
            message = receive_data(client)
            # myLogging.logQueue.put(f"T moi nhan duoc {message}")
        except ConnectionResetError or ConnectionAbortedError:
            message = None
        if message == DIS_MES:
            connected = False
            try:
                send_data(client, "*Bye*")
            except ConnectionResetError:
                pass
            # clients.remove(client)
        elif not message:
            break
        elif message in order_request:
            order = message
            message = receive_data(client)
            myLogging.logQueue.put(f"[{addr}] requested \"{message}\" with {order}.")
            try:
                # send_data(client, "Here is a file")
                # send_data(client, message)
                # make_chunk(order, message)
                if order == "Critical":
                    with c_lock:
                        c_files.append([message, 0])

                if order == "High":
                    with h_lock:
                        h_files.append([message, 0])

                if order == "Normal":
                    with n_lock:
                        n_files.append([message, 0])
                send_event.set()

                if not sending:
                    sending = True
                    send_thread = threading.Thread(target=send_file,
                                                   args=(client, addr,
                                                         [
                                                            send_event, c_lock, c_files, h_lock, h_files, n_lock,
                                                            n_files
                                                         ],
                                                         chunks, chunk_data, close_event)).start()

            except ConnectionResetError:
                myLogging.logQueue.put(f"{addr} has disconnected before file is transfer")
                break

            # send_file(client, order, message)
    close_event.set()
    # t = time.time()
    # print(f"{t} u")
    if type(send_thread) is threading.Thread:
        send_thread.join()
    if send_event.is_set():
        myLogging.logQueue.put(f"[{addr}] has close connection before receiving all files")
    else:
        myLogging.logQueue.put(f"[{addr}] has close connection")
    client.close()


def start():
    while not stop_event.is_set():
        client, addr = server.accept()
        # clients.append(client)
        send_default_mes(client)
        myLogging.logQueue.put(threading.active_count())
        threading.Thread(target=handle_client, args=(client, addr)).start()
        # thread


def stop(_, _1):
    print("Stop")
    stop_event.set()


signal.signal(signal.SIGINT, stop)
threading.Thread(target=myLogging.log, args=(), daemon=True).start()
print(f"Server is running on {SERVER_IP}")
start()

while not stop_event.is_set():
    time.sleep(0.05)
