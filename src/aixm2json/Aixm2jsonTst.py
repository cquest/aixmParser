#!/usr/bin/env python3

import bpaTools
import aixm2json

from shapely.geometry import Point   #Polygon, mapping
from pyproj import Proj, transform


__ClsName__     = bpaTools.getFileName(__file__)

class Aixm2jsonTst:
    
    def __init__(self, oCtrl):
        bpaTools.initEvent(__file__, oCtrl.oLog)
        self.oCtrl = oCtrl
        self.oAixm2json = aixm2json.Aixm2json4_5(oCtrl)
        print()
        self.oCtrl.oLog.info("Tests de génération Geojson", outConsole=True)
        return
    
    
    def testAll(self):
        self.tstGeojsonPosition()
        self.tstGeojsonArcHorAntihor()
        self.tstGeojsonZonesCTR_LORIENT()
        self.tstGeojsonObjects()
        self.oCtrl.oLog.info("Fin des tests", outConsole=True)
        return
    
    """
    Contrôle d'interprétation des positionnements depuis une source 'aixm'
    """
    def tstGeojsonPosition(self):
        geojson=[]
        
        lon1, lat1 = self.oAixm2json.geo2coordinates(None,
                                        latitude="494300.00N",
                                        longitude="0024007.00E")
        p1 = Point(lon1, lat1)
        geojson.append(self.oAixm2json.make_point(p1, "Point {0}".format(Point)))
        #print(p1)
        
        lon2, lat2 = self.oAixm2json.geo2coordinates(None,
                                        latitude="494300N",
                                        longitude="0024007E")
        p2 = Point(lon2, lat2)
        geojson.append(self.oAixm2json.make_point(p2, "Point {0}".format(Point)))
        #print(p2)
        
        ret=[]
        #Ajout spécifique des points complémentaires pour map des cartographies
        for g0 in geojson:
            for g1 in g0:
                ret.append(g1)
                
        self.oAixm2json.writeGeojsonFile(__ClsName__ + "-Position", ret)
        return

    
    def tstGeojsonArcHorAntihor(self):
        geojson=[]
        
        #Ligne 1 : CWA
        lon, lat = self.oAixm2json.geo2coordinates(None, latitude="480138.00N", longitude="0032614.00W")
        p1 = Point(lon, lat)
        lon, lat = self.oAixm2json.geo2coordinates(None, latitude="474538.00N", longitude="0032624.00W")
        c1 = Point(lon, lat)
        radius = float(16*1852)       #1852 = Nautic Mile to meters
        #Ligne 2 : GRC
        lon, lat = self.oAixm2json.geo2coordinates(None, latitude="474041.00N", longitude="0030347.00W")
        p2 = Point(lon, lat)
        #Ligne 3 : CWA
        lon, lat = self.oAixm2json.geo2coordinates(None, latitude="472939.00N", longitude="0032534.00W")
        p3 = Point(lon, lat)
        lon, lat = self.oAixm2json.geo2coordinates(None, latitude="474538.00N", longitude="0032624.00W")
        c3 = Point(lon, lat) 
        #Ligne 4 : GRC
        lon, lat = self.oAixm2json.geo2coordinates(None, latitude="475007.00N", longitude="0034916.00W")
        p4 = Point(lon, lat)        
        
        #Tests Arc horaires
        g = self.oAixm2json.make_arc2(c1, p1, p2, radius=0.0, clockwiseArc=True)
        g = {"type":"LineString", "coordinates":g}
        geojson.append({"type":"Feature", "properties":{"name": "Arc"}, "geometry":g})
        
        g = self.oAixm2json.make_arc2(c3, p3, p4, radius=0.0, clockwiseArc=True)
        g = {"type":"LineString", "coordinates":g}
        geojson.append({"type":"Feature", "properties":{"name": "Arc"}, "geometry":g})
        
        """
        g = self.oAixm2json.make_arc2(c3, p1, p3, radius=0.0, clockwiseArc=True)
        g = {"type":"LineString", "coordinates":g}
        geojson.append({"type":"Feature", "properties":{"name": "Arc"}, "geometry":g})
        
        g = self.oAixm2json.make_arc2(c3, p2, p3, radius=0.0, clockwiseArc=True)
        g = {"type":"LineString", "coordinates":g}
        geojson.append({"type":"Feature", "properties":{"name": "Arc"}, "geometry":g}
        
        g = self.oAixm2json.make_arc2(c3, p2, p4, radius=0.0, clockwiseArc=True)
        g = {"type":"LineString", "coordinates":g}
        geojson.append({"type":"Feature", "properties":{"name": "Arc"}, "geometry":g})
        
        g = self.oAixm2json.make_arc2(c3, p3, p1, radius=0.0, clockwiseArc=True)
        g = {"type":"LineString", "coordinates":g}
        geojson.append({"type":"Feature", "properties":{"name": "Arc"}, "geometry":g})
        
        g = self.oAixm2json.make_arc2(c3, p3, p2, radius=0.0, clockwiseArc=True)
        g = {"type":"LineString", "coordinates":g}
        geojson.append({"type":"Feature", "properties":{"name": "Arc"}, "geometry":g})
        """
        
        #Tests Arcs Antihoraires
        """
        g = self.oAixm2json.make_arc2(c1, p2, p1, radius=0.0, clockwiseArc=False)
        g = {"type":"LineString", "coordinates":g}
        geojson.append({"type":"Feature", "properties":{"name": "Arc"}, "geometry":g})
        
        g = self.oAixm2json.make_arc2(c3, p4, p3, radius=0.0, clockwiseArc=False)
        g = {"type":"LineString", "coordinates":g}
        geojson.append({"type":"Feature", "properties":{"name": "Arc"}, "geometry":g})
        
        g = self.oAixm2json.make_arc2(c3, p3, p1, radius=0.0, clockwiseArc=False)
        g = {"type":"LineString", "coordinates":g}
        geojson.append({"type":"Feature", "properties":{"name": "Arc"}, "geometry":g})
        
        g = self.oAixm2json.make_arc2(c3, p3, p1, radius=0.0, clockwiseArc=False)
        g = {"type":"LineString", "coordinates":g}
        geojson.append({"type":"Feature", "properties":{"name": "Arc"}, "geometry":g})
        """
        
        self.oAixm2json.writeGeojsonFile(__ClsName__ + "-ArcHorAntihor", geojson)
        return


    def tstGeojsonZonesCTR_LORIENT(self):
        geojson=[]
        
        #Ligne 1 : CWA
        lon, lat = self.oAixm2json.geo2coordinates(None, latitude="480138.00N", longitude="0032614.00W")
        p1 = Point(lon, lat)
        lon, lat = self.oAixm2json.geo2coordinates(None, latitude="474538.00N", longitude="0032624.00W")
        c1 = Point(lon, lat)
        radius = float(16*1852)       #1852 = Nautic Mile to meters
        #Ligne 2 : GRC
        lon, lat = self.oAixm2json.geo2coordinates(None, latitude="474041.00N", longitude="0030347.00W")
        p2 = Point(lon, lat)   
        #Ligne 3 : CWA
        lon, lat = self.oAixm2json.geo2coordinates(None, latitude="472939.00N", longitude="0032534.00W")
        p3 = Point(lon, lat)
        lon, lat = self.oAixm2json.geo2coordinates(None, latitude="474538.00N", longitude="0032624.00W")
        c3 = Point(lon, lat) 
        #Ligne 4 : GRC
        lon, lat = self.oAixm2json.geo2coordinates(None, latitude="475007.00N", longitude="0034916.00W")
        p4 = Point(lon, lat)

        #Tracé des points
        g = {"type":"Point", "coordinates":self.oAixm2json.Point2array(p1)}
        geojson.append({"type":"Feature", "properties":{"name": "p1"}, "geometry":g})
        g = {"type":"Point", "coordinates":self.oAixm2json.Point2array(c1)}
        geojson.append({"type":"Feature", "properties":{"name": "c1"}, "geometry":g})
        g = {"type":"Point", "coordinates":self.oAixm2json.Point2array(p2)}
        geojson.append({"type":"Feature", "properties":{"name": "p2"}, "geometry":g})
        g = {"type":"Point", "coordinates":self.oAixm2json.Point2array(p3)}
        geojson.append({"type":"Feature", "properties":{"name": "p3"}, "geometry":g})
        g = {"type":"Point", "coordinates":self.oAixm2json.Point2array(p4)}
        geojson.append({"type":"Feature", "properties":{"name": "p4"}, "geometry":g})

        g = self.oAixm2json.make_arc2(c1, p1, p2, radius=0.0, clockwiseArc=True)
        g = {"type":"LineString", "coordinates":g}
        geojson.append({"type":"Feature", "properties":{"name": "Arc"}, "geometry":g})
        
        g = [self.oAixm2json.Point2array(p2), self.oAixm2json.Point2array(p3)]
        g = {"type":"LineString", "coordinates":g}
        geojson.append({"type":"Feature", "properties":{"name": "line"}, "geometry":g})

        g = self.oAixm2json.make_arc2(c3, p3, p4, radius=0.0, clockwiseArc=True)
        g = {"type":"LineString", "coordinates":g}
        geojson.append({"type":"Feature", "properties":{"name": "Arc"}, "geometry":g})
        
        g = [self.oAixm2json.Point2array(p4), self.oAixm2json.Point2array(p1)]
        g = {"type":"LineString", "coordinates":g}
        geojson.append({"type":"Feature", "properties":{"name": "line"}, "geometry":g})
        
        self.oAixm2json.writeGeojsonFile(__ClsName__ + "-CtrLORIENT", geojson)
        return

    
    """
    Différents tests pour mise au point des constructions d'objects sous geojson
    """
    def tstGeojsonObjects(self):
        lon, lat = self.oAixm2json.geo2coordinates(None,                        #abd.circle
                                        latitude="484140.20N",       #abd.geolatcen.string
                                        longitude="0022002.50E")     #abd.geolongcen.string
        
        geojson=[]
        p0 = Point(lon, lat)
        radius20 = float("20")      #en mètres
        radius2k = float("2000")    #en mètres
        
        #Old function - Error !?
        p1 = Point(p0.x-0.06, p0.y)
        g = self.oAixm2json.make_circle_ortho(p1.x, p1.y, radius2k, Proj(proj="ortho", lat_0=p0.y, lon_0=p0.x))
        g = {"type":"Polygon", "coordinates":[g]}
        geojson.append({"type":"Feature", "properties":{"name": "Function Error - make_circle_ortho()"}, "geometry":g})
        #print(g)
        #print(str(g).replace(chr(39),chr(34)))          #Pour extraire le cercle dans la fenêtre de debug...

        #Creation d'un Cercle avec Point en son centre
        g = {"type":"Point", "coordinates":self.oAixm2json.Point2array(p0)}
        geojson.append({"type":"Feature", "properties":{"name": "Center"}, "geometry":g})
        g = self.oAixm2json.make_arc(p0, radius2k)
        g = {"type":"Polygon", "coordinates":[g]}
        geojson.append({"type":"Feature", "properties":{"name": "Cercle" + str(radius2k) + "m"}, "geometry":g})
        
        #Creation de 2 Arcs avec Point en son centre
        p2 = Point(p0.x+0.06, p0.y)
        g = {"type":"Point", "coordinates":self.oAixm2json.Point2array(p2)}
        geojson.append({"type":"Feature", "properties":{"name": "Center of Arcs"}, "geometry":g})
        g = self.oAixm2json.make_arc(p2, radius2k, 10.0, 135.0)
        g = {"type":"LineString", "coordinates":g}
        geojson.append({"type":"Feature", "properties":{"name": "Arc line 10°/135°"}, "geometry":g})
        g = self.oAixm2json.make_arc(p2, radius2k, 190.0, 300.0)
        g.append(g[0])      #Duplication du premier point pour fermeture d'un Polygone
        g = {"type":"Polygon", "coordinates":[g]}
        geojson.append({"type":"Feature", "properties":{"name": "Arc polygon 190°/300°"}, "geometry":g})      
        
        compObject = self._tstGeojsonComplexeObjects(p0, 1)
        for o in compObject:    geojson.append(o)
        
        compObject = self._tstGeojsonComplexeObjects(p0, 5)
        for o in compObject:    geojson.append(o)
        
        compObject = self._tstGeojsonComplexeObjects(p0, 20)
        for o in compObject:    geojson.append(o)
        
        compObject = self._tstGeojsonComplexeObjects(p0, 50, True)
        for o in compObject:    geojson.append(o)
            
        compObject = self._tstGeojsonComplexeObjects(p0, 200)
        for o in compObject:    geojson.append(o)
        
        self.oAixm2json.writeGeojsonFile(__ClsName__ + "-Objects", geojson)
        return

    """
    Construction d'un d'objet complexe sous geojson
    """
    def _tstGeojsonComplexeObjects(self, Pref, coef, detail=False):
        assert(isinstance(coef, int))
        
        geojson=[]
        polygon=[]
        
        #Creation des bases d'un rectangle
        p11 = Point(Pref.x-(0.05*coef), Pref.y-(0.05*coef))
        g = {"type":"Point", "coordinates":self.oAixm2json.Point2array(p11)}
        geojson.append({"type":"Feature", "properties":{"name": "Point 11, 1er rectangle"}, "geometry":g})
        p12 = Point(p11.x, p11.y-(0.05*coef))
        g = {"type":"Point", "coordinates":self.oAixm2json.Point2array(p12)}
        geojson.append({"type":"Feature", "properties":{"name": "Point 12, 2ieme du rectangle"}, "geometry":g})
        p13 = Point(p11.x+(0.1*coef), p11.y-(0.05*coef))
        g = {"type":"Point", "coordinates":self.oAixm2json.Point2array(p13)}
        geojson.append({"type":"Feature", "properties":{"name": "Point 13, 3ieme du rectangle"}, "geometry":g})
        p14 = Point(p11.x+(0.1*coef), p11.y)
        g = {"type":"Point", "coordinates":self.oAixm2json.Point2array(p14)}
        geojson.append({"type":"Feature", "properties":{"name": "Point 14, 4ieme du rectangle"}, "geometry":g})
        
        #Centre du rectangle
        p10  = Point(p11.x+((p14.x-p11.x)/2), p11.y-((p11.y-p12.y)/2))
        g = {"type":"Point", "coordinates":self.oAixm2json.Point2array(p10)}
        geojson.append({"type":"Feature", "properties":{"name": "Point 10, Centre du rectangle"}, "geometry":g})
        
        #Completude de formes pour complexifier le rectangle
        p111 = Point(p11.x-(0.01*coef), p11.y-(0.01*coef))
        g = {"type":"Point", "coordinates":self.oAixm2json.Point2array(p111)}
        geojson.append({"type":"Feature", "properties":{"name": "Point 111"}, "geometry":g})
        p121 = Point(p12.x-(0.01*coef), p12.y+(0.01*coef))
        g = {"type":"Point", "coordinates":self.oAixm2json.Point2array(p121)}
        geojson.append({"type":"Feature", "properties":{"name": "Point 121"}, "geometry":g})
        
        #Creation d'une ligne de contour
        g = [self.oAixm2json.Point2array(p11), self.oAixm2json.Point2array(p111)]
        polygon = polygon + g
        g = {"type":"LineString", "coordinates":g}
        geojson.append({"type":"Feature", "properties":{"name": "line"}, "geometry":g})
            
        #Creation d'un arc de cercle de type horaire
        pCA = Point(p11.x-(0.03*coef), p10.y)
        g = {"type":"Point", "coordinates":self.oAixm2json.Point2array(pCA)}
        geojson.append({"type":"Feature", "properties":{"name": "Arc Center"}, "geometry":g})
        g = self.oAixm2json.make_arc2(pCA, p111, p121, clockwiseArc=True)
        arc1=g
        polygon = polygon + g
        g = {"type":"LineString", "coordinates":g}
        #print(str(g).replace(chr(39),chr(34)))
        geojson.append({"type":"Feature", "properties":{"name": "Arc"}, "geometry":g})
        
        """
        #Marquages spécifiques pour préciser les points de départ et de fin de l'Arc
        pA1 = Point(arc1[0][0], arc1[0][1])
        g = {"type":"Point", "coordinates":self.oAixm2json.Point2array(pA1)}
        geojson.append({"type":"Feature", "properties":{"name": "First Point of Arcs"}, "geometry":g})
        pA2 = Point(arc1[-1][0], arc1[-1][1])
        g = {"type":"Point", "coordinates":self.oAixm2json.Point2array(pA2)}
        geojson.append({"type":"Feature", "properties":{"name": "Last Point of Arcs"}, "geometry":g})
        """
        
        #Marquages spécifiques pour préciser les lignes entre le centre et départ de l'Arc
        g =[self.oAixm2json.Point2array(pCA), self.oAixm2json.Point2array(p111)]
        g = {"type":"LineString", "coordinates":g}
        geojson.append({"type":"Feature", "properties":{"name": "line"}, "geometry":g})
        g =[self.oAixm2json.Point2array(pCA), self.oAixm2json.Point2array(p121)]
        g = {"type":"LineString", "coordinates":g}
        geojson.append({"type":"Feature", "properties":{"name": "line"}, "geometry":g})
        
        #Creation d'une ligne de contour
        g = [self.oAixm2json.Point2array(p121), self.oAixm2json.Point2array(p12)]
        polygon = polygon + g
        g = {"type":"LineString", "coordinates":g}
        geojson.append({"type":"Feature", "properties":{"name": "line"}, "geometry":g})
        
        #Complexification de la formes
        p122s = Point(p12.x+(0.01*coef), p12.y)
        g = {"type":"Point", "coordinates":self.oAixm2json.Point2array(p122s)}
        geojson.append({"type":"Feature", "properties":{"name": "Debut d'arc anti-horaire"}, "geometry":g})
        p122c = Point(p12.x+(0.03*coef), p12.y+(0.01*coef))
        g = {"type":"Point", "coordinates":self.oAixm2json.Point2array(p122c)}
        geojson.append({"type":"Feature", "properties":{"name": "Centre d'arc anti-horaire"}, "geometry":g})
        
        #Poursuite de la ligne de raccrochage
        g = [self.oAixm2json.Point2array(p12), self.oAixm2json.Point2array(p122s)]
        polygon = polygon + g
        g = {"type":"LineString", "coordinates":g}
        geojson.append({"type":"Feature", "properties":{"name": "line"}, "geometry":g})
        
        #Creation d'un arc anti-horaire
        g = self.oAixm2json.make_arc3(p122c, p122s, 0.0, -120.0, 45.0)
        arc1=g
        polygon = polygon + g
        g = {"type":"LineString", "coordinates":g}
        geojson.append({"type":"Feature", "properties":{"name": "Arc"}, "geometry":g})        
        
        p122e = Point(arc1[-1][0], arc1[-1][1])
        g = {"type":"Point", "coordinates":self.oAixm2json.Point2array(p122e)}
        geojson.append({"type":"Feature", "properties":{"name": "Last Point of Arcs"}, "geometry":g})
        
        p123 = Point(p122e.x+(0.03*coef), p122e.y)
        g = {"type":"Point", "coordinates":self.oAixm2json.Point2array(p123)}
        geojson.append({"type":"Feature", "properties":{"name": "Point de décallage"}, "geometry":g})
        
        p124 = Point(p123.x, p12.y)
        g = {"type":"Point", "coordinates":self.oAixm2json.Point2array(p124)}
        geojson.append({"type":"Feature", "properties":{"name": "Point de raccrochage"}, "geometry":g})
        
         #Creation de lignes de raccrochage
        g = [self.oAixm2json.Point2array(p122e), self.oAixm2json.Point2array(p123)]
        polygon = polygon + g
        g = {"type":"LineString", "coordinates":g}
        geojson.append({"type":"Feature", "properties":{"name": "line"}, "geometry":g})
        
        #Poursuite de la ligne de contours
        g = [self.oAixm2json.Point2array(p123), self.oAixm2json.Point2array(p124)]
        polygon = polygon + g
        g = {"type":"LineString", "coordinates":g}
        geojson.append({"type":"Feature", "properties":{"name": "line"}, "geometry":g})
        
        g = [self.oAixm2json.Point2array(p124), self.oAixm2json.Point2array(p13)]
        polygon = polygon + g
        g = {"type":"LineString", "coordinates":g}
        geojson.append({"type":"Feature", "properties":{"name": "line"}, "geometry":g})
        
        g = [self.oAixm2json.Point2array(p13), self.oAixm2json.Point2array(p14)]
        polygon = polygon + g
        g = {"type":"LineString", "coordinates":g}
        geojson.append({"type":"Feature", "properties":{"name": "line"}, "geometry":g})
        
        g = [self.oAixm2json.Point2array(p14), self.oAixm2json.Point2array(p11)]
        polygon = polygon + g
        g = {"type":"LineString", "coordinates":g}
        geojson.append({"type":"Feature", "properties":{"name": "line"}, "geometry":g})
        
        if not detail:
            geojson=[]
            g = {"type":"Polygon", "coordinates":[polygon]}
            geojson.append({"type":"Feature", "properties":{"name": "Complex object"}, "geometry":g})
            
        return geojson
