#!/usr/bin/env python3

import bpaTools
import aixmReader


### Context applicatif
callingContext      = "RemoteCall"                              #Your app calling context
appName             = "aixmParser"                              #or your app name
appPath             = bpaTools.getFilePath(__file__)            #or your app path
appVersion          = bpaTools.getVersionFile()                 #or your app version
appId               = appName + " v" + appVersion
outPath             = appPath + "../out/"
logFile             = outPath + "_" + appName + ".log"


####  Source test file  ####
srcFile = "../tst/aixm4.5_SIA-FR_map-Airspaces.xml"


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
oLog = bpaTools.Logger(appId, logFile, callingContext, isSilent=bool(aixmReader.CONST.optSilent in oOpts))

if aixmReader.CONST.optCleanLog in oOpts:
    oLog.resetFile()                                #Clean du log si demandé
oLog.writeCommandLine(aArgv)                        #Trace le contexte d'execution
bpaTools.createFolder(outPath)                      #Init dossier de sortie

#### Appel du parser  ####
aixmCtrl = aixmReader.AixmControler(srcFile, outPath, oLog)     #Init controler
aixmCtrl.execParser(oOpts)                                      #Execution des traitements

#Bilan des traitements disponible en mode 'Silent' ;-)
if aixmReader.CONST.optSilent in oOpts:
    if oLog.CptCritical or oLog.CptError:
        print("/!\ Processing Error(s)")
        print(oLog.getReport())
    
