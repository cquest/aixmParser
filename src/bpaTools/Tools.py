#!/usr/bin/env python3
from datetime import datetime as dt2
from dateutil.relativedelta import *
from dateutil.rrule import *
import os, sys, re, traceback, logging, calendar, datetime
import json, unicodedata

def isInteger(s:str) -> bool:
    try:
        n:int = int(s)
        return True
    except ValueError:
        return False

def isFloat(s:str) -> bool:
    try:
        n:float = float(s)
        return True
    except ValueError:
        return False

def cleanAccent(s:str) -> str:
    return unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore')

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

#Extract data, samples:
#   getContentOf("{"1":"Value}", "{", "}", bRetSep=True) -> {"1":"Value}
#   getContentOf("*AActiv [HX]  ...", "[", "]") -> "HX"
#   getContentOf("UTC(01/01->31/12)", "(", ")") -> "01/01->31/12"
#   getContentOf("tyty et toto sur ", "(", ")") -> None
#   getContentOf("FFVP-Prot RMZ Selestat App(120.700) (GLIDER)", "(", ")")            -> 120.700
#   getContentOf("FFVP-Prot RMZ Selestat App(120.700) (GLIDER)", "(", ")", iNoInst=1) -> 120.700
#   getContentOf("FFVP-Prot RMZ Selestat App(120.700) (GLIDER)", "(", ")", iNoInst=2) -> GLIDER
#   getContentOf("FFVP-Prot RMZ Selestat App(120.700) (GLIDER)", "(", ")", iNoInst=3) -> None
def getContentOf(sSrc:str, sSepLeft:str, sSepRight:str, iNoInst:int=1, bRetSep:bool=False) -> str:
    lIdxLeft:int = -1
    lIdxRight:int = -1
    for idx in range(0, iNoInst):
        lIdxLeft  = sSrc.find(sSepLeft, lIdxLeft+1)
        lIdxRight = sSrc.find(sSepRight, lIdxLeft+1)
        if lIdxLeft<0 or lIdxRight<0:   break
    if lIdxLeft>=0 and lIdxRight>=0:
        if bRetSep:
            return sSrc[lIdxLeft:lIdxRight+len(sSepRight)]
        else:
            return sSrc[lIdxLeft+len(sSepLeft):lIdxRight]
    else:
        return None

#Extract data, samples:
#   getLeftOf("UTC(01/01->31/12)", "(") -> "UTC"
#   getLeftOf("tyty et toto sur ", "(",) -> None
def getLeftOf(sSrc:str, sFind:str) -> str:
    lIdxFind = sSrc.find(sFind)
    if lIdxFind>=0:
        return sSrc[:lIdxFind]
    else:
        return None

#Extract data, samples:
#   getRightOf("*AActiv [HX] tyty et toto", "]") -> " tyty et toto"
#   getRightOf("tyty et toto sur ", ")",) -> None
def getRightOf(sSrc:str, sFind:str) -> str:
    lIdxFind = sSrc.find(sFind)
    if lIdxFind>=0:
        return sSrc[lIdxFind+1]
    else:
        return None

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
#    theDate = datetime.datetime.now()   #or datetime.date.today()  or datetime(2021,2,16)
#    print("Now        ", addDatetime(theDate))
#    print("minutes= -1", addDatetime(theDate, minutes=-1))
#    print("minutes=+10", addDatetime(theDate, minutes=+10))
#    print("  hours= -1", addDatetime(theDate, hours=-1))
#    print("  hours= +2", addDatetime(theDate, hours=+2))
#    print("   days= -1", addDatetime(theDate, days=-1))
#    print("   days= +2", addDatetime(theDate, days=+2))
#    print("   days=+31", addDatetime(theDate, days=+31))
#    print("  weeks= -1", addDatetime(theDate, weeks=-1))
#    print("  weeks= +2", addDatetime(theDate, weeks=+2))
#    print(" months= -1", addDatetime(theDate, months=-1))
#    print(" months= +2", addDatetime(theDate, months=+2))
#    print(" months=+12", addDatetime(theDate, months=+12))
#    print(" months=+24", addDatetime(theDate, months=+24))
#    print("  years= -1" , addDatetime(theDate, years=-1))
#    print("  years= +2" , addDatetime(theDate, years=+2))
#    print("last day of month         " , addDatetime(theDate, day=31))
#    print("last day of last month    " , addDatetime(addDatetime(theDate, months=-1), day=31))
#    print("last day of next month    " , addDatetime(addDatetime(theDate, months=+1), day=31))
#    print("previous day of next month" , addDatetime(addDatetime(theDate, months=+1), days=-1))
#    #Use datetime.strftime("%Y/%d/%m") -> datetime.datetime(2021, 1, 28).strftime("%Y/%m/%d")
def addDatetime(srcdate:datetime, minutes:int=0, hours:int=0, day:int=0, days:int=0, weeks:int=0, months:int=0, years:int=0) -> datetime:
    ret:datetime = srcdate
    if minutes:     ret += datetime.timedelta(minutes=minutes)
    if hours:       ret += datetime.timedelta(hours=hours)
    if day:         ret += relativedelta(day=day)
    if days:        ret += datetime.timedelta(days=days)
    if weeks:       ret += datetime.timedelta(weeks=weeks)
    if months:      ret += relativedelta(months=months)
    if years:       ret += relativedelta(years=years)
    return ret


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
        if argv[0][0]=='-':                 #Found a "-name value" pair
            aSplit = argv[0].split("=")     #find combined attribute
            if len(aSplit)==2:
                opts[aSplit[0]] = aSplit[1]
            else:
                opts[argv[0]] = argv[0]     #Add key and value to the dictionary
        argv = argv[1:]                     #Reduce the argument list
    #print(opts)
    return opts


if __name__ == '__main__':
    #sFile = __file__
    #dCre = getFileCreationDate(sFile)
    #dMod = getFileModificationDate(sFile)
    #print(sFile, "\n", dCre, "\n", dMod, "\n", getDate(dMod))

    """
    print(addMonths(datetime.date.today(), -1))
    print(addMonths(datetime.date.today(), +0))
    print(addMonths(datetime.date.today(), +1))
    print(addMonths(datetime.date.today(), +2))
    print(addMonths(datetime.date.today(), +3))
    print(addMonths(datetime.date.today(), 12))
    print(addMonths(datetime.date.today(), 25))

    print(datetime.date.today() + datetime.timedelta(days=-1))
    print(datetime.date.today() + datetime.timedelta(days=0))
    print(datetime.date.today() + datetime.timedelta(days=1))
    print(datetime.date.today() + datetime.timedelta(days=10))
    print(datetime.date.today() + datetime.timedelta(days=20))
    print(datetime.date.today() + datetime.timedelta(days=31))
    """


    theDate = datetime.datetime.now()   #or datetime.date.today()  or datetime(2021,2,16)
    print("Now        ", addDatetime(theDate))
    print("minutes= -1", addDatetime(theDate, minutes=-1))
    print("minutes=+10", addDatetime(theDate, minutes=+10))
    print("  hours= -1", addDatetime(theDate, hours=-1))
    print("  hours= +2", addDatetime(theDate, hours=+2))
    print("   days= -1", addDatetime(theDate, days=-1))
    print("   days= +2", addDatetime(theDate, days=+2))
    print("   days=+31", addDatetime(theDate, days=+31))
    print("  weeks= -1", addDatetime(theDate, weeks=-1))
    print("  weeks= +2", addDatetime(theDate, weeks=+2))
    print(" months= -1", addDatetime(theDate, months=-1))
    print(" months= +2", addDatetime(theDate, months=+2))
    print(" months=+12", addDatetime(theDate, months=+12))
    print(" months=+24", addDatetime(theDate, months=+24))
    print("  years= -1" , addDatetime(theDate, years=-1))
    print("  years= +2" , addDatetime(theDate, years=+2))
    print("last day of month         " , addDatetime(theDate, day=31))
    print("last day of last month    " , addDatetime(addDatetime(theDate, months=-1), day=31))
    print("last day of next month    " , addDatetime(addDatetime(theDate, months=+1), day=31))
    print("previous day of next month" , addDatetime(addDatetime(theDate, months=+1), days=-1))
    print()

    #Calculate the last day of last month
    theDate = theDate + relativedelta(months=-1)
    theDate = theDate + relativedelta(day=31)

    #Generate a list of the last day for 9 months from the calculated date
    x = list(rrule(freq=MONTHLY, count=9, dtstart=theDate, bymonthday=(-1,)))
    print("Last day")
    for ld in x:
        print(ld)

    #Generate a list of the 2nd Tuesday in each of the next 9 months from the calculated date
    print("\n2nd Tuesday")
    x = list(rrule(freq=MONTHLY, count=9, dtstart=theDate, byweekday=TU(2)))
    for tuesday in x:
        print(tuesday)


    """
    print(getContentOf('{"1":"Value"}', "{", "}", bRetSep=True))
    print(getContentOf("FFVP-Prot RMZ Selestat App(120.700) (GLIDER)", "(", ")"))
    print(getContentOf("FFVP-Prot RMZ Selestat App(120.700) (GLIDER)", " (", ")"))
    print(getContentOf("FFVP-Prot RMZ Selestat App(120.700) (GLIDER)", "(", ")", iNoInst=1))
    print(getContentOf("FFVP-Prot RMZ Selestat App(120.700) (GLIDER)", "(", ")", iNoInst=2))
    print(getContentOf("FFVP-Prot RMZ Selestat App(120.700) (GLIDER)", "(", ")", iNoInst=3))
    print(getContentOf("FFVP-Prot RMZ Selestat App(120.700) (GLIDER)", "(", ")", iNoInst=5))
    print(getContentOf("FFVP-Prot RMZ Selestat App(120.700) (GLIDER)", "(", ")", iNoInst=10))
    """


