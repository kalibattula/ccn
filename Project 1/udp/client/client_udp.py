import socket
import sys
import os
import time

# If condition to specify the format of cmd line arguments
if len(sys.argv) < 4:
    print("The commnad line arguments are not specified correctly")
    print("The format is filename.py hostname control port data port")
    sys.exit(1)

# Using this socket we are sending control and data commands to diffrent ports.
c = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
host = sys.argv[1]
control_port = int(sys.argv[2])
data_port = int(sys.argv[3])

control_tup = (host, control_port)
data_tup = (host, data_port)

# code for checking connection establishment
c.sendto(str.encode("Hii from client"), control_tup)
c.sendto(str.encode("Hii from client"), data_tup)

while True:
    cmd = input("Enter Command:")
    print("The command entered is:"+cmd)

    if cmd == "quit":
        c.sendto(str.encode(cmd), control_tup)
        c.close()
        sys.exit(1)
    elif cmd[:2] == 'cd':
        c.sendto(str.encode(cmd), control_tup)
        c.sendto(str.encode(""), data_tup)
        data, addr = c.recvfrom(1024)
        print(' Current directory is:', data.decode())

    elif cmd[:2] == 'ls':
        c.sendto(str.encode(cmd), control_tup)
        c.sendto(str.encode(""), data_tup)
        data, addr = c.recvfrom(1024)
        print(data.decode())

    elif cmd[:3] == 'get':
        print("In get kali")

        c.sendto(str.encode(cmd), control_tup)
        c.sendto(str.encode(""), data_tup)
        print("After cmd")

        # Client receving the size of the file and storing it in filesize variable.
        data, addr = c.recvfrom(1024)
        filesize = int(data.decode())
        print("\nFilesize is:", filesize)

        with open('new_'+cmd[4:], 'wb') as f:

            # receving the data(CHUNK 1) from server.
            res, addr = c.recvfrom(1024)

            # Waiting for 1 second to receive the msg.
            time.sleep(1)

            # if the msg received length is greater than 0 then send ACK to server.
            if len(res) > 0:
                c.sendto(str.encode("ACK"), addr)
            else:
                print("Did Not Receive valid data from Client. Terminating.")
                sys.exit(1)

            totRecv = len(res)
            f.write(res)
            while totRecv < int(filesize):
                res, addr = c.recvfrom(1024)
                # Waiting for 1 second to receive the msg.
                time.sleep(1)

                # if the msg received length is greater than 0 then send ACK to server.
                if len(res) > 0:
                    c.sendto(str.encode("ACK"), addr)
                else:
                    print("Did Not Receive valid data from Client. Terminating.")
                    sys.exit(1)

                totRecv += len(res)
                if totRecv == int(filesize):
                    c.sendto(str.encode("FIN"), addr)
                f.write(res)
            print("Download Complete")

    elif cmd[:3] == 'put':
        print("\nIn method put")

        file_name = cmd[4:]

        # Sending the command through control channel
        c.sendto(str.encode(cmd), control_tup)
        c.sendto(str.encode(""), data_tup)

        if os.path.isfile(file_name):
            print("file exists in client")
            print(str.encode("Exists File Size is:" +
                             str(os.path.getsize(file_name))))

            # Sending the filesize to the server using data channel
            c.sendto(str.encode(str(os.path.getsize(file_name))), data_tup)

            with open(file_name, 'rb') as f:
                bytesToSend = f.read(1024)
                # Sending first Chunk of data to server
                c.sendto(bytesToSend, data_tup)
                # waiting for 1 sec to receive ack from client.
                time.sleep(1)
                # Receving acknowledgement from server.
                res, addr = c.recvfrom(1024)
                if res.decode() == "ACK":
                    print("\n ACK Recevied")
                    while bytesToSend != "":
                        bytesToSend = f.read(1024)
                        # Sending Other chunks of data to client.
                        c.sendto(bytesToSend, addr)
                        # Waiting for 1 sec before receving the Acknowledgement
                        time.sleep(1)
                        # Receving Acknowledgement
                        res, addr = c.recvfrom(1024)
                        if res.decode() == "ACK":
                            print("\n ACK Recevied")
                            continue
                        elif res.decode() == "FIN":
                            print("\n FIN Recevied")
                            print("\n Done Sending the file")
                            break
                        else:
                            print("resend the packets for 3 times")
                else:
                    print(" Resend the length and msg packets for 3 times ")

        else:
            print("File with that name doesn't exists")
