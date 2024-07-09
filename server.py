import socket
import threading
import os
import time
import signal
import myLogging

# get server ip
SERVER_IP = socket.gethostbyname(socket.gethostname())
# setup server parameter
PORT = 5050
HEADER = 64
ADDR = (SERVER_IP, PORT)
# initialize server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)
server.listen()

# message format
FORMAT = 'utf-8'
DIS_MES = "!DISCONNECT"
MESS_LEN = 4 * 1024

# stop event
stop_event = threading.Event()

# get path
def read_list_file(filename):
    file_list = {}
    with open(filename, 'r') as f:
        n = int(f.readline())
        for line in f:
            data = line.split(',')
            data[1] = data[1].strip("\n")
            file_list[data[0]] = data[1]
    return file_list


path = os.getcwd()  # path to the files
files = read_list_file("listOfFile.txt")  # list of files in the path
# clients list
clients = []


def parse_message(msg):
    msg_len = len(msg)
    new_msg = '\0' * (MESS_LEN - msg_len)
    new_msg += msg
    return new_msg
# send data


def send_data(client, data):
    try:
        user_input_bytes = parse_message(data).encode(FORMAT)
        client.send(user_input_bytes)
    except ConnectionResetError:
        raise ConnectionResetError


def send_default_mes(client):
    send_data(client, f"{len(files)}")
    for index, file in enumerate(files):
        filename = os.path.basename(file)
        msg = f"{filename}|{files[file]}"
        send_data(client, msg)


# send message to all current client when one client connected ????
def broadcast():
    for client in clients:
        send_default_mes(client)
    

# send file
def send_file(client, filename):
    global path
    try:
        myLogging.logQueue.put("Sending file")

        filename = os.path.basename(filename)
        filename = path + '\\' + filename
        with open(filename, "rb") as file:
            file_data = file.read(MESS_LEN)
            data_len = len(file_data)
            while data_len == MESS_LEN:
                client.send(file_data)
                file_data = file.read(MESS_LEN)
                data_len = len(file_data)

            file_data = file_data + bytes('\0' * (MESS_LEN - data_len), FORMAT) 
            client.send(file_data)
        send_data(client, "EOF")
        send_data(client, str(data_len))
        myLogging.logQueue.put("File has been sent")
    except ConnectionResetError:
        raise ConnectionResetError


def handle_client(client, addr):
    myLogging.logQueue.put(f"Connection from {addr} has been established!")
    connected = True
    while connected and not stop_event.is_set():
        try:
            message = client.recv(MESS_LEN).decode(FORMAT).strip('\0')
        except ConnectionResetError:
            message = None
        if message == DIS_MES:
            connected = False
            send_data(client, "bye")
            # clients.remove(client)
        elif not message:
            break
        elif message in files:
            # message is the filename
            myLogging.logQueue.put(f"[{addr}] {message}")
            myLogging.logQueue.put(f"Selected file is: {message}")
            try:
                send_data(client, "Here is a file")
                send_data(client, message)
                send_file(client, message)
            except ConnectionResetError:
                myLogging.logQueue.put(f"{addr} has disconnected before file is transfer")
                break
    if not connected:
        myLogging.logQueue.put(f"[{addr}] has close connection")

    client.close()
    
   
def start():
    while not stop_event.is_set():
        client, addr = server.accept()
        # clients.append(client)
        send_default_mes(client)
        threading.Thread(target=handle_client, args=(client, addr)).start()
        # thread


def stop(_, _1):
    print("Stop")
    stop_event.set()


signal.signal(signal.SIGINT, stop)
threading.Thread(target=myLogging.log, args=(), daemon=True).start()
print(f"Server is running on {SERVER_IP}")
threading.Thread(target=start, args=()).start()

while not stop_event.is_set():
    time.sleep(0.05)

server.close()

