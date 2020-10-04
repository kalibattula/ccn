import socket
import sys
import os
import time
import subprocess

# If condition to specify the format of cmd line arguments
if len(sys.argv) < 3:
    print("The commnad line arguments are not specified correctly")
    print("The format is filename.py control port data port")
    sys.exit(1)

control_port = int(sys.argv[1])
data_port = int(sys.argv[2])

# GEtting the host name of the server
hostname = socket.gethostname()
hostIP = socket.gethostbyname(hostname)
print(hostIP)

# Creating control socket
consoc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
consoc.bind((hostIP, control_port))

# creating data socket
dsoc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
dsoc.bind((hostIP, data_port))

print("Data received by control channel :"+consoc.recvfrom(1024)[0].decode())
print("Data received by data channel :"+dsoc.recvfrom(1024)[0].decode())

while True:

    con_d, con_addr = consoc.recvfrom(1024)
    data_d, d_addr = dsoc.recvfrom(1024)

    print("\n The command entered is:"+con_d.decode())

    if con_d.decode() == 'quit':
        print("Successfully exited")
        consoc.close()
        dsoc.close()
        sys.exit(1)

    elif con_d.decode()[:2] == 'cd':
        try:
            os.chdir(con_d.decode()[3:])
        except:
            print("No such path exists")
        currentWD = os.getcwd()+">"
        try:
            consoc.sendto(str.encode(currentWD), con_addr)
        except socket.error as err:
            print("Error while sending data"+str(err))

    elif con_d.decode()[:2] == "ls":
        data = subprocess.Popen(con_d.decode(), shell=True, stdout=subprocess.PIPE,
                                stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        output_byte = data.stdout.read() + data.stderr.read()
        output_str = str(output_byte, "utf-8")
        try:
            consoc.sendto(str.encode(output_str), con_addr)
        except socket.error as err:
            print("Error while sending data"+str(err))

    elif con_d.decode()[:3] == 'get':
        # Getting the file name from the client
        file_name = con_d.decode()[4:]
        print(file_name)

        if os.path.isfile(file_name):  # Checking wheather the file exists or not
            print(" file exists")
            print(str.encode(str(os.path.getsize(file_name))))

            # Sending the size of the file from server to client.
            dsoc.sendto(str.encode(str(os.path.getsize(file_name))), d_addr)
            print("Sent filesize")

            with open(file_name, 'rb') as f:

                # Reading 1024 bytes from the file
                bytesToSend = f.read(1024)

                # Sending first Chunk of data to client
                dsoc.sendto(bytesToSend, d_addr)

                # waiting for 1 sec to receive ack from client.
                time.sleep(1)
                # Receving acknowledgement from server.
                res, addr = dsoc.recvfrom(1024)
                if res.decode() == "ACK":
                    print("\n ACK Recevied")
                    while bytesToSend:
                        bytesToSend = f.read(1024)
                        # Sending Other chunks of data to client.
                        dsoc.sendto(bytesToSend, addr)
                        # Waiting for 1 sec before receving the Acknowledgement
                        time.sleep(1)
                        # Receving Acknowledgement
                        res, addr = dsoc.recvfrom(1024)
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
            print("File with that name doesnot exists")

    elif con_d.decode()[:3] == 'put':
        print("\n In server put")

        # Receving the filesize from client.
        data_d, d_addr = dsoc.recvfrom(1024)
        # decoding it and storing it in filesize variable.
        filesize = data_d.decode()
        # Creating a new file and opening it in write mode.
        with open("from_client_"+con_d.decode()[-5]+".txt", 'wb') as f:
            # Waiting for 1 second to receive the msg.
            time.sleep(1)
            # receving the data(CHUNK 1) from client.
            res, addr = dsoc.recvfrom(1024)
            # Waiting for 1 second to receive the msg.
            time.sleep(1)

            # if the msg received length is greater than 0 then send ACK to server.
            if len(res) > 0:
                dsoc.sendto(str.encode("ACK"), addr)
            else:
                print("Did Not Receive valid data from Client. Terminating.")
                sys.exit(1)

            totRecv = len(res)
            f.write(res)
            while totRecv < int(filesize):
                res, addr = dsoc.recvfrom(1024)
                # Waiting for 1 second to receive the msg.
                time.sleep(1)

                # if the msg received length is greater than 0 then send ACK to server.
                if len(res) > 0:
                    dsoc.sendto(str.encode("ACK"), addr)
                else:
                    print("Did Not Receive valid data from Client. Terminating.")
                    sys.exit(1)

                totRecv += len(res)
                if totRecv == int(filesize):
                    dsoc.sendto(str.encode("FIN"), addr)
                f.write(res)
            print("Download Complete")
