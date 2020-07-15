#!/usr/bin/python3
from __future__ import print_function
import os
import sys
import socket
import datetime
import time
import signal

host = '127.0.0.1'
port_command = 12345
port_data = 12346

# Ce serveur est un serveur concurrent qui peut gérer plusieurs clients simultanément.
# on lui passe sur la ligne de commande 1 argument : le port d'écoute.

def ecoute(socket):
	recu = socket.recv(4096)
	if len(recu)==0:
		print("Client déconnecté")
		socket.close
		sys.exit()
	recu = str(recu,'utf-8')
	return recu

def envoi(socket, message):
	socket.send(bytes(message,'utf-8'))



signal.signal(signal.SIGCHLD,signal.SIG_IGN)

sockfd=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
sockfd.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
try:
	print('Listening on ', host, ':', port_command)
	sockfd.bind((host, port_command))
except socket.error as msg:
		print("Erreur :",msg)
		sys.exit()
sockfd.listen(10)
while True:
	print("Attente d'un client")
	# Attente de connexion
	connfd,client=sockfd.accept() 
	# connfd contient un nouvel objet socket et client les coordonnées (IP,port) du client connecté 
	print("Connection de",client)
	n = os.fork()	# création d'un processus fils
	if n == 0:	# dans le fils
		while True:
			essai = 0
			recu = ecoute(connfd)
			if recu == 'BONJ':
				while essai < 3:
					envoi(connfd, 'WHO')
					username = ecoute(connfd)
					envoi(connfd, 'PASSWD')
					password = ecoute(connfd)
					essai += 1
					auth_file = open('secret.txt', 'r')
					auth_lines = auth_file.readlines()
					for line in auth_lines:
						if line.split()[0] == username and line.split()[1] == password:
							envoi(connfd, 'WELC')
							
							while True:
								cmd = ecoute(connfd)
								if cmd == 'rls':
									r, w = os.pipe()
									ls_pid = os.fork()
									if ls_pid == 0:
										os.close(r)
										os.dup2(w, 1)
										os.execlp("ls", "ls", "-l")
										os.close(w)
										sys.exit()

									if ls_pid != 0:
										os.close(w)
										ls_list = os.read(r, 1000)
										os.close(r)
										envoi(connfd, str(ls_list, 'utf-8'))

								elif cmd == 'rpwd':
									r, w = os.pipe()
									pwd_pid = os.fork()
									if pwd_pid == 0:
										os.close(r)
										os.dup2(w, 1)
										os.execlp("pwd", "pwd")
										os.close(w)
										sys.exit()

									if pwd_pid != 0:
										os.close(w)
										pwd = os.read(r, 1000)
										os.close(r)
										envoi(connfd, str(pwd, 'utf-8'))
								
								elif cmd.startswith('rcd '):
									try:
										os.chdir(cmd.split()[1])
										envoi(connfd,'CDOK')
									except:
										envoi(connfd,'NOCD')
								else:
									envoi(connfd, 'NOK')

					else:
						envoi(connfd, 'RETRY')
						time.sleep(0.01)

				envoi(connfd, 'BYE')
				connfd.close
				sys.exit()

			elif recu == 'QUIT':
				envoi(connfd, 'BYE')
				connfd.close
				sys.exit()
	
			else:
				envoi(connfd, 'NAUTH')
			
			
			
			
	connfd.close()		# dans le père, on ferme la socket connectée