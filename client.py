import socket 
import threading
import os

import time
import myLogging
import signal

PORT = 5050
FORMAT = 'utf-8'
DIS_MES = "!DISCONNECT"
MESS_LEN = 4 * 1024
SERVER_IP = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER_IP, PORT)
stop_event = threading.Event()

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)


def parse_message(msg):
    msg_len = len(msg)
    new_msg = '\0' * (MESS_LEN - msg_len)
    new_msg += msg
    return new_msg


def send_data(data):
    global client
    try:
        user_input_bytes = parse_message(data).encode(FORMAT)
        client.send(user_input_bytes)
    except ConnectionResetError:
        raise ConnectionResetError


def receive_data():
    received_data_bytes = client.recv(MESS_LEN)
    data = received_data_bytes.decode(FORMAT).strip('\0')
    return data


def receive_file(filename):
    global stop_event
    filename = os.path.basename(filename)
    os.makedirs(os.getcwd() + "\\output", exist_ok=True)
    myLogging.logQueue.put(f"Name of the file: {filename}")
    client_path = os.getcwd() + "\\output\\" + filename
    if stop_event.is_set():
        return
    with open(client_path, "wb") as file:

        file_data = client.recv(MESS_LEN)
        pre_data = file_data
        if stop_event.is_set():
            return
        file_data = client.recv(MESS_LEN)
        while file_data:
            if stop_event.is_set():
                return
            file.write(pre_data)
            pre_data = file_data
            file_data = client.recv(MESS_LEN)
            if stop_event.is_set():
                return
            if file_data.endswith("EOF".encode(FORMAT)):
                break
        if stop_event.is_set():
            return
        msg_len = client.recv(MESS_LEN).decode(FORMAT)
        msg_len = msg_len.strip('\0')
        msg_len = int(msg_len)
        pre_data = pre_data[:msg_len]
        file.write(pre_data)
    myLogging.logQueue.put("File has been downloaded")


downloadable_file = {}


def print_menu():
    global downloadable_file
    n = len(downloadable_file.keys())
    if n > 1:
        myLogging.logQueue.put(f"We have {n} files:")
    else:
        myLogging.logQueue.put(f"We have {n} file:")
    for i, key in enumerate(downloadable_file):
        myLogging.logQueue.put(f"{i + 1}. {key}")


def received_message():
    global downloadable_file
    while not stop_event.is_set():
        try:
            message = receive_data()
            if not message:
                break
            myLogging.logLock.acquire()
            if message == "Here is a file":
                filename = receive_data()
                myLogging.logQueue.put("Downloading file")
                receive_file(filename)
            elif message == "bye":
                continue
            else:
                number_of_file = int(message)
                for i in range(number_of_file):
                    data = receive_data().split('|')
                    downloadable_file[data[0]] = data[1]
                print_menu()
            myLogging.logLock.release()
        except ConnectionResetError:
            break
        time.sleep(0.01)


def read_file():
    file_set = set()
    start = time.time()
    while not stop_event.is_set():
        with open("input.txt", "r") as f:
            for line in f:
                line = line.strip('\n')
                if line not in file_set:
                    if line not in downloadable_file:
                        myLogging.logQueue.put("The item you were looking does not exist")
                    else:
                        send_message(line)
                file_set.add(line)
        while time.time() - start <= 2.01 and not stop_event.is_set():
            time.sleep(0.01)
        start = time.time()
    client.send(parse_message(DIS_MES).encode(FORMAT))


def send_message(message):
    global client
    # client.send(message.encode(FORMAT))
    send_data(message)


threading.Thread(target=myLogging.log, args=(), daemon=True).start()
received_thread = threading.Thread(target=received_message, args=(), daemon=True)
received_thread.start()

readFile_thread = threading.Thread(target=read_file, args=())
readFile_thread.start()


def stop(_, _1):
    stop_event.set()


signal.signal(signal.SIGINT, stop)

while not stop_event.is_set():
    time.sleep(.05)

received_thread.join()
readFile_thread.join()
client.close()
