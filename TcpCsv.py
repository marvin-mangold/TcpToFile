import socket
import queue
import threading
import time
from pytimedinput import timedInput
import sys
import os
import json


class TcpServer(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.messagebuffer = queue.Queue()  # create Buffer for messages from TCP connections

    @staticmethod
    def timestampprint(message=""):
        """
        print messages with the actual timestamp
        "[23.05.2021 11:12:20] message"
        """
        now = time.strftime("%d.%m.%Y %H:%M:%S")
        message = "[{time}] {message}".format(time=now, message=message)
        print(message)

    def checkmessagebuffer(self):
        """
        check the messagebuffer queue for messages
        if message: print() the message
        else: pass
        """
        try:  # check for messages in messagebuffer
            message = self.messagebuffer.get(block=False)
            self.timestampprint(message)
        except queue.Empty:  # no messages in messagebuffer
            pass

    def run(self):
        self.timestampprint("Server starting @ [IP: {host} Port: {port}]".format(host=self.host, port=self.port))
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:  # create an INET, STREAMing socket
            try:
                connection.bind((self.host, self.port))  # bind the socket to a host and port
            except Exception as errormessage:  # an error occurred
                print("------ Error ------")
                print(errormessage)
                print("-------------------")
                time.sleep(10)  # keep window open to read the error for some seconds
            else:
                self.timestampprint("Server started")
                self.timestampprint("Server listening for connections...")
                while True:
                    try:
                        connection.listen()  # wait for a partner to request a connection
                        connection.settimeout(0.1)  # break after 0.1 seconds to do other stuff
                        channel, addr = connection.accept()  # accept the connection request
                    except Exception as errormessage:  # an error occurred
                        if "timed out" in str(errormessage):
                            # this is the connection.settimeout(0.1) break we wanted to do other things
                            self.checkmessagebuffer()
                        else:
                            # an unwanted error occurred
                            print("------ Error ------")
                            print(errormessage)
                            print("-------------------")
                            time.sleep(10)  # keep window open to read the error for some seconds
                            break
                    else:
                        self.timestampprint("[IP: {partnerip} Port: {partnerport}] --> connected".format(
                            partnerip=addr[0], partnerport=addr[1]))
                        Connection(channel, addr, self.messagebuffer)


class Connection(object):
    def __init__(self, channel, addr, messagebuffer):
        # Connection parameters
        self.channel = channel  # Connection data
        self.ip = addr[0]  # IP-Address
        self.port = addr[1]  # Portnumber
        # Buffers
        self.buffer_message = messagebuffer  # buffer for messages
        # Threading parameters
        self.thread = threading.Thread(target=self.run, args=())  # function to be running in thread
        self.thread.daemon = True  # setup thread to end after main programm ends
        self.thread.start()  # start thread
        # Client data
        self.file = ""
        self.string = ""

    def run(self):
        while True:
            # RECEIVE DATA
            recv = self.channel.recv(1000)  # waiting for maximal 1000 bytes data
            recv = recv.decode("utf-8", "ignore")  # format received data
            if not recv:  # if no data in received data, then partner has closed connection
                message = "[IP: {ip} Port: {port}] --> connection closed".format(ip=self.ip, port=self.port)
                self.buffer_message.put(message)
                break
            else:
                # PROCESS DATA
                commandmessage = "[IP: {ip} Port: {port}] --> ".format(ip=self.ip, port=self.port)
                answermessage = "[IP: {ip} Port: {port}] <-- ".format(ip=self.ip, port=self.port)
                command = recv[:9]  # first 10 chars = command
                if "!status" in command:
                    commandmessage += "!status"
                    self.buffer_message.put(commandmessage)
                    send = "!status:OK"
                    answermessage += send
                    self.buffer_message.put(answermessage)
                elif "!delete" in command:
                    commandmessage += "!delete"
                    self.buffer_message.put(commandmessage)
                    self.string = ""
                    send = "!delete:OK"
                    answermessage += send
                    self.buffer_message.put(answermessage)
                    pass
                elif "!concat" in command:
                    data = recv[7:]  # data starts at the 7th char
                    commandmessage += "!concat: {data}".format(data=data)
                    self.buffer_message.put(commandmessage)
                    self.string += data
                    send = "!concat:OK"
                    answermessage += send
                    self.buffer_message.put("{message}: {string}".format(message=answermessage, string=self.string))
                elif "!length" in command:
                    commandmessage += "!length"
                    self.buffer_message.put(commandmessage)
                    length = len(self.string)
                    send = "!length:{length}".format(length=length)
                    answermessage += send
                    self.buffer_message.put(answermessage)
                elif "!setfile" in command:
                    data = recv[8:]  # data starts at the 8th char
                    commandmessage += "!setfile: {data}".format(data=data)
                    self.buffer_message.put(commandmessage)
                    try:
                        with open(data, mode="w") as file:
                            file.close()
                            pass
                    except Exception as errormessage:  # an error occurred
                        self.buffer_message.put(errormessage)
                        send = "!setfile:NOK"
                        answermessage += send
                        self.buffer_message.put(answermessage)
                        self.file = ""
                    else:
                        send = "!setfile:OK"
                        answermessage += send
                        self.buffer_message.put(answermessage)
                        self.file = data
                elif "!isfile" in command:
                    data = recv[7:]  # data starts at the 7th char
                    commandmessage += "!isfile: {data}".format(data=data)
                    self.buffer_message.put(commandmessage)
                    if os.path.exists(data):
                        send = "!isfile:OK"
                    else:
                        send = "!isfile:NOK"
                    answermessage += send
                    self.buffer_message.put(answermessage)
                elif "!setpath" in command:
                    data = recv[8:]  # data starts at the 8th char
                    commandmessage += "!setpath: {data}".format(data=data)
                    self.buffer_message.put(commandmessage)
                    try:
                        os.mkdir(data)
                    except Exception as errormessage:  # an error occurred
                        self.buffer_message.put(errormessage)
                        send = "!setpath:NOK"
                        answermessage += send
                        self.buffer_message.put(answermessage)
                    else:
                        send = "!setfile:OK"
                        answermessage += send
                        self.buffer_message.put(answermessage)
                elif "!ispath" in command:
                    data = recv[7:]  # data starts at the 7th char
                    commandmessage += "!ispath: {data}".format(data=data)
                    self.buffer_message.put(commandmessage)
                    if os.path.isdir(data):
                        send = "!ispath:OK"
                    else:
                        send = "!ispath:NOK"
                    answermessage += send
                    self.buffer_message.put(answermessage)
                elif "!save" in command:
                    commandmessage += "!save"
                    self.buffer_message.put(commandmessage)
                    try:
                        with open(self.file, mode="a") as file:
                            file.writelines(self.string + "\n")
                    except Exception as errormessage:  # an error occurred
                        self.buffer_message.put(errormessage)
                        send = "!save:NOK"
                        answermessage += send
                        self.buffer_message.put(answermessage)
                    else:
                        send = "!save:OK"
                        answermessage += send
                        answermessage += " {file} >> {string}".format(file=self.file, string=self.string)
                        self.buffer_message.put(answermessage)
                        self.string = ""
                else:
                    data = recv  # data is complete string
                    commandmessage += "bad command: {data}".format(data=data)
                    self.buffer_message.put(commandmessage)
                    send = "!error"
                    answermessage += send
                    self.buffer_message.put(answermessage)
                # SEND DATA
                send = send.encode("utf-8", "ignore")  # format send data
                self.channel.send(send)
        self.channel.close()


def serversettings():
    print("Type 'help' to see all commands")
    while True:
        # refresh settings
        with open("config.txt") as temp_configfile:
            temp_configfile = json.load(temp_configfile)
        # check command
        command = input(">> ")
        if command[:4] == "help":
            print("ip               - show the IP-Address the Server will host")
            print("port             - show the Portnumber the Server will host")
            print("set ip 127.0.0.1 - set the IP-Address the Server will host")
            print("set port 2000    - set the Portnumber the Server will host")
            print("start            - exit settings and start Server")
        elif command[:2] == "ip":
            print(temp_configfile["IP"])
        elif command[:4] == "port":
            print(temp_configfile["PORT"])
        elif command[:6] == "set ip":
            temp_configfile["IP"] = command[7:]
            with open("config.txt", "w", encoding="utf-8") as f:
                json.dump(temp_configfile, f, ensure_ascii=False, indent=4)
        elif command[:8] == "set port":
            try:
                newport = int(command[9:])
                temp_configfile["PORT"] = newport
                with open("config.txt", "w", encoding="utf-8") as f:
                    json.dump(temp_configfile, f, ensure_ascii=False, indent=4)
            except ValueError:
                print("{port} is not a number!".format(port=command[9:]))
        elif command[:5] == "start":
            break
        else:
            print("bad command")


def serverstart(_ip, _port):
    server = TcpServer(_ip, int(_port))
    server.run()


if __name__ == "__main__":
    # Read JSON file (configfile)
    with open("config.txt") as configfile:
        configfile = json.load(configfile)
    print("Server will start in 10s on [IP: {ip} Port: {port}]".format(ip=configfile["IP"], port=configfile["PORT"]))
    if sys.__stdin__.isatty():  # check if the console is interactive
        userText, timedOut = timedInput(prompt="Press <ENTER> to interrupt and go to settings menu >> ", timeOut=10)
        if timedOut:
            serverstart(configfile["IP"], int(configfile["PORT"]))
        else:
            serversettings()
            with open("config.txt") as configfile:
                configfile = json.load(configfile)
            serverstart(configfile["IP"], int(configfile["PORT"]))
    else:  # no interactive console, direct start
        time.sleep(10)
        serverstart(configfile["IP"], int(configfile["PORT"]))
