#!/usr/bin/env python3

import bpaTools
from shapely.geometry import LineString, Point
import aixmReader


class Aixm2openair:
    
    def __init__(self, oCtrl):
        bpaTools.initEvent(__file__, oCtrl.oLog)
        self.oCtrl = oCtrl
        self.oAirspacesCatalog = None
        self.geoBorders = None                    #Geographic borders dictionary
        self.geoAirspaces = None                  #Geographic airspaces dictionary
        return        

    def parseGeographicBorders(self):
        sTitle = "Geographic borders"
        sXmlTag = "Gbr"
        
        sMsg = "Parsing {0} to OpenAir - {1}".format(sXmlTag, sTitle)
        self.oCtrl.oLog.info(sMsg)
        
        if self.geoBorders == None:
            self.geoBorders = dict()
            oList = self.oCtrl.oAixm.doc.find_all(sXmlTag)
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

    def gbr2openair(self, gbr):
        openair = []
        l = []
        sName = list(self.oCtrl.oAixmTools.getField(gbr.GbrUid, "txtName").values())[0]
        openair.append("AC G")
        openair.append("AN {0} (Geographic border)".format(sName))
        openair.append("AH SFC")        #or "AH 500 FT AMSL"
        openair.append("AL SFC")
        # geometry
        for gbv in gbr.find_all("Gbv"):
            if gbv.codeType.string not in ("GRC", "END"):
                self.oCtrl.oLog.critical("codetype non reconnu\n{0}".format(gbv), outConsole=True)
            lon, lat = self.oCtrl.oAixmTools.geo2coordinates(gbv)
            l.append((lon, lat))
            lat1, lon1 = bpaTools.GeoCoordinates.geoDd2dms(lat,"lat", lon,"lon", ":"," ")
            openair.append("DP {0} {1}".format(lat1, lon1))
        return openair, l

    def findOpenairObjectAirspacesBorders(self, sAseUid):
        for o in self.geoAirspaces:
            if o["properties"]["UId"]==sAseUid:
                return o["geometry"]
        return None
    
    def parseAirspacesBorders(self, airspacesCatalog):
        self.oAirspacesCatalog = airspacesCatalog
        
        #Controle de prerequis
        if self.geoBorders == None:
            self.parseGeographicBorders()
            
        sTitle = "Airspaces Borders"
        sXmlTag = "Abd"
        
        if not self.oCtrl.oAixm.doc.find(sXmlTag):
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
                        self.oCtrl.oLog.warning("Missing Airspaces Borders AseUid={0} of {1}".format(sAseUid, oZone["nameV"]), outConsole=False)
                    else:
                        openair = self.findOpenairObjectAirspacesBorders(sAseUidBase)       #Recherche si la zone de base a déjà été parsé
                        if openair:
                            self.geoAirspaces.append({"type":"Openair", "properties":oZone, "geometry":openair})
                        else:
                            oBorder = self.oAirspacesCatalog.findAixmObjectAirspacesBorders(sAseUidBase)
                            if oBorder==None:
                                self.oCtrl.oLog.warning("Missing Airspaces Borders AseUid={0} AseUidBase={1} of {2}".format(sAseUid, sAseUidBase, oZone["nameV"]), outConsole=False)
                            else:
                                self.parseAirspaceBorder(oZone, oBorder)
            barre.update(idx)
            
        barre.reset()
        return

    def parseAirspaceBorder(self, oZone, oBorder):
        g = []          #in memory
        openair = []    #geometry
        
        if oBorder.Circle:
            #Openair sample
            #V X=48:55:37 N 002:50:02 E
            #DC 2
            
            lon_c, lat_c = self.oCtrl.oAixmTools.geo2coordinates(oBorder.Circle,
                                           latitude=oBorder.Circle.geoLatCen.string,
                                           longitude=oBorder.Circle.geoLongCen.string)
            
            lat1, lon1 = bpaTools.GeoCoordinates.geoDd2dms(lat_c,"lat", lon_c,"lon", ":"," ")
            openair.append("V X={0} {1}".format(lat1, lon1))
            radius = float(oBorder.Circle.valRadius.string)
            radius = self.oCtrl.oAixmTools.convertLength(radius, oBorder.uomRadius.string, "NM")   #Convert radius in Nautical Mile for Openair format
            openair.append("DC {0}".format(radius))
            self.geoAirspaces.append({"type":"Openair", "properties":oZone, "geometry":openair})
            return

        #else:
        avx_list = oBorder.find_all("Avx")
        firstPoint = lastPoint = None
        for avx_cur in range(0,len(avx_list)):
            avx = avx_list[avx_cur]
            codeType = avx.codeType.string
            
            # 'Great Circle' or 'Rhumb Line' segment
            if codeType in ["GRC", "RHL"]:
                #Openair sample
                #DP 48:51:25 N 002:33:26 E
                
                lon, lat = self.oCtrl.oAixmTools.geo2coordinates(avx)
                g.append([lon, lat])
                lat1, lon1 = bpaTools.GeoCoordinates.geoDd2dms(lat,"lat", lon,"lon", ":"," ")
                sPoint = "DP {0} {1}".format(lat1, lon1)
                if sPoint != lastPoint:
                    openair.append(sPoint)
                firstPoint = self.pointMemory(firstPoint, sPoint)
                lastPoint = sPoint

            # 'Counter clockWise Arc' or 'Clockwise Arc'
            #Nota: 'ABE' = 'Arc By Edge' ne semble pas utilisé dans les fichiers SIA-France et Eurocontrol-Europe
            elif codeType in ["CCA", "CWA"]:
                #Openair sample
                #DP 48:24:15 N 002:07:55 E
                #V D=-
                #V X=48:22:52 N 002:04:26 E
                #DB 48:24:15 N 002:07:55 E,48:21:26 N 002:00:59 E
                #DP 48:21:26 N 002:00:59 E
                
                start = self.oCtrl.oAixmTools.geo2coordinates(avx, recurse=False)  
                g.append(start)
                
                if avx_cur+1 == len(avx_list):
                    stop = g[0]
                else:
                    stop = self.oCtrl.oAixmTools.geo2coordinates(avx_list[avx_cur+1], recurse=False)
                
                center = self.oCtrl.oAixmTools.geo2coordinates(avx,
                                         latitude=avx.geoLatArc.string,
                                         longitude=avx.geoLongArc.string)
                
                if codeType=="CCA":             #'Counter clockWise Arc'
                    openair.append("V D=-")
                else:
                    openair.append("V D=+")

                lonc, latc = center
                lons, lats = start
                lone, late = stop
                lat1c, lon1c = bpaTools.GeoCoordinates.geoDd2dms(latc,"lat", lonc,"lon", ":"," ")
                lat1s, lon1s = bpaTools.GeoCoordinates.geoDd2dms(lats,"lat", lons,"lon", ":"," ")
                lat1e, lon1e = bpaTools.GeoCoordinates.geoDd2dms(late,"lat", lone,"lon", ":"," ")
                
                sPoint = "DP {0} {1}".format(lat1s, lon1s)
                firstPoint = self.pointMemory(firstPoint, sPoint)
                if sPoint != lastPoint:
                    openair.append(sPoint)
                openair.append("V X={0} {1}".format(lat1c, lon1c))
                openair.append("DB {0} {1}, {2} {3}".format(lat1s, lon1s, lat1e, lon1e))
                sPoint = "DP {0} {1}".format(lat1e, lon1e)
                lastPoint = sPoint
                if sPoint != firstPoint:
                    openair.append(sPoint)

            # 'Sequence of geographical (political) border vertexes'
            elif codeType == "FNT":
                # geographic borders
                start = self.oCtrl.oAixmTools.geo2coordinates(avx)
                if avx_cur+1 == len(avx_list):
                    stop = g[0]
                else:
                    stop = self.oCtrl.oAixmTools.geo2coordinates(avx_list[avx_cur+1])
                    
                if avx.GbrUid["mid"] in self.geoBorders:
                    fnt = self.geoBorders[avx.GbrUid["mid"]]
                    start_d = fnt.project(Point(start[0], start[1]), normalized=True)
                    stop_d = fnt.project(Point(stop[0], stop[1]), normalized=True)
                    geom = self.oCtrl.oAixmTools.substring(fnt, start_d, stop_d, normalized=True)
                    for c in geom.coords:
                        lon, lat = c
                        g.append([lon, lat])
                        lat1, lon1 = bpaTools.GeoCoordinates.geoDd2dms(lat,"lat", lon,"lon", ":"," ")
                        sPoint = "DP {0} {1}".format(lat1, lon1)
                        lastPoint = sPoint
                        openair.append(sPoint)
                else:
                    self.oCtrl.oLog.warning("Missing geoBorder GbrUid='{0}' Name={1} of {2}".format(avx.GbrUid["mid"], avx.GbrUid.txtName.string, oZone["nameV"]), outConsole=False)
                    g.append(start)
            else:
                self.oCtrl.oLog.warning("Default case - GbrUid='{0}' Name={1} of {2}".format(avx.GbrUid["mid"], avx.GbrUid.txtName.string, oZone["nameV"]), outConsole=False)
                lon, lat = self.oCtrl.oAixmTools.geo2coordinates(avx)
                g.append([lon, lat])
                lat1, lon1 = bpaTools.GeoCoordinates.geoDd2dms(lat,"lat", lon,"lon", ":"," ")
                sPoint = "DP {0} {1}".format(lat1, lon1)
                if sPoint != lastPoint:
                    openair.append(sPoint)
                firstPoint = self.pointMemory(firstPoint, sPoint)
                lastPoint = sPoint

        self.geoAirspaces.append({"type":"Openair", "properties":oZone, "geometry":openair})
        return

    def pointMemory(self, memory:str, point:str) -> str:
        if memory==None:
            return point
        else:
            return memory

    def saveAirspacesFilter(self, aContext):
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

    def saveAirspacesFilter2(self, aContext, gpsType="", exceptDay=""):
        context = aContext[0]
        sMsg = "Prepare Openair file - {0} / {1} / {2}".format(aContext[1], gpsType, exceptDay)
        self.oCtrl.oLog.info(sMsg)
        barre = bpaTools.ProgressBar(len(self.oAirspacesCatalog.oAirspaces), 20, title=sMsg, isSilent=self.oCtrl.oLog.isSilent)
        idx = 0
        openair = []       #Initialisation avant filtrage spécifique
        for o in self.geoAirspaces:
            oZone = o["properties"]
            idx+=1
            include = False
            if not oZone["groupZone"]:                          #Ne pas traiter les zones de type 'Regroupement'
                if context=="all":                              include = True
                if context=="ifr" and not oZone["vfrZone"]:     include = True
                if context=="vfr" and oZone["vfrZone"]:         include = True
                if context=="ff" and oZone["freeFlightZone"]:   include = True
                if include==True and exceptDay!="":
                    if exceptDay in oZone:                      include = False
                if include==True:
                    openair.append(self.makeOpenair(o, gpsType))
            barre.update(idx)
        barre.reset()        
        if openair:
            self.oCtrl.oAixmTools.writeOpenairFile("airspaces", openair, context, gpsType, exceptDay)
        return



    #* Rappel: Syntaxe déclarative des Classes dans le format OpenAir
    #* 	AC <classType>
    #*   	  <ClassType> = Type of airspace class, see below:
    #*     		A	Class A
    #*     		B	Class B
    #*     		C	Class C
    #*     		D	Class D
    #*     		E	Class E
    #*     		F	Class F
    #*     		G	Class G
    #*     		W	Wave Window (espaces réservés aux vélivoles)
    #*     		R 	Restricted
    #*     		Q 	Danger
    #*     		P	Prohibited
    #*     		GP  Glider Prohibited
    #*     		CTR	CONTROL TRAFFIC AREAS
    #*		ZMT	ZONE REGLEMENTE TEMPORAIRE
    #*		RMZ	Radio Mandatory Zone
    #*		TMZ	Transponder Mandatory Zone
    #*		ZSM	Zone de Sensibilité Majeure (Protection Rapaces, Urubus, etc...)
    def makeOpenair(self, oAirspace:dict, gpsType):
        openair = []
        oZone = oAirspace["properties"]
                
        theClass = oZone["class"]
        theType = oZone["type"]

        #1/ Specific translations for Openair format
        if theClass=="D" and theType=="CTR":    theClass="CTR"     #CTR CONTROL TRAFFIC AREAS
        #2/ Specific translations for Openair format
        if   theType=="RMZ":                    theClass="RMZ"
        elif theType=="TMZ":                    theClass="TMZ"
        
        openair.append("AC {0}".format(theClass))
        openair.append("AN {0}".format(oZone["nameV"]))
        openair.append("*AAlt {0} {1}".format(oZone["alt"], oZone["altM"]))
        openair.append("*AUID UId={0} - Id={1}".format(oZone["UId"], oZone["id"]))
        if "desc" in oZone:    openair.append("*ADescr {0}".format(oZone["desc"]))
        if "activationCode" in oZone and ("activationDesc" in oZone):       openair.append("*AActiv [{0}] {1}".format(oZone["activationCode"], oZone["activationDesc"]))
        if not("activationCode" in oZone) and "activationDesc" in oZone:    openair.append("*AActiv {0}".format(oZone["activationDesc"]))
        if "activationCode" in oZone and not ("activationDesc" in oZone):   openair.append("*AActiv [{0}]".format(oZone["activationCode"]))
        if "exceptSAT" in oZone:    openair.append("*AExSAT {0}".format(oZone["exceptSAT"]))
        if "exceptSUN" in oZone:    openair.append("*AExSUN {0}".format(oZone["exceptSUN"]))
        if "exceptHOL" in oZone:    openair.append("*AExHOL {0}".format(oZone["exceptHOL"]))
        if "seeNOTAM" in oZone:     openair.append("*ASeeNOTAM {0}".format(oZone["seeNOTAM"]))
        openair.append("AH {0}".format(self.parseAlt("AH", gpsType, oZone)))
        openair.append("AL {0}".format(self.parseAlt("AL", gpsType, oZone)))
        openair += oAirspace["geometry"]
        return openair
        

    def parseAlt(self, altRef, gpsType, oZone:dict) -> str:
        if altRef=="AH":
            if gpsType=="-gpsWithoutTopo" and ("ordinalUpperM" in oZone):
                altM = oZone["upperM"]
                altFT = int(float(altM+100) / aixmReader.CONST.ft)      #Surélévation du plafond de 100 mètres pour marge d'altitude
                ret = "{0}FT AMSL".format(altFT)
                return ret
            sType = oZone["upperType"]
            sValue =  oZone["upperValue"]
            sUnit = oZone["upperUnit"]
        else:
            if gpsType=="-gpsWithoutTopo" and ("ordinalLowerM" in oZone):
                altM = oZone["lowerM"]
                altFT = int(float(altM-100) / aixmReader.CONST.ft)      #Abaissement du plancher de 100 mètres pour marge d'altitude
                if altFT <= 0:
                    ret = "SFC"
                else:
                    ret = "{0}FT AMSL".format(altFT)
                return ret
            sType = oZone["lowerType"]
            sValue =  oZone["lowerValue"]
            sUnit = oZone["lowerUnit"]        
        
        ret = "???"
        if   sValue=="0":
            ret = "SFC"                         #sample AH SFC
        elif sValue=="999" and sUnit=="FL":
            ret = "UNL"                         #sample AH UNL (or UNLIM)
        elif sUnit == "FL":
            ret = sUnit + sValue                #sample AH FL115
        elif sUnit in ["FT","SM","M"]:
            if sUnit=="SM":
                ret = sValue + "M"              #sample AH 2500M
            else:
                ret = sValue + sUnit            #sample AH 2500FT or AH 2500M
            if sType=="HEI":
                ret += " AGL"                    #sample AH 2500FT AGL     (or ASFC)
            else:
                ret += " AMSL"                   #sample AH 2500FT AMSL
        else:   
            self.oCtrl.oLog.error("parseAlt() error sType={0} sValue={1} sUnit={2}".format(sType, sValue, sUnit), outConsole=False)

        return ret



    
    