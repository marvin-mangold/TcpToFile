"""
TcpToFile - Save data from multiple TCP-Clients on TCP-Server Filesystem as .txt or .csv
Copyright (C) 2021  Marvin Mangold (Marvin.Mangold00@googlemail.com)
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import socket
import queue
import threading
import time
import os
import json
import ansicon
import msvcrt


# activate ansicon to enable ANSI codes im command prompt for coloured text
ansicon.load()


class TcpServer(object):
    """
    -provide the user interface (help information / settings menu / TCP eventlog)
    -listen for TCP-connections and initiate a new communication channel for each
    """
    def __init__(self):
        # read JSON file (configfile) to get the saved server settings
        with open("config.txt") as configfile:
            self.configfile = json.load(configfile)
        self.host = self.configfile["IP"]
        self.port = self.configfile["PORT"]
        self.delay = 10  # startup delay to start the server, press <ESC> during the delay to go to settings menu
        self.setupflag = False  # flag to memorize if <ESC> was pressed during the startup delay
        self.messagebuffer = queue.Queue()  # create buffer for messages from multiple TCP connections

    def startup(self):
        """
        -print user information about server settings and how to change them
        -startup server mainloop after the start delay
        -if <ESC> is pressed during the delay go to settings menu
        -if <ESC> is not pressed during the delay start the server mainloop
        """
        msg = "Server will start in 10s on [IP: {ip} Port: {port}]".format(ip=self.host, port=self.port)
        specialprint(message=msg, timestamp=False, color="white")
        msg = "Press <ESC> to interrupt and go to settings menu >> "
        specialprint(message=msg, timestamp=False, color="yellow")
        delay = time.time() + self.delay  # end of delay = actual time + delay
        while time.time() < delay and not self.setupflag:  # delay
            if msvcrt.kbhit():
                key_stroke = msvcrt.getch()
                if key_stroke == b'\x1b':
                    self.set_setup()
        if self.setupflag:
            self.setup()
        self.run()  # run server mainloop

    def set_setup(self):
        """
        -<ESC> was pressed during server startup delay
        """
        self.setupflag = True

    def setup(self):
        """
        -print user information how to get help information
        -listen for user input (commands) and respond
        -----------------------------------------------------------------------------------
        commands:
        help                show help information
        ip                  show the Server IP-Address
        port                show the Server Portnumber
        set ip 127.0.0.1    set the Server IP-Address
        set port 2000       set the Server Portnumber
        start               exit settings and start Server
        -----------------------------------------------------------------------------------
        """
        specialprint(message="Type 'help' to see all commands", timestamp=False, color="white")
        while True:
            # refresh settings
            with open("config.txt") as configfile:
                self.configfile = json.load(configfile)
            # check for incoming commands
            command = input("\033[0;97m>> ")
            if command[:4] == "help":
                specialprint(message="ip               - show the Server IP-Address", timestamp=False, color="white")
                specialprint(message="port             - show the Server Portnumber", timestamp=False, color="white")
                specialprint(message="set ip 127.0.0.1 - set the Server IP-Address", timestamp=False, color="white")
                specialprint(message="set port 2000    - set the Server Portnumber", timestamp=False, color="white")
                specialprint(message="start            - exit settings and start Server", timestamp=False,
                             color="white")
            elif command[:2] == "ip":
                specialprint(message=self.configfile["IP"], timestamp=False, color="white")
            elif command[:4] == "port":
                specialprint(message=str(self.configfile["PORT"]), timestamp=False, color="white")
            elif command[:6] == "set ip":
                self.configfile["IP"] = command[7:]
                with open("config.txt", "w", encoding="utf-8") as f:
                    json.dump(self.configfile, f, ensure_ascii=False, indent=4)
            elif command[:8] == "set port":
                try:
                    newport = int(command[9:])
                    self.configfile["PORT"] = newport
                    with open("config.txt", "w", encoding="utf-8") as f:
                        json.dump(self.configfile, f, ensure_ascii=False, indent=4)
                except ValueError:
                    specialprint(message="{port} is not a number!".format(port=command[9:]), timestamp=False,
                                 color="red")
            elif command[:5] == "start":
                break
            else:
                specialprint(message="bad command", timestamp=False, color="red")

    def run(self):
        """
        -print user information about server settings
        -start server mainloop
        -listen for TCP-connections and call a connection object (thread) for each client connection
        """
        message = "Server starting @ [IP: {host} Port: {port}]".format(host=self.host, port=self.port)
        specialprint(message=message, timestamp=True, color="white")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:  # create an INET, STREAMing socket
            try:
                connection.bind((self.host, self.port))  # bind the socket to the host and port
            except Exception as errormessage:  # an error occurred
                specialprint(message="------ Error ------", timestamp=False, color="red")
                specialprint(message=str(errormessage), timestamp=False, color="red")
                specialprint(message="-------------------", timestamp=False, color="red")
                time.sleep(10)  # keep window open to read the error for some seconds
            else:
                specialprint(message="Server started", timestamp=True, color="white")
                specialprint(message="Server listening for connections...", timestamp=True, color="white")
                while True:
                    try:
                        connection.listen()  # wait for a partner to request a connection
                        connection.settimeout(0.1)  # break after 0.1 seconds to do other stuff
                        channel, addr = connection.accept()  # accept the connection request
                    except Exception as errormessage:  # an error occurred
                        if "timed out" in str(errormessage):
                            # this is the connection.settimeout(0.1) error to break the listening to do other things
                            self.checkmessagebuffer()
                        else:
                            # an unwanted error occurred
                            specialprint(message="------ Error ------", timestamp=False, color="red")
                            specialprint(message=str(errormessage), timestamp=False, color="red")
                            specialprint(message="-------------------", timestamp=False, color="red")
                            time.sleep(10)  # keep window open to read the error for some seconds
                            break
                    else:  # a connection request was recieved
                        message = "[IP: {ip} Port: {port}] --> connected".format(ip=addr[0], port=addr[1])
                        specialprint(message=message, timestamp=True, color="magenta")
                        Connection(channel, addr, self.messagebuffer)

    def checkmessagebuffer(self):
        """
        -check the messagebuffer queue for TCP client commands
            if message: print() the message
            else: pass
        """
        try:  # check for messages in messagebuffer
            message, timestamp, color = self.messagebuffer.get(block=False)
            specialprint(message=message, timestamp=timestamp, color=color)
        except queue.Empty:  # no messages in messagebuffer
            pass


class Connection(object):
    """
    -start a thread for a TCP-connection client
    -run the loop for the thread
    -listen for TCP-data from client
    -look for commands in the TCP-data and send a respond to the client
    -put the
    """
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
        """
        -listen for TCP-data from client
        -process TCP-commands
        -send respond via TCP to client
        -----------------------------------------------------------------------------------
        commands:       action                          respond
        !status         check connection state          !status:OK
        !delete         delete saved string             !delete:OK
        !concat         add string to actual string     !concat:OK
        !length         get actual string length        !length:"length of actual string"
        !setfile        create empty file               !setfile:OK / !setfile:NOK
        !isfile         check if file exists            !isfile:OK / !isfile:NOK
        !setpath        create empty folder             !setpath:OK / !setpath:NOK
        !ispath         check if folder exists          !ispath:OK / !ispath:NOK
        !save           save actual string in file      !save:OK / !save:NOK
        ???             bad command recieved            !error
        -----------------------------------------------------------------------------------
        """
        while True:
            # RECEIVE DATA
            recv = self.channel.recv(1000)  # waiting for max 1000 bytes data
            recv = recv.decode("utf-8", "ignore")  # format received data
            if not recv:  # if no data in received data, then partner has closed connection
                message = "[IP: {ip} Port: {port}] --> connection closed".format(ip=self.ip, port=self.port)
                self.buffer_message.put((message, True, "magenta"))
                break
            else:
                # PROCESS DATA
                commandmessage = "[IP: {ip} Port: {port}] --> ".format(ip=self.ip, port=self.port)
                answermessage = "[IP: {ip} Port: {port}] <-- ".format(ip=self.ip, port=self.port)
                command = recv[:9]  # first 10 chars = command
                if "!status" in command:
                    commandmessage += "!status"
                    self.buffer_message.put((commandmessage, True, "green"))
                    send = "!status:OK"
                    answermessage += send
                    self.buffer_message.put((answermessage, True, "cyan"))
                elif "!delete" in command:
                    commandmessage += "!delete"
                    self.buffer_message.put((commandmessage, True, "green"))
                    self.string = ""
                    send = "!delete:OK"
                    answermessage += send
                    self.buffer_message.put((answermessage, True, "cyan"))
                    pass
                elif "!concat" in command:
                    data = recv[7:]  # data starts at the 7th char
                    commandmessage += "!concat: {data}".format(data=data)
                    self.buffer_message.put((commandmessage, True, "green"))
                    self.string += data
                    send = "!concat:OK"
                    answermessage += send
                    answermessage = "{message}: {string}".format(message=answermessage, string=self.string)
                    self.buffer_message.put((answermessage, True, "cyan"))
                elif "!length" in command:
                    commandmessage += "!length"
                    self.buffer_message.put((commandmessage, True, "green"))
                    length = len(self.string)
                    send = "!length:{length}".format(length=length)
                    answermessage += send
                    self.buffer_message.put((answermessage, True, "cyan"))
                elif "!setfile" in command:
                    data = recv[8:]  # data starts at the 8th char
                    commandmessage += "!setfile: {data}".format(data=data)
                    self.buffer_message.put((commandmessage, True, "green"))
                    try:
                        with open(data, mode="w") as file:
                            file.close()
                            pass
                    except Exception as errormessage:  # an error occurred
                        self.buffer_message.put((str(errormessage), True, "red"))
                        send = "!setfile:NOK"
                        answermessage += send
                        self.buffer_message.put((answermessage, True, "cyan"))
                        self.file = ""
                    else:
                        send = "!setfile:OK"
                        answermessage += send
                        self.buffer_message.put((answermessage, True, "cyan"))
                        self.file = data
                elif "!isfile" in command:
                    data = recv[7:]  # data starts at the 7th char
                    commandmessage += "!isfile: {data}".format(data=data)
                    self.buffer_message.put((commandmessage, True, "green"))
                    if os.path.exists(data):
                        send = "!isfile:OK"
                    else:
                        send = "!isfile:NOK"
                    answermessage += send
                    self.buffer_message.put((answermessage, True, "cyan"))
                elif "!setpath" in command:
                    data = recv[8:]  # data starts at the 8th char
                    commandmessage += "!setpath: {data}".format(data=data)
                    self.buffer_message.put((commandmessage, True, "green"))
                    try:
                        os.mkdir(data)
                    except Exception as errormessage:  # an error occurred
                        self.buffer_message.put((str(errormessage), True, "red"))
                        send = "!setpath:NOK"
                        answermessage += send
                        self.buffer_message.put((answermessage, True, "cyan"))
                    else:
                        send = "!setpath:OK"
                        answermessage += send
                        self.buffer_message.put((answermessage, True, "cyan"))
                elif "!ispath" in command:
                    data = recv[7:]  # data starts at the 7th char
                    commandmessage += "!ispath: {data}".format(data=data)
                    self.buffer_message.put((commandmessage, True, "green"))
                    if os.path.isdir(data):
                        send = "!ispath:OK"
                    else:
                        send = "!ispath:NOK"
                    answermessage += send
                    self.buffer_message.put((answermessage, True, "cyan"))
                elif "!save" in command:
                    commandmessage += "!save"
                    self.buffer_message.put((commandmessage, True, "green"))
                    try:
                        with open(self.file, mode="a") as file:
                            file.writelines(self.string + "\n")
                    except Exception as errormessage:  # an error occurred
                        self.buffer_message.put((str(errormessage), True, "red"))
                        send = "!save:NOK"
                        answermessage += send
                        self.buffer_message.put((answermessage, True, "cyan"))
                    else:
                        send = "!save:OK"
                        answermessage += send
                        answermessage += " {file} >> {string}".format(file=self.file, string=self.string)
                        self.buffer_message.put((answermessage, True, "cyan"))
                        self.string = ""
                else:
                    data = recv  # data is complete string
                    commandmessage += "bad command: {data}".format(data=data)
                    self.buffer_message.put((commandmessage, True, "red"))
                    send = "!error"
                    answermessage += send
                    self.buffer_message.put((answermessage, True, "cyan"))
                # SEND DATA
                send = send.encode("utf-8", "ignore")  # format send data
                self.channel.send(send)
        self.channel.close()


def specialprint(message="", timestamp=False, color=None):
    """
    print messages with the actual timestamp
    "[23.05.2021 11:12:20] message"
    """
    # define colors
    colors = {"black": "\033[0;90m",
              "red": "\033[0;91m",
              "green": "\033[0;92m",
              "yellow": "\033[0;93m",
              "blue": "\033[0;94m",
              "magenta": "\033[0;95m",
              "cyan": "\033[0;96m",
              "white": "\033[0;97m"}
    if color is not None:
        message = colors[color]+message
    if timestamp:
        now = time.strftime("%d.%m.%Y %H:%M:%S")
        message = "{color}[{time}] {message}".format(color=colors["white"], time=now, message=message)
    print(message)


if __name__ == "__main__":
    os.system("color")
    server = TcpServer()
    server.startup()
