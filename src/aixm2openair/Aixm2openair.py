#!/usr/bin/env python3
import json
import decimal
from decimal import Decimal
from shapely.geometry import LineString, Point
from rdp import rdp

import bpaTools
import aixmReader
#import numpy as np   #Matrix sample: arr = np.array([["2","xx"], ["3","yy"], ["4","zz"]]); print(arr[:, 0]) ; print(arr[:, 1])


cstGeometry:str             = "geometry"         #Stockage du tracé Openair
openairAixmHeader:str       = "***(aixmParser) "
openairAixmSegmnt:str       = openairAixmHeader + "Openair Segments "
openairAixmWrn:str          = openairAixmHeader + "Warning "
errLocalisationPoint:list   = ["DP 45:00:00 N 005:00:00 W"]


#   digit = Integer parameter for optimize Openair output geometry coordinates (Default=-1 no-change source, n for round(coords, n, sample=0)
#   epsilonReduce = Float parameter of Ramer-Douglas-Peucker Algorithm (https://github.com/fhirschmann/rdp) for optimize output (Default=0 removal-duplicates-values and no-optimize, <0 for no-optimize or >0 for optimize, sample=0.0001)
def makeOpenair(oAirspace:dict, gpsType:str, digit:float=-1, epsilonReduce:float=-1, nbMaxSegment:int=-1, epsilonrDyn:bool=False, oLog:bpaTools.Logger=None) -> list:
    openair:list = []
    oZone:dict = oAirspace.get("properties", oAirspace)
    theClass:str = oZone["class"]
    theName:str  = oZone["nameV"]

    #theType = oZone["type"]
    #1/ Specific translations for Openair format
    #if theClass=="D" and theType=="CTR":    theClass="CTR"     #CTR CONTROL TRAFFIC AREAS
    #2/ Specific translations for Openair format
    #if   theType=="RMZ":                    theClass="RMZ"
    #elif theType=="TMZ":                    theClass="TMZ"

    openair.append("AC {0}".format(theClass))
    openair.append("AN {0}".format(theName))
    #old openair.append('*AAlt ["{0}", "{1}"]'.format(aixmReader.getSerializeAlt(oZone)[1:-1], aixmReader.getSerializeAltM(oZone)[1:-1]))
    aAlt:list = []
    aAlt.append("{0}".format(aixmReader.getSerializeAlt (oZone)[1:-1]))
    aAlt.append("{0}".format(aixmReader.getSerializeAltM(oZone)[1:-1]))
    if "freeFlightZoneExt" in oZone:
        if oZone["freeFlightZoneExt"] and (not oZone["freeFlightZone"]):
            aAlt.append("ffExt=Yes")
    #if "lowerM" in oZone:
    #    if float(oZone.get("lowerM", 0)) > 3504:  #FL115 = 3505m
    #        aAlt.append("ffExt=Yes")
    if len(aAlt)==3:
        openair.append('*AAlt ["{0}", "{1}", "{2}"]'.format(aAlt[0], aAlt[1], aAlt[2]))
    else:
        openair.append('*AAlt ["{0}", "{1}"]'.format(aAlt[0], aAlt[1]))

    sGUId:str = oZone.get("srcGUId", None)
    if sGUId==None:     sGUId = oZone.get("GUId", "!")
    sUId:str = oZone.get("srcUId", None)
    if sUId==None:      sUId:str = oZone.get("UId", "!")
    sId:str = oZone.get("id", "!")
    openair.append("*AUID GUId={0} UId={1} Id={2}".format(sGUId, sUId, sId))

    if "desc" in oZone:     openair.append("*ADescr {0}".format(oZone["desc"]))
    if "Mhz" in oZone:
        if isinstance(oZone["Mhz"], str):
            sDict:str = bpaTools.getContentOf(oZone["Mhz"], "{", "}", bRetSep=True)
            oAMhz:dict = json.loads(sDict)
        elif isinstance(oZone["Mhz"], dict):
            oAMhz:dict = oZone["Mhz"]
        else:
            oAMhz:dict = None
        openair.append("*AMhz {0}".format(json.dumps(oAMhz, ensure_ascii=False)))
    if ("activationCode" in oZone) and ("activationDesc" in oZone):       openair.append("*AActiv [{0}] {1}".format(oZone["activationCode"], oZone["activationDesc"]))
    if ("activationCode" in oZone) and not ("activationDesc" in oZone):   openair.append("*AActiv [{0}]".format(oZone["activationCode"]))
    if not("activationCode" in oZone) and ("activationDesc" in oZone):    openair.append("*AActiv {0}".format(oZone["activationDesc"]))
    if bool(oZone.get("declassifiable",  False)):   openair.append("*ADecla Yes")
    if "timeScheduling" in oZone:   openair.append("*ATimes {0}".format(json.dumps(oZone["timeScheduling"], ensure_ascii=False)))
    if bool(oZone.get("exceptSAT", False)):         openair.append("*AExSAT Yes")
    if bool(oZone.get("exceptSUN", False)):         openair.append("*AExSUN Yes")
    if bool(oZone.get("exceptHOL", False)):         openair.append("*AExHOL Yes")
    if bool(oZone.get("seeNOTAM",  False)):         openair.append("*ASeeNOTAM Yes")
    openair.append("AH {0}".format(parseAlt("AH", gpsType, oZone)))
    if oZone.get("ordinalUpperMaxM", False):        openair.append("*AH2 {0}".format(oZone["upperMax"]))
    openair.append("AL {0}".format(parseAlt("AL", gpsType, oZone)))
    if oZone.get("ordinalLowerMinM", False):        openair.append("*AL2 {0}".format(oZone["lowerMin"]))

    #Récupération des tracés de base
    oaMap:list = []
    if cstGeometry in oAirspace:
        oaMap = oAirspace[cstGeometry]
    iOrgSize:int = __getNbSegments(oaMap)

    #if theName in ["R 222 B (SeeNotam)"]:
    #    print("map")

    #Optimisation contextuelle des tracés
    #if epsilonReduce<0: --> do not change oaMap !
    if iOrgSize>9 and epsilonReduce>=0:                 #Ne pas optimiser les petites zones (ou cercles n'ayants que 2 segments ex: 'V X=49:16:30N 4:45:20E' + 'DC 1.0')
        if epsilonReduce==0 and epsilonrDyn and (theClass in ["GP","ZSM","G","E","Q","FFVL","FFVP"] or theName[:10]=="LTA FRANCE"):
            epsilonReduce=0.0001                        #Imposer une optimisation pour certaines zones

        if   iOrgSize > 6000:
            epsilonReduce = round(epsilonReduce*16, 6)  #0.0 standard || 0.0001->0.0016 filtre || 0.0004->0.0096 région
        elif iOrgSize > 4000:
            epsilonReduce = round(epsilonReduce*14, 6)  #0.0 standard || 0.0001->0.0014 filtre || 0.0004->0.0084 région
        elif iOrgSize > 3000:
            epsilonReduce = round(epsilonReduce*12, 6)  #0.0 standard || 0.0001->0.0012 filtre || 0.0004->0.0072 région
        elif iOrgSize > 2000:
            epsilonReduce = round(epsilonReduce*10, 6)  #0.0 standard || 0.0001->0.0010 filtre || 0.0004->0.0060 région
        elif iOrgSize > 1000:
            epsilonReduce = round(epsilonReduce* 8, 6)  #0.0 standard || 0.0001->0.0008 filtre || 0.0004->0.0048 région
        elif iOrgSize > 600:
            epsilonReduce = round(epsilonReduce* 6, 6)  #0.0 standard || 0.0001->0.0006 filtre || 0.0004->0.0036 région
        elif iOrgSize > 400:
            epsilonReduce = round(epsilonReduce* 4, 6)  #0.0 standard || 0.0001->0.0004 filtre || 0.0004->0.0024 région
        elif iOrgSize > 200:
            epsilonReduce = round(epsilonReduce* 2, 6)  #0.0 standard || 0.0001->0.0002 filtre || 0.0004->0.0012 région
        elif iOrgSize < 20:
            epsilonReduce=0.0                           #0.0 imposer la suppression de doublons
        #else:  #Cas 20 <= iOrgSize < 200
        #    Ne pas changer le coef 'epsilonReduce'     #0.0 standard || 0.0001 filtre || 0.0006 région
        oaMap = __optimizeMap(oaMap, digit, epsilonReduce, oLog)

    iNewSize:int = __getNbSegments(oaMap)
    iCount:int = 0
    if nbMaxSegment>0 and iNewSize>nbMaxSegment:
        #Cas spécifique d'une demande de limitation d'un nombre maximal de segment
        iDelta:int = iNewSize - nbMaxSegment
        orgEpsilonReduce:float = epsilonReduce
        #oLog.debug("RDP Optimisation Delta: {0} - count={1} rdp={2} / orgSize{3} newSize={4} (delta={5})".format(theName, iCount, epsilonReduce, iOrgSize, iNewSize, iDelta), level=1, outConsole=False)
        while iCount<50 and iDelta>0:
            iCount += 1                                                             #End While: iCount==50
            epsilonReduce:float = round(orgEpsilonReduce*(1 + (iCount*0.2)), 6)     #End while: 0.002*(1 + (0.2*50)) = 0.022
            oaMap = __optimizeMap(oaMap, digit, epsilonReduce, oLog)
            iNewSize = __getNbSegments(oaMap)
            iDelta = iNewSize - nbMaxSegment
            #oLog.debug("RDP Optimisation Delta: {0} - count={1} rdp={2} / orgSize{3} newSize={4} (delta={5})".format(theName, iCount, epsilonReduce, iOrgSize, iNewSize, iDelta), level=1, outConsole=False)

    if iNewSize>0 and iNewSize!=iOrgSize:
        if oLog:
            percent:float = round((1-(iNewSize/iOrgSize))*100,1)
            percent = int(percent) if percent>=1.0 else percent
            if iCount>0:
                sOpti:str = "Optimisés à {0}% ({1}->{2}) [rdp={3}, iCount={4}]".format(percent, iOrgSize, iNewSize, epsilonReduce, iCount)
            else:
                sOpti:str = "Optimisés à {0}% ({1}->{2}) [rdp={3}]".format(percent, iOrgSize, iNewSize, epsilonReduce)
            if oaMap[0][:len(openairAixmSegmnt)]==openairAixmSegmnt:
                sOpti = oaMap[0] + " // " + sOpti
            #Sortie dans le log uniquement en debug level>0
            oLog.debug("Openair RDP Optimisation: {0} - {1}".format(theName, sOpti), level=1, outConsole=False)
            #Sortie dans l'Openair uniquement en debug level>0
            if oLog.debugLevel>0:
                if oaMap[0][:len(openairAixmSegmnt)]==openairAixmSegmnt:
                    oaMap[0] = sOpti
                else:
                    openair.append(openairAixmSegmnt+sOpti)
    else:
        #Sortie dans l'Openair uniquement en debug level>1
        if oLog.debugLevel>1:
            if oaMap[0][:len(openairAixmSegmnt)]!=openairAixmSegmnt:
                openair.append(openairAixmSegmnt+"{0}".format(iOrgSize))

    openair += oaMap
    return openair


def __getNbSegments(oaMap:list) -> int:
    iSize:int = len(oaMap)
    if oaMap[0][:len(openairAixmSegmnt)]==openairAixmSegmnt:
        iSize -= 1
    return iSize


#Optimisation de la sortie Openair selon l'algo 'Ramer-Douglas-Peucker'
#Optimise les coordonnées Openair sur la base des coordonnées DMS au format Openair
def __optimizeMap(oaMap:list, digit:float, epsilonReduce:float, oLog:bpaTools.Logger=None) -> list:
    newMap:list = []
    oIdx:dict = {}

    def optimize(oIdx:dict) -> list:
        retMap:list = []
        oaDeb:int = oIdx["oaDeb"]
        retMap = oaMap[oaDeb:oaDeb+iNbPt]
        if iNbPt>3:     #Ne jamais optimiser les tracés de moins de 3 points (car si l'on supprime 1 pt, il ne subsiste qu'1 ligne)
            tmpMap:list = []
            for dmsPt in retMap:
                if dmsPt[0:len(openairAixmHeader)]==openairAixmHeader:
                    print("stop")
                aPtDms = dmsPt.split(" ")
                ptDD = bpaTools.GeoCoordinates.geoStr2coords(aPtDms[1], aPtDms[2], "dd", 8)
                tmpMap.append(ptDD[::-1])                           #Invertion des coordonnées
            rdpMap = rdp(tmpMap, epsilon=epsilonReduce)             #Optimisation du tracé des coordonnées
            if len(rdpMap)!=len(tmpMap):
                newMap:list = []
                for ddPt in rdpMap:
                    lon, lat = ddPt
                    ptDMS = bpaTools.GeoCoordinates.geoStr2coords(lat, lon, "dms", sep1=":", sep2="", bOptimize=True, digit=digit)
                    sPoint:str = "DP {0} {1}".format(ptDMS[0], ptDMS[1])
                    newMap.append(sPoint)
                    if oLog:
                        aTocken:list=[":60",":61"]      #Chercher err dans minutes/secondes (les degrees a plus de 60 sont valides '61:28:0W')
                        if any(sTocken in sPoint for sTocken in aTocken):
                            sMsg:str = "Convertion error - ddPt={0} ptDMS={1}".format(ddPt, ptDMS)
                            oLog.error(sMsg, outConsole=False)
                retMap = newMap

        oaDeb+=iNbPt
        oIdx.update({"oaDeb":oaDeb})
        return retMap

    iNbPt:int = 0
    oIdx.update({"oaDeb":iNbPt})
    for iIdx in range(0, len(oaMap)):
        oaPt = oaMap[iIdx]
        #if oaPt[:3] in ["V X","DC ","V D","DB ","***"]:     #Old - Ne pas optimiser les Cercles ou Arcs ou autres
        if oaPt[:3]!="DP ":                                  #N'optimiser que les séries de Points (ex:'DP 49:50:0N 0:37:0E')
            if iNbPt>0:
                newMap += optimize(oIdx)
                iNbPt:int = 0
            newMap.append(oaPt)
            oaDeb:int = oIdx["oaDeb"]
            oIdx.update({"oaDeb":oaDeb+1})
        else:
            iNbPt += 1
    newMap += optimize(oIdx)
    return newMap


def parseAlt(altRef:str, gpsType:str, oZone:dict) -> str:
    if altRef=="AH":
        if gpsType=="-gpsWithoutTopo" and (("ordinalUpperMaxM" in oZone) or ("ordinalUpperM" in oZone)):
            altM = oZone["upperM"]
            altFT = int(float(altM+100) / aixmReader.CONST.ft)      #Surélévation du plafond de 100 mètres pour marge d'altitude
            ret = "{0}FT AMSL".format(altFT)
            return ret
        #elif "ordinalUpperMaxM" in oZone:
        #    return oZone["upperMax"]
        else:
            if ("upper" in oZone):
                return oZone["upper"]
            else:
                return "FL999"
    elif altRef=="AL":
        if gpsType=="-gpsWithoutTopo" and (("ordinalLowerMinM" in oZone) or ("ordinalLowerM" in oZone)):
            altM = oZone["lowerM"]
            altFT = int(float(altM-100) / aixmReader.CONST.ft)      #Abaissement du plancher de 100 mètres pour marge d'altitude
            if altFT <= 0:
                ret = "SFC"
            else:
                ret = "{0}FT AMSL".format(altFT)
            return ret
        #elif "ordinalLowerMinM" in oZone:
        #    return oZone["lowerMin"]
        else:
            if ("lower" in oZone):
                return oZone["lower"]
            else:
                return "SFC"
    else:
        print("parseAlt() calling error !")
    return


class Aixm2openair:

    def __init__(self, oCtrl) -> None:
        bpaTools.initEvent(__file__, oCtrl.oLog)
        self.oCtrl = oCtrl
        self.oAirspacesCatalog = None
        self.geoBorders = None                  #Geographic borders dictionary
        self.geoAirspaces = None                #Geographic airspaces dictionary
        self.openairDigitOptimize:int = -1      #Parameter for optimize output geometry coordinates (default=-1 no-optimize)
        self.epsilonReduce:float = -1           #Default value=-1 for no-compression
        self.sOutFrmt = "D:M:S.ssX" if self.oCtrl.bOpenairOptimizePoint else "DD:MM:SS.ssX"
        return

    def parseGeographicBorders(self) -> None:
        sTitle = "Geographic borders"
        sXmlTag = "Gbr"

        sMsg = "Parsing {0} to OpenAir - {1}".format(sXmlTag, sTitle)
        self.oCtrl.oLog.info(sMsg)

        if self.geoBorders == None:
            self.geoBorders = dict()
            oList = self.oCtrl.oAixm.root.find_all(sXmlTag, recursive=False)
            barre = bpaTools.ProgressBar(len(oList), 20, title=sMsg, isSilent=self.oCtrl.oLog.isSilent)
            idx = 0
            openair = []
            for gbr in oList:
                idx+=1
                j,l = self.gbr2openair(gbr)
                openair.append(j)
                self.geoBorders[gbr.GbrUid["mid"]] = LineString(l)
                barre.update(idx)
        barre.reset()
        self.oCtrl.oAixmTools.writeOpenairFile("borders", openair)
        return

    def gbr2openair(self, gbr) -> list:
        openair = []
        l = []
        sName = list(self.oCtrl.oAixmTools.getField(gbr.GbrUid, "txtName").values())[0]
        openair.append("AC G")
        openair.append("AN {0} (Geographic border)".format(sName))
        openair.append("AH SFC")        #or "AH 500 FT AMSL"
        openair.append("AL SFC")
        # geometry
        for gbv in gbr.find_all("Gbv", recursive=False):
            if gbv.codeType.string not in ("GRC", "END"):
                self.oCtrl.oLog.critical("codetype non reconnu\n{0}".format(gbv), outConsole=True)
            lat, lon = self.oCtrl.oAixmTools.geo2coordinates("dd", gbv)
            l.append((lon, lat))
            lat1, lon1 = self.oCtrl.oAixmTools.geo2coordinates(self.sOutFrmt, gbv)
            openair.append("DP {0} {1}".format(lat1, lon1))
        return openair, l

    def findOpenairObjectAirspacesBorders(self, sAseUid) -> dict:
        for o in self.geoAirspaces:
            if o["properties"]["UId"]==sAseUid:
                return o
        return None

    def parseAirspacesBorders(self, airspacesCatalog) -> None:
        self.oAirspacesCatalog = airspacesCatalog

        #Controle de prerequis
        if self.geoBorders == None:
            self.parseGeographicBorders()

        sTitle = "Airspaces Borders"
        sXmlTag = "Abd"

        if not self.oCtrl.oAixm.root.find(sXmlTag, recursive=False):
            sMsg = "Missing tags {0} - {1}".format(sXmlTag, sTitle)
            self.oCtrl.oLog.warning(sMsg, outConsole=True)
            return

        sMsg = "Parsing {0} to OpenAir - {1}".format(sXmlTag, sTitle)
        self.oCtrl.oLog.info(sMsg)

        barre = bpaTools.ProgressBar(len(self.oAirspacesCatalog.oAirspaces), 20, title=sMsg, isSilent=self.oCtrl.oLog.isSilent)
        idx = 0
        self.geoAirspaces = []                #Réinitialisation avant traitement global
        for k,oZone in self.oAirspacesCatalog.oAirspaces.items():
            idx+=1
            if not oZone["groupZone"]:          #Ne pas traiter les zones de type 'Regroupement'
                sAseUid = oZone["UId"]
                oBorder = self.oAirspacesCatalog.findAixmObjectAirspacesBorders(sAseUid)
                if oBorder:
                    self.parseAirspaceBorder(oZone, oBorder)
                else:
                    sAseUidBase = self.oAirspacesCatalog.findZoneUIdBase(sAseUid)           #Identifier la zone de base (de référence)
                    if sAseUidBase==None:
                        sWrn:str = "Missing Airspaces Borders AseUid={0} of {1}".format(sAseUid, oZone["nameV"])
                        self.oCtrl.oLog.warning(sWrn, outConsole=False)
                        self.geoAirspaces.append({"type":"Openair", "properties":oZone, cstGeometry:[openairAixmWrn+sWrn]+errLocalisationPoint})
                    else:
                        o:dict = self.findOpenairObjectAirspacesBorders(sAseUidBase)       #Recherche si la zone de base a déjà été parsé
                        if o:
                            openair:list = o.get(cstGeometry, None)
                            self.geoAirspaces.append({"type":"Openair", "properties":oZone, cstGeometry:openair})
                        else:
                            oBorder = self.oAirspacesCatalog.findAixmObjectAirspacesBorders(sAseUidBase)
                            if oBorder==None:
                                sWrn:str = "Missing Airspaces Borders AseUid={0} AseUidBase={1} of {2}".format(sAseUid, sAseUidBase, oZone["nameV"])
                                self.oCtrl.oLog.warning(sWrn, outConsole=False)
                                self.geoAirspaces.append({"type":"Openair", "properties":oZone, cstGeometry:[openairAixmWrn+sWrn]+errLocalisationPoint})
                            else:
                                self.parseAirspaceBorder(oZone, oBorder)
            barre.update(idx)

        barre.reset()
        return

    def parseAirspaceBorder(self, oZone, oBorder) -> None:
        openair:list = []   #geometry Openair

        #Init
        bIsSpecCircle:bool = False
        bIsCircle:bool = bool(oBorder.Circle)   #Zone uniqumement contituée d'un cercle
        if not bIsCircle:
            #Extraction des vecteurs
            avx_list = oBorder.find_all("Avx", recursive=False)

            #Si la zone est 'Danger' ou 'Vol libre et Vol a voile' ; et uniquement déclarée sous forme d'un 'Point' ; alors reconstituer un cercle !
            if len(avx_list)==1 and oZone.get("class",None) in ["Q","W"]:   bIsSpecCircle = True

        #Construction d'un cercle standard
        if bIsCircle:
            #Openair sample
            #V X=48:55:37 N 002:50:02 E
            #DC 2

            sLat_c, sLon_c = self.oCtrl.oAixmTools.geo2coordinates(self.sOutFrmt,
                                                                   oBorder.Circle,
                                                                   latitude=oBorder.Circle.geoLatCen.string,
                                                                   longitude=oBorder.Circle.geoLongCen.string,
                                                                   oZone=oZone)

            openair.append("V X={0} {1}".format(sLat_c, sLon_c))
            radius:float = float(oBorder.Circle.valRadius.string)
            radius = self.oCtrl.oAixmTools.convertLength(radius, oBorder.uomRadius.string, "NM")    #Convert radius in Nautical Mile for Openair format
            #Rappel: 'Bulle de quiétude' - La FFVL a négocié avec les LPO un espace protégé de 150m (0.081 MN - Milles Nautics) autour et au dessus des nids d'oiseaux. De mon coté, je retiens 0.1 MN = 185m
            nInt, nDec = str(radius).split(".")
            if radius > 1:                          #Au delà d'un rayon de 1850 mètres (1 Mile Nautic)
                if len(nDec)>3:                     #Reste de division du type '0.01'
                    radius2:Decimal = Decimal(radius).quantize(Decimal('0.1'), decimal.ROUND_UP)            #Arrondi suppérieur
                else:
                    radius2:Decimal = radius        #Pas besoin d'arrondi
            else:
                if len(nDec)>4:                     #Reste de division du type '0.001'
                    radius2:Decimal = Decimal(radius).quantize(Decimal('0.01'), decimal.ROUND_05UP)         #Arrondi suppérieur au delà du demi
                else:
                    radius2:Decimal = radius        #Pas besoin d'arrondi
            openair.append("DC {0}".format(radius2))
            self.geoAirspaces.append({"type":"Openair", "properties":oZone, cstGeometry:openair})
            return

        #Construction spécifique d'un cercle sur la base d'un Point unique
        elif bIsSpecCircle:
            sLat_c, sLon_c = self.oCtrl.oAixmTools.geo2coordinates(self.sOutFrmt, avx_list[0], oZone=oZone)
            openair.append("V X={0} {1}".format(sLat_c, sLon_c))

            #radius in Nautical Mile for Openair format / Depend of area type
            radius:float = float(0.54)              #Fixe un rayon de 1000m par défaut
            if   oZone["type"] in ["TRVL"]:         #TRVL Treuil-Vol-Libre
                radius = float(1.08)                #Fixe un rayon de 2000m
            elif oZone["type"] in ["TRPLA"]:        #TRPLA Treuil Planeurs
                radius = float(2.7)                 #Fixe un rayon de 5000m
            elif oZone["type"] in ["PJE"]:          #PJE=Parachute Jumping Exercise
                radius = float(0.54)                #Fixe un rayon de 1000m

            openair.append("DC {0}".format(radius))
            self.geoAirspaces.append({"type":"Openair", "properties":oZone, cstGeometry:openair})
            return

        #Construction d'un tracé sur la base d'une suite de Points et/ou Arcs
        firstCoords = {}                        #Mémorisation des coordonees du premier point (en dd et DMS.d)
        firstPoint = lastPoint = None           #Mémorisation des lignes: premier et dernier point
        for avx_cur in range(0,len(avx_list)):
            avx = avx_list[avx_cur]
            codeType = avx.codeType.string

            # 'Great Circle' or 'Rhumb Line' segment
            if codeType in ["GRC", "RHL"]:
                #Openair sample
                #DP 48:51:25 N 002:33:26 E

                if not "dd" in firstCoords:
                    ptDD = self.oCtrl.oAixmTools.geo2coordinates("dd", avx, oZone=oZone)
                    firstCoords.update({"dd":ptDD})
                ptDMS = self.oCtrl.oAixmTools.geo2coordinates(self.sOutFrmt, avx, oZone=oZone)
                if not "dms" in firstCoords:        firstCoords.update({"dms":ptDMS})
                sPoint = "DP {0} {1}".format(ptDMS[0], ptDMS[1])
                if sPoint != lastPoint:
                    openair.append(sPoint)
                firstPoint = self.pointMemory(firstPoint, sPoint)
                lastPoint = sPoint

            # 'Counter clockWise Arc' or 'Clockwise Arc'
            #Nota: 'ABE' = 'Arc By Edge' ne semble pas utilisé dans les fichiers SIA-France et Eurocontrol-Europe
            elif codeType in ["CCA", "CWA"]:
                #Openair sample
                #DP 48:24:15 N 002:07:55 E          --> Point de début d'arc, souvent précisé mais optionnel dans l'Openair
                #V X=48:22:52 N 002:04:26 E
                #V D=-
                #DB 48:24:15 N 002:07:55 E,48:21:26 N 002:00:59 E
                #DP 48:21:26 N 002:00:59 E          --> Point de fin d'arc, souvent précisé mais optionnel dans l'Openair

                if not "dd" in firstCoords:
                    startDD = self.oCtrl.oAixmTools.geo2coordinates("dd", avx, oZone=oZone)
                    firstCoords.update({"dd":startDD})
                startDMS = self.oCtrl.oAixmTools.geo2coordinates(self.sOutFrmt, avx, oZone=oZone)
                if not "dms" in firstCoords:        firstCoords.update({"dms":startDMS})

                if avx_cur+1 == len(avx_list):
                    stopDMS = firstCoords["dms"]
                else:
                    stopDMS = self.oCtrl.oAixmTools.geo2coordinates(self.sOutFrmt, avx_list[avx_cur+1], oZone=oZone)

                centerDMS = self.oCtrl.oAixmTools.geo2coordinates(self.sOutFrmt, avx,
                                         latitude=avx.geoLatArc.string,
                                         longitude=avx.geoLongArc.string,
                                         oZone=oZone)

                #BPa 14/02/2021 - Optimisation possible par flag 'bOpenairOptimizeArc' car duplication du point de départ d'arc optionnel
                sPoint = "DP {0} {1}".format(startDMS[0], startDMS[1])
                firstPoint = self.pointMemory(firstPoint, sPoint)
                if sPoint != lastPoint and not self.oCtrl.bOpenairOptimizeArc:
                    openair.append(sPoint)
                    lastPoint = sPoint

                openair.append("V X={0} {1}".format(centerDMS[0], centerDMS[1]))
                if codeType=="CCA":             #'Counter clockWise Arc'
                    openair.append("V D=-")
                else:
                    openair.append("V D=+")
                openair.append("DB {0} {1}, {2} {3}".format(startDMS[0], startDMS[1], stopDMS[0], stopDMS[1]))

                #BPa 14/02/2021 - Optimisation possible par flag 'bOpenairOptimizeArc' car duplication du point de sortie d'arc optionnel
                if not self.oCtrl.bOpenairOptimizeArc:
                    sPoint = "DP {0} {1}".format(stopDMS[0], stopDMS[1])
                    openair.append(sPoint)
                    lastPoint = sPoint

            # 'Sequence of geographical (political) border vertexes'
            elif codeType == "FNT":
                # geographic borders
                if avx.GbrUid["mid"] in self.geoBorders:
                    startDD = self.oCtrl.oAixmTools.geo2coordinates("dd", avx, oZone=oZone)
                    if avx_cur+1 == len(avx_list):
                        stopDD  = firstCoords["dd"]
                    else:
                        stopDD = self.oCtrl.oAixmTools.geo2coordinates("dd", avx_list[avx_cur+1], oZone=oZone)
                    fnt = self.geoBorders[avx.GbrUid["mid"]]
                    start_d = fnt.project(Point(startDD[::-1]), normalized=True)                            #Invertion des coordonnees
                    stop_d = fnt.project(Point(stopDD[::-1]), normalized=True)                              #Invertion des coordonnees
                    geom = self.oCtrl.oAixmTools.substring(fnt, start_d, stop_d, normalized=True)
                    sPointPrev = None
                    for ptDD in geom.coords:
                        lon, lat = ptDD
                        if not "dd" in firstCoords:         firstCoords.update({"dd":ptDD[::-1]})           #Invertion des coordonnees
                        ptDMS = bpaTools.GeoCoordinates.geoStr2coords(lat, lon, "dms", sep1=":", sep2="", bOptimize=True, digit=self.oCtrl.openairDigitOptimize)
                        if not "dms" in firstCoords:        firstCoords.update({"dms":ptDMS})
                        sPoint = "DP {0} {1}".format(ptDMS[0], ptDMS[1])
                        firstPoint = self.pointMemory(firstPoint, sPoint)
                        if sPoint != sPointPrev:
                            lastPoint = sPoint
                            openair.append(sPoint)
                            sPointPrev = sPoint
                else:
                    sWrn:str = "Missing geoBorder GbrUid='{0}' Name={1} of {2}".format(avx.GbrUid["mid"], avx.GbrUid.txtName.string, oZone["nameV"])
                    self.oCtrl.oLog.warning(sWrn, outConsole=False)
                    openair.append(openairAixmWrn+sWrn)
                    if not "dd" in firstCoords:
                        startDD = self.oCtrl.oAixmTools.geo2coordinates("dd", avx, oZone=oZone)
                        firstCoords.update({"dd":startDD})
                    startDMS = self.oCtrl.oAixmTools.geo2coordinates(self.sOutFrmt, avx, oZone=oZone)
                    if not "dms" in firstCoords:      firstCoords.update({"dms":startDMS})
                    sPoint = "DP {0} {1}".format(startDMS[0], startDMS[1])
                    openair.append(sPoint)
                    lastPoint = sPoint
            else:
                sWrn:str = "Default case - GbrUid='{0}' Name={1} of {2}".format(avx.GbrUid["mid"], avx.GbrUid.txtName.string, oZone["nameV"])
                self.oCtrl.oLog.warning(sWrn, outConsole=False)
                openair.append(openairAixmWrn+sWrn)
                if not "dd" in firstCoords:
                    ptDD = self.oCtrl.oAixmTools.geo2coordinates("dd", avx, oZone=oZone)
                    firstCoords.update({"dd":ptDD})
                ptDMS = self.oCtrl.oAixmTools.geo2coordinates(self.sOutFrmt, avx, oZone=oZone)
                if not "dms" in firstCoords:      firstCoords.update({"dms":ptDMS})
                sPoint = "DP {0} {1}".format(ptDMS[0], ptDMS[1])
                if sPoint != lastPoint:
                    openair.append(sPoint)
                firstPoint = self.pointMemory(firstPoint, sPoint)
                lastPoint = sPoint

        #Contrôle de fermeture du Polygone
        if lastPoint != firstPoint:
            openair.append(firstPoint)
            lastPoint = firstPoint

        self.geoAirspaces.append({"type":"Openair", "properties":oZone, cstGeometry:openair})
        return

    def pointMemory(self, memory:str, point:str) -> str:
        if memory==None:
            return point
        else:
            return memory

    #Use epsilonReduce for compress shape in file (Nota. epsilonReduce=0 for no-doubling with no-compression, =0.0001 for good compression)
    def saveAirspacesFilter(self, aContext:list, digit:float=None, epsilonReduce:float=None) -> None:
        if digit and digit>0:
            self.openairDigitOptimize = digit
        else:
            self.openairDigitOptimize = self.oCtrl.openairDigitOptimize
        if epsilonReduce and epsilonReduce>0:
            self.epsilonReduce = epsilonReduce
        else:
            self.epsilonReduce = self.oCtrl.epsilonReduce
        context = aContext[0]
        if context=="ff":
            self.saveAirspacesFilter2(aContext, "-gpsWithTopo")
            self.saveAirspacesFilter2(aContext, "-gpsWithTopo", "exceptSAT")
            self.saveAirspacesFilter2(aContext, "-gpsWithTopo", "exceptSUN")
            self.saveAirspacesFilter2(aContext, "-gpsWithTopo", "exceptHOL")
            self.saveAirspacesFilter2(aContext, "-gpsWithoutTopo")
            self.saveAirspacesFilter2(aContext, "-gpsWithoutTopo", "exceptSAT")
            self.saveAirspacesFilter2(aContext, "-gpsWithoutTopo", "exceptSUN")
            self.saveAirspacesFilter2(aContext, "-gpsWithoutTopo", "exceptHOL")
        else:    #context == "all", "ifr" or "vfr"
            self.saveAirspacesFilter2(aContext, "-gpsWithTopo")
        return

    def saveAirspacesFilter2(self, aContext:list, gpsType:str="", exceptDay:str="") -> None:
        if not self.geoAirspaces:                                   #Contrôle si le fichier est vide
            return
        context = aContext[0]
        sMsg = "Prepare Openair file - {0} / {1} / {2}".format(aContext[1], gpsType, exceptDay)
        self.oCtrl.oLog.info(sMsg)
        barre = bpaTools.ProgressBar(len(self.oAirspacesCatalog.oAirspaces), 20, title=sMsg, isSilent=self.oCtrl.oLog.isSilent)
        idx = 0
        openair = []       #Initialisation avant filtrage spécifique
        for o in self.geoAirspaces:
            oZone = o["properties"]
            idx+=1
            include = not oZone["groupZone"]                            #Ne pas traiter les zones de type 'Regroupement'
            if include and ("excludeAirspaceNotCoord" in oZone):        #Ne pas traiter les zones qui n'ont pas de coordonnées geometriques
                include = not oZone["excludeAirspaceNotCoord"]
            if include:
                if len(o[cstGeometry])==1:
                    #Exclure toutes zones en erreur de localisation (oAs.oBorder[0]!=errLocalisationPoint)
                    include = False
                elif len(o[cstGeometry])==2 and o[cstGeometry][0][:4]!="V X=":
                    #Exclure les doubles points fixes (DP.. + DP..) mais autoriser les cercles (V X=.. + DP..)
                   include = False
                else:
                    include = False
                    if context=="all":
                        include = True
                    elif context=="ifr":
                        include = (not oZone["vfrZone"]) and (not oZone["groupZone"])
                    elif context=="vfr":
                        include = oZone["vfrZone"]
                        include = include or oZone.get("vfrZoneExt", False)   			#Exporter l'extension de vol possible en VFR de 0m jusqu'au FL195/5944m
                    elif context=="ff":
                        include = oZone["freeFlightZone"]
                        include = include or oZone.get("freeFlightZoneExt", False)		#Exporter l'extension de vol possible en VFR de 0m jusqu'au FL195/5944m
                if include==True and exceptDay!="":
                    if exceptDay in oZone:                              include = False
                if include==True:
                    openair.append(makeOpenair(o, gpsType, digit=self.openairDigitOptimize, epsilonReduce=self.epsilonReduce, oLog=self.oCtrl.oLog))
            barre.update(idx)
        barre.reset()
        if openair:
            self.oCtrl.oAixmTools.writeOpenairFile("airspaces", openair, context, gpsType, exceptDay, digit=self.openairDigitOptimize, epsilonReduce=self.epsilonReduce)
        return

    #Nétoyage du catalogue de zones pour desactivation d'éléments non-valides; ou constitués que d'un ou de deux 'Point'
    #Ces simples 'Point remarquable' sont supprimés de la cartographie freefligth (ex: un VOR, un émméteur radio, un centre de piste)
    #Idem, suppression des 'lignes' (ex: Axe d'approche d'un aérodrome ou autres...)
    def cleanAirspacesCalalog(self, airspacesCatalog) -> None:
        if not self.geoAirspaces:                                   #Contrôle si le fichier est vide
            return
        self.oAirspacesCatalog = airspacesCatalog
        #if self.oAirspacesCatalog.cleanAirspacesCalalog:     #Contrôle si l'optimisation est déjà réalisée
        #    return

        sMsg = "Clean catalog"
        self.oCtrl.oLog.info(sMsg)
        barre = bpaTools.ProgressBar(len(self.geoAirspaces), 20, title=sMsg, isSilent=self.oCtrl.oLog.isSilent)
        idx = 0
        lNbChange = 0
        for o in self.geoAirspaces:
            oZone = o["properties"]
            idx+=1

            #Flag all not valid area
            oGeom:dict = o[cstGeometry]                          #Sample - "geometry": {"type": "Polygon", "coordinates": [[['DP 44:21:02 N 001:28:43 E'], ../..
            if len(oGeom)==0:
                oZone.update({"excludeAirspaceNotCoord":True})          #Flag this change in catalog
                lNbChange+=1

            if len(oGeom)==1:                               #Point
                exclude=True
                oZone.update({"geometryType":"Point"})        #info for catalog "Point"
                #Transformer systématiquement les 'Point simples' en cercle de rayon 1 Km = 0.54 NM (Nautic Milles)
                #exemple d'un Point d'ogigine: ['DP 44:21:02 N 001:28:43 E']
                #se transforme en - ['V X=44:21:02 N 001:28:43 E', 'DC 0.54']
                oGeom[0] = "V X=" + oGeom[0][3:]
                oGeom.append("DC 0.54")
            elif len(oGeom)==2 and oGeom[0][:4]!="V X=":    #Line
                exclude=True
            else:
                exclude=False
            if exclude:
                oZone.update({"freeFlightZone":False})              	#Change value in catalog
                if oZone.get("freeFlightZoneExt", False)==True:
                    oZone.update({"freeFlightZoneExt":False})           #Change value in catalog
                oZone.update({"excludeAirspaceNotFfArea":True})       	#Flag this change in catalog
                lNbChange+=1
            barre.update(idx)
        barre.reset()

        if lNbChange>0:
            self.oAirspacesCatalog.saveAirspacesCalalog()               #Save the new catalogs

        self.oAirspacesCatalog.cleanAirspacesCalalog = True  #Marqueur de traitement réalisé
        return
