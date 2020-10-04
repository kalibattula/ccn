import socket
import os
import subprocess
import sys
import time

# If condition to specify the format of cmd line arguments
if len(sys.argv) < 3:
    print("The commnad line arguments are not specified correctly")
    print("The format is filename.py control port data port")
    sys.exit(1)

control_port = int(sys.argv[1])
data_port = int(sys.argv[2])

# Getting the host name of the server
hostname = socket.gethostname()
hostIP = socket.gethostbyname(hostname)
print(hostIP)


# Creating control socket
consoc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
consoc.bind((hostIP, control_port))

# creating data socket
dsoc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
dsoc.bind((hostIP, data_port))

# Listening to clients
print("Control and Data Sockets are created successfully and listening for connections")
consoc.listen(5)
dsoc.listen(5)

# Accepting the connections
client_consoc, con_addr = consoc.accept()
client_dsoc, d_addr = dsoc.accept()

print("Connections has been successfully established with Control channel IP:" +
      str(con_addr[0])+" Port:"+str(con_addr[1]))
print("Connections has been successfully established with Data channel IP:" +
      str(d_addr[0])+" Port:"+str(d_addr[1]))


while True:
    try:
        cmd = client_consoc.recv(1024).decode()
    except socket.error as err:
        print("Error while receving data"+str(err))

    print("\n The command entered by the user is:", cmd)

    if cmd == "quit":
        print("Successfully exited")
        client_consoc.close()
        consoc.close()
        client_dsoc.close()
        dsoc.close()
        sys.exit(1)

    elif cmd[:2] == "cd":
        try:
            os.chdir(cmd[3:])
        except:
            print("No such path exists")
        currentWD = os.getcwd()+">"
        try:
            client_consoc.send(str.encode(currentWD))
        except socket.error as err:
            print("Error while sending data"+str(err))

    elif cmd[:2] == "ls":
        data = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        output_byte = data.stdout.read() + data.stderr.read()
        output_str = str(output_byte, "utf-8")
        # currentWD = os.getcwd()
        try:
            client_consoc.send(str.encode(output_str))
        except socket.error as err:
            print("Error while sending data"+str(err))

    if cmd[:3] == 'get':
        file_path = cmd[4:]
        print(file_path)
        if os.path.isfile(file_path):
            # print(str.encode("Exists " + str(os.path.getsize(file_path))))
            # Sending the file exists and filesize msg using data channel.
            client_dsoc.send(str.encode(
                "Exists " + str(os.path.getsize(file_path))))
            usrRes = client_dsoc.recv(1024).decode()

            if usrRes[:2] == "OK":
                with open(file_path, 'rb') as f:
                    bytesToSend = f.read(1024)
                    client_dsoc.send(bytesToSend)
                    while bytesToSend:
                        bytesToSend = f.read(1024)
                        client_dsoc.send(bytesToSend)
                    print("Completed Sending")
        else:
            client_dsoc.send("Not Exists")

    elif cmd[:3] == 'put':
        file_path = cmd[4:]
        # print(file_name)

        filesize = int(client_dsoc.recv(1024).decode())

        client_dsoc.send(str.encode("OK"))
        f = open('from_client_'+cmd[-5]+'.txt', 'wb')
        res = client_dsoc.recv(1024)
        totRecv = len(res)
        f.write(res)
        while totRecv < int(filesize):
            res = client_dsoc.recv(1024)
            totRecv += len(res)
            f.write(res)
        f.close()
        print("Download Complete")
