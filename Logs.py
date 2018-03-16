#!/usr/bin/env python
# -*-coding:utf-8 -*

"""
    Script permettant de recevoir quotidiennement les erreurs NGINX de tous les projets par mail et/ou slack

    Auteur                : Fabien Bellanger
    Date de création      : 2018-03-12
    Dernière modification : 2018-03-16
"""

import sys
import sh
from datetime import date, timedelta
from os import path
from io import StringIO
import re
import smtplib
from email.message import EmailMessage

# ==========
# Constantes
# ==========
LOGS_PATH        = ""
FILE_SUFIX       = "-error.log"
DATE_LOG_FORMAT  = "%Y/%m/%d"
YESTERDAY        = date.strftime(date.today() - timedelta(1), DATE_LOG_FORMAT)
GREP_PATTERN     = YESTERDAY + ".*Fatal error"
EMAIL_FROM       = ""
DEVELOPERS_EMAIL = [
    "mon-email",
]

# Liste des projets
PROJECTS = [
    "mon-project"
]

# Liste des serveurs
SERVERS = [
    "ovh"
]

# =========
# Fonctions
# =========
def getFileName(project):
    """
        Retourne le nom du fichier à lire
        =================================

        Auteur : Fabien Bellanger

        :param project: Nom du projet
        :type project: string

        :return: Le nom du fichier
        :rtype:  string
    """

    return LOGS_PATH + project + FILE_SUFIX

def displayLine(date, number, timeStart, timeEnd, message):
    """
        Affichage des lignes de log
        ===========================

        Auteur : Fabien Bellanger

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

    return "{:>4d}" . format(number) + " x " + date + "[" + timeStart + " - " + timeEnd + "] " + message + "\n"

def displayProject(project, linesNumber, linesArray):
    """
        Affichage des erreurs par projet
        ================================

        Auteur : Fabien Bellanger

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
                                 line["date"],
                                 line["timeStart"],
                                 line["timeEnd"],
                                 line["message"])

    return error

def getErrorLogs(project):
    """
        Récupération des logs d"erreurs
        ===============================

        Auteur : Fabien Bellanger

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
        else:
            if path.isfile(oldFilePath) and path.getsize(oldFilePath) != 0:
                fileToRead = oldFilePath
    
    if len(fileToRead) > 0:
        try:
            buffer       = StringIO()
            projectLines = ""
            linesArray   = []
            lineArray    = {}
            linesNumber  = 0

            for line in sh.grep(GREP_PATTERN, fileToRead):
                # On parse la chaîne pour extraire la date, l'heure et le message
                # ---------------------------------------------------------------
                matchObject = re.match(r"(\d{4}/\d{2}/\d{2})\s(\d{2}:\d{2}:\d{2}).*PHP Fatal error: (.*).*",
                                       line,
                                       re.M|re.I)

                if matchObject:
                    messagePresent   = False
                    date             = matchObject.group(1)
                    time             = matchObject.group(2)
                    message          = matchObject.group(3)
                    currentIndex     = 0
                    linesArrayNumber = len(linesArray)

                    # Un message est-il déjà dans le tableau ?
                    # ----------------------------------------
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
            print("[Erreur] Grep sur " + filePath + " : pas de résultat")
        except sh.ErrorReturnCode_2:
            print("[Erreur] Fichier(s) non trouvé(s) : " + filePath + " et/ou " + oldFilePath)
    
    return error

def sendMail(serverName, content):
    """
        Envoi du mail
        =============

        Auteur : Fabien Bellanger
        :param serverName:  Nom du serveur
        :type serverName:   string
        :param content:     Contenu du mail
        :type content:      string
    """
    msg = EmailMessage()
    msg.set_content(content)
    
    msg["Subject"] = "[" + serverName + "] Logs erreurs du " + YESTERDAY
    msg["From"]    = EMAIL_FROM
    msg["To"]      = DEVELOPERS_EMAIL

    # Send the message via our own SMTP server
    with smtplib.SMTP("localhost") as s:
        s.send_message(msg)
        s.quit()

def main():
    """
        Traitement principal
        ====================

        On parcours tous les fichiers et on récupère ceux ayant une "Fatal error" PHP

        Auteur : Fabien Bellanger
    """

    # Récupération des arguments
    # --------------------------
    arguments  = sys.argv
    if len(arguments) != 2:
        print("[Erreur] Le nom du serveur n'est pas renseigné")
        sys.exit(-1)
    else:
        serverName = arguments[1]

        if not arguments[1] in SERVERS:
            print("[Erreur] Le nom du serveur n'est pas valide " + str(SERVERS))
            sys.exit(-2)
            
    # Gestion des erreurs
    # -------------------
    errors = ""
    for project in PROJECTS:
        errors += getErrorLogs(project)
    print(errors)

    # TODO: Envoyer les erreurs par Slack
    # -----------------------------------
    if len(errors) != 0:
        content = "Log sur " + serverName + " du " + YESTERDAY + "\n"
        content += "-" * 80 + "\n"
        content += errors

        # Envoi du mail
        # -------------
        sendMail(serverName, content)

    # Fermeture du programme
    # ----------------------
    sys.exit(0)

# ===================
# Lancement du script
# ===================
main()
