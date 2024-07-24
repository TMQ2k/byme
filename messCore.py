import socket

FORMAT = 'utf-8'
DIS_MES = "!DISCONNECT"
MESS_LEN = 4 * 1024

def parse_message(msg):
    msg_len = len(msg)
    new_msg = '\0' * (MESS_LEN - msg_len)
    new_msg += msg
    return new_msg

EOF_MESS = parse_message("EOF").encode(FORMAT)

def receive_data_raw(client):
    try:
        received_data_bytes = client.recv(MESS_LEN)
        while len(received_data_bytes) < MESS_LEN:
            received_data_bytes += client.recv(MESS_LEN - len(received_data_bytes))
    except ConnectionResetError:
        raise ConnectionResetError
    return received_data_bytes

def receive_data(client):
    try:
        data = receive_data_raw(client)
    except ConnectionResetError:
        raise ConnectionResetError
    data = data.decode(FORMAT).strip('\0')
    return data

def send_data_raw(client, data):
    try:
        data = data + bytes('\0' * (MESS_LEN - len(data)), FORMAT)
        client.sendall(data)
    except ConnectionResetError:
        raise ConnectionResetError

def send_data(client, data):
    try:
        user_input_bytes = parse_message(data).encode(FORMAT)
        client.sendall(user_input_bytes)
    except ConnectionResetError:
        raise ConnectionResetError
    
