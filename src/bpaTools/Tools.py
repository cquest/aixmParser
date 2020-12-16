#!/usr/bin/env python3
from datetime import datetime as dt2
import os, sys, re, traceback, logging, calendar, datetime
import json

def str2bool(v:str) -> bool:
  return bool(v.lower() in ("true","t","vrai","v","yes","y","1","-1"))

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

def getFileExt(sFile:str) -> str:
    return os.path.splitext(sFile)[1]

def getFilePath(sFile:str) -> str:
    #return os.path.dirname(sFile) + "/"                  #Non-Fonctionnel sous Linux
    return os.path.dirname(os.path.abspath(sFile)) + "/"  #Fonctionnel sous Linux

def getFileModificationDate(sFile:str) -> datetime:
    try:
        mtime:float = os.path.getmtime(sFile)
    except OSError:
        mtime:float = 0
    return dt2.fromtimestamp(mtime)

def getFileCreationDate(sFile:str) -> datetime:
    try:
        ctime:float = os.path.getctime(sFile)
    except OSError:
        ctime:float = 0
    return dt2.fromtimestamp(ctime)

#Samples
#   str(bpaTools.getNow())                      -> "2020-11-16 12:50:03.726297"
#   bpaTools.getNow().strftime("%Y%m%d-%H%M%S") -> Specific format "20201208-164204"
def getNow() -> datetime:
    return datetime.datetime.now()

#Sample bpaTools.getNowISO() -> ISO Format "2020-11-16T12:45:29.405387"
def getNowISO() -> str:
    return datetime.datetime.now().isoformat()

#Samples
#   bpaTools.getDateNow()                       -> "20201116"
#   bpaTools.getDateNow(frmt="ymd")             -> "20201116"
#   bpaTools.getDateNow(frmt="dmy")             -> "16112020"
#   bpaTools.getDateNow(frmt="dmy")             -> "16112020"
#   bpaTools.getDateNow(sep="/", frmt="dmy")    -> "16/11/2020"
#   bpaTools.getDateNow(frmt="%Y%m%d-%H%M%S")   -> Specific format "20201208-164204"
def getDateNow(sep:str="", frmt="ymd") -> str:
    return getDate(datetime.datetime.now(), sep=sep, frmt=frmt)

#Samples
#   bpaTools.getDate(datetime.datetime.now())                       -> "20201116"
#   bpaTools.getDate(datetime.datetime.now(), frmt="ymd")           -> "20201116"
#   bpaTools.getDate(datetime.datetime.now(), frmt="dmy")           -> "16112020"
#   bpaTools.getDate(datetime.datetime.now(), frmt="dmy")           -> "16112020"
#   bpaTools.getDate(datetime.datetime.now(), sep="/", frmt="dmy")  -> "16/11/2020"
#   bpaTools.getDate(datetime.datetime.now(), "%Y%m%d-%H%M%S")      -> Specific format "20201208-164204"
def getDate(date:datetime, sep:str="", frmt="ymd") -> str:
    if   frmt=="ymd":
        sFrmt = "%Y" + sep + "%m" + sep + "%d"
    elif frmt=="dmy":
        sFrmt = "%d" + sep + "%m" + sep + "%Y"
    else:
        sFrmt = frmt            #Specific format
    return date.strftime(sFrmt)

#Samples
#   addMonths(datetime.date.today(), 1)
#   addMonths(datetime.date.today(), 12)
#   addMonths(datetime.date.today(), 25)
def addMonths(sourcedate:datetime, months:int):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year,month)[1])
    return datetime.date(year, month, day)

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
    json.dump(jdata, jsonFile, ensure_ascii=False)
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

if __name__ == '__main__':
    sFile = __file__
    dCre = getFileCreationDate(sFile)
    dMod = getFileModificationDate(sFile)
    print(sFile, "\n", dCre, "\n", dMod, "\n", getDate(dMod))

