import socket
import select
import sqlite3


def run_server():
    """
    Start a server to facilitate the chat between clients.
    The server uses a single socket to accept incoming connections
    which are then added to a list (socket_list) and are listened to
    to recieve incoming messages. Messages are then stored in a database
    and are transmitted back out to the clients.
    """

    # Define where the server is running. 127.0.0.1 is the loopback address,
    # meaning it is running on the local machine.
    host = "127.0.0.1"
    port = 5000
  
    # Create a socket for the server to listen for connecting clients
    server_socket = socket.socket()
    server_socket.bind((host, port))
    server_socket.listen(10)

    # Create a list to manage all of the sockets
    socket_list = []
    # Add the server socket to this list
    socket_list.append(server_socket)

    # I added this dictionary here, to allow the /NICK command to work:
    dictionary = dict() # socket -> name 
    socket_to_name = dict() # name -> socket

    usernames = []
    
    # Data Base code:
    connection = sqlite3.connect('DataBase.db')
    cursor = connection.cursor()
    cursor.execute('''CREATE TABLE if not exists SocketDB  (roomName,Sockets)''')

    default_chat_room = 'global'


    # Start listening for input from both the server socket and the clients
    while True:

        # Monitor all of the sockets in socket_list until something happens
        ready_to_read, ready_to_write, in_error = select.select(socket_list, [], [], 0)

        # When something happens, check each of the ready_to_read sockets
        for sock in ready_to_read:
            # A new connection request recieved
            if sock == server_socket:
                # Accept the new socket request
                sockfd, addr = server_socket.accept()
                # Add the socket to the list of sockets to monitor
                socket_list.append(sockfd)
                # Log what has happened on the server
                print ("Client (%s, %s) connected" % (addr[0],addr[1]))

                # My Code:
                # if a client is connected to the server, conect them to the default chat room:
                #cursor.execute('INSERT INTO SocketDB (roomName, Sockets) values (\'%s\', \'%s\')' % (default_chat_room,addr[1]))
                
                

            # A message from a client has been recieved
            else:
                #pass
                # YOUR CODE HERE
                # Extract the data from the socket and iterate over the socket_list
                # to send the data to each of the connected clients.
                bytesRecieved = sock.recv(1024)
                message = bytesRecieved.decode('utf-8')
                

                # special / commands:
                if ('/NICK' in message):
                    command = message.split(" ")[0]
                    name = message.split(" ")[1]
                    # handeling nick name changes:
                    if (dictionary.get(sock) in usernames):
                    	usernames.remove(dictionary.get(sock))
                    if (name in usernames):
                        sock.send("Error: This name is being used by another client")
                    else:
                        dictionary[sock] = name
                        socket_to_name[name] = sock
                        usernames.append(name)
                
                if ('/WHO' in message):
                    command = message.split(" ")[0]
                    for currentUser in usernames:
                        sock.send(currentUser.encode()) 

                if ('/MSG' in message):
                    splitList = message.split()

                    command = splitList[0] # /MSG ...
                    receiver_name = splitList[1] # <name> name of receiver ...

                    splitList.remove(command)
                    splitList.remove(receiver_name)

                    to_send = ' '.join(splitList) # <message> to send ...
                    
                    receiver_socket = socket_to_name.get(receiver_name + "\n")
                    if (receiver_socket == None):
                    	sock.send("Error: the user doesn't exist!")
                    else:	
                        receiver_socket.send(dictionary.get(sock) + " : " + to_send.encode())
                
                if ('/JOIN' in message):   
                    command = message.split(" ")[0]
                    room_name = message.split(" ")[1]

                    #unique_id = sock.getpeername()[1]
                    cursor.execute('INSERT INTO SocketDB (roomName, Sockets) values (\'%s\', \'%s\')' % (room_name,sock))




                for current_soc in socket_list:
                    # send no message after a client sets their user name.
                    # or if they have used any of the special commands:
                    if ('/NICK' in message or '/WHO' in message or '/MSG' in message or '/JOIN' in message):
                        break 

                    room = "test"
                    for row in connection.execute('SELECT roomName,Sockets from SocketDB'):
                        if (row[1] == sock.getpeername()[1]):
                            room = row[0]

                    for row in connection.execute('SELECT roomName,Sockets from SocketDB'):
                        if (row[0] == room):
                            row[1].send(message.encode())
                    break        
     
                        
                    # the extra condition on the end is to ensure that the client 
                    # that just sent the message doesn't get the message again!
                    if (current_soc is not server_socket and current_soc is not sock):
                        #print(sock in dictionary.keys())
                        if (sock in dictionary.keys()):
                            current_soc.send(dictionary.get(sock) + " : " + message.encode())
                        else:
                            current_soc.send(message.encode())


     
if __name__ == '__main__':
    run_server()