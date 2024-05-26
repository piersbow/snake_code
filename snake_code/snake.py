import socket
import subprocess
from json import loads

server_socket = socket.socket()  # get instance
server_socket.bind(("", 5000))  # bind host address and port together

# start video stream
stream = subprocess.Popen(["./mediamtx"], cwd="/home/robosnake/mediamtx")

try:
    # what does this line do? why is it 2?
    server_socket.listen(2)
    conn, address = server_socket.accept()  # accept new connection
    print("Connection from: " + str(address))


    def wait_for_data():
        data = conn.recv(2048)
        # send ack
        conn.send(b'ack')
        return data


    if __name__ == '__main__':
        while True:
            data_raw = wait_for_data()
            data = loads(data_raw.decode())
            print(data)

except:
    stream.kill()
