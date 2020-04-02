#!/usr/bin/env python3

import os, sys, re, traceback
import datetime
import json

def theQuit():
    sys.exit()
    return

def ctrlPythonVersion():
    pyMajorVersion, pyMinorVersion = sys.version_info[:2]
    if not (pyMajorVersion==3 and pyMinorVersion>=5):
        sys.stderr.write("Sorry, only Python 3.5 or and higher are supported at this time.\n")
        traceback.print_exc(file=sys.stdout)
        sys.exit()
    return

#Use: bpaTools.initEvent(__file__)
def initEvent(sFile, oLog=None):
    msg = "({0}) Initialisation".format(getFileName(sFile))
    if oLog:
        oLog.debug(msg, outConsole=True)
    else:
        print(msg)
    return

def getFileName(sFile):
    return os.path.basename(sFile).split(".")[0]
    

def getFilePath(sFile):
    return os.path.dirname(sFile) + "/"

    
def getDateNow(sep=""):
    return getDate(datetime.datetime.now())

def getDate(date, sep=""):
    sFrmt = "%Y" + sep + "%m" + sep + "%d"
    return date.strftime(sFrmt)


def getVersionFile():
    versionFile = "_version.py"
    fileContent = open(versionFile, "rt").read()
    token = r"^__version__ = ['\"]([^'\"]*)['\"]"
    oFound = re.search(token, fileContent, re.M)
    if oFound:
        sVersion = oFound.group(1)
    else:
        raise RuntimeError("Unable to find version string in %s." % (versionFile,))
    return sVersion


def readJsonFile(sFile):
    if os.path.exists(sFile):
        jsonFile = open(sFile, "rt", encoding="utf-8")
        jdata = json.load(jsonFile)
    else:
        jdata = {}
    return jdata


def writeJsonFile(sFile, jdata):
    jsonFile = open(sFile, "w", encoding="utf-8")
    json.dump(jdata, jsonFile)
    return


### Default file encoding
def defaultEncoding():
    return encodingUTF8()

def encodingUTF8():
    return 'utf-8'


### Create folder if not exists
def createFolder(path):
    try:
        if not os.path.exists(path):
            os.mkdir(path)
    except OSError as e:
        print ("Erreur en création du dossier {0}. ".format(e))
    return


### Remove file if exixts
def deleteFile(file):
    try:
        if os.path.exists(file):
            os.remove(file)
    except OSError as e:
        print ("Erreur en supression du fichier. {0}".format(e))
    return


### Collect Command-Line Options in a dictionary
#   Samples:
#       python aixmParser.py -h
#            argv = ['aixmParser.py', '-h']
#            opts = {'-h': '-h'}
#       python aixmParser.py -json srcfile
#            argv = ['aixmParser.py', 'srcfile', '-json']
#            opts = {'-json': '-json'}
#       python aixmParser.py param0 -idx1 param1 -idx2 param2
#           argv = ['aixmParser.py', 'srcfile', '-json', '-Openair' '-CleanLog']
#           opts = {'-json': '-json', '-Openair': '-Openair', '-CleanLog': '-CleanLog'}
def getCommandLineOptions(argv):
    #print(argv)
    opts = dict()
    while argv:
        if argv[0][0]=='-':             #Found a "-name value" pair
            opts[argv[0]] = argv[0]     #Add key and value to the dictionary
        argv = argv[1:]                 #Reduce the argument list
    #print(opts)
    return opts

