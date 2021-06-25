#!/usr/bin/env python3

import bpaTools
import aixmReader
import aixm2json
import aixm2openair
import sys, traceback


class CONST:
    nm = 1852                           # Nautic Mile to Meter
    ft = 0.3048                         # Foot to Meter
    pi = 3.1415926                      # PI angle
    frmtGEOJSON = "-Fgeojson"
    frmtOPENAIR = "-Fopenair"
    frmtALL = "-Fall"
    typeAIRSPACES = "-Airspaces"
    typeOBSTACLES = "-Obstacles"
    typeAERODROMES = "-Aerodromes"
    typeRUNWAYCENTER = "-RunwayCenter"
    typeCTRLTOWERS = "-ControlTowers"
    typeGEOBORDER = "-GeoBorders"
    typeGATESTANDS = "-GateStands"
    typeALL = "-Tall"
    optHelp = "-h"
    optCleanLog = "-CleanLog"
    optSilent = "-Silent"
    optALL = "-ALL"
    optIFR = "-IFR"
    optVFR = "-VFR"
    optFreeFlight = "-FreeFlight"
    optDraft = "-Draft"
    optOpenairDigitOptimize = "-OpenairDigitOptimize"     #parameter for optimize Openair output geometry coordinates
    optGeojsonDigitOptimize = "-GeojsonDigitOptimize"     #parameter for optimize Geojson output geometry coordinates
    optEpsilonReduce = "-EpsilonReduce"     #parameter for Ramer-Douglas-Peucker Algorithm (https://github.com/fhirschmann/rdp)
    optTstGeojson = "-TstGeojson"
    optMakePoints4map = "-MakePoints4map"
    fileSuffixAndMsg = {
            optALL:["all", "All Airspaces map"],
            optIFR:["ifr", "IFR map (Instrument Flihgt Rules"],
            optVFR:["vfr", "VFR map (Visual Flihgt Rules"],
            optFreeFlight:["ff", "FreeFlight map (Paragliding / Hanggliding)"]
            }



class AixmControler:

    def __init__(self, sSrcFile, sOutPath, sOutHeadFile="", oLog=None):
        bpaTools.initEvent(__file__, oLog)
        self.srcFile:str        = sSrcFile          #Source file
        self.sOutPath:str       = sOutPath          #Destination folder
        self.sOutHeadFile:str   = sOutHeadFile      #File name header for outputs files
        if sOutHeadFile!="":
            self.sOutHeadFile += "@"
        self.oLog:bpaTools.Logger = oLog            #Log file
        self.oAixm = None                           #Lecteur xml du fichier source
        self.oAixmTools = None                      #Utilitaire pour geojson
        self.sEncoding:str      = "utf-8"           #Encoding du fichier source
        self.__ALL:bool         = False             #Generation de toutes zones cartographie IFR+VFR
        self.__IFR:bool         = False             #Generation spécifique pour cartographie IFR (au dessus de FL115)
        self.__VFR:false        = False             #Generation spécifique pour cartographie VFR (en dessous FL115)
        self.__FreeFlight:bool  = False             #Generation spécifique pour le Vol Libre avec différents filtrages (E, F, G...)
        self.__Draft:bool       = False             #Limitation du nombre de segmentation des arcs et cercles en geojson
        self.__MakePoints4map:bool = False          #Construction de points complémentaires pour mise au point de la sorties geojson

        self.bOpenairOptimizeArc:bool = False       #Openair - Ne pas optimiser l'Arc car l'alignement du 1er point de l'arc de cercle ne coincide souvent pas avec le point théorique du départ de l'arc !? - Optimisation des sorties d'Arc en Openair (suppression des Point de début et de Fin d'arc (DP) en doublon avec la description de l'arc)
        self.bOpenairOptimizePoint:bool = True      #Openair - Optimisation des sorties des Points (DP). Exp src="DP 46:03:04.000 N 000:31:01.1200 W" optimize="DP 46:3:4N 0:31:1.12W"
        self.geojsonDigitOptimize:int =  6          #parameter for optimize output geometry coordinates (default=6 digits)
        self.openairDigitOptimize:int = -1          #parameter for optimize output geometry coordinates (default=-1 no-optimize)
        self.epsilonReduce:float = -1               #parameter for Ramer-Douglas-Peucker Algorithm (https://github.com/fhirschmann/rdp) (default=-1 no-optimize)
        return


    @property
    def Draft(self):
        return self.__Draft
    @Draft.setter
    def Draft(self, bValue):
        assert(isinstance(bValue, bool))
        self.__Draft = bValue
        if bValue:
            self.oLog.warning("/!\ Draft mode for circles design", outConsole=True)
        return


    @property
    def MakePoints4map(self):
        return self.__MakePoints4map
    @MakePoints4map.setter
    def MakePoints4map(self, bValue):
        assert(isinstance(bValue, bool))
        self.__MakePoints4map = bValue
        if bValue:
            self.oLog.warning("/!\ Complementary points for Map", outConsole=True)
        return

    @property
    def ALL(self):
        return self.__ALL       # Complet : IFR + VFR
    @ALL.setter
    def ALL(self, bValue):
        assert(isinstance(bValue, bool))
        self.__ALL = bValue
        return

    @property
    def IFR(self):
        return self.__IFR
    @IFR.setter
    def IFR(self, bValue):
        assert(isinstance(bValue, bool))
        self.__IFR = bValue
        return

    @property
    def VFR(self):
        return self.__VFR
    @VFR.setter
    def VFR(self, bValue):
        assert(isinstance(bValue, bool))
        self.__VFR = bValue
        return

    @property
    def FreeFlight(self):
        return self.__FreeFlight
    @FreeFlight.setter
    def FreeFlight(self, bValue):
        assert(isinstance(bValue, bool))
        self.__FreeFlight = bValue
        return


    def getFactory(self, context, out=None):
        if self.oAixm == None:
            return
        if self.oAixmTools == None:
            self.oAixmTools = aixmReader.AixmTools(self)
        if context=="reader":
            if self.oAixm.srcVersion == "4.5":
                return aixmReader.AixmAirspaces4_5(self)
            elif self.oAixm.srcVersion == "5.1":
                sys.stderr.write("Sorry, at thise time, the aixm 5.1 are not supported.\n")
                traceback.print_exc(file=sys.stdout)
                sys.exit()
            else:
                sys.stderr.write("Sorry, only aixm 4.5 are supported at this time.\n")
                traceback.print_exc(file=sys.stdout)
                sys.exit()
        if out=="geojson":
            if self.oAixm.srcVersion == "4.5":
                return aixm2json.Aixm2json4_5(self)
            elif self.oAixm.srcVersion == "5.1":
                sys.stderr.write("Sorry, at thise time, the aixm 5.1 are not supported.\n")
                traceback.print_exc(file=sys.stdout)
                sys.exit()
            else:
                sys.stderr.write("Sorry, only aixm 4.5 are supported at this time.\n")
                traceback.print_exc(file=sys.stdout)
                sys.exit()
        elif out=="openair":
            return aixm2openair.Aixm2openair(self)
        else:
            sys.stderr.write("Sorry, this format are not supported at this time.\n")
            traceback.print_exc(file=sys.stdout)
            sys.exit()
        return


    def saveAirspaces(self, parser, criticalErrCatalog=0):
        if self.ALL:    # and criticalErrCatalog==0:
            parser.saveAirspacesFilter(aixmReader.CONST.fileSuffixAndMsg[aixmReader.CONST.optALL])
        if self.IFR:    # and criticalErrCatalog==0:
            parser.saveAirspacesFilter(aixmReader.CONST.fileSuffixAndMsg[aixmReader.CONST.optIFR])
        if self.VFR:
            parser.saveAirspacesFilter(aixmReader.CONST.fileSuffixAndMsg[aixmReader.CONST.optVFR])
        if self.FreeFlight:
            parser.saveAirspacesFilter(aixmReader.CONST.fileSuffixAndMsg[aixmReader.CONST.optFreeFlight])
        return


    def execParser(self, oOpts, bOnlyCatalogConstruct:bool=False):
        self.ALL:bool                   = bool(CONST.optALL in oOpts)
        self.IFR:bool                   = bool(CONST.optIFR in oOpts)
        self.VFR:bool                   = bool(CONST.optVFR in oOpts)
        self.FreeFlight:bool            = bool(CONST.optFreeFlight in oOpts)
        self.Draft:bool                 = bool(CONST.optDraft in oOpts)
        self.MakePoints4map:bool        = bool(CONST.optMakePoints4map in oOpts)
        self.geojsonDigitOptimize:int   = int(oOpts.get(aixmReader.CONST.optGeojsonDigitOptimize, 6))       #Default=6 digits for Decimal.Degrees calculation/outputs
        self.openairDigitOptimize:int   = int(oOpts.get(aixmReader.CONST.optOpenairDigitOptimize, -1))      #Default=-1 not optimized
        self.epsilonReduce:float        = float(oOpts.get(aixmReader.CONST.optEpsilonReduce, -1))           #Defualt=-1 not optimized

        bExec = False

        #############################################################################################
        #Phase0 - Mise au point pour sorties geojson (sans lecture de fichier source)
        if CONST.optTstGeojson in oOpts:
            o2jsonTst = aixm2json.Aixm2jsonTst(self)
            o2jsonTst.testAll()
            return True

        #############################################################################################
        #Phase0 - Lecture du fichier aixm source
        found = any(item in (CONST.frmtGEOJSON, CONST.frmtOPENAIR, CONST.frmtALL) for item in oOpts.keys())
        if found:
            self.oAixm = aixmReader.AixmReader(self)

        #############################################################################################
        #Phase1 'geojson simplifiée'
        found = any(item in (CONST.frmtGEOJSON, CONST.frmtALL) for item in oOpts.keys())
        if found:
            o2json = self.getFactory("parser", "geojson")       #Récupération dynamique du parser aixm/geojson associé au format du fichier source

            #Phase1.1 - Traitement des Obstacles à la navigation aérienne
            found = any(item in (CONST.typeOBSTACLES, CONST.typeALL) for item in oOpts.keys())
            if found :
                o2json.parseObstacles()
                bExec = True

            #Phase1.2 - Traitement des Aérodromes
            found = any(item in (CONST.typeAERODROMES, CONST.typeALL) for item in oOpts.keys())
            if found :
                o2json.parseAerodromes()
                bExec = True

            #Phase1.3 - Traitement des Centres de pistes
            found = any(item in (CONST.typeRUNWAYCENTER, CONST.typeALL) for item in oOpts.keys())
            if found :
                o2json.parseRunwayCenterLinePosition()
                bExec = True

            #Phase1.4 - Traitement des Tours de contrôles
            found = any(item in (CONST.typeCTRLTOWERS, CONST.typeALL) for item in oOpts.keys())
            if found :
                o2json.parseControlTowers()
                bExec = True

            #Phase1.5 - Traitement des Aires de stationnement d'avions
            found = any(item in (CONST.typeGATESTANDS, CONST.typeALL) for item in oOpts.keys())
            if found :
                o2json.parseGateStands()
                bExec = True

            #Phase1.6 - Traitement de Bordures géographique
            found = any(item in (CONST.typeGEOBORDER, CONST.typeALL) for item in oOpts.keys())
            if found :
                o2json.parseGeographicBorders()
                bExec = True

        #############################################################################################
        #Phase2 - Traitements complexes concernant les espaces aériens (sorties multi-formats)
        found = any(item in (CONST.typeAIRSPACES, CONST.typeALL) for item in oOpts.keys())
        if found:
            oAs = self.getFactory("reader")                                     #Récupération dynamique du lecteur geojson associé au format du fichier source
            oAs.initAirspacesCatalogIdx()                                       #Initialisation des index pour construction du catalogue
            if not bOnlyCatalogConstruct:   oAs.initAirspacesBordersIdx()       #Initialisation de l'index des bordures de zones
            oAs.loadAirspacesCatalog()                                          #Lecture/Chargement de toutes les zones aériennes (classification & Propriétés)
            bOnlyCatalogConstruct:          oAs.ctrlReferentialContent()        #Contrôle de cohérence des référentiels
            oAs.saveAirspacesCalalog()                                          #Construction des catalogues
            oAs.clearAirspaceIdx()                                              #Libération de mémoire

            if bOnlyCatalogConstruct:
                return True

            #En cas d'err, interruption nécessaire pour mise à niveau du référentiel 'refGroundEstimatedHeight.json'
            criticalErrCatalog = self.oLog.CptCritical

            found = any(item in (CONST.frmtGEOJSON, CONST.frmtALL) for item in oOpts.keys())
            if found:
                if o2json == None:
                    o2json = self.getFactory("parser", "geojson")       #Récupération dynamique du parser aixm/geojson associé au format du fichier source
                o2json.parseAirspacesBorders(oAs)
                o2json.cleanAirspacesCalalog(oAs)
                self.saveAirspaces(o2json, criticalErrCatalog)
                bExec = True

            found = any(item in (CONST.frmtOPENAIR, CONST.frmtALL) for item in oOpts.keys())
            if found:
                o2openair = self.getFactory("parser", "openair")        #Récupération dynamique du parser aixm/openair associé au format du fichier source
                o2openair.parseAirspacesBorders(oAs)
                o2openair.cleanAirspacesCalalog(oAs)
                self.saveAirspaces(o2openair, criticalErrCatalog)
                bExec = True

            #if criticalErrCatalog>0:
            #    self.oLog.critical("Interrupt process; probably for update referential 'groundEstimatedHeight' - Show Critical errors details in log file", outConsole=True)
            if self.oLog.CptCritical>criticalErrCatalog:
                self.oLog.error("Show Critical errors items in log file", outConsole=True)

        return bExec

