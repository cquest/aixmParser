#!/usr/bin/env python3

import bpaTools
import aixmReader

import math
from shapely.geometry import LineString, Point
from pyproj import Proj, transform


class Aixm2json4_5:
    
    def __init__(self, oCtrl):
        bpaTools.initEvent(__file__, oCtrl.oLog)
        self.oCtrl = oCtrl
        self.oAirspacesCatalog = None
        self.__geoBorders = None                    #Geographic borders dictionary
        self.__geoAirspaces = None                  #Geographic airspaces dictionary
        return 

    def parseControlTowers(self):
        sTitle = "Aerodrome control towers"
        sXmlTag = "Uni"
        
        sMsg = "Parsing {0} to GeoJSON - {1}".format(sXmlTag, sTitle)
        self.oCtrl.oLog.info(sMsg) 
        
        oList = self.oCtrl.oAixm.doc.find_all(sXmlTag)
        barre = bpaTools.ProgressBar(len(oList), 20, title=sMsg, isSilent=self.oCtrl.oLog.isSilent)
        idx = 0
        geojson = []
        for uni in oList:
            idx+=1
            twr = self.tower2json(uni)
            if twr:
                geojson.append(twr)
            barre.update(idx)
        
        barre.reset
        self.oCtrl.oAixmTools.writeGeojsonFile("towers", geojson)
        return

    def tower2json(self, uni):
        if uni.codeType.string in ("TWR", "OTHER"):
            if uni.find("geoLat"):
                prop = self.oCtrl.oAixmTools.initProperty("Aerodrome Control Tower")
                prop = self.oCtrl.oAixmTools.addProperty(prop, uni.OrgUid, "txtName", "organisationAuthority")
                prop = self.oCtrl.oAixmTools.addProperty(prop, uni, "codeType", "codeType")
                prop = self.oCtrl.oAixmTools.addProperty(prop, uni.UniUid, "txtName", "name")
                geom = {"type":"Point", "coordinates":self.oCtrl.oAixmTools.geo2coordinates(uni)}
                return {"type":"Feature", "properties":prop, "geometry":geom}
            else:
                self.oCtrl.oLog.warning("Missing TWR coordinates {0}".format(uni.UniUid), outConsole=True)
        return


    def parseAerodromes(self):
        sTitle = "Aerodromes / Heliports"
        sXmlTag = "Ahp"
        
        sMsg = "Parsing {0} to GeoJSON - {1}".format(sXmlTag, sTitle)
        self.oCtrl.oLog.info(sMsg)
        
        oList = self.oCtrl.oAixm.doc.find_all(sXmlTag)
        barre = bpaTools.ProgressBar(len(oList), 20, title=sMsg, isSilent=self.oCtrl.oLog.isSilent)
        idx = 0
        geojson = []
        for ahp in oList:
            idx+=1
            geojson.append(self.ahp2json(ahp))
            barre.update(idx)
        barre.reset()
        self.oCtrl.oAixmTools.writeGeojsonFile("aerodromes", geojson)
        return
    
    def ahp2json(self, ahp):
        prop = self.oCtrl.oAixmTools.initProperty("Aerodrome / Heliport")
        prop = self.oCtrl.oAixmTools.addProperty(prop, ahp.OrgUid, "txtName", "organisationAuthority")
        prop = self.oCtrl.oAixmTools.addProperty(prop, ahp, "codeType")
        prop = self.oCtrl.oAixmTools.addProperty(prop, ahp, "txtName", "name")
        prop = self.oCtrl.oAixmTools.addProperty(prop, ahp.AhpUid, "codeId", "codeId")
        prop = self.oCtrl.oAixmTools.addProperty(prop, ahp, "codeIcao", optional=True)
        prop = self.oCtrl.oAixmTools.addProperty(prop, ahp, "codeIata", optional=True)
        prop = self.oCtrl.oAixmTools.addProperty(prop, ahp, "valElev", "elevation", optional=True)
        prop = self.oCtrl.oAixmTools.addProperty(prop, ahp, "uomDistVer", "verticalUnit", optional=True)
        prop = self.oCtrl.oAixmTools.addProperty(prop, ahp, "txtDescrRefPt", "description", optional=True)
        prop = self.oCtrl.oAixmTools.addProperty(prop, ahp, "txtDescrSite", "descriptionSite", optional=True)
        prop = self.oCtrl.oAixmTools.addProperty(prop, ahp, "txtNameCitySer", "cityServing", optional=True)
        prop = self.oCtrl.oAixmTools.addProperty(prop, ahp, "txtNameAdmin", "nameAdmin", optional=True)
        prop = self.oCtrl.oAixmTools.addProperty(prop, ahp, "txtRmk", "remark", optional=True)
        geom = {"type":"Point", "coordinates":self.oCtrl.oAixmTools.geo2coordinates(ahp)}
        return {"type":"Feature", "properties":prop, "geometry":geom}


    def parseObstacles(self):
        sTitle = "Obstacles"
        sXmlTag = "Obs"
        
        sMsg = "Parsing {0} to GeoJSON - {1}".format(sXmlTag, sTitle)
        self.oCtrl.oLog.info(sMsg)

        oList = self.oCtrl.oAixm.doc.find_all(sXmlTag)
        barre = bpaTools.ProgressBar(len(oList), 20, title=sMsg, isSilent=self.oCtrl.oLog.isSilent)
        idx = 0
        geojson = []
        for obs in oList:
            idx+=1
            geojson.append(self.obs2json(obs))
            barre.update(idx)
        barre.reset()
        self.oCtrl.oAixmTools.writeGeojsonFile("obstacles", geojson)
        return

    def obs2json(self, obs):
        prop = self.oCtrl.oAixmTools.initProperty("Obstacle")
        prop = self.oCtrl.oAixmTools.addProperty(prop, obs, "txtDescrType", "type")
        prop = self.oCtrl.oAixmTools.addProperty(prop, obs, "txtName", "name")
        prop = self.oCtrl.oAixmTools.addProperty(prop, obs, "txtDescrMarking", "marked", optional=True)
        prop = self.oCtrl.oAixmTools.addProperty(prop, obs, "codeLgt", "codeLight")
        prop = self.oCtrl.oAixmTools.addProperty(prop, obs, "txtDescrLgt", "descrLight", optional=True)
        prop = self.oCtrl.oAixmTools.addProperty(prop, obs, "valElev", "elevation")
        prop = self.oCtrl.oAixmTools.addProperty(prop, obs, "valHgt", "height", optional=True)
        prop = self.oCtrl.oAixmTools.addProperty(prop, obs, "uomDistVer", "verticalUnit")
        prop = self.oCtrl.oAixmTools.addProperty(prop, obs, "txtRmk", "remark", optional=True)
        geom = {"type":"Point", "coordinates":self.oCtrl.oAixmTools.geo2coordinates(obs)}
        return {"type":"Feature", "properties":prop, "geometry":geom}


    def parseRunwayCenterLinePosition(self):
        sTitle = "Runway Center Line Position"
        sXmlTag = "Rcp"
        
        sMsg = "Parsing {0} to GeoJSON - {1}".format(sXmlTag, sTitle)
        self.oCtrl.oLog.info(sMsg)
        
        oList = self.oCtrl.oAixm.doc.find_all(sXmlTag)
        barre = bpaTools.ProgressBar(len(oList), 20, title=sMsg, isSilent=self.oCtrl.oLog.isSilent)
        idx = 0
        geojson = []
        for rcp in oList:
            idx+=1
            geojson.append(self.rcp2json(rcp))
            barre.update(idx)
        barre.reset()
        self.oCtrl.oAixmTools.writeGeojsonFile("runwaysCenter", geojson)
        return
    
    def rcp2json(self, rcp):
        prop = self.oCtrl.oAixmTools.initProperty("Runway Center")
        prop = self.oCtrl.oAixmTools.addProperty(prop, rcp.RcpUid.RwyUid.AhpUid, "codeId")
        prop = self.oCtrl.oAixmTools.addProperty(prop, rcp.RcpUid.RwyUid, "txtDesig", "designator")
        prop = self.oCtrl.oAixmTools.addProperty(prop, rcp, "valElev", "elevation", optional=True)
        prop = self.oCtrl.oAixmTools.addProperty(prop, rcp, "uomDistVer", "verticalUnit", optional=True)
        geom = {"type":"Point", "coordinates":self.oCtrl.oAixmTools.geo2coordinates(rcp)}
        return {"type":"Feature", "properties":prop, "geometry":geom}


    def parseGateStands(self):
        sTitle = "Gates and Stands"
        sXmlTag = "Gsd"
        
        sMsg = "Parsing {0} to GeoJSON - {1}".format(sXmlTag, sTitle)
        self.oCtrl.oLog.info(sMsg) 

        oList = self.oCtrl.oAixm.doc.find_all(sXmlTag)
        barre = bpaTools.ProgressBar(len(oList), 20, title=sMsg, isSilent=self.oCtrl.oLog.isSilent)
        idx = 0
        geojson = []
        for gsd in oList:
            idx+=1
            geojson.append(self.gsd2json(gsd))
            barre.update(idx)
        barre.reset()
        self.oCtrl.oAixmTools.writeGeojsonFile("gates-stands", geojson)
        return
    
    def gsd2json(self, gsd):
        prop = self.oCtrl.oAixmTools.initProperty("Gate or Stand")
        prop = self.oCtrl.oAixmTools.addProperty(prop, gsd.GsdUid, "txtDesig", "designator")
        prop = self.oCtrl.oAixmTools.addProperty(prop, gsd.ApnUid, "txtName", "parkingPosition")
        prop = self.oCtrl.oAixmTools.addProperty(prop, gsd.ApnUid.AhpUid, "codeId")
        prop = self.oCtrl.oAixmTools.addProperty(prop, gsd, "codeType")
        prop = self.oCtrl.oAixmTools.addProperty(prop, gsd, "txtDescrRestrUse", optional=True)
        prop = self.oCtrl.oAixmTools.addProperty(prop, gsd, "txtRmk", optional=True)
        geom = {"type":"Point", "coordinates":self.oCtrl.oAixmTools.geo2coordinates(gsd)}
        return {"type":"Feature", "properties":prop, "geometry":geom}


    def parseGeographicBorders(self):
        sTitle = "Geographic borders"
        sXmlTag = "Gbr"
        
        sMsg = "Parsing {0} to GeoJSON - {1}".format(sXmlTag, sTitle)
        self.oCtrl.oLog.info(sMsg)
        
        if self.__geoBorders == None:
            self.__geoBorders = dict()
            oList = self.oCtrl.oAixm.doc.find_all(sXmlTag)
            barre = bpaTools.ProgressBar(len(oList), 20, title=sMsg, isSilent=self.oCtrl.oLog.isSilent)
            idx = 0
            geojson = []
            for gbr in oList:
                idx+=1
                j,l = self.gbr2json(gbr)
                geojson.append(j)
                self.__geoBorders[gbr.GbrUid["mid"]] = LineString(l)
                barre.update(idx)
        barre.reset()
        self.oCtrl.oAixmTools.writeGeojsonFile("borders", geojson)
        return
    
    def gbr2json(self, gbr):    
        prop = self.oCtrl.oAixmTools.initProperty("Geographic border")
        prop = self.oCtrl.oAixmTools.addProperty(prop, gbr, "codeType", "type")
        prop = self.oCtrl.oAixmTools.addProperty(prop, gbr.GbrUid, "txtName", "name")
        prop = self.oCtrl.oAixmTools.addProperty(prop, gbr, "txtRmk", "desc", optional=True)
        # geometry
        g = []
        l = []
        for gbv in gbr.find_all("Gbv"):
            if gbv.codeType.string not in ("GRC", "END"):
                self.oCtrl.oLog.critical("codetype non reconnu\n{0}".format(gbv), outConsole=True)
            g.append(self.oCtrl.oAixmTools.geo2coordinates(gbv))
            l.append((g[-1][0], g[-1][1]))
        geom = {"type":"LineString", "coordinates":g}        
        return ({"type":"Feature", "properties":prop, "geometry":geom}, l)


    def findAixmObjectAirspacesBorders(self, sAseUid):
        #----Old src - Lenteur de recherche
        #oBorder = [tagAbd for tagAbd in (self.oCtrl.oAixm.doc.findAll("Abd")) if tagAbd.AbdUid.AseUid["mid"]==sAseUid]
        #if len(oBorder)==1:
        #    return oBorder[0]
        #New optimized source with index
        oBorder=None
        if sAseUid in self.oAirspacesCatalog.oAirspacesBorders:
            oBorder = self.oAirspacesCatalog.oAirspacesBorders[sAseUid]
        return oBorder

    def findJsonObjectAirspacesBorders(self, sAseUid):
        for o in self.__geoAirspaces:
            if o["properties"]["UId"]==sAseUid:
                return o["geometry"]
        return None

    def parseAirspacesBorders(self, airspacesCatalog):
        self.oAirspacesCatalog = airspacesCatalog
        
        #Controle de prerequis
        if self.__geoBorders == None:
            self.parseGeographicBorders()
            
        sTitle = "Airspaces Borders"
        sXmlTag = "Abd"
        
        if not self.oCtrl.oAixm.doc.find(sXmlTag):
            sMsg = "Missing tags {0} - {1}".format(sXmlTag, sTitle)
            self.oCtrl.oLog.warning(sMsg, outConsole=True)
            return
        
        sMsg = "Parsing {0} to GeoJSON - {1}".format(sXmlTag, sTitle)
        self.oCtrl.oLog.info(sMsg)
        
        barre = bpaTools.ProgressBar(len(self.oAirspacesCatalog.oAirspaces), 20, title=sMsg, isSilent=self.oCtrl.oLog.isSilent)
        idx = 0
        self.__geoAirspaces = []                #Réinitialisation avant traitement global
        for k,oZone in self.oAirspacesCatalog.oAirspaces.items():
            idx+=1
            if not oZone["groupZone"]:          #Ne pas traiter les zones de type 'Regroupement'
                sAseUid = oZone["UId"]
                oBorder = self.findAixmObjectAirspacesBorders(sAseUid)
                if oBorder:
                    self.parseAirspaceBorder(oZone, oBorder)
                else:
                    sAseUidBase = self.oAirspacesCatalog.findZoneUIdBase(sAseUid)         #Identifier la zone de base (de référence)
                    if sAseUidBase==None:
                        self.oCtrl.oLog.warning("Missing Airspaces Borders AseUid={0}".format(sAseUid), outConsole=False)
                    else:
                        geom = self.findJsonObjectAirspacesBorders(sAseUidBase)  #Recherche si la zone de base a déjà été pasrsé
                        if geom:
                            self.__geoAirspaces.append({"type":"Feature", "properties":oZone, "geometry":geom})
                        else:
                            oBorder = self.findAixmObjectAirspacesBorders(sAseUidBase)
                            if oBorder==None:
                                self.oCtrl.oLog.warning("Missing Airspaces Borders AseUid={0} AseUidBase={1}".format(sAseUid, sAseUidBase), outConsole=False)
                            else:
                                self.parseAirspaceBorder(oZone, oBorder)
            barre.update(idx)
            
        barre.reset()
        return
        

    def saveAirspaces(self):
        if self.oCtrl.ALL:
            self.saveAirspacesFilter("all", "All Airspaces map")
        if self.oCtrl.IFR:
            self.saveAirspacesFilter("ifr", "IFR map (Instrument Flihgt Rules")
        if self.oCtrl.VFR:
            self.saveAirspacesFilter("vfr", "VFR map (Visual Flihgt Rules")
        if self.oCtrl.FreeFlight:
            self.saveAirspacesFilter("ff", "FreeFlight map (Paragliding / Hanggliding)")
        return


    def saveAirspacesFilter(self, context, title):
        sMsg = "Prepare GeoJSON file - {0}".format(title)
        self.oCtrl.oLog.info(sMsg)
        barre = bpaTools.ProgressBar(len(self.oAirspacesCatalog.oAirspaces), 20, title=sMsg, isSilent=self.oCtrl.oLog.isSilent)
        idx = 0
        oGeojson = []       #Initialisation avant filtrage spécifique
        for o in self.__geoAirspaces:
            oZone = o["properties"]
            idx+=1
            if not oZone["groupZone"]:          #Ne pas traiter les zones de type 'Regroupement'
                if context=="all":
                    oGeojson.append(o)
                if context=="ifr" and not oZone["vfrZone"]:
                    oGeojson.append(o)
                if context=="vfr" and oZone["vfrZone"]:
                    oGeojson.append(o)
                if context=="ff" and oZone["freeFlightZone"]:
                    oGeojson.append(o)
            barre.update(idx)
        barre.reset()        
        if oGeojson:
            self.oCtrl.oAixmTools.writeGeojsonFile("airspaces", oGeojson, context)
        return


    def parseAirspaceBorder(self, oZone, oBorder):
        g = []              #geometry
        points4map = []
        
        if oBorder.Circle:
            lon_c, lat_c = self.oCtrl.oAixmTools.geo2coordinates(oBorder.Circle,
                                           latitude=oBorder.Circle.geoLatCen.string,
                                           longitude=oBorder.Circle.geoLongCen.string)
            
            radius = float(oBorder.Circle.valRadius.string)
            if oBorder.uomRadius.string == "NM":
                radius = radius * aixmReader.CONST.nm
            if oBorder.uomRadius.string == "KM":
                radius = radius * 1000
            
            if self.oCtrl.bMakeWithNewSrc:
                Pcenter = Point(lon_c, lat_c)
                if self.oCtrl.MakePoints4map:
                    points4map.append(self.oCtrl.oAixmTools.make_point(Pcenter, "Circle Center of {0}".format(oZone["nameV"])))
                g = self.oCtrl.oAixmTools.make_arc(Pcenter, radius)
            else:
                srs = Proj(proj="ortho", lat_0=lon_c, lon_0=lat_c)
                g = self.oCtrl.oAixmTools.make_circle_ortho(lon_c, lat_c, radius, srs, oBorder)

            geom = {"type":"Polygon", "coordinates":[g]}
            
        else:
            avx_list = oBorder.find_all("Avx")
            for avx_cur in range(0,len(avx_list)):
                avx = avx_list[avx_cur]
                
                codeType = avx.codeType.string
                
                # 'Great Circle' or 'Rhumb Line' segment
                if codeType in ["GRC", "RHL"]:
                    p = self.oCtrl.oAixmTools.geo2coordinates(avx)
                    if self.oCtrl.MakePoints4map:
                        pt = Point(p[0], p[1])
                        points4map.append(self.oCtrl.oAixmTools.make_point(pt, "Point {0} of {1}; type={2}".format(avx_cur, oZone["nameV"], codeType)))
                    g.append(p)
                    
                # 'Counter Clockwise Arc' or 'Clockwise Arc'
                #Nota: 'ABE' = 'Arc By Edge' ne semble pas utilisé dans les fichiers SIA-France et Eurocontrol-Europe
                elif codeType in ["CCA", "CWA"]:
                    start = self.oCtrl.oAixmTools.geo2coordinates(avx, recurse=False)
                    if not self.oCtrl.bMakeWithNewSrc:
                        g.append(start)    #Pas la peine d'ajouter ce point ds le nouveau source car imposé dans le tracé du cercle/arc
                    
                    if avx_cur+1 == len(avx_list):
                        stop = g[0]
                    else:
                        stop = self.oCtrl.oAixmTools.geo2coordinates(avx_list[avx_cur+1], recurse=False)
                    
                    center = self.oCtrl.oAixmTools.geo2coordinates(avx,
                                             latitude=avx.geoLatArc.string,
                                             longitude=avx.geoLongArc.string)
                    
                    #New source
                    Pcenter = Point(center[0], center[1])
                    Pstart = Point(start[0], start[1])
                    Pstop = Point(stop[0], stop[1])
                    
                    if self.oCtrl.MakePoints4map:
                        points4map.append(self.oCtrl.oAixmTools.make_point(Pstart, "Arc Start {0} of {1}".format(avx_cur, oZone["nameV"])))
                        points4map.append(self.oCtrl.oAixmTools.make_point(Pcenter, "Arc Center {0} of {1}".format(avx_cur, oZone["nameV"])))
                        points4map.append(self.oCtrl.oAixmTools.make_point(Pstop, "Arc Stop {0} of {1}".format(avx_cur, oZone["nameV"])))
                    
                    #Alignement pas toujours idéal sur les extremités d'arcs
                    radius = float(avx.valRadiusArc.string)
                    if avx.uomRadiusArc.string == "NM":
                        radius = radius * aixmReader.CONST.nm
                    if avx.uomRadiusArc.string == "KM":
                        radius = radius * 1000
                        
                    if self.oCtrl.bMakeWithNewSrc:
                        #Test non-concluant - Tentative d'amélioration des arc par recalcul systématique du rayon sur la base des coordonnées des points
                        #arc = self.oCtrl.oAixmTools.make_arc2(Pcenter, Pstart, Pstop, 0.0, (codeType=="CWA"))
                        arc = self.oCtrl.oAixmTools.make_arc2(Pcenter, Pstart, Pstop, radius, (codeType=="CWA"))
                        for o in arc:   g.append(o)
                    else:
                        #Old and bad source :-(
                        # Convert to local meters
                        #srs = Proj(proj="ortho", lat_0=center[1], lon_0=center[0])             #ChristQ Err :-(
                        srs = Proj(proj="ortho", lat_0=center[0], lon_0=center[1])              #BPascal src ;-)
                        start_x, start_y = transform(p1=self.oCtrl.oAixmTools.pWGS, p2=srs, x=start[0], y=start[1])
                        stop_x, stop_y = transform(p1=self.oCtrl.oAixmTools.pWGS, p2=srs, x=stop[0], y=stop[1])
                        center_x, center_y = transform(p1=self.oCtrl.oAixmTools.pWGS, p2=srs, x=center[0], y=center[1])
                        # start / stop angles sont exprimés en raidans
                        start_angle = round(self.xy2angle(start_x-center_x, start_y-center_y), self.oCtrl.digit4roundArc)
                        stop_angle = round(self.xy2angle(stop_x-center_x, stop_y-center_y), self.oCtrl.digit4roundArc)
                                            
                        if codeType == "CWA" and stop_angle > start_angle:
                            stop_angle = stop_angle - 2 * aixmReader.CONST.pi
                        if codeType == "CCA" and stop_angle < start_angle:
                            start_angle = start_angle - 2 * aixmReader.CONST.pi
                        
                        # recompute radius from center/start coordinates in local projection
                        radius = math.sqrt(start_x**2+start_y**2)                 
                        
                        #Détermination du pas d'incrément de l'angle de l'arc de cercle
                        if self.oCtrl.Draft:
                            step = 0.10
                        else:
                            step = 0.025
                        
                        #Inversion du pas d'incrément dans le cas d'un arc anti-horaire...
                        if codeType == "CWA":
                            step = step*-1
    
                        #Construction des segments de l'arc
                        for a in self.frange(start_angle+step/2, stop_angle-step/2, step):
                            x = center_x + math.cos(a) * radius
                            y = center_y + math.sin(a) * radius
                            lon, lat = transform(p1=srs, p2=self.oCtrl.oAixmTools.pWGS, x=x, y=y)
                            if lon==math.inf or lat==math.inf:
                                sMsg = " - Context oBorder.aseuid[mid']={0} a={1} x={2} y={3}".format(oBorder.AseUid["mid"], a, x, y)
                                self.oCtrl.oLog.critical("transform() return error" + sMsg, outConsole=True)
                            else:
                                g.append([lon, lat])

                # 'Sequence of geographical (political) border vertexes'    
                elif codeType == "FNT":
                    # geographic borders
                    start = self.oCtrl.oAixmTools.geo2coordinates(avx)
                    if avx_cur+1 == len(avx_list):
                        stop = g[0]
                    else:
                        stop = self.oCtrl.oAixmTools.geo2coordinates(avx_list[avx_cur+1])
                        
                    if avx.GbrUid["mid"] in self.__geoBorders:
                        fnt = self.__geoBorders[avx.GbrUid["mid"]]
                        start_d = fnt.project(Point(start[0], start[1]), normalized=True)
                        stop_d = fnt.project(Point(stop[0], stop[1]), normalized=True)
                        geom = self.oCtrl.oAixmTools.substring(fnt, start_d, stop_d, normalized=True)
                        for c in geom.coords:
                            lon, lat = c
                            g.append([lon, lat])
                    else:
                        self.oCtrl.oLog.warning("Missing geoBorder GbrUid='{0}' Name={1}".format(avx.GbrUid["mid"], avx.GbrUid.txtName.string), outConsole=False)
                        g.append(start)
                else:
                    g.append(self.oCtrl.oAixmTools.geo2coordinates(avx))
    
            if len(g) == 0:
                self.oCtrl.oLog.error("Geometry vide\n{0}".format(oBorder.prettify()), outConsole=True)
                geom = None
            elif len(g) == 1:
                geom = {"type":"Point", "coordinates":g[0]}
            elif len(g) == 2:
                geom = {"type":"LineString", "coordinates":g}
            else:
                #Contrôle de fermeture du Polygone
                if g[0] != g[-1]:
                    g.append(g[0])
                geom = {"type":"Polygon", "coordinates":[g]}
        
        #Ajout spécifique des points complémentaires pour map des cartographies
        for g0 in points4map:
            for g1 in g0:
                self.__geoAirspaces.append(g1)
        self.__geoAirspaces.append({"type":"Feature", "properties":oZone, "geometry":geom})
        return

