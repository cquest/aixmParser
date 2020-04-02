#!/usr/bin/env python3

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
        bpaTools.initEvent(__file__, oCtrl.oLog)
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
        sOutFile = sFileName + ".geojson"
        sizeMap = len(oGeojson)
        self.oCtrl.oLog.info("Write file {0} - {1} areas in map".format(sOutFile, sizeMap), outConsole=True)
        with open(self.oCtrl.sOutPath + sOutFile, "w", encoding=self.oCtrl.sEncoding) as output:
            output.write(json.dumps({"type":"FeatureCollection", "headerFile":self.getJsonPropHeaderFile(sFileName, context, sizeMap), "features":oGeojson}, ensure_ascii=False))
        return


    def writeJsonFile(self, sFileName, oJson):
        assert(isinstance(sFileName, str))
        sOutFile = sFileName + ".json"
        self.oCtrl.oLog.info("Write file {0}".format(sOutFile), outConsole=True)
        with open(self.oCtrl.sOutPath + sOutFile, "w", encoding=self.oCtrl.sEncoding) as output:
            output.write(json.dumps(oJson, ensure_ascii=False))
        return


    def writeTextFile(self, sFileName, oText, fileExtention="txt"):
        assert(isinstance(sFileName, str))
        sOutFile = sFileName + "." + fileExtention
        self.oCtrl.oLog.info("Write file {0}".format(sOutFile), outConsole=True)
        with open(self.oCtrl.sOutPath + sOutFile, "w", encoding=self.oCtrl.sEncoding) as output:
            output.write(oText)
        return

    
    def getJsonPropHeaderFile(self, sFileName="", context="", sizeMap=0):
        prop = dict()
        prop.update({"software": self.oCtrl.oLog.sLogName})
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
            prop.update({"srcAixmFile":self.oCtrl.srcFile})
            prop.update({"srcAixmOrigin":self.oCtrl.oAixm.srcOrigin})
            prop.update({"srcAixmVersion":self.oCtrl.oAixm.srcVersion})
            prop.update({"srcAixmCreated":self.oCtrl.oAixm.srcCreated})
            prop.update({"srcAixmEffective":self.oCtrl.oAixm.srcEffective})
        return prop

        
    def geo2coordinates(self, o, latitude=None, longitude=None, recurse=True):
        #assert(isinstance(latitude, float))
        #assert(isinstance(longitude, float))
        
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
        codedatum = o.find("codeDatum", recursive=recurse).string
        if not codedatum in ("WGE", "U"):
            self.oCtrl.oLog.critical("geo2coordinates() codedatum is {0}\n{1}".format(codedatum, o), outConsole=True)

        if latitude:
            s = latitude
        else:
            s = o.find("geoLat", recursive=recurse).string
            
        lat = s[:-1]
        if len(lat)==2 or lat[2]==".": # DD[.dddd]
            lat = float(lat)
        elif len(lat)==4 or lat[4]==".": # DDMM[.mmmm]
            lat = int(lat[0:2])+float(lat[2:])/60
        else: # DDMMSS[.sss]
            if self.oCtrl.bMakeWithNewSrc:
                lat = int(lat[0:2])+int(lat[2:4])/60+float(lat[4:])/3600
            else:
                lat = int(lat[0:2])+int(lat[2:4])/60+float(lat[4:-1])/3600
        if s[-1] == "S":
            lat = -lat
    
        if longitude:
            s = longitude
        else:
            s = o.find("geoLong", recursive=recurse).string
            
        lon = s[:-1]
        if len(lon) == 3 or lon[3] == ".":
            lon = float(lon)
        elif len(lon) == 5 or lon[5] == ".":
            lon = int(lon[0:3])+float(lon[3:])/60
        else:
            if self.oCtrl.bMakeWithNewSrc:
                lon = int(lon[0:3])+int(lon[3:5])/60+float(lon[5:])/3600
            else:
                lon = int(lon[0:3])+int(lon[3:5])/60+float(lon[5:-1])/3600
        if s[-1] == "W":
            lon = -lon
        return([round(lon,self.oCtrl.digit4roundPoint), round(lat,self.oCtrl.digit4roundPoint)])
        

    def getField(self, o, inputname, outputname=None, optional=False):
        if (o is None) and (not self.oCtrl.oLog is None):
            self.oCtrl.oLog.error("Object is none !? in={0} out={1}\n{2}".format(inputname, outputname, o), outConsole=True)
            return None
        if self.oCtrl.oAixm.openType == "lxml":
            inputname = inputname.lower()
        if outputname is None:
            outputname = inputname
        value = o.find(inputname, recursive=False)
        if value:
            ret = value.string.replace("#"," ")
            ret = ret.replace("\n"," ")
            ret = ret.replace(" :",":")
            ret = ret.replace(" ;",";")
            ret = ret.replace(" ,",",")
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
    geojson Colors attributes: stroke; stroke-width; stroke-opacity; fill; fill-opacity
        Red:    stroke=#ff0000; stroke-width=2; stroke-opacity=1; fill=#ff8080; fill-opacity=0.5
        Purple: stroke=#800080; stroke-width=2; stroke-opacity=1; fill=#ffb9dc; fill-opacity=0.5
        Blue:   stroke=#0000ff; stroke-width=2; stroke-opacity=1; fill=#80ffff; fill-opacity=0.3
        Green:  stroke=#008040; stroke-width=2; stroke-opacity=1; fill=#80ff80; fill-opacity=0.3
    """
    def addColorProperties(self, prop):
        sClass = prop["class"]
        #Red
        if sClass in ["A","B","C","P","CTR","CTR-P","CTA","CTA-P","TMA","TMA-P","FIR","FIR-P","NO-FIR","PART","CLASS","SECTOR","SECTOR-C","OCA","OCA-P","OTA","OTA-P","UTA","UTA-P","UIR","UIR-P","TSA","CBA","RCA","RAS","TRA","AMA","ASR","ADIZ","POLITICAL"]:
            sStroke = "#ff0000"
            sFill = "#ff8080"
            nFillOpacity = 0.5
        #Purple
        elif sClass in ["D","D-AMC","R","R-AMC","ZMT"]:
            sStroke = "#800080"
            sFill = "#ffb9dc"
            nFillOpacity = 0.5
        #Blue
        elif sClass in ["Q", "GP","RMZ","TMZ","ZSM","BIRD","PROTECT","D-OTHER"]:
            sStroke = "#0000ff"
            sFill = "#80ffff"
            nFillOpacity = 0.3
        #Green
        elif sClass in ["E","F","G"]:
            sStroke = "#008040"
            sFill = "#80ff80"
            nFillOpacity = 0.3
        else:
            self.oCtrl.oLog.warning("GeoJSON Color not found for Class={0}".format(sClass), outConsole=True)
            return

        prop = self.addField(prop, {"stroke": sStroke})
        prop = self.addField(prop, {"stroke-width": 2})
        prop = self.addField(prop, {"stroke-opacity": 1})
        prop = self.addField(prop, {"fill": sFill})
        prop = self.addField(prop, {"fill-opacity": nFillOpacity})
        return

    
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
        
        nbSegments = (2*radius*aixmReader.CONST.pi)/100              #Nombre de segments de 100 mètres (Circonférence/100)
        if nbSegments<40:                           nbSegments = 10 if self.oCtrl.Draft else 40
        elif nbSegments>=40 and nbSegments<300:     nbSegments = nbSegments/4 if self.oCtrl.Draft else nbSegments
        elif nbSegments>=300 and nbSegments<1000:   nbSegments = nbSegments/6 if self.oCtrl.Draft else nbSegments/1.5
        else:                                       nbSegments = nbSegments/10 if self.oCtrl.Draft else nbSegments/2
        return int(nbSegments)

    
    """
    Construct array of coords for make Arc or Circle
        Pcenter: center-point of arc = Point([lon,lat]) in float values
        radius: is a float value in meters
        angles: in degrees (default values for construct a 'Circle')
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
        
        g = []
        numsegments = self._getNbrSegment(radius)
        angles = np.linspace(start_angle, stop_angle, numsegments)
        polygon = geog.propagate(Pcenter, angles, radius)
        #print(json.dumps(mapping(Polygon(polygon))))
        #print(json.dumps(mapping(LineString(polygon))))
        for o in polygon:
            g.append([round(o[0],self.oCtrl.digit4roundArc), round(o[1],self.oCtrl.digit4roundArc)])
        return g
    
    """
    Construct array of coords for make Arc or Circle
        Pcenter, Pstart and Pstop : Points of arc = Point([lon,lat]) in float values
        radius: is a float value in meters (par défaut, est calculé avec l'écart entre Pstart et Pcenter)
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
        start_x, start_y = transform(p1=self.pWGS, p2=srs, x=latS, y=lonS)
        stop_x, stop_y = transform(p1=self.pWGS, p2=srs, x=latE, y=lonE)

        if radius==0:
            radius = math.sqrt(start_x**2+start_y**2)

        #Calcul des angles de départ et d'arrivées en degrés
        degStart = math.degrees(math.atan2(start_y-center_y, start_x-center_x))
        degStop  = math.degrees(math.atan2(stop_y-center_y, stop_x-center_x))
        
        g = self.make_arc(Pcenter, radius, degStart, degStop, clockwiseArc)
        
        #Ajout complémentaire des points Start et Stop afin de que "le Polygon" finale se referme parfaitement
        if g[0][0]!=Pstart.x or g[0][1]!=Pstart.y:
            g.insert(0, [Pstart.x, Pstart.y])
        if g[-1][0]!=Pstop.x or g[-1][1]!=Pstop.y:
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
        
        #Ajout complémentaire du point Start afin de que le Polygon soit parfaitement fermer
        if g[0][0]!=Pstart.x or g[0][1]!=Pstart.y:
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


