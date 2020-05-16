#!/usr/bin/env python3

import bpaTools
import aixmReader


### Context applicatif
appName     = "YourAppName"                             #or original name "aixmParser" ;-)
appPath     = bpaTools.getFilePath(__file__)            #or YourAppPath
appVersion     = bpaTools.getVersionFile()              #or YourAppVersion
appId     = appName + " v" + appVersion
outPath     = appPath + "../out/"
logFile     = outPath + appName + ".log"


####  Quelques fichiers source  ####
srcPath = "../tst/"
#------- fichiers officiels & opérationnels ---
#srcFile = srcPath + "aixm4.5_SIA-FR_2020-04-23.xml"
#srcFile = srcPath + "aixm4.5_Eurocontrol-FR_2020-03-26.xml"
#srcFile = srcPath + "20200510_BPa_FR-ZSM_Protection-des-rapaces_aixm45.xml"
#srcFile = srcPath + "20191210_BPa_ZonesComplementaires_aixm45.xml"
#srcFile = srcPath + "20190401_WPa_ParcCevennes_aixm45.xml"
#------- fichiers de tests  ---
#srcFile = srcPath + "20191213_FFVP_AIRSPACE_FRANCE_TXT_1911_aixm45.xml"
#srcFile = srcPath + "20191214_BPa_FR-BPa4XCsoar_aixm45.xml"
#srcFile = srcPath + "aixm5.1_testHeader.xml"
srcFile = srcPath + "aixm4.5_SIA-FR_map-Airspaces2.xml"


####  Préparation de quelques options d'appels  ####
#Simulation des arguments d'appels 'sys.argv' via le tableau 'aArgv'
#aArgv = [appName, aixmReader.CONST.optHelp, aixmReader.CONST.optSilent]
#------- tests unitaires ---
#aArgv = [appName, srcFile, "-Fgeojson", aixmReader.CONST.optTstGeojson, aixmReader.CONST.optDraft, aixmReader.CONST.optCleanLog]
#aArgv = [appName, srcFile, "-Fgeojson", aixmReader.CONST.typeAIRSPACES, aixmReader.CONST.optFreeFlight, aixmReader.CONST.optDraft, aixmReader.CONST.optMakePoints4map, aixmReader.CONST.optCleanLog]
#------- tests de non-reg ---
#aArgv = [appName, srcFile, "-Fall", aixmReader.CONST.typeCTRLTOWERS, aixmReader.CONST.optCleanLog]
#aArgv = [appName, srcFile, "-Fall", aixmReader.CONST.typeAERODROMES, aixmReader.CONST.optCleanLog]
#aArgv = [appName, srcFile, "-Fall", aixmReader.CONST.typeOBSTACLES, aixmReader.CONST.optCleanLog]
#aArgv = [appName, srcFile, "-Fall", aixmReader.CONST.typeRUNWAYCENTER, aixmReader.CONST.optCleanLog]
#aArgv = [appName, srcFile, "-Fall", aixmReader.CONST.typeGATESTANDS, aixmReader.CONST.optCleanLog]
#aArgv = [appName, srcFile, "-Fall", aixmReader.CONST.typeGEOBORDER, aixmReader.CONST.optCleanLog]
#aArgv = [appName, srcFile, "-Fall", aixmReader.CONST.typeAIRSPACES, aixmReader.CONST.optIFR, aixmReader.CONST.optVFR, aixmReader.CONST.optFreeFlight, aixmReader.CONST.optCleanLog]
#------- appels standards ---
#aArgv = [appName, srcFile, "-Fall", aixmReader.CONST.typeAIRSPACES, aixmReader.CONST.optFreeFlight, aixmReader.CONST.optDraft, aixmReader.CONST.optCleanLog]
aArgv = [appName, srcFile, "-Fall", aixmReader.CONST.typeAIRSPACES, aixmReader.CONST.optFreeFlight, aixmReader.CONST.optCleanLog]
aArgv = [appName, srcFile, "-Fall", aixmReader.CONST.typeAIRSPACES, aixmReader.CONST.optFreeFlight, aixmReader.CONST.optSilent]
aArgv = [appName, srcFile, "-Fall", "-Tall", aixmReader.CONST.optALL, aixmReader.CONST.optIFR, aixmReader.CONST.optVFR, aixmReader.CONST.optFreeFlight, aixmReader.CONST.optCleanLog]
aArgv = [appName, srcFile, "-Fall", "-Tall", aixmReader.CONST.optALL, aixmReader.CONST.optIFR, aixmReader.CONST.optVFR, aixmReader.CONST.optFreeFlight, aixmReader.CONST.optSilent]



####  Préparation d'appel ####
oOpts = bpaTools.getCommandLineOptions(aArgv)                   #Arguments en dictionnaire
oLog = bpaTools.Logger(appId, logFile, isSilent=bool(aixmReader.CONST.optSilent in oOpts))
if aixmReader.CONST.optCleanLog in oOpts:
    oLog.resetFile()                                            #Clean du log si demandé
bpaTools.createFolder(outPath)                                  #Init dossier de sortie

#### Appel du parser  ####
aixmCtrl = aixmReader.AixmControler(srcFile, outPath, oLog)     #Init controler
aixmCtrl.execParser(oOpts)                                      #Execution des traitements

