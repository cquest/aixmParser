#!/usr/bin/env python3

import sys
import bpaTools
import aixmReader

### Context applicatif
bpaTools.ctrlPythonVersion()
__AppName__     = bpaTools.getFileName(__file__)
__AppPath__     = bpaTools.getFilePath(__file__)
__AppVers__     = bpaTools.getVersionFile()
___AppId___     = __AppName__ + " v" + __AppVers__
__OutPath__     = __AppPath__ + "../out/"
__LogFile__     = __OutPath__ + __AppName__ + ".log"
oLog = bpaTools.Logger(___AppId___,__LogFile__)

def syntaxe():
    print("Aeronautical Information Exchange Model (AIXM) Converter")
    print("Call: " + __AppName__ + " <[drive:][path]filename> <Format> <Type> [<Type2> ... <TypeN>] [<Option(s)>]")
    print("With:")
    print("  <[drive:][path]filename>       AIXM source file")
    print("")
    print("  <Format> - Output formats:")
    print("    " + aixmReader.CONST.frmtGEOJSON + "        GeoJSON for GoogleMap")
    print("    " + aixmReader.CONST.frmtKML + "            KML for GoogleEatrh")
    print("    " + aixmReader.CONST.frmtOPENAIR + "        OpenAir for aeronautical software")
    print("    " + aixmReader.CONST.frmtALL + "            All output formats (simultaneously)")    
    print("")
    print("  <Type(s)> - Data to export:")
    print("    " + aixmReader.CONST.typeAIRSPACES)
    print("    " + aixmReader.CONST.typeGEOBORDER)
    print("    " + aixmReader.CONST.typeOBSTACLES)
    print("    " + aixmReader.CONST.typeAERODROMES)
    print("    " + aixmReader.CONST.typeRUNWAYCENTER)
    print("    " + aixmReader.CONST.typeCTRLTOWERS)
    print("    " + aixmReader.CONST.typeGATESTANDS)
    print("    " + aixmReader.CONST.typeALL + "           All exported type (simultaneously)")
    print("")
    print("  <Option(s)> - Complementary Options:")
    print("    " + aixmReader.CONST.optHelp + "              Help syntax")
    print("    " + aixmReader.CONST.optCleanLog + "       Clean log file before exec")
    print("    " + aixmReader.CONST.optIFR + "            Specific upper vues of aeronautic maps (IFR areas)")    
    print("    " + aixmReader.CONST.optVFR + "            Specific lower vues of aeronautic maps (only IFR areas, without IFR areas)")    
    print("    " + aixmReader.CONST.optFreeFlight + "     Specific Paragliding/Hanggliding maps (out E,F,G,W areas and others...)")
    print("    " + aixmReader.CONST.optDraft + "          Size limitation for geojson output")
    print("")
    print("  Samples: " + __AppName__ + " ../tst/aixm4.5_SIA-FR_2019-12-05.xml " + aixmReader.CONST.frmtALL + " " + aixmReader.CONST.typeALL + " " + aixmReader.CONST.optCleanLog)
    print("           " + __AppName__ + " ../tst/aixm4.5_SIA-FR_2019-12-05.xml " + aixmReader.CONST.frmtGEOJSON + " " + aixmReader.CONST.typeAIRSPACES + " " + aixmReader.CONST.typeOBSTACLES + " " + aixmReader.CONST.typeCTRLTOWERS + " " + aixmReader.CONST.optCleanLog)
    print("           " + __AppName__ + " ../tst/aixm4.5_SIA-FR_2019-12-05.xml " + aixmReader.CONST.frmtALL + " " + aixmReader.CONST.typeAIRSPACES + " " + aixmReader.CONST.optFreeFlight + " " + aixmReader.CONST.optCleanLog)
    print("")
    print("  Resources")
    print("     GeoJSON test format: http://geojson.tools/  -or-  http://geojson.io")
    print("     OpenAir test format: http://xcglobe.com/cloudapi/browser  -or-  http://cunimb.net/openair2map.php")
    return

### Context d'excecution
if len(sys.argv)<2:
    #oLog.isDebug = True     # Write the debug-messages in the log file
    sSrcPath = "../tst/"
    #sSrcFile = sSrcPath+"aixm5.1_testHeader.xml"
    sSrcFile = sSrcPath+"aixm4.5_SIA-FR_map-Airspaces2.xml"
    #sSrcFile = sSrcPath + "aixm4.5_SIA-FR_2019-12-05.xml"
    #sSrcFile = sSrcPath + "aixm4.5_Eurocontrol-FR_2019-11-07.xml"
    #sSrcFile = sSrcPath + "aixm4.5_Eurocontrol-EU_2019-11-07.xml"
    #------- tests unitaires ---
    #sys.argv += [sSrcFile, "-Fgeojson", aixmReader.CONST.optTstGeojson", "-Draft", aixmReader.CONST.optCleanLog]
    #sys.argv += [sSrcFile, "-Fgeojson", aixmReader.CONST.typeAIRSPACES, "-FreeFlight", "-Draft", "-MakePoints4map", aixmReader.CONST.optCleanLog, ]
    #------- tests de non-reg ---
    #sys.argv += [sSrcFile, "-Fall", aixmReader.CONST.typeCTRLTOWERS, aixmReader.CONST.optCleanLog]
    #sys.argv += [sSrcFile, "-Fall", aixmReader.CONST.typeAERODROMES, aixmReader.CONST.optCleanLog]
    #sys.argv += [sSrcFile, "-Fall", aixmReader.CONST.typeOBSTACLES, aixmReader.CONST.optCleanLog]
    #sys.argv += [sSrcFile, "-Fall", aixmReader.CONST.typeRUNWAYCENTER, aixmReader.CONST.optCleanLog]
    #sys.argv += [sSrcFile, "-Fall", aixmReader.CONST.typeGATESTANDS, aixmReader.CONST.optCleanLog]
    #sys.argv += [sSrcFile, "-Fall", aixmReader.CONST.typeGEOBORDER, aixmReader.CONST.optCleanLog]
  #  sys.argv += [sSrcFile, "-Fall", aixmReader.CONST.typeAIRSPACES, aixmReader.CONST.optIFR, aixmReader.CONST.optVFR, aixmReader.CONST.optFreeFlight, aixmReader.CONST.optCleanLog]
    #------- appels standards ---
    #sys.argv += [sSrcFile, "-Fall", aixmReader.CONST.typeAIRSPACES, "-FreeFlight", "-Draft", aixmReader.CONST.optCleanLog]
    #sys.argv += [sSrcFile, "-Fall", aixmReader.CONST.typeAIRSPACES, "-FreeFlight", aixmReader.CONST.optCleanLog]
    #sys.argv += [sSrcFile, "-Fall", "-Tall", "-FreeFlight", aixmReader.CONST.optCleanLog]
    #sys.argv += [sSrcFile, aixmReader.CONST.optHelp]
    sys.argv += [aixmReader.CONST.optHelp]


sSrcFile = sys.argv[1]                              #Nom de fichier
oOpts = bpaTools.getCommandLineOptions(sys.argv)    #Arguments en dictionnaire
oLog.writeCommandLine(sys.argv)                     #Trace le contexte d'execution


if aixmReader.CONST.optHelp in oOpts:
    syntaxe()                                       #Aide en ligne
    oLog.closeFile()
else:
    if aixmReader.CONST.optCleanLog in oOpts:
        oLog.resetFile()                            #Clean du log si demandé
    
    bpaTools.createFolder(__OutPath__)              #Init dossier de sortie
   
    #Initialisation du controler de traitements
    aixmCtrl = aixmReader.AixmControler(sSrcFile, __OutPath__, oLog)
    #Execution des traitements
    if not aixmCtrl.execParser(oOpts):
       syntaxe()
