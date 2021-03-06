#!/usr/bin/python3
from __future__ import print_function
import os
import sys
import socket

host = '127.0.0.1'
port_command = 12345

sockfd=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
sockfd.connect((host, port_command)) # Connexion au socket

auth = 0 	# Variable qui sert à tracker l'authentification
			# 0 non authen, 1 en cours d'auth, 2 authentifié

while True:
	if auth != 1: # Si l'utilisateur n'est pas en cours d'auth
		cmd = input("Tapez votre commande:\n")
		
		if cmd == 'QUIT': # On ferme le programme proprement
			sockfd.send(bytes(cmd,'utf-8'))
			print('Fermeture du programme.')
			sockfd.close()
			quit()

		if auth == 2: # Si authentifié on peut executer les commandes
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
			
			elif cmd == 'pwd':
				r, w = os.pipe()
				n = os.fork()
				if n == 0:
					os.close(r)
					os.dup2(w, 1)
					os.execlp("pwd", "pwd")
					os.close(w)
					sys.exit()
				else:
					os.close(w)
					pwd = os.read(r, 1000)
					os.close(r)
					os.wait()
					print(str(pwd, 'utf-8'))
				continue

			elif cmd.startswith('cd '):
				try:
					print('Changement de repertoire pour', cmd.split()[1])
					os.chdir(cmd.split()[1])
					print('Succés')
				except:
					print('Erreur')
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

	if recu == 'WHO':
		auth = 1
		cmd = input("Username: ")
		sockfd.send(bytes(cmd,'utf-8'))

	elif recu == 'PASSWD':
		cmd = input("Password: ")
		sockfd.send(bytes(cmd,'utf-8'))

	elif recu == 'RETRY':
		print("Erreur d'identification, réessayez.")

	elif recu == 'BYE':
		print("3 erreurs d'identification, fermeture du programme.")
		sockfd.close()
		quit()

	elif recu == 'WELC':
		print("Identification réussie, connexion établie.")
		auth = 2

	elif recu == 'DATA':
		sock_data=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		sock_data.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
		sock_data.bind(('',0))
		data_port = str(sock_data.getsockname()[1])
		sockfd.send(bytes(data_port,'utf-8'))
		sock_data.listen(1)
		condata, clientdata = sock_data.accept()
		data = condata.recv(4096)
		sock_data.close()
		print(str(data,'utf-8'))

	elif recu == 'NOK':
		print("Commande non réconnue.")
	
	elif recu == 'CDOK':
		print("Succés de la commande rcd.")

	elif recu == 'NOCD':
		print("Echec de la commande rcd.")

	elif recu == 'NAUTH':
		print("BONJ pour vous identifiez.")
