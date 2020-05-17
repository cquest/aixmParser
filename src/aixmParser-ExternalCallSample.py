#!/usr/bin/env python3

import bpaTools
import aixmReader


### Context applicatif
appName     = "aixmParser"                             #or yourAppName
appPath     = bpaTools.getFilePath(__file__)            #or yourAppPath
appVersion     = bpaTools.getVersionFile()              #or yourAppVersion
appId     = appName + " v" + appVersion
outPath     = appPath + "../out/"
logFile     = outPath + "_" + appName + ".log"


####  Quelques fichiers source  ####
srcPath = "../tst/"
#------- fichiers officiels & opérationnels ---
srcFile = srcPath + "20200618_aixm4.5_SIA-FR.xml"
#srcFile = srcPath + "20200326_aixm4.5_Eurocontrol-FR.xml"
#srcFile = srcPath + "20200510_BPa_FR-ZSM_Protection-des-rapaces_aixm45.xml"
#srcFile = srcPath + "20191210_BPa_ZonesComplementaires_aixm45.xml"
#srcFile = srcPath + "20190401_WPa_ParcCevennes_aixm45.xml"
#------- fichiers de tests  ---
#srcFile = srcPath + "20191213_FFVP_AIRSPACE_FRANCE_TXT_1911_aixm45.xml"
#srcFile = srcPath + "20191214_BPa_FR-BPa4XCsoar_aixm45.xml"
#srcFile = srcPath + "aixm5.1_testHeader.xml"
#srcFile = srcPath + "aixm4.5_SIA-FR_map-Airspaces2.xml"


####  Préparation de quelques options d'appels  ####
#Simulation des arguments d'appels 'sys.argv' via le tableau 'aArgv'
#aArgv = [appName, aixmReader.CONST.optHelp]
#------- tests unitaires ---
#aArgv = [appName, srcFile, "-Fgeojson", aixmReader.CONST.optTstGeojson, aixmReader.CONST.optDraft]
#aArgv = [appName, srcFile, "-Fgeojson", aixmReader.CONST.typeAIRSPACES, aixmReader.CONST.optFreeFlight, aixmReader.CONST.optDraft, aixmReader.CONST.optMakePoints4map]
#------- tests de non-reg ---
#aArgv = [appName, srcFile, "-Fall", aixmReader.CONST.typeCTRLTOWERS]
#aArgv = [appName, srcFile, "-Fall", aixmReader.CONST.typeAERODROMES]
#aArgv = [appName, srcFile, "-Fall", aixmReader.CONST.typeOBSTACLES]
#aArgv = [appName, srcFile, "-Fall", aixmReader.CONST.typeRUNWAYCENTER]
#aArgv = [appName, srcFile, "-Fall", aixmReader.CONST.typeGATESTANDS]
#aArgv = [appName, srcFile, "-Fall", aixmReader.CONST.typeGEOBORDER]
#aArgv = [appName, srcFile, "-Fall", aixmReader.CONST.typeAIRSPACES, aixmReader.CONST.optIFR, aixmReader.CONST.optVFR, aixmReader.CONST.optFreeFlight]
#aArgv = [appName, srcFile, "-Fall", aixmReader.CONST.typeAIRSPACES, aixmReader.CONST.optFreeFlight, aixmReader.CONST.optDraft]
#------- appels standards ---
#aArgv = [appName, srcFile, "-Fall", aixmReader.CONST.typeAIRSPACES, aixmReader.CONST.optFreeFlight]
aArgv = [appName, srcFile, "-Fall", "-Tall", aixmReader.CONST.optALL, aixmReader.CONST.optIFR, aixmReader.CONST.optVFR, aixmReader.CONST.optFreeFlight]


####  Ajout de l'option d'appel pour la gestion du Log  ####
aArgv += [aixmReader.CONST.optCleanLog]     #Mode classique avec log et afficages sur console système
#aArgv += [aixmReader.CONST.optSilent]      #Mode silencieux sans utilisation du fichier log et sans retour d'affichage




####  Préparation d'appel ####
oOpts = bpaTools.getCommandLineOptions(aArgv)                   #Arguments en dictionnaire
oLog = bpaTools.Logger(appId, logFile, isSilent=bool(aixmReader.CONST.optSilent in oOpts))
if aixmReader.CONST.optCleanLog in oOpts:
    oLog.resetFile()                                            #Clean du log si demandé
bpaTools.createFolder(outPath)                                  #Init dossier de sortie

#### Appel du parser  ####
aixmCtrl = aixmReader.AixmControler(srcFile, outPath, oLog)     #Init controler
aixmCtrl.execParser(oOpts)                                      #Execution des traitements

