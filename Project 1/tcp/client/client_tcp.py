import socket
import sys
import os


# If condition to specify the format of cmd line arguments
if len(sys.argv) < 4:
    print("The commnad line arguments are not specified correctly")
    print("The format is filename.py hostname control port data port")
    sys.exit(1)

host = socket.gethostbyname(sys.argv[1])

control_port = int(sys.argv[2])
data_port = int(sys.argv[3])

control_tup = (host, control_port)
data_tup = (host, data_port)


try:
    consoc = socket.socket()
    dsoc = socket.socket()
except socket.error as err:
    print("error occured while creating Client Sockets " + str(err))

consoc.connect(control_tup)
dsoc.connect(data_tup)

while True:

    cmd = input("Enter Command:")

    if(cmd == "quit"):
        consoc.send(str.encode(cmd))
        consoc.close()
        dsoc.close()
        sys.exit(1)

    elif cmd[:2] == "cd" or cmd[:2] == "ls":
        consoc.send(str.encode(cmd))
        server_response = str(consoc.recv(1024), 'utf-8')
        print(server_response, end="")

    elif cmd[:3] == "get":
        print("In get kali")
        consoc.send(str.encode(cmd))
        data = dsoc.recv(1024).decode()
        print(data)
        if data[:6] == "Exists":
            print("File Exists in server")
            filesize = data[6:]
            dsoc.send(str.encode('OK'))
            f = open('server_'+cmd[4:], 'wb')
            res = dsoc.recv(1024)
            print(res)
            totRecv = len(res)
            f.write(res)
            while totRecv < int(filesize):
                res = dsoc.recv(1024)
                print(res)
                totRecv += len(res)
                f.write(res)
            print("Download Complete")

    elif cmd[:3] == 'put':
        print("In put method")
        # Sending the command using the control socket
        consoc.send(str.encode(cmd))
        file_name = cmd[4:]
        print(file_name)
        if os.path.isfile(file_name):               # Checking the file exists or not
            print("File exists on client machine")
            # Sending the file size using data socket
            filesize_put = os.path.getsize(file_name)
            print("FIlesize is:", filesize_put)
            dsoc.send(str.encode(str(filesize_put)))
            res = dsoc.recv(1024).decode()
            if res == "OK":
                with open(file_name, 'rb') as f:
                    bytesToSend = f.read(1024)
                    dsoc.send(bytesToSend)
                    if len(bytesToSend) < filesize_put:
                        while bytesToSend != "":
                            bytesToSend = f.read(1024)
                            dsoc.send(bytesToSend)
            else:
                print("Server is not instrested in receving the file")
        else:
            print("There is no file with that name")

    else:
        print("Enter the correct command")
