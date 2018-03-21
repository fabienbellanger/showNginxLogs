#!/usr/bin/env python
# -*-coding:utf-8 -*

"""
	Script permettant de recevoir quotidiennement les erreurs NGINX de tous les projets par mail et/ou slack

	Author                : Fabien Bellanger
	Date de création      : 2018-03-12
	Dernière modification : 2018-03-19
"""

import sys
import sh
import re
import config
import smtplib
from os import path
from io import StringIO
from email.message import EmailMessage
from colorama import init, Fore, Back, Style

# TODO: Amériorer configuration
# - paramètres SMTP
# - paramètres Slack

# =========
# Fonctions
# =========
def getFileName(project):
	"""
		Retourne le nom du fichier à lire
		=================================

		Author: Fabien Bellanger

		:param project: Nom du projet
		:type project: string

		:return: Le nom du fichier
		:rtype:  string
	"""

	return config.LOGS_PATH + project + config.FILE_SUFIX

def displayLine(number, timeStart, timeEnd, message):
	"""
		Affichage des lignes de log
		===========================

		Author: Fabien Bellanger

		:param number:    Nombre de fois où l'erreur est survenue
		:type project:    string
		:param timeStart: Heure de la première erreur
		:type project:    string
		:param timeEnd:   Heure de la dernière erreur
		:type project:    string
		:param message:   Message d'erreur
		:type project:    string

		:return: Une chaîne de caractères contenant la ligne
		:rtype:  string
	"""

	return "{:>4d}" . format(number) + " x [" + timeStart + " - " + timeEnd + "] " + message + "\n"

def displayProject(project, linesNumber, linesArray):
	"""
		Affichage des erreurs par projet
		================================

		Author: Fabien Bellanger

		:param project:     Nom du projet
		:type project:      string
		:param linesNumber: Nombre de lignes
		:type linesNumber:  integer
		:param linesArray:  Tableau des lignes d'erreur
		:type linesArray:   array

		:return: Une chaîne de caractères contenant les erreurs
		:rtype:  string
	"""

	# Libellés
	# --------
	totalErrorLabel     = " erreurs totales"
	differentErrorLabel = " erreurs différentes"
	if linesNumber <= 1:
		totalErrorLabel = " erreur totale"
	if len(linesArray) <= 1:
		differentErrorLabel = " erreur différente"

	error = ""

	if linesNumber != 0:
		error += "\n" + project.title()
		error += " (" + str(linesNumber) + totalErrorLabel
		error += " / " + str(len(linesArray)) + differentErrorLabel + ")\n"
		error += "-" * 80
		error += "\n"
		
		for line in linesArray:
			error += displayLine(line["number"],
								 line["timeStart"],
								 line["timeEnd"],
								 line["message"])

	return error

def getErrorLogs(project):
	"""
		Récupération des logs d"erreurs
		===============================

		Author: Fabien Bellanger

		:param project: Nom du projet
		:type project: string

		:return: Une chaîne de caractères contenant les erreurs
		:rtype:  string
	"""

	filePath    = getFileName(project)
	oldFilePath = filePath + ".1"
	fileToRead  = ""
	error       = ""
	
	# Les fichiers de log doivent exister et ne doivent pas être vide
	# ---------------------------------------------------------------
	if path.isfile(filePath):
		if path.getsize(filePath) != 0:
			fileToRead = filePath
		elif path.isfile(oldFilePath) and path.getsize(oldFilePath) != 0:
			fileToRead = oldFilePath
	
	if len(fileToRead) > 0:
		try:
			buffer       = StringIO()
			projectLines = ""
			linesArray   = []
			lineArray    = {}
			linesNumber  = 0

			for line in sh.grep(config.GREP_PATTERN, fileToRead):
				# On parse la chaîne pour extraire la date, l'heure et le message
				# ---------------------------------------------------------------
				matchObject = re.match(config.GREP_REGEX, line, re.M|re.I)

				if matchObject:
					messagePresent = False
					date           = matchObject.group(1)
					time           = matchObject.group(2)
					client         = matchObject.group(4) if (matchObject.group(4)) else ""
					server         = matchObject.group(5) if (matchObject.group(5)) else ""
					request        = matchObject.group(6) if (matchObject.group(6)) else ""
					upstream       = matchObject.group(7) if (matchObject.group(7)) else ""
					host           = matchObject.group(8) if (matchObject.group(8)) else ""

					if matchObject.group(3):
						message = matchObject.group(3)
					elif matchObject.group(9):
						message = matchObject.group(9)

					# Un message est-il déjà dans le tableau ?
					currentIndex     = 0
					linesArrayNumber = len(linesArray)

					while not (currentIndex == linesArrayNumber or linesArray[currentIndex]["message"] == message):
						currentIndex += 1
					
					if currentIndex == linesArrayNumber:
						# Pas de message trouvé, on ajoute au tableau
						lineArray = {
							"date":         date,
							"timeStart":    time,
							"message":      message,
							"timeEnd":      time,
							"number":       1,
						}
						linesArray.append(lineArray)
					else:
						# On modifie l'heure de fin et le compteur
						linesArray[currentIndex - 1]["timeEnd"] = time
						linesArray[currentIndex - 1]["number"]  += 1

					# Nombre de lignes total
					linesNumber += 1

			# Ajout à la chaîne de caractères d'erreurs globale
			# -------------------------------------------------
			error += displayProject(project, linesNumber, linesArray)

		except sh.ErrorReturnCode_1:
			print(Fore.RED + "[Erreur]",
				  Fore.GREEN + "{:<30s}" . format("[" + project + "]"),
				  Style.RESET_ALL + " : Fichier non trouvé ou vide ou bien pas de résultat")
		except sh.ErrorReturnCode_2:
			print(Fore.RED + "[Erreur]",
				  Fore.GREEN + "{:<30s}" . format("[" + project + "]"),
				  Style.RESET_ALL + " : Fichier non trouvé ou vide ou bien pas de résultat")
	else:
		print(Fore.RED + "[Erreur]",
			  Fore.GREEN + "{:<30s}" . format("[" + project + "]"),
			  Style.RESET_ALL + " : Fichiers non trouvés ou vides")
		
	return error

def sendMail(serverName, content):
	"""
		Envoi du mail
		=============

		Author: Fabien Bellanger

		:param serverName:  Nom du serveur
		:type serverName:   string
		:param content:     Contenu du mail
		:type content:      string
	"""
	msg = EmailMessage()

	# Contenu du message
	bodyContent = "\nLogs erreurs " + serverName + " du " + config.DATE_LOG_MAIL_OBJECT + "\n"
	bodyContent += "-" * 80 + "\n\n"
	bodyContent += content
	msg.set_content(bodyContent)
	
	msg["Subject"] = "[" + serverName + "] Logs erreurs du " + config.DATE_LOG_MAIL_OBJECT
	msg["From"]    = config.EMAIL_FROM
	msg["To"]      = config.DEVELOPERS_EMAIL

	# Envoi du message
	# ----------------
	with smtplib.SMTP("localhost") as s:
		s.send_message(msg)
		s.quit()

def main():
	"""
		Traitement principal
		====================

		On parcours tous les fichiers et on récupère ceux ayant une "Fatal error" PHP

		Author: Fabien Bellanger
	"""

	# Initialisation de colorama
	# --------------------------
	init()

	# Titre
	# -----
	print()
	print(Fore.YELLOW + " |=============================================|")
	print(Fore.YELLOW + " | Envoi des logs d'erreurs NGINX de la veille |")
	print(Fore.YELLOW + " |---------------------------------------------|")
	print(Fore.YELLOW + " | Fabien Bellanger                            |")
	print(Fore.YELLOW + " |=============================================|\n")

	# Récupération des arguments
	# --------------------------
	arguments  = sys.argv
	if len(arguments) != 2:
		print(Fore.RED + "[Erreur]" + Style.RESET_ALL + " Le nom du serveur n'est pas renseigné\n")
		sys.exit(-1)
	else:
		serverName = arguments[1]

		if not serverName or not arguments[1] in config.SERVERS:
			print(Fore.RED + "[Erreur]" + Style.RESET_ALL + " Le nom du serveur n'est pas valide " + str(config.SERVERS) + "\n")
			sys.exit(-2)
			
	# Gestion des erreurs
	# -------------------
	errors   = ""
	projects = config.PROJECTS.sort()
	for project in config.PROJECTS:
		errors += getErrorLogs(project)
	print(errors)

	# Envoi les erreurs par mail et/ou Slack
	# --------------------------------------
	if len(errors) != 0:
		if "mail" in config.SENDING_TYPE:
			# Envoi du mail
			# -------------
			sendMail(serverName, errors)

		# if "slack" in config.SENDING_TYPE:
			# TODO: Envoi par Slack
			# ---------------------

	# Fermeture du programme
	# ----------------------
	print()
	sys.exit(0)

# ===================
# Lancement du script
# ===================
main()
