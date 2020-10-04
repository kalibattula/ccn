import socket
import sys
import os


# If condition to specify the format of cmd line arguments
if len(sys.argv) < 4:
    print("The commnad line arguments are not specified correctly")
    print("The format is filename.py hostname control port data port")
    sys.exit(1)

host = socket.gethostbyname(sys.argv[1])  # converting hostname to IP Address.

control_port = int(sys.argv[2])  # Getting Control Port
data_port = int(sys.argv[3])  # Getting Data Port

# creating control and data tcp sockets to connect to server.
try:
    consoc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    dsoc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except socket.error as err:
    print("error occured while creating Client Sockets " + str(err))

# Connecting to the server.
consoc.connect((host, control_port))
dsoc.connect((host, data_port))

while True:

    cmd = input("Enter Command:")

    # Closing the connections for after calling quit.
    if(cmd == "quit"):

        # Sending command to the server
        consoc.send(str.encode(cmd))

        consoc.close()
        dsoc.close()
        sys.exit(1)

    # if the command is cd or ls it prints the response.
    elif cmd[:2] == "cd" or cmd[:2] == "ls":
        # Sending command to the server
        consoc.send(str.encode(cmd))

        server_response = str(consoc.recv(1024), 'utf-8')
        print(server_response)

    # if the command is get
    elif cmd[:3] == "get":

        # Sending command to the server
        consoc.send(str.encode(cmd))
        fname = cmd[-5]
        data = dsoc.recv(1024).decode()
        if data[:6] == "Exists":
            filesize = data[6:]
            dsoc.send(str.encode('OK'))
            f = open('server_'+fname+".txt", 'wb')
            res = dsoc.recv(1024)
            totRecv = len(res)
            f.write(res)
            while totRecv < int(filesize):
                res = dsoc.recv(1024)
                totRecv += len(res)
                f.write(res)
            f.close()
            print("Download Complete")

    elif cmd[:3] == 'put':

        # Sending the command using the control socket
        file_name = cmd[4:]
        print(file_name)
        if os.path.isfile(file_name):               # Checking the file exists or not

            # Sending the command to the server
            consoc.send(str.encode(cmd))

            # Sending the file size using data socket
            filesize_put = os.path.getsize(file_name)

            # print("FIlesize is:", filesize_put)

            dsoc.send(str.encode(str(filesize_put)))
            res = dsoc.recv(1024).decode()
            if res == "OK":
                with open(file_name, 'rb') as f:
                    bytesToSend = f.read(1024)
                    dsoc.send(bytesToSend)
                    if len(bytesToSend) < filesize_put:
                        while bytesToSend:
                            bytesToSend = f.read(1024)
                            dsoc.send(bytesToSend)
            else:
                print("Server is not instrested in receving the file")
        else:
            print("There is no file with that name")

    else:
        print("Enter the correct command")
