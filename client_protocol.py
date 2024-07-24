import threading
import os

import time
import myLogging
import signal
from messCore import *
from colorama import just_fix_windows_console
just_fix_windows_console()
PORT = 5050
ip = input("Please enter an ip addresss: ")
if ip is None or ip == "":
    ip = socket.gethostbyname(socket.gethostname())
    
# SERVER_IP = socket.gethostbyname(socket.gethostname())

ADDR = (ip, PORT)
stop_event = threading.Event()

hold_event = threading.Event()
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

chunk_dict = []
progress_lock = threading.Lock()
progress_dict = {}
previous_progress_len = 0
downloadable_file = {}


def move_cursor_up(lines):
    if lines > 0:
        myLogging.logQueue.put((f"\033[{lines}A", ""))
        # sys.stdout.flush()


def clear_line():
    myLogging.logQueue.put(("\033[K", ""))
    # sys.stdout.flush()


def update_progress():
    global progress_dict, previous_progress_len
    # with progress_lock:

    for filename, progress in progress_dict.items():
        clear_line()
        myLogging.logQueue.put(
            f"Downloading {filename} .... {progress / int(downloadable_file[filename]) * 100:.2f}%")
    move_cursor_up(len(progress_dict))  # Move cursor up to overwrite previous progress lines
    # previous_progress_len = len(progress_dict)


def receive_file(client, data):
    os.makedirs(os.getcwd() + "output", exist_ok=True)
    global stop_event, chunk_dict
    data = data.split('|')
    number_of_chunks = int(data[1])
    filename = data[0]
    for i in range(number_of_chunks):
        chunk = receive_chunk(client)
        if chunk is None:
            continue
        if stop_event.is_set():
            break
        # chunk_id = chunk['chunk_id']

        if filename not in chunk_dict:
            with open(f"output\\{filename}", "wb"):
                pass
            chunk_dict.append(filename)
            progress_dict[filename] = 0

        # chunk_dict[filename].append(chunk)

        # Sort chunks by chunk_id to ensure correct order
        # chunk_dict[filename].sort(key=lambda x: x['chunk_id'])
        file_path = os.path.join(os.getcwd(), "output", filename)
        with open(file_path, "ab") as file:
            file.write(chunk['data'])
        progress_dict[filename] += chunk["size_of_chunk"]
        if chunk['end_file']:
            chunk_dict.remove(filename)
            clear_line()
            myLogging.logQueue.put(
                f"Downloading {filename} .... {progress_dict[filename] / int(downloadable_file[filename]) * 100:.2f}%")
            progress_dict.pop(filename)

            # myLogging.logQueue.put(f"File {filename} has been downloaded")

    update_progress()
    # myLogging.logQueue.put("Stopping file receive process")


def receive_mess():
    global client, stop_event
    while not stop_event.is_set():
        message = receive_data(client)
        if message == "*Bye*":
            continue
        elif message == "*Intro*":
            default_read()
            hold_event.set()
        else:
            receive_file(client, message)


# def receive_file(chunk):
#     global stop_event
#     filename = chunk ['filename']
#     os.makedirs(os.getcwd() + "\\output-ex2", exist_ok=True)
#     myLogging.logQueue.put(f"Name of the file: {filename}")
#     client_path = os.getcwd() + "\\output-ex2\\" + filename
#     cnt = 0
#     if stop_event.is_set():
#         return
#     with open(client_path, "wb") as file:
#         make_dic_download(filename, )
#         file_data = dic_download[filename][cnt]
#         pre_data = file_data
#         if stop_event.is_set():
#             return
#         file_data = dic_download[filename][cnt + 1]
#         while file_data:
#             if stop_event.is_set():
#                 return
#             file.write(pre_data)
#             pre_data = file_data
#             cnt += 1
#             file_data = dic_download[filename][cnt]
#             if stop_event.is_set():
#                 return
#             if file_data.endswith("EOF".encode(FORMAT)):
#                 break
#         if stop_event.is_set():
#             return
#         msg_len = client.recv(MESS_LEN).decode(FORMAT)
#         msg_len = msg_len.strip('\0')
#         msg_len = int(msg_len)
#         pre_data = pre_data[:msg_len]
#         file.write(pre_data)
#     myLogging.logQueue.put("File has been downloaded")


def receive_chunk(client):
    # buffer_size = MESS_LEN
    data = receive_data_raw(client)
    
    if not data:
        return None
    
    metadata, chunk_data = data.split(b'||', 1)
    metadata = metadata.decode(FORMAT).split('|')
    size_of_chunk, end_file = metadata
    end_file = end_file == "1"

    chunk_data = chunk_data[:int(size_of_chunk)]

    chunk = {
        # "filename": filename,
        "size_of_chunk": int(size_of_chunk),
        "end_file": end_file,
        "data": chunk_data
    }
    return chunk


def print_menu():
    global downloadable_file
    n = len(downloadable_file.keys())
    if n > 1:
        myLogging.logQueue.put(f"We have {n} files:")
    else:
        myLogging.logQueue.put(f"We have {n} file:")
    for i, key in enumerate(downloadable_file):
        myLogging.logQueue.put(f"{i + 1}. {key}")


def default_read():
    message = receive_data(client)
    number_of_file = int(message)
    for i in range(number_of_file):
        data = receive_data(client).split('|')
        downloadable_file[data[0]] = data[1]
    print_menu()


def read_file():
    file_set = set()
    # start = time.time()
    # default_read()
    while not hold_event.is_set():
        time.sleep(0.1)
    order_request = ["Critical", "High", "Normal"]
    while not stop_event.is_set():
        with open("input.txt", "r") as f:
            for line in f:
                line = line.strip('\n')
                data = line.split(',')
                if len(data) != 2:
                    clear_line()
                    myLogging.logQueue.put(f"Invalid input line \"{line}\"")
                    continue
                data[0] = data[0].strip(' ')
                data[1] = data[1].strip(' ')
                if data[0] not in file_set:
                    if data[0] not in downloadable_file:
                        clear_line()
                        myLogging.logQueue.put(f"The item \"{data[0]}\" does not exist")
                    elif data[1] not in order_request:
                        clear_line()
                        myLogging.logQueue.put(f"{data[1]} is a unsupported download order")
                    else:
                        send_data(client, data[1])
                        send_data(client, data[0])
                        # nhan file
                        # receive_file(client)
                        file_set.add(data[0])
        start = time.time()
        while time.time() - start < 2 and not stop_event.is_set():
            time.sleep(0.01)

        # time.sleep(0.1)
    file_set.clear()


threading.Thread(target=myLogging.log, args=(), daemon=True).start()
# received_thread = threading.Thread(target=received_message, args=(), daemon=True)
# received_thread.start()
receive_mess_thread = threading.Thread(target=receive_mess, args=())
receive_mess_thread.start()

readFile_thread = threading.Thread(target=read_file, args=())
readFile_thread.start()


def stop(_, _1):
    stop_event.set()
    send_data(client, DIS_MES)


signal.signal(signal.SIGINT, stop)

while not stop_event.is_set():
    time.sleep(.05)

# received_thread.join()
readFile_thread.join()
receive_mess_thread.join()
client.close()
myLogging.wait()
