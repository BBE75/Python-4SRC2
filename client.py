#!/usr/bin/python3
from __future__ import print_function
import os
import sys
import socket

host = '127.0.0.1'
port = 12345

sockfd=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
sockfd.connect((host, port))

auth = 0 

while True:
	if auth != 1:
		cmd = input("Tapez votre commande:\n")
		
		if cmd == 'QUIT':
			sockfd.send(bytes(cmd,'utf-8'))
			print('Fermeture du programme.')
			sockfd.close()
			quit()

		if auth == 2:
			if cmd == 'ls':
				r, w = os.pipe()
				n = os.fork()
				if n == 0:
					os.close(r)
					os.dup2(w, 1)
					os.execlp("ls", "ls", "-l")
					os.close(w)
					sys.exit()
				else:
					os.close(w)
					ls_list = os.read(r, 1000)
					os.close(r)
					os.wait()
					print(str(ls_list, 'utf-8'))
				
				continue
			else:
				sockfd.send(bytes(cmd,'utf-8'))

		else:
			sockfd.send(bytes(cmd,'utf-8'))

			
	
	recu = sockfd.recv(4096)
	if len(recu)==0:
		print("Serveur déconnecté.")
		break
	recu = str(recu, 'utf-8')
	print(recu)

	if recu == 'WHO':
		auth = 1
		cmd = input("Username: ")
		sockfd.send(bytes(cmd,'utf-8'))

	elif recu == 'PASSWD':
		cmd = input("Password: ")
		sockfd.send(bytes(cmd,'utf-8'))

	elif recu == 'RETRY':
		print("Erreur d'identification, réessayez")

	elif recu == 'BYE':
		print("3 erreurs d'identification, fermeture du programme")
		sockfd.close()
		quit()

	elif recu == 'WELC':
		print("Identification réussie, connexion établie.")
		auth = 2

	elif recu == 'NOK':
		print("Commande non réconnue.")

	elif recu == 'NAUTH':
		print("BONJ pour vous identifiez.")
