#!/usr/bin/env python3

try:
    import bpaTools
except ImportError:
    import os, sys
    sLocalSrc:str = "../"                                       #Include local modules/librairies
    module_dir = os.path.dirname(__file__)
    sys.path.append(os.path.join(module_dir, sLocalSrc))
    import bpaTools


import aixmReader

import math
import datetime
import json
import numpy as np
import geog
from shapely.geometry import LineString, Point
from pyproj import Proj, transform


class AixmTools:

    def __init__(self, oCtrl):
        if oCtrl:  bpaTools.initEvent(__file__, oCtrl.oLog)
        self.oCtrl = oCtrl
        #self.pLocal = Proj("epsg:2154")         # EPSG:2154 = RGF93 / Lambert-93 - Projected coordinate system for France) :: Deprecated format --> Proj(init="epsg:2154")
        self.pWGS = Proj("epsg:4326")            # EPSG:4326 = WGS84 / Geodetic coordinate system for World  :: Deprecated format --> Proj(init="epsg:4326")
        return

    def writeGeojsonFile(self, sFileName, oGeojson, context=""):
        assert(isinstance(sFileName, str))
        if sFileName=="airspaces":
            if context=="all":              sFileName = sFileName + "-all"            #Suffixe pour fichier toutes zones
            if context=="ifr":              sFileName = sFileName + "-ifr"            #Suffixe pour fichier Instrument-Fligth-Rules
            if context=="vfr":              sFileName = sFileName + "-vfr"            #Suffixe pour fichier Visual-Fligth-Rules
            if context=="ff":               sFileName = sFileName + "-freeflight"     #Suffixe pour fichier Vol-Libre (Paraglinding/Hanggliding)
            if self.oCtrl.Draft:            sFileName = sFileName + "-draft"          #Suffixe pour fichier en mode draft
            if self.oCtrl.MakePoints4map:   sFileName = sFileName + "-points4map"     #Suffixe pour fichier avec ajout des points de séparation
        sOutFile = self.oCtrl.sOutHeadFile + sFileName + ".geojson"
        sizeMap = len(oGeojson)
        if sizeMap:
            headMsg = "Write"
            with open(self.oCtrl.sOutPath + sOutFile, "w", encoding=self.oCtrl.sEncoding) as output:
                output.write(json.dumps(
                        {"type":"FeatureCollection", "headerFile":self.getJsonPropHeaderFile(sFileName, context, sizeMap), "features":oGeojson},
                        ensure_ascii=False))
        else:
            headMsg = "Unwritten"
        self.oCtrl.oLog.info("{0} file {1} - {2} areas in map".format(headMsg, sOutFile, sizeMap), outConsole=True)
        return

    def makeHeaderOpenairFile(self, oHeader, oOpenair, context="", gpsType="", exceptDay="", sAreaKey="", sAreaDesc="", sAddHeader="") -> str:
        lLeftMargin:int=3
        sRet:str=""
        sizeMap = len(oOpenair)
        if sizeMap:
            sRet += "*"*50 + "\n"
            for oKey, oVal in oHeader.items():
                if isinstance(oVal, dict):
                    sRet += "*" + " "*lLeftMargin + "{0}:\n".format(oKey)
                    lFileCnt:int = 0
                    for oKey2, oVal2 in oVal.items():
                        #Demande de Léo 01/2021, sortir toutes les références des fichiers
                        #if lFileCnt<5:
                            lFileCnt += 1
                            if isinstance(oVal2, dict):
                                oVal2 = json.dumps(oVal2, ensure_ascii=False)
                            sRet += "*" + " "*2*lLeftMargin + "{0} - {1}\n".format(oKey2, oVal2)
                        #else:
                        #    sRet += "*" + " "*2*lLeftMargin + "../.. and {0} complementary sources files. See Catalog file header for all details.\n".format(len(oHeader)-lFileCnt+1)
                        #    break
                else:
                    sRet += "*" + " "*lLeftMargin + "{0} - {1}\n".format(oKey, oVal)

            sRet += "*" + " "*lLeftMargin + "-"*44 + "\n"

            if sAddHeader:
                sRet += "*" + " "*lLeftMargin + "(i)Information - " + sAddHeader + "\n"
            if sAreaKey:
                sRet += "*" + " "*lLeftMargin + "(i)Information - '{0}' - Cartographie avec filtrage géographique des zones aériennes : {1}\n".format(sAreaKey, sAreaDesc)

            if context=="ifr":
                sRet += "*" + " "*lLeftMargin + "/!\Warning - 'IFR Map' - Cartographie de l'espace aérien IFR (zones majotitairement situées au dessus du niveau FL115)\n"
            elif context=="vfr":
                sRet += "*" + " "*lLeftMargin + "/!\Warning - 'VFR Map' - Cartographie de l'espace aérien VFR (zones situées de la surface jusqu'au FL195/5944m)\n"
            elif context=="ff":
                sRet += "*" + " "*lLeftMargin + "/!\Warning - 'Free Flight Map' - Version VFR spécifique Parapente/Deltaplane (zones situées en dessous le niveau FL195 avec filtrage des zones de type 'E, F, G et W')\n"
            else:
                sRet += "*" + " "*lLeftMargin + "(i)Information - 'ALL Map' - Cartographie complète de l'espace aérien (IFR + VFR)\n"

            if gpsType=="-gpsWithTopo":
                gpsSample = "XCsoar / LK8000 / XCTrack / FlyMe / Compass / Syride ; et tout autres appareils/logiciels AVEC Carte-Topographique (en capacité de connaître les altitudes terrain)"
            elif gpsType=="-gpsWithoutTopo":
                gpsSample = "Flytec ou Brauniger ; et tout autres appareils/logiciels SANS Carte-Topographique (n'ayant pas la capacité de connaître les altitudes terrain)"
            else:
                gpsSample = "???"
            sRet += "*" + " "*lLeftMargin + "/!\Warning - '{0}' - Cartographie pour {1}\n".format(gpsType[1:], gpsSample)

            if exceptDay:
                if exceptDay=="exceptSAT":
                    sDay1 = "SATerday"
                    sDay2 = "Samedis"
                elif exceptDay=="exceptSUN":
                    sDay1 = "SUNday"
                    sDay2 = "Dimanches"
                elif exceptDay=="exceptHOL":
                    sDay1 = "HOLiday"
                    sDay2 = "Jours-Fériés"
                ext4exceptDay = exceptDay.replace("except","-for")
                sRet += "*" + " "*lLeftMargin + "/!\Warning - '{0}' - Fichier spécifiquement utilisable les '{1}/{2}' (dépourvu des zones non-activables '{3}')\n".format(ext4exceptDay[1:], sDay1, sDay2, exceptDay)

            sRet += "*"*50 + "\n\n"
        return sRet

    def writeOpenairFile(self, sFileName, oOpenair, context="", gpsType="-gpsWithTopo", exceptDay=""):
        assert(isinstance(sFileName, str))
        if sFileName=="airspaces":
            if context=="all":              sFileName = sFileName + "-all"            #Suffixe pour fichier toutes zones
            if context=="ifr":              sFileName = sFileName + "-ifr"            #Suffixe pour fichier Instrument-Fligth-Rules
            if context=="vfr":              sFileName = sFileName + "-vfr"            #Suffixe pour fichier Visual-Fligth-Rules
            if context=="ff":               sFileName = sFileName + "-freeflight"     #Suffixe pour fichier Vol-Libre (Paraglinding/Hanggliding)

        ext4exceptDay = exceptDay.replace("except","-for")
        sOutFile = self.oCtrl.sOutHeadFile + sFileName + gpsType + ext4exceptDay + ".txt"
        sizeMap = len(oOpenair)
        if sizeMap:
            headMsg = "Written"
            with open(self.oCtrl.sOutPath + sOutFile, "w", encoding="cp1252", errors="replace") as output:
                oHeader = self.getJsonPropHeaderFile(sFileName, context, sizeMap)
                sHeader:str = self.makeHeaderOpenairFile(oHeader, oOpenair, context, gpsType, exceptDay)
                output.write(sHeader)
                for airspace in oOpenair:
                    output.write("\n".join(airspace))
                    output.write("\n\n")
        else:
            headMsg = "Unwritten"

        self.oCtrl.oLog.info("{0} file {1} - {2} areas in map".format(headMsg, sOutFile, sizeMap), outConsole=True)
        return

    def writeJsonFile(self, sPath="", sFileName="", oJson=None):
        if sFileName!="":
            sOutFile = self.oCtrl.sOutHeadFile + sFileName + ".json"
            self.oCtrl.oLog.info("Written file {0}".format(sOutFile), outConsole=True)
            if sPath=="":
                sPath = self.oCtrl.sOutPath
            with open(sPath + sOutFile, "w", encoding=self.oCtrl.sEncoding) as output:
                output.write(json.dumps(oJson, ensure_ascii=False))
        return


    def writeTextFile(self, sPath="", sFileName="", oText=None, fileExtention="txt", sencoding="cp1252"):
        if sFileName!="":
            sOutFile = self.oCtrl.sOutHeadFile + sFileName + "." + fileExtention
            self.oCtrl.oLog.info("Written file {0}".format(sOutFile), outConsole=True)
            if sPath=="":
                sPath = self.oCtrl.sOutPath
            with open(sPath + sOutFile, "w", encoding=sencoding, errors="replace") as output:
                output.write(oText)
        return


    def getJsonPropHeaderFile(self, sFileName="", context="", sizeMap=0) -> dict:
        prop = dict()
        prop.update({"software": self.oCtrl.oLog.getLongName()})
        prop.update({"created": datetime.datetime.now().isoformat()})
        prop.update({"content": sFileName})
        if context=="all":
            prop.update({"allMap": True})
        if context=="ifr":
            prop.update({"ifrMap": True})
        if context=="vfr":
            prop.update({"vfrMap": True})
        if context=="ff":
            prop.update({"freeFlightMap": True})
        if sizeMap>0:
            prop.update({"numberOfAreas": sizeMap})
        if "airspaces" in sFileName:
            if self.oCtrl.Draft:
                prop.update({"draftMode": True})
            if self.oCtrl.MakePoints4map:
                prop.update({"makePoints4map": True})
        if self.oCtrl.oAixm:
            oFiles:dict = {}
            oFiles.update({"srcAixmFile":self.oCtrl.srcFile})
            oFiles.update({"srcAixmOrigin":self.oCtrl.oAixm.srcOrigin})
            oFiles.update({"srcAixmVersion":self.oCtrl.oAixm.srcVersion})
            oFiles.update({"srcAixmCreated":self.oCtrl.oAixm.srcCreated})
            oFiles.update({"srcAixmEffective":self.oCtrl.oAixm.srcEffective})
            prop.update({"srcFiles":{"1":oFiles}})
        return prop


    #outputFormat enumeration: [
    #   ""              = Native format                                                     (without change)
    #   "dd"            = Degrés décimaux (D.d)
    #   "dmd"           = Degrés minutes décimaux (DM.d)
    #   "DDMMSS.ssX"    = Short (DMS.d) - Standard serialize without separator
    #   "DD:MM:SS.ssX"  = Long  (DMS.d) - Optimized Serialize with separators (use for Openair format)
    def geo2coordinates(self, outputFormat:str, o, latitude=None, longitude=None, oZone:dict=None) -> list:
        """ codeDatum or CODE_DATUM Format:
            WGE [WGS-84 (GRS-80).]
            WGC [WGS-72.]
            EUS [European 1950 (ED 50).]
            EUT [European 1979 (ED 79).]
            ANS [Austria NS.]
            BEL [Belgium 50.]
            BRN [Berne 1873.]
            CHI [CH-1903.]
            DGI [Danish GI 1934.]
            IGF [Nouvelle Triangulation de France (Greenwich Zero Meridian).]
            POT [Potsdam.]
            GRK [GGRS 87 (Greece).]
            HJO [Hjorsey 55 (Iceland).]
            IRL [Ireland 65.]
            ROM [Rome (Italy) 1940.]
            IGL [Nouvelle Triangulation de Luxembourg.]
            OGB [Ordnance Survey of Great Britain 36.]
            DLX [Portugal DLX.]
            PRD [Portugal 1973.]
            RNB [RNB 72 (Belgium).]
            STO [RT90 (Sweden).]
            NAS [North American 1927.]
            NAW [North American 1983.]
            U [Other datum or unknown..]
        """
        #Ctrl du référentiel des coordonnées
        if o:
            codedatum = o.find("codeDatum", recursive=False)
            if codedatum == None:
                codedatum = o.parent.find("codeDatum", recursive=False)
            if codedatum == None:
                self.oCtrl.oLog.critical("geo2coordinates() codeDatum not found ! {0}".format(o), outConsole=True)
            codedatum = codedatum.string
            if not codedatum in ("WGE","U","WGC","NAW"):
                self.oCtrl.oLog.critical("geo2coordinates() codedatum is {0}\n{1}".format(codedatum, o), outConsole=False)
                if type(oZone)==dict:
                    oZone.update({"CriticalCodedatum":codedatum})

        if latitude:
            sLat = latitude
        else:
            sLat = o.find("geoLat", recursive=False)
            if sLat == None:
                self.oCtrl.oLog.critical("geo2coordinates() geoLat not found ! {0}".format(o), outConsole=True)
            sLat = sLat.string

        if longitude:
            sLon = longitude
        else:
            sLon = o.find("geoLong", recursive=False)
            if sLon == None:
                self.oCtrl.oLog.critical("geo2coordinates() geoLong not found ! {0}".format(o), outConsole=True)
            sLon = sLon.string

        """ # Aixm LATITUDE native format:
                •DDMMSS.ssX: ‘000000.00N’, ‘131415.5S’, ’455959.9988S’, ‘900000.00N’.
                •DDMMSSX: ‘000000S’, ’261356N’, ‘900000S’.
                •DDMM.mm...X : ‘0000.0000S’, ’1313.12345678S’, ‘1234.9S’, ‘9000.000S’.
                •DDMMX: ‘0000N’, ’1313S’, ‘1234N’, ‘9000S’.
                •DD.dd...X : ‘00.00000000N’, ’13.12345678S’, ‘34.9N’, ‘90.000S’.
            # Aixm LONGITUDE native format:
                •DDDMMSS.ssY: ‘0000000.00E’, ‘0010101.1E’, ’1455959.9967W’, ‘1800000.00W’.
                •DDDMMSSY: ‘0000000W’, ’1261356E’, ‘1800000E’.
                •DDDMM.mm...Y : ‘00000.0000W’, ’01313.12345678E’, ‘11234.9E’, ‘18000.000W’.
                •DDDMMY: ‘00000E’, ’01313W’, ‘11234E’, ‘18000W’.
                •DDD.dd...Y : ‘000.00000000W’, ’113.12345678E’, ‘134.9W’, ‘180.000W’.
        """
        try:
            if outputFormat=="":
                return [sLat, sLon]
            elif outputFormat=="dd":
                if self.oCtrl:
                    iDigit:int = self.oCtrl.digit4roundPoint
                else:
                    iDigit:int = 6
                lat, lon = bpaTools.GeoCoordinates.geoStr2coords(sLat, sLon, outFrmt=outputFormat)
                return [round(lat, iDigit), round(lon, iDigit)]
            elif outputFormat=="dmd":
                sLat2, sLon2 = bpaTools.GeoCoordinates.geoStr2coords(sLat, sLon, outFrmt=outputFormat)
                return [sLon2, sLat2]
            elif outputFormat in ["dms", "DDMMSS.ssX",]:
                sLat2, sLon2 = bpaTools.GeoCoordinates.geoStr2coords(sLat, sLon, outFrmt="dms")
                return [sLat2, sLon2]
            elif outputFormat=="D:M:S.ssX":
                sLat2, sLon2 = bpaTools.GeoCoordinates.geoStr2coords(sLat, sLon, outFrmt="dms", sep1=":", sep2="", bOptimize=True)
                return [sLat2, sLon2]
            elif outputFormat=="DD:MM:SS.ssX":
                sLat2, sLon2 = bpaTools.GeoCoordinates.geoStr2coords(sLat, sLon, outFrmt="dms", sep1=":", sep2=" ", bOptimize=False)
                return [sLat2, sLon2]
            else:
                if self.oCtrl:
                    self.oCtrl.oLog.error("geo2coordinates() outputFormat error '{0}'".format(outputFormat), outConsole=True)
                else:
                    print("geo2coordinates() outputFormat error '{0}'".format(outputFormat))
        except Exception as err:
            sErrMsg:str = "geo2coordinates() {0}\n{1}".format(err, o)
            self.oCtrl.oLog.critical(sErrMsg.format(err, o), outConsole=False)
            raise Exception(sErrMsg)

    def convertLength(self, length:float, srcRef:str, dstRef:str) -> float:
        srcRef = srcRef.upper()
        dstRef = dstRef.upper()
        if not srcRef in ["NM","KM","M","FT"]:      raise Exception("Invalid input - srcRef")
        if not dstRef in ["NM","M"]:                raise Exception("Invalid input - dstRef")
        if srcRef == dstRef:
            return length

        #Just for documentation
        #CONST.nm = 1852                # Nautic Mile to Meter
        #CONST.ft = 0.3048              # Foot to Meter

        #Use for GeoJSON format
        if   dstRef=="M" and srcRef=="NM":                      #1,6 NM = 2963,2 M
            length = length * aixmReader.CONST.nm
        elif dstRef=="M" and srcRef=="KM":                      #1.6 KM = 1600 M
            length = length * 1000
        elif dstRef=="M" and srcRef=="FT":                      #1.6 FT = 0,48768 M
            length = length * aixmReader.CONST.ft

        #Use for Openair format
        elif dstRef=="NM" and srcRef=="KM":                     #1.6 KM = 0,863931 NM
            length = (length * 1000) / aixmReader.CONST.nm
        elif dstRef=="NM" and srcRef=="M":                      #1.6 M = 0,000863931 NM
            length = length / aixmReader.CONST.nm
        elif dstRef=="NM" and srcRef=="FT":                     #1.6 FT = 0,000263326 NM
            length = (length * aixmReader.CONST.ft) / aixmReader.CONST.nm

        #Raise error
        else:
            self.oCtrl.oLog.critical("convertLength() error value={0} srcRef={1} srcRef={2}}".format(length, srcRef, dstRef), outConsole=False)

        return length


    def getField(self, o, inputname, outputname=None, optional=False):
        if (not optional) and (o is None) and (not self.oCtrl.oLog is None):
            self.oCtrl.oLog.error("Object is none !? in={0} out={1}\n{2}".format(inputname, outputname, o), outConsole=True)
            return None
        elif optional and (o is None):
            return None
        if self.oCtrl:
            if self.oCtrl.oAixm.openType == "lxml":
                inputname = inputname.lower()
        if outputname is None:
            outputname = inputname
        value = o.find(inputname, recursive=False)
        if value:
            ret = value.string.replace("\u2009", " ")   #for UnicodeEncodeError: 'charmap' codec can't encode character '\u2009'
            ret = ret.replace("&apos;","'")
            ret = ret.replace("&quot;",'"')
            ret = ret.replace("#"," ")
            ret = ret.replace("\n"," ")
            ret = ret.replace(" :",":")
            ret = ret.replace(" ;",";")
            ret = ret.replace(" ,",",")
            ret = ret.replace(" .",".")
            ret = ret.replace("  "," ")
            return {outputname:ret}
        else:
            if (not optional) and (not self.oCtrl.oLog is None):
                self.oCtrl.oLog.error("Field not Found in={0} out={1}\n{2}".format(inputname, outputname, o), outConsole=True)
        return None


    def addField(self, prop, field):
        if field: prop.update(field)
        return prop


    def addProperty(self, prop, o, inputname, outputname=None, optional=False):
        field = self.getField(o, inputname, outputname, optional)
        return self.addField(prop, field)


    def initProperty(self, context):
        prop = dict()
        prop = self.addField(prop, {"zoneType":context})
        return prop

    """
    Transformation d'un objet shapely.Point en un tableau simple de coordonnées
    """
    def Point2array(self, P):
        assert(isinstance(P, Point))
        return [P.x, P.y]

    """
    Détermine le nombre de segment d'un cercle selon le context aqppelé (avec limitation en mode draft..)
    """
    def _getNbrSegment(self, radius):
        assert(isinstance(radius, float))

        nbSegments = (2*radius*aixmReader.CONST.pi)/1000              #Nombre de segments de 1000 mètres (Circonférence/1000)
        if nbSegments<40:                           nbSegments = 10 if self.oCtrl.Draft else 40
        elif nbSegments>=40 and nbSegments<100:     nbSegments = 20 if self.oCtrl.Draft else nbSegments
        elif nbSegments>=100 and nbSegments<200:    nbSegments = 20 if self.oCtrl.Draft else nbSegments/2
        elif nbSegments>=200 and nbSegments<300:    nbSegments = 30 if self.oCtrl.Draft else nbSegments/3
        elif nbSegments>=300 and nbSegments<400:    nbSegments = 30 if self.oCtrl.Draft else nbSegments/4
        elif nbSegments>=400 and nbSegments<500:    nbSegments = 30 if self.oCtrl.Draft else nbSegments/5
        elif nbSegments>=500 and nbSegments<600:    nbSegments = 40 if self.oCtrl.Draft else nbSegments/6
        elif nbSegments>=600 and nbSegments<700:    nbSegments = 40 if self.oCtrl.Draft else nbSegments/7
        elif nbSegments>=700 and nbSegments<800:    nbSegments = 40 if self.oCtrl.Draft else nbSegments/8
        elif nbSegments>=800 and nbSegments<900:    nbSegments = 50 if self.oCtrl.Draft else nbSegments/9
        elif nbSegments>=900 and nbSegments<1000:   nbSegments = 50 if self.oCtrl.Draft else nbSegments/10
        else:                                       nbSegments = 50 if self.oCtrl.Draft else 100
        return int(nbSegments)


    """
    Construct array of coords for make Arc or Circle
        Pcenter: center-point of arc = Point([lon,lat]) in float values
        radius: is a float value in meters
        angles: in degrees (default values for construct a 'Circle')
        clockwiseArc : is boolean value ; True='Clockwise Arc' and False='Counter Clockwise Arc'
    """
    def make_arc(self, Pcenter, radius, start_angle=0.0, stop_angle=360.0, clockwiseArc=False):
        assert(isinstance(Pcenter, Point))
        assert(isinstance(radius, float))
        assert(isinstance(start_angle, float))
        assert(isinstance(stop_angle, float))

        if clockwiseArc and (start_angle < stop_angle):
            start_angle = start_angle+360
        if (not clockwiseArc) and (stop_angle < start_angle):
            stop_angle  = stop_angle+360

        g  = []
        numsegments = self._getNbrSegment(radius)
        angles = np.linspace(start_angle, stop_angle, numsegments)
        polygon = geog.propagate(Pcenter, angles, radius)
        ##   #print(json.dumps(mapping(Polygon(polygon))))
        ##   #print(json.dumps(mapping(LineString(polygon))))
        for o in polygon:
            g.append([round(o[0],self.oCtrl.digit4roundArc), round(o[1],self.oCtrl.digit4roundArc)])

        #Other function - https://stackoverflow.com/questions/30762329/how-to-create-polygons-with-arcs-in-shapely-or-a-better-library
        #theta = np.radians(angles)
        #x = Pcenter.x + (radius * np.cos(theta))
        #y = Pcenter.y + (radius * np.sin(theta))
        #polygon = LineString(np.column_stack([x, y]))
        #for o in polygon.coords:
        #    g.append([round(o[0],self.oCtrl.digit4roundArc), round(o[1],self.oCtrl.digit4roundArc)])

        return g

    """
    Construct array of coords for make Arc or Circle
        Pcenter, Pstart and Pstop : Points of arc = Point([lon,lat]) in float values
        radius: is a float value in meters (par défaut, est calculé avec les écarts entre Pstart/Pstop et Pcenter)
        clockwiseArc : is boolean value ; True='Clockwise Arc' and False='Counter Clockwise Arc'
    """
    def make_arc2(self, Pcenter, Pstart, Pstop, radius=0.0, clockwiseArc=True):
        assert(isinstance(Pcenter, Point))
        assert(isinstance(Pstart, Point))
        assert(isinstance(Pstop, Point))
        assert(isinstance(radius, float))

        lonC = Pcenter.x
        latC = Pcenter.y
        lonS = Pstart.x
        latS = Pstart.y
        lonE = Pstop.x
        latE = Pstop.y

        # Convert to local meters
        srs = Proj(proj="ortho", lat_0=latC, lon_0=lonC)

        center_x, center_y = transform(p1=self.pWGS, p2=srs, x=latC, y=lonC)
        start_x,   start_y = transform(p1=self.pWGS, p2=srs, x=latS, y=lonS)
        stop_x,     stop_y = transform(p1=self.pWGS, p2=srs, x=latE, y=lonE)

        if radius==0:
            radiusS = math.sqrt(start_x**2+start_y**2)      #Rayon au point d'entrée
            radiusE = math.sqrt(stop_x**2+stop_y**2)        #Rayon au point de sortie
            radius = (radiusS + radiusE) / 2                #Moyenne des 2 rayons pour réalignement systématique...
            #radius = radiusS

        #Calcul des angles de départ et d'arrivées en degrés
        degStart = math.degrees(math.atan2(start_y-center_y, start_x-center_x))
        degStop  = math.degrees(math.atan2(stop_y-center_y, stop_x-center_x))

        g = self.make_arc(Pcenter, radius, degStart, degStop, clockwiseArc)

        #Ajout complémentaire des points Start et Stop afin de respecter les points d'entrée/sortie de l'arc
        if (g[0][0], g[0][1]) != (Pstart.x, Pstart.y):
            g.insert(0, [Pstart.x, Pstart.y])
        if (g[-1][0], g[-1][1]) != (Pstop.x, Pstop.y):
            g.append([Pstop.x, Pstop.y])

        return g

    """
    Construct array of coords for make Arc or Circle
        Pcenter and Pstart : Points of arc = Point([lon,lat]) in float values
        radius: is a float value in meters (par défaut, est calculé avec l'écart entre Pstart et Pcenter)
        angles: in degrees (default values for construct a 'Circle')
    """
    def make_arc3(self, Pcenter, Pstart, radius=0.0, start_angle=0.0, stop_angle=360.0):
        assert(isinstance(Pcenter, Point))
        assert(isinstance(Pstart, Point))
        assert(isinstance(radius, float))
        assert(isinstance(start_angle, float))
        assert(isinstance(stop_angle, float))

        if radius==0:
            lonC = Pcenter.x
            latC = Pcenter.y
            lonS = Pstart.x
            latS = Pstart.y
            # Convert to local meters
            srs = Proj(proj="ortho", lat_0=latC, lon_0=lonC)
            center_x, center_y = transform(p1=self.pWGS, p2=srs, x=latC, y=lonC)
            start_x, start_y = transform(p1=self.pWGS, p2=srs, x=latS, y=lonS)
            radius = math.sqrt(start_x**2+start_y**2)

        g = self.make_arc(Pcenter, radius, start_angle, stop_angle)

        #Ajout complémentaire du point Start afin de respecter le point d'entrée de l'arc
        if (g[0][0], g[0][1]) != (Pstart.x, Pstart.y):
            g.insert(0, [Pstart.x, Pstart.y])

        return g

    """
    Construction d'un Point sous geojson
    """
    def make_point(self, p, name):
        assert(isinstance(p, Point))
        geom=[]
        #Creation d'un point
        g = {"type":"Point", "coordinates":self.Point2array(p)}
        geom.append({"type":"Feature", "properties":{"name": name}, "geometry":g})
        #Ajout du tracé des axes
        self.make_axes(p, geom)
        #ret = {"type":"FeatureCollection", "features":geom}
        #print(str(ret).replace(chr(39),chr(34)))
        return geom

    """
    Construction des axes x/y pour marquer le positionnement d'un Point sous geojson
    """
    def make_axes(self, p, geom):
        assert(isinstance(p, Point))
        assert(isinstance(geom, list))
        #Tracé de l'axe des x
        p1 = Point(p.x-0.0125, p.y)
        p2 = Point(p.x+0.0125, p.y)
        g = [self.Point2array(p1), self.Point2array(p2)]
        g = {"type":"LineString", "coordinates":g}
        geom.append({"type":"Feature", "properties":{"name": "lineX"}, "geometry":g})
        #Tracé de l'axe des y
        p1 = Point(p.x, p.y-0.00625)
        p2 = Point(p.x, p.y+0.00625)
        g = [self.Point2array(p1), self.Point2array(p2)]
        g = {"type":"LineString", "coordinates":g}
        geom.append({"type":"Feature", "properties":{"name": "lineY"}, "geometry":g})
        return

    """
    Return a line segment between specified distances along a linear geometry.
    Negative distance values are taken as measured in the reverse
    direction from the end of the geometry. Out-of-range index
    values are handled by clamping them to the valid range of values.
    If the start distances equals the end distance, a point is being returned.
    If the normalized arg is True, the distance will be interpreted as a
    fraction of the geometry's length.
    from shapely 1.7
    """
    def substring(self, geom, start_dist, end_dist, normalized=False):
        assert(isinstance(geom, LineString))
        assert(isinstance(start_dist, float))
        assert(isinstance(end_dist, float))

        # Filter out cases in which to return a point
        if start_dist == end_dist:
            return geom.interpolate(start_dist, normalized)
        elif not normalized and start_dist >= geom.length and end_dist >= geom.length:
            return geom.interpolate(geom.length, normalized)
        elif not normalized and -start_dist >= geom.length and -end_dist >= geom.length:
            return geom.interpolate(0, normalized)
        elif normalized and start_dist >= 1 and end_dist >= 1:
            return geom.interpolate(1, normalized)
        elif normalized and -start_dist >= 1 and -end_dist >= 1:
            return geom.interpolate(0, normalized)

        start_point = geom.interpolate(start_dist, normalized)
        end_point = geom.interpolate(end_dist, normalized)

        min_dist = min(start_dist, end_dist)
        max_dist = max(start_dist, end_dist)
        if normalized:
            min_dist *= geom.length
            max_dist *= geom.length

        if start_dist < end_dist:
            vertex_list = [(start_point.x, start_point.y)]
        else:
            vertex_list = [(end_point.x, end_point.y)]
        coords = list(geom.coords)
        for i, p in enumerate(coords):
            pd = geom.project(Point(p))
            if min_dist < pd < max_dist:
                vertex_list.append(p)
            elif pd >= max_dist:
                break
        if start_dist < end_dist:
            vertex_list.append((end_point.x, end_point.y))
        else:
            vertex_list.append((start_point.x, start_point.y))
            # reverse direction result
            vertex_list = reversed(vertex_list)

        return LineString(vertex_list)

    def getAirspaceFunctionalKeyName(self, airspaceProperties:dict) -> str:
        sKey = "{0}.{1}.{2}".format(airspaceProperties["srcClass"], airspaceProperties["srcType"], airspaceProperties["name"])
        return sKey

    def getAirspaceFunctionalKey(self, airspaceProperties:dict) -> str:
        sKey = "{0}@{1}".format(self.getAirspaceFunctionalKeyName(airspaceProperties), aixmReader.getSerializeAlt(airspaceProperties))
        return sKey

    def getAirspaceFunctionalLowerKey(self, airspaceProperties:dict) -> str:
        if ("nameV" in airspaceProperties) and \
            ("lowerType" in airspaceProperties) and \
            ("lowerValue" in airspaceProperties) and \
            ("lowerUnit" in airspaceProperties):
            sKey = "{0}@{1}.{2}.{3}".format(airspaceProperties["nameV"], airspaceProperties["lowerType"], airspaceProperties["lowerValue"], airspaceProperties["lowerUnit"])
        else:
            sKey = None
        return sKey

if __name__ == '__main__':
    """ # Aixm LATITUDE native format:
            •DDMMSS.ssX: ‘000000.00N’, ‘131415.5S’, ’455959.9988S’, ‘900000.00N’.
            •DDMMSSX: ‘000000S’, ’261356N’, ‘900000S’.
            •DDMM.mm...X : ‘0000.0000S’, ’1313.12345678S’, ‘1234.9S’, ‘9000.000S’.
            •DDMMX: ‘0000N’, ’1313S’, ‘1234N’, ‘9000S’.
            •DD.dd...X : ‘00.00000000N’, ’13.12345678S’, ‘34.9N’, ‘90.000S’.
        # Aixm LONGITUDE native format:
            •DDDMMSS.ssY: ‘0000000.00E’, ‘0010101.1E’, ’1455959.9967W’, ‘1800000.00W’.
            •DDDMMSSY: ‘0000000W’, ’1261356E’, ‘1800000E’.
            •DDDMM.mm...Y : ‘00000.0000W’, ’01313.12345678E’, ‘11234.9E’, ‘18000.000W’.
            •DDDMMY: ‘00000E’, ’01313W’, ‘11234E’, ‘18000W’.
            •DDD.dd...Y : ‘000.00000000W’, ’113.12345678E’, ‘134.9W’, ‘180.000W’.
        """
    aPoints:list = [["131415S", "0010101E"],
                    ["131415.5S", "0010101.1E"],
                    ["455959.9988S", "1455959.9967W"],
                ]

    oTools = AixmTools(None)
    for aPt in aPoints:
        print(oTools.geo2coordinates("", None, aPt[0], aPt[1]))
        print(oTools.geo2coordinates("DD:MM:SS.ssX", None, aPt[0], aPt[1]))
        print(oTools.geo2coordinates("dd", None, aPt[0], aPt[1]))
        print("---")


