#!/usr/bin/env python3

import bpaTools
from groundEstimatedHeight import GroundEstimatedHeight


if __name__ == '__main__':
    ### Context applicatif
    callingContext      = "Paragliding-OpenAir-FrenchFiles"         #Your app calling context
    linkContext         = "http://pascal.bazile.free.fr/paraglidingFolder/divers/GPS/OpenAir-Format/"
    appName             = "groundEstimatedHeight"                   #or your app name
    appPath             = bpaTools.getFilePath(__file__)            #or your app path
    appVersion          = "1.1.0"                                   #or your app version
    appId               = appName + " v" + appVersion
    outPath             = appPath + "../out/"
    srcPath             = outPath
    refPath             = outPath + "referentials/"
    logFile             = outPath + "_" + appName + ".log"
    bpaTools.createFolder(outPath)                                  #Init dossier de sortie
    
    oLog = bpaTools.Logger(appId,logFile)
    oLog.resetFile()

    oGEH = GroundEstimatedHeight(oLog, srcPath, refPath)
    oGEH.parseUnknownGroundHeightRef()
    print()
    oLog.Report()
    oLog.closeFile
    
    