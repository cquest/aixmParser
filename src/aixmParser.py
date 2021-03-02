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
__LogFile__     = __OutPath__ + "_" + __AppName__ + ".log"
bpaTools.createFolder(__OutPath__)                                  #Init dossier de sortie


def syntaxe():
    print("Aeronautical Information Exchange Model (AIXM) Converter")
    print("Call: " + __AppName__ + " <[drive:][path]filename> <Format> <Type> [<Type2> ... <TypeN>] [<Option(s)>]")
    print("With:")
    print("  <[drive:][path]filename>       AIXM source file")
    print("")
    print("  <Format> - Output formats:")
    print("    " + aixmReader.CONST.frmtGEOJSON + "        GeoJSON for GoogleMap")
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
    print("    " + aixmReader.CONST.optSilent + "         Silent mode (no log-file, no system-message, but log-report is available ;-)")
    print("    " + aixmReader.CONST.optCleanLog + "       Clean log-file before exec")
    print("    " + aixmReader.CONST.optALL + "            All areas of aeronautic maps (IFR+VFR areas)")
    print("    " + aixmReader.CONST.optIFR + "            Specific upper vues of aeronautic maps (IFR areas)")
    print("    " + aixmReader.CONST.optVFR + "            Specific lower vues of aeronautic maps (only IFR areas, without IFR areas)")
    print("    " + aixmReader.CONST.optFreeFlight + "     Specific Paragliding/Hanggliding maps (out E,F,G,W areas and others...)")
    print("    " + aixmReader.CONST.optDraft + "          Size limitation for geojson output")
    print("    " + aixmReader.CONST.optEpsilonReduce + "  Float parameter of Ramer-Douglas-Peucker Algorithm (https://github.com/fhirschmann/rdp) for optimize output (Default=0 no-optimize, sample=0.0001)")

    print("")
    print("  Samples: " + __AppName__ + " ../tst/aixm4.5_SIA-FR_2020-04-23.xml " + aixmReader.CONST.frmtALL + " " + aixmReader.CONST.typeALL + " " + aixmReader.CONST.optCleanLog)
    print("           " + __AppName__ + " ../tst/aixm4.5_SIA-FR_2020-04-23.xml " + aixmReader.CONST.frmtGEOJSON + " " + aixmReader.CONST.typeAIRSPACES + " " + aixmReader.CONST.typeOBSTACLES + " " + aixmReader.CONST.typeCTRLTOWERS + " " + aixmReader.CONST.optCleanLog)
    print("           " + __AppName__ + " ../tst/aixm4.5_SIA-FR_2020-04-23.xml " + aixmReader.CONST.frmtALL + " " + aixmReader.CONST.typeAIRSPACES + " " + aixmReader.CONST.optFreeFlight + " " + aixmReader.CONST.optCleanLog + " " + aixmReader.CONST.optEpsilonReduce + "=0.0001")
    print("")
    print("  Resources")
    print("     GeoJSON test format: http://geojson.tools/  -or-  http://geojson.io")
    print("     OpenAir test format: http://xcglobe.com/cloudapi/browser  -or-  http://cunimb.net/openair2map.php")
    return

if __name__ == '__main__':
    ### Context d'excecution
    oOpts = bpaTools.getCommandLineOptions(sys.argv)    #Arguments en dictionnaire
    oLog = bpaTools.Logger(___AppId___, __LogFile__, isSilent=bool(aixmReader.CONST.optSilent in oOpts))

    if len(sys.argv)<2 or (aixmReader.CONST.optHelp in oOpts):
        syntaxe()                                                           #Aide en ligne
        oLog.closeFile()
    else:
        if aixmReader.CONST.optCleanLog in oOpts:
            oLog.resetFile()                                                #Clean du log

        oLog.writeCommandLine(sys.argv)                                     #Trace le contexte d'execution
        sSrcFile = sys.argv[1]                                              #Nom de fichier
        aixmCtrl = aixmReader.AixmControler(sSrcFile, __OutPath__, oLog=oLog)    #Controler de traitements
        if aixmCtrl.execParser(oOpts):                                      #Execution des traitements
            print()
            oLog.Report()
        else:
           syntaxe()
    oLog.closeFile()

