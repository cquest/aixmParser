#!/usr/bin/env python3

import bpaTools
import groundEstimatedHeight
from groundEstimatedHeight import GroundEstimatedHeight

if __name__ == '__main__':
    ### Context applicatif
    callingContext      = "Paragliding-OpenAir-French-Files"         #Your app calling context
    linkContext         = "http://pascal.bazile.free.fr/paraglidingFolder/divers/GPS/OpenAir-Format/"
    appName             = "groundEstimatedHeight"                   #or your app name
    appPath             = bpaTools.getFilePath(__file__)            #or your app path
    appVersion          = groundEstimatedHeight.appVersion          #or your app version
    appId               = appName + " v" + appVersion

    if False:            #For map only
        #outPath         = appPath + "../../poaff/output/SIA/"
        #headFileName    = "SIA@"
        outPath         = appPath + "../../poaff/output/Tests/"
        headFileName    = "BPa-Test4Clean@"
    else:
        outPath         = appPath + "../out/"
        headFileName    = ""

    srcPath             = outPath
    refPath             = outPath + "referentials/"
    logFile             = outPath + "_" + appName + ".log"
    bpaTools.createFolder(outPath)                                  #Init dossier de sortie

    oLog = bpaTools.Logger(appId,logFile)
    oLog.resetFile()

    oGEH = GroundEstimatedHeight(oLog, srcPath, refPath, headFileName)
    oGEH.parseUnknownGroundHeightRef()
    print()
    oLog.Report()
    oLog.closeFile

