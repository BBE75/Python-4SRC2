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

# Ce serveur est un serveur concurrent qui peut gérer plusieurs clients simultanément.
# on lui passe sur la ligne de commande 1 argument : le port d'écoute.


# Fonction pour écouter sur un socket
def ecoute(socket):
	recu = socket.recv(4096)
	if len(recu)==0:
		print("Client déconnecté")
		socket.close
		sys.exit()
	recu = str(recu,'utf-8')
	return recu

# Fonction pour envoyer de l'information sur un socket
def envoi(socket, message):
	socket.send(bytes(message,'utf-8'))


# On évite les processus zombies
signal.signal(signal.SIGCHLD,signal.SIG_IGN)

# Création du socket avec l'option reuse addresss pour pouvoir le relancer en cas de crash  
sockfd=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
sockfd.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
try:
	print('Listening on ', host, ':', port_command)
	sockfd.bind((host, port_command))
except socket.error as msg:
		print("Erreur :",msg)
		sys.exit()
sockfd.listen(10)

# Boucle principale 
while True:
	print("Attente d'un client")
	# Attente de connexion
	connfd,client = sockfd.accept() 
	# connfd contient un nouvel objet socket et client les coordonnées (IP,port) du client connecté 
	print("Connection de",client)
	n = os.fork()	# création d'un processus fils
	if n == 0:	# dans le fils
		while True:
			essai = 0 # Compteur pour les essais d'authentification
			recu = ecoute(connfd)
			if recu == 'BONJ': # Si on reçoit BONJ on lance la sequence d'authentification
				while essai < 3:
					envoi(connfd, 'WHO')
					username = ecoute(connfd)
					envoi(connfd, 'PASSWD')
					password = ecoute(connfd)
					essai += 1
					auth_file = open('secret.txt', 'r') # On ouvre le fichier secret.txt qui contient les users et mot de passe
					auth_lines = auth_file.readlines()
					for line in auth_lines:
						if line.split()[0] == username and line.split()[1] == password: # Si le username et le mot de passe match, on envoi WELC
							envoi(connfd, 'WELC')
							
							while True: # Boucle principale d'execution des commandes une fois authentifié
								cmd = ecoute(connfd)
								if cmd == 'rls':
									envoi(connfd,'DATA') # On envoie DATA au client pour qu'il ouvre un socket et on récupère le port associé
									data_port = ecoute(connfd)
									sockdata = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
									sockdata.connect((host, int(data_port)))

									r, w = os.pipe() # On créer un pipe pour faire transiter l'information entre 2 process.
									ls_pid = os.fork() # On créer un processus enfant qui va executer la commande ls
									if ls_pid == 0:
										os.close(r) # On ferme la lecture du pipe
										os.dup2(w, 1) # On redirige stdout vers le pipe en écriture
										os.execlp("ls", "ls", "-l") # On execute ls -l
										os.close(w) # Fermeture du pipe en écriture
										sys.exit() # Fin du processus

									if ls_pid != 0:
										os.close(w) # Fermeture du pipe en écriture
										ls_list = os.read(r, 1000) # On récupére les 1000 premières lignes si disponible dans le pipe en lecture
										os.close(r) # On ferme le pipe
										envoi(sockdata, str(ls_list, 'utf-8')) # On envoie le resultat dans le data socket
										sockdata.close() # Fermeture du data socket

								elif cmd == 'rpwd':
									envoi(connfd,'DATA')
									data_port = ecoute(connfd)
									sockdata = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
									sockdata.connect((host, int(data_port)))

									
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
										envoi(sockdata, str(pwd, 'utf-8'))
								
								elif cmd.startswith('rcd '): # Si la commande commence par rcd, on split en 2 rcd + path
									try: # On tente un chdir sur path dans un try, en cas de reussite on envoi CDOK
										os.chdir(cmd.split()[1])
										envoi(connfd,'CDOK')
									except: # Sinon on envoi NOCD
										envoi(connfd,'NOCD')
								else:
									envoi(connfd, 'NOK')

					
					envoi(connfd, 'RETRY') # En cas d'echec d'authentification on envoi un RETRY
					time.sleep(0.01)

				envoi(connfd, 'BYE') # Si on échoue l'auth 3 fois on envoie un BYE au client
				connfd.close
				sys.exit()

			elif recu == 'QUIT': # Si le client envoie QUIT on lui renvoie BYE
				envoi(connfd, 'BYE')
				connfd.close
				sys.exit()
	
			else:
				envoi(connfd, 'NAUTH') # Si le client n'est pas authentifié et n'envoie pas un BONJ on lui renvoie Not AUTH
			
			
			
			
	connfd.close()		# dans le père, on ferme la socket connectée