#!/usr/bin/env python3

import sys, logging, datetime
import bpaTools


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
    def __init__(self, sLogName:str, sLogFile:str, sContext="", sLink=None, debugLevel:int=0, isSilent:bool=False)-> None:
        bpaTools.initEvent(__file__, isSilent=isSilent)
        #print(self.__class__.__name__, self.__class__.__module__, self.__class__.__dir__)
        self.startTime = datetime.datetime.now()
        self.sLogName:str = sLogName
        self.sLogFile:str = sLogFile
        self.sContext:str = sContext
        self.sLink:str = sLink
        self.log:logging.Logger = None
        self.isSilent:bool = isSilent    # set 'True' for silent mode (no log-file, no system-message, but log-report is available ;-)
        self.debugLevel:int = debugLevel # set level value for write the debug-messages in the log-file. Default=0 NoneExit; -1=allExit ; 1 to n for set level [9 for initEvent())]
        if not self.isSilent:
            msg = self.getMediumName()
            print(msg + "\n" + ("-" * len(msg)))
        self.__initFile__()
        return

    ### Ouverture du fichier log
    def __initFile__(self)-> None:
        self.resetCpt()
        if not self.isSilent:
            oLogger:logging.Logger = logging.getLogger(self.sLogName)
            oLogger.setLevel(logging.DEBUG)
            #oFormatter = logging.Formatter("%(asctime)-15s %(levelname)s %(name)s [%(filename)s:%(funcName)s:%(lineno)d] %(message)s")
            oFormatter:logging.Formatter = logging.Formatter("%(asctime)-15s %(name)s %(levelname)s %(message)s")
            oFH:logging.FileHandler = logging.FileHandler(self.sLogFile, encoding='utf-8')
            oFH.setLevel(logging.DEBUG)
            oFH.setFormatter(oFormatter)
            oLogger.addHandler(oFH)
            oCH:logging.StreamHandler = logging.StreamHandler(stream=sys.stdout)
            oCH.setLevel(logging.DEBUG)
            oCH.setFormatter(oFormatter)
            oLogger.addHandler(oFH)
            self.log:logging.Logger = oLogger
            self.info("Logger started - {0}".format(self.getInfo()))
        return

    def resetCpt(self)-> None:
        self.CptInfo:int = 0
        self.CptDebug:int = 0
        self.CptWarning:int = 0
        self.CptError:int = 0
        self.CptCritical:int = 0
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
        actTime = datetime.datetime.now()
        sMsg = self.getInfo() + " - Report"
        if self.CptInfo:                            sMsg += "\n{0:8d} (i)Info".format(self.CptInfo)
        if self.CptDebug and self.debugLevel!=0:    sMsg += "\n{0:8d} (i)Debug".format(self.CptDebug)
        if self.CptWarning:                         sMsg += "\n{0:8d} (!)Warning".format(self.CptWarning)
        if self.CptError:                           sMsg += "\n{0:8d} /!\Error".format(self.CptError)
        if self.CptCritical:                        sMsg += "\n{0:8d} /!\Critical".format(self.CptCritical)
        sMsg += "\n"+" "*4+"{} Temps d'execution (hh:mm:ss.ms)".format(actTime-self.startTime)
        return sMsg

    def Report(self) -> None:
        self.info(self.getReport(), outConsole=True)
        if self.CptWarning or self.CptError or self.CptCritical:
            if not self.isSilent: print()
            self.info("/!\Show log file for details - {0}".format(self.sLogFile), outConsole=True)
        return

    def default(self) -> logging.Logger:
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
            sMsg:str = "{}".format(*args)
            self.log.info(sMsg)
            outConsole:bool = kw.get("outConsole", False)
            if outConsole:  print(sMsg)
        return

    def debug(self, *args, **kw) -> None:
        if self.debugLevel!=0 and not self.isSilent:
            level:int = kw.get("level", -1)
            if self.debugLevel<0 or level<0 or self.debugLevel>=level:
                self.CptDebug += 1
                sMsg:str = "{}".format(*args)
                self.log.debug(sMsg)
                outConsole:bool = kw.get("outConsole", False)
                if outConsole:
                    sMsg:str = "(i)Debug--> {}".format(sMsg)
                    print(sMsg)
        return

    def warning(self, *args, **kw) -> None:
        self.CptWarning += 1
        if not self.isSilent:
            sMsg:str = "{}".format(*args)
            self.log.warning(sMsg)
            outConsole:bool = kw.get("outConsole", False)
            if outConsole:
                sMsg:str = "(!)Warning--> {}".format(sMsg)
                print(sMsg)
        return

    def error(self, *args, **kw) -> None:
        self.CptError += 1
        if not self.isSilent:
            sMsg:str = "{}".format(*args)
            self.log.error(sMsg)
            outConsole:bool = kw.get("outConsole", False)
            if outConsole:
                sMsg:str = "/!\Error--> {}".format(sMsg)
                print(sMsg)
        return

    def critical(self, *args, **kw) -> None:
        self.CptCritical += 1
        if not self.isSilent:
            sMsg:str = "{}".format(*args)
            self.log.critical(sMsg)
            outConsole:bool = kw.get("outConsole", False)
            if outConsole:
                sMsg:str = "/!\Critical--> {}".format(sMsg)
                print(sMsg)
        return

    def writeCommandLine(self, argv) -> None:
        if not self.isSilent:
            self.info("Command line:")
            idx = 0
            for arg in argv:
                self.info("    argv[{0}] {1}".format(idx, arg))
                idx += 1
        return
