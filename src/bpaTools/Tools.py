#!/usr/bin/env python3
import os, sys, re, traceback, logging, datetime
import json

def theQuit():
    sys.exit()
    return

def sysExit():
    sys.exit()
    return

def sysExitError(sError:str) -> None:
    sys.stderr.write(sError)
    traceback.print_exc(file=sys.stdout)
    sys.exit(sError)
    return

def ctrlPythonVersion() -> None:
    pyMajorVersion, pyMinorVersion = sys.version_info[:2]
    if not (pyMajorVersion==3 and pyMinorVersion>=5):
        sysExitError("Sorry, only Python 3.5 or and higher are supported at this time.\n")
    return

#Use: bpaTools.initEvent(__file__)
def initEvent(sFile:str, oLog:logging=None, isSilent:bool=False) -> None:
    msg = "({0}) Initialisation".format(getFileName(sFile))
    if oLog:
        oLog.debug(msg, outConsole=True)
    elif not isSilent:
        print(msg)
    return

def getFileName(sFile:str) -> str:
    return os.path.basename(sFile).split(".")[0]

def getFilePath(sFile:str) -> str:
    #return os.path.dirname(sFile) + "/"                  #Non-Fonctionnel sous Linux
    return os.path.dirname(os.path.abspath(sFile)) + "/"  #Fonctionnel sous Linux

#Sample str(ret) -> "2020-11-16 12:50:03.726297"
def getNow() -> datetime:
    return datetime.datetime.now()

#Sample "2020-11-16T12:45:29.405387"
def getNowISO() -> str:
    return datetime.datetime.now().isoformat()

def getDateNow(sep:str="", frmt="ymd") -> str:
    return getDate(datetime.datetime.now(), sep=sep, frmt=frmt)

def getDate(date:datetime, sep:str="", frmt="ymd") -> str:
    if   frmt=="ymd":
        sFrmt = "%Y" + sep + "%m" + sep + "%d"
    elif frmt=="dmy":
        sFrmt = "%d" + sep + "%m" + sep + "%Y"
    return date.strftime(sFrmt)

def getVersionFile(versionPath:str="", versionFile:str="_version.py") -> str:
    fileContent = open(versionPath + versionFile, "rt").read()
    token = r"^__version__ = ['\"](.*)['\"]"      #old - r"^__version__ = ['\"]([^'\"]*)['\"]"
    oFound = re.search(token, fileContent, re.M)
    if oFound:
        sVersion = oFound.group(1)
    else:
        raise RuntimeError("Unable to find version string in %s." % (versionFile,))
    return sVersion

def getParamTxtFile(sFile:str, paramVar:str, valueType:str="str") -> str:
    fileContent = open(sFile, "rt").read()
    token = r"^" + paramVar
    if   valueType=="str":
        token += " = ['\"](.*)['\"]"        #get __version__ = "2.1.3"
    elif valueType=="lst":
        token += " = ['](.*)[']"            #get __webPublicationDates__ = '["02/01/2014","28/01/2014", ... , "14/06/2014"]'
    oFound = re.search(token, fileContent, re.M)
    if oFound:
        sParam = oFound.group(1)
    else:
        raise RuntimeError("Unable to find param:{0} in file:{1}".format(paramVar, sFile))
    return sParam

def getParamJsonFile(sFile:str, paramVar:str):
    fileContent:dict = readJsonFile(sFile)
    if paramVar in fileContent:
        oRet = fileContent[paramVar]
    else:
        raise RuntimeError("Unable to find param:{0} in file:{1}".format(paramVar, sFile))
    return oRet

def readJsonFile(sFile:str) -> dict:
    if os.path.exists(sFile):
        jsonFile = open(sFile, "rt", encoding="utf-8")
        jdata = json.load(jsonFile)
        jsonFile.close()
    else:
        jdata = {}
    return jdata

def writeJsonFile(sFile:str, jdata:dict) -> None:
    jsonFile = open(sFile, "w", encoding="utf-8")
    json.dump(jdata, jsonFile)
    jsonFile.close()
    return

def writeTextFile(sFile:str, stext:str, sencoding:str="cp1252"):
    textFile = open(sFile, "w", encoding=sencoding, errors="replace")
    textFile.write(stext)
    textFile.close()
    return

### Default file encoding
def defaultEncoding() -> str:
    return encodingUTF8()

def encodingUTF8() -> str:
    return 'utf-8'

### Create folder if not exists
def createFolder(path:str) -> None:
    try:
        if not os.path.exists(path):
            os.mkdir(path)
    except OSError as e:
        print("Erreur en création du dossier {0}. ".format(e))
    return

### Remove file if exixts
def deleteFile(file:str) -> None:
    try:
        if os.path.exists(file):
            os.remove(file)
    except OSError as e:
        print("Erreur en supression du fichier. {0}".format(e))
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
def getCommandLineOptions(argv) -> dict:
    #print(argv)
    opts = dict()
    while argv:
        if argv[0][0]=='-':             #Found a "-name value" pair
            opts[argv[0]] = argv[0]     #Add key and value to the dictionary
        argv = argv[1:]                 #Reduce the argument list
    #print(opts)
    return opts

