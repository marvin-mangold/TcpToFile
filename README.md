# TcpToFile

TcpToFile is a Sotfware to save data from multiple TCP-clients on TCP-server Filesystem as .txt or .csv

- start TcpToFile.exe
- interrupt the startup process by pressing ESC within the first 10 seconds to enter the setup menu:

        -----------------------------------------------------------------------------------
        commands:
        help                show help information
        ip                  show the server IP-Address
        port                show the server Portnumber
        set ip 127.0.0.1    set the server IP-Address
        set port 2000       set the server Portnumber
        start               exit settings and start server
        -----------------------------------------------------------------------------------

- if the startup is done the server is litening for TCP-client connections
- each TCP-client is running in its own thread
- the server is now listening for incoming commands from the clients
- all commands and responses are logged in the console
  
        -----------------------------------------------------------------------------------
        commands:       action:                         respond:
        !status         check connection state          !status:OK
        !delete         delete saved string             !delete:OK
        !concat         add string to actual string     !concat:OK
        !length         get actual string length        !length: "length of actual string"
        !setfile        create empty file               !setfile:OK / !setfile:NOK
        !isfile         check if file exists            !isfile:OK / !isfile:NOK
        !setpath        create empty folder             !setpath:OK / !setpath:NOK
        !ispath         check if folder exists          !ispath:OK / !ispath:NOK
        !save           save actual string in file      !save:OK / !save:NOK
        ???             bad command recieved            !error
        -----------------------------------------------------------------------------------

  
  ![Statemachine](https://user-images.githubusercontent.com/10088323/129964679-96305bad-85d0-4605-8512-46547a227ade.png)

        

https://user-images.githubusercontent.com/10088323/129979732-febbaaf1-733d-47c4-8b84-1f09165cf0f0.mp4

