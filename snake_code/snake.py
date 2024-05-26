import socket
from json import loads

import numpy as np

server_socket = socket.socket()  # get instance
server_socket.bind(("127.0.0.1", 5000))  # bind host address and port together

# what does this line do? why is it 2?
server_socket.listen(2)
conn, address = server_socket.accept()  # accept new connection
print("Connection from: " + str(address))


def wait_for_data():
    return conn.recv(2048)


if __name__ == '__main__':
    while True:
        data_raw = wait_for_data()
        data = loads(data_raw.decode())
        print(data)

