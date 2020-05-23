#!/usr/bin/env python3

import bpaTools
import sys, logging


class Logger:
    
    ### Initialisation d'un fichier de log
    #   How to use this concept
    #       oLog = Logger(sLogName, sLogFile)
    #       print(oLog)
    #       print(oLog.getInfo())
    #       ../..
    #       oLog.log.info("Un message d'Information")
    #       oLog.log.debug("Un message de Debug")
    #       oLog.log.warning("%s un Warning %s", "Ceci est", ";-)")
    #       oLog.log.error("Parsing {0} to {1}".format(src, dst))
    #       oLog.log.critical("Un message Critique")
    #       ../..
    #       oLog.closeFile()
    def __init__(self, sLogName:str, sLogFile:str, sContext="", sLink=None, isDebug:bool=False, isSilent:bool=False)-> None:
        bpaTools.initEvent(__file__, isSilent=isSilent)
        #print(self.__class__.__name__, self.__class__.__module__, self.__class__.__dir__)
        self.sLogName = sLogName
        self.sLogFile = sLogFile
        self.sContext = sContext
        self.sLink = sLink
        self.log = None
        self.isSilent = isSilent    # Set as 'True' for Silent mode (no log-file, no system-message, but log-report is available ;-)
        self.isDebug = isDebug      # Set as 'True' for write the debug-messages in the log-file
        if not self.isSilent:
            msg = self.getMediumName()
            print(msg + "\n" + ("-" * len(msg)))
        self.__initFile__()
        return

    ### Ouverture du fichier log
    def __initFile__(self)-> None:
        self.CptInfo = 0
        self.CptDebug = 0
        self.CptWarning = 0
        self.CptError = 0
        self.CptCritical = 0
        if not self.isSilent:
            oLogger = logging.getLogger(self.sLogName)
            oLogger.setLevel(logging.DEBUG)
            #oFormatter = logging.Formatter("%(asctime)-15s %(levelname)s %(name)s [%(filename)s:%(funcName)s:%(lineno)d] %(message)s")
            oFormatter = logging.Formatter("%(asctime)-15s %(name)s %(levelname)s %(message)s")
            oFH = logging.FileHandler(self.sLogFile)
            oFH.setLevel(logging.DEBUG)
            oFH.setFormatter(oFormatter)
            oLogger.addHandler(oFH)
            oCH = logging.StreamHandler(stream=sys.stdout)
            oCH.setLevel(logging.DEBUG)
            oCH.setFormatter(oFormatter)
            oLogger.addHandler(oFH)
            self.log = oLogger
            self.info("Logger started - {0}".format(self.getInfo()))
        return
          
    ### Destruction de la classe
    def __del__(self) -> None:
        self.closeFile()
        return
    
    def __repr__(self) -> str:
        #Org value - print(self.__class__.__repr__)
        return "[{0}.{1}]logName={2};logFile={3}".format(self.__class__.__module__, self.__class__.__name__, self.sLogName, self.sLogFile)

    def getShortName(self) -> str:
        return self.sLogName
    
    def getMediumName(self) -> str:
        return "({0}) {1}".format(self.sLogName, self.sContext)     
    
    def getLongName(self) -> str:
        ret = self.getMediumName()
        if self.sLink:
            ret += " - " + self.sLink
        return ret 

    def getInfo(self) -> str:
        return "[{0}.{1}]{2}".format(self.__class__.__module__, self.__class__.__name__, self.sLogName)
    
    def getReport(self) -> str:
        sMsg = self.getInfo() + " - Report"
        if self.CptInfo:                    sMsg += "\n{0:6d} (i)Info".format(self.CptInfo)
        if self.CptDebug and self.isDebug:  sMsg += "\n{0:6d} (i)Debug".format(self.CptDebug)
        if self.CptWarning:                 sMsg += "\n{0:6d} (!)Warning".format(self.CptWarning)
        if self.CptError:                   sMsg += "\n{0:6d} /!\Error".format(self.CptError)
        if self.CptCritical:                sMsg += "\n{0:6d} /!\Critical".format(self.CptCritical)
        return sMsg
    
    def Report(self) -> None:
        self.info(self.getReport(), outConsole=True)
        if self.CptWarning or self.CptError or self.CptCritical:
            self.info("\n/!\Show log file for details - {0}".format(self.sLogFile), outConsole=True)
        return
    
    def default(self) -> logging:
        return self.log
    
    ### Fermeture du/des fichiers de logs
    def closeFile(self) -> None:
        if self.log!=None:
            self.info("Logger closed - {0}".format(self.getInfo()))
            oHandlers = self.log.handlers[:]
            for oHandler in oHandlers:
                oHandler.flush
                oHandler.close()
                self.log.removeHandler(oHandler)
            self.log=None
        return
    
    def resetFile(self) -> None:
        self.closeFile()
        if not self.isSilent:
            bpaTools.deleteFile(self.sLogFile)
        self.__initFile__()
        return

    def info(self, *args, **kw) -> None:
        self.CptInfo += 1
        if not self.isSilent:
            self.log.info(*args)
            outConsole = kw.get("outConsole", False)
            sMsg = "{}".format(*args)
            if outConsole:  print(sMsg)
        return

    def debug(self, *args, **kw) -> None:
        self.CptDebug += 1
        if self.isDebug and not self.isSilent:
            self.log.debug(*args)
            outConsole = kw.get("outConsole", False)
            sMsg = "(i)Debug--> {}".format(*args)
            if outConsole:  print(sMsg)          
        return
    
    def warning(self, *args, **kw) -> None:
        self.CptWarning += 1
        if not self.isSilent:
            self.log.warning(*args)
            outConsole = kw.get("outConsole", False)
            sMsg = "(!)Warning--> {}".format(*args)
            if outConsole:  print(sMsg)
        return
    
    def error(self, *args, **kw) -> None:
        self.CptError += 1
        if not self.isSilent:
            self.log.error(*args)
            outConsole = kw.get("outConsole", False)
            sMsg = "/!\Error--> {}".format(*args)
            if outConsole:  print(sMsg)
        return
    
    def critical(self, *args, **kw) -> None:
        self.CptCritical += 1
        if not self.isSilent:
            self.log.critical(*args)
            outConsole = kw.get("outConsole", False)
            sMsg = "/!\Critical--> {}".format(*args)
            if outConsole:  print(sMsg)
        return

    def writeCommandLine(self, argv) -> None:
        if not self.isSilent:
            self.info("Command line:")
            idx = 0
            for arg in argv:
                self.info("    argv[{0}] {1}".format(idx, arg))
                idx += 1        
        return
