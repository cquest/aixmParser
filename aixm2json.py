#!/usr/bin/env python3

import sys
import json
import math

from shapely.geometry import LineString, Point
from shapely.ops import split, nearest_points, snap
from bs4 import BeautifulSoup
from pyproj import Proj, transform


def substring(geom, start_dist, end_dist, normalized=False):
    """Return a line segment between specified distances along a linear geometry.

    Negative distance values are taken as measured in the reverse
    direction from the end of the geometry. Out-of-range index
    values are handled by clamping them to the valid range of values.
    If the start distances equals the end distance, a point is being returned.
    If the normalized arg is True, the distance will be interpreted as a
    fraction of the geometry's length.

    from shapely 1.7
    """

    assert(isinstance(geom, LineString))
    
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


def geo2coordinates(o, latitude=None, longitude=None, recurse=True):
    if latitude:
        s = latitude
    else:
        s = o.find('geolat', recursive=recurse).string
    lat = int(s[0:2])+int(s[2:4])/60+float(s[4:-1])/3600
    if s[-1] == 'S':
        lat = -lat

    if longitude:
        s = longitude
    else:
        s = o.find('geolong', recursive=recurse).string
    lon = int(s[0:3])+int(s[3:5])/60+float(s[5:-1])/3600
    if s[-1] == 'W':
        lon = -lon
    return([lon, lat])


def getfield(o, inputname, outputname=None):
    if outputname is None:
        outputname = inputname
    
    value = o.find(inputname.lower(), recursive=False)
    if value:
        return {outputname: value.string.replace('#','\n')}
    else:
        return None


def addfield(prop, field):
    if field:
        prop.update(field)
    return prop


def ahp2json(ahp):
    "Aerodrome / Heliport"

    # geometry
    geom = {"type": "Point", "coordinates": geo2coordinates(ahp)}

    # properties
    prop = dict()
    prop = addfield(prop, getfield(ahp, 'txtname', 'name'))
    prop = addfield(prop, getfield(ahp, 'codetype'))
    prop = addfield(prop, getfield(ahp, 'codeicao'))
    prop = addfield(prop, getfield(ahp, 'codeiata'))
    prop = addfield(prop, getfield(ahp, 'valelev','elevation'))
    prop = addfield(prop, getfield(ahp, 'uomdistver','vertical_unit'))
    prop = addfield(prop, getfield(ahp, 'txtdescrrefpt', 'description'))

    return {"type": "Feature", "geometry": geom, "properties": prop}


def obs2json(obs):
    "Obstacle"

    # geometry
    geom = {"type": "Point", "coordinates": geo2coordinates(obs)}

    # properties
    prop = dict()
    prop = addfield(prop, getfield(obs, 'txtname', 'name'))
    prop = addfield(prop, getfield(obs, 'txtdescrtype', 'description'))
    prop = addfield(prop, getfield(obs, 'txtDescrMarking', 'marked'))
    prop = addfield(prop, getfield(obs, 'codeLgt', 'light'))
    prop = addfield(prop, getfield(obs, 'valElev','elevation'))
    prop = addfield(prop, getfield(obs, 'valHgt','height'))
    prop = addfield(prop, getfield(obs, 'uomdistver','vertical_unit'))

    return {"type": "Feature", "geometry": geom, "properties": prop}

    # <Obs>
    #     <ObsUid mid="1577950">
    #         <geoLat>482936.00N</geoLat>
    #         <geoLong>0015526.00W</geoLong>
    #     </ObsUid>
    #     <txtName>22033</txtName>
    #     <txtDescrType>Pylône</txtDescrType>
    #     <codeGroup>N</codeGroup>
    #     <codeLgt>N</codeLgt>
    #     <txtDescrMarking>non balisé</txtDescrMarking>
    #     <codeDatum>U</codeDatum>
    #     <valElev>318</valElev>
    #     <valHgt>167</valHgt>
    #     <uomDistVer>FT</uomDistVer>
    # </Obs>


def rcp2json(o):
    "Runway Center line Position"

    # geometry
    geom = {"type": "Point", "coordinates": geo2coordinates(o.rcpuid)}

    # properties
    prop = dict()
    if o.ahpuid:
        prop = addfield(prop, getfield(o.ahpuid, 'codeid', 'codeicao'))
    if o.rwyuid:
        prop = addfield(prop, getfield(o.rwyuid, 'txtDesig', 'name'))
    prop = addfield(prop, getfield(o, 'valElev','elevation'))
    prop = addfield(prop, getfield(o, 'uomdistver','vertical_unit'))

    return {"type": "Feature", "geometry": geom, "properties": prop}

    # <Rcp>
    #     <RcpUid mid="1532169">
    #         <RwyUid mid="1528969">
    #             <AhpUid mid="1521170">
    #                 <codeId>LFMD</codeId>
    #             </AhpUid>
    #             <txtDesig>04/22</txtDesig>
    #         </RwyUid>
    #         <geoLat>433253.80N</geoLat>
    #         <geoLong>0065736.42E</geoLong>
    #     </RcpUid>
    #     <codeDatum>WGE</codeDatum>
    #     <valElev>10</valElev>
    #     <uomDistVer>FT</uomDistVer>
    # </Rcp>


def frange(start, stop, step):
    "Float range"
    if step > 0:
        while start < stop:
            yield start
            start += step
    else:
        while start > stop:
            yield start
            start += step


def xy2angle(x,y):
    if x == 0:
        if y>0:
            angle = pi/2
        else:
            angle = -pi/2
    else:
        angle = math.atan(y/x)
    if x<0:
        angle = angle + pi
    elif y<0:
        angle = (angle + 2 * pi)
    return angle % (2*pi)


def make_circle(lon, lat, radius, srs):
    g = []
    step = pi*2/120 if radius > 100 else pi*2/8
    center_x, center_y = transform(pWGS, srs, lon, lat)
    for a in frange(0, pi*2, step):
        x = center_x + math.cos(a) * radius
        y = center_y + math.sin(a) * radius
        lon, lat = transform(srs, pWGS, x, y)
        g.append([round(lon,6), round(lat,6)])
    return g

def abd2json(o):
    "Airspace Border"
    # properties
    prop = dict()
    prop.update({"uid": o.abduid['mid']})
    if o.aseuid:
        prop = addfield(prop, getfield(o.aseuid, 'codetype'))
        prop = addfield(prop, getfield(o.aseuid, 'codeid'))

    if o.aseuid["mid"] in ase:
        a = ase[o.aseuid["mid"]]
        prop = addfield(prop, getfield(a, 'txtname', 'name'))
        prop = addfield(prop, getfield(a, 'codeclass', 'class'))
        prop = addfield(prop, getfield(a, 'codedistverupper', 'upper_type'))
        prop = addfield(prop, getfield(a, 'valdistverupper', 'upper_value'))
        prop = addfield(prop, getfield(a, 'uomdistverupper', 'upper_unit'))
        prop = addfield(prop, getfield(a, 'codedistverlower', 'lower_type'))
        prop = addfield(prop, getfield(a, 'valdistverlower', 'lower_value'))
        prop = addfield(prop, getfield(a, 'uomdistverlower', 'lower_unit'))
        prop = addfield(prop, getfield(a, 'txtrmk', 'remark'))
        # approximate altitudes in meters
        up = None
        if a.uomdistverupper.string == 'FL':
            up = float(a.valdistverupper.string) * ft * 100
        elif a.uomdistverupper.string == 'FT':
            up = float(a.valdistverupper.string) * ft
        elif a.uomdistverupper.string == 'M':
            up = float(a.valdistverupper.string)
        if up is not None:
            prop.update({"upper_m": int(up)})
        low = None
        if a.uomdistverlower.string == 'FL':
            low = float(a.valdistverlower.string) * ft * 100
        elif a.uomdistverlower.string == 'FT':
            low = float(a.valdistverlower.string) * ft
        elif a.uomdistverlower.string == 'M':
            low = float(a.valdistverlower.string)
        if low is not None:
            prop.update({"lower_m": int(low)})

    # geometry
    g = []
    if o.circle:
        lon_c, lat_c = geo2coordinates(o.circle,
                                       latitude=o.geolatcen.string,
                                       longitude=o.geolongcen.string)
        radius = float(o.valradius.string)
        if o.uomradius.string == 'NM':
            radius = radius * nm
        g = make_circle(lon_c, lat_c, radius, Proj(proj='ortho', lat_0=lat_c, lon_0=lon_c))
        geom = {"type": "Polygon", "coordinates": [g]}

        prop = addfield(prop, getfield(o.valradius, 'radius'))
        prop = addfield(prop, getfield(o.uomradius, 'radius_unit'))
    else:
        avx_list = o.find_all('avx')
        for avx_cur in range(0,len(avx_list)):
            avx = avx_list[avx_cur]
            codetype = avx.codetype.string
            if codetype in ['GRC', 'RHL']:
                # great-circle segment
                g.append(geo2coordinates(avx))
            elif codetype in ['CCA', 'CWA']:
                # arcs
                start = geo2coordinates(avx, recurse=False)
                if avx_cur+1 == len(avx_list):
                    stop = g[0]
                else:
                    stop = geo2coordinates(avx_list[avx_cur+1], recurse=False)
                center = geo2coordinates(avx,
                                         latitude=avx.geolatarc.string,
                                         longitude=avx.geolongarc.string)
                g.append(start)
                radius = float(avx.valradiusarc.string)
                if avx.uomradiusarc.string == 'NM':
                    radius = radius * nm
                # convert to local meters
                srs = Proj(proj='ortho', lat_0=center[1], lon_0=center[0])
                start_x, start_y = transform(pWGS, srs, start[0], start[1])
                stop_x, stop_y = transform(pWGS, srs, stop[0], stop[1])
                center_x, center_y = transform(pWGS, srs, center[0], center[1])
                # start / stop angles
                start_angle = xy2angle(start_x-center_x, start_y-center_y)
                stop_angle = xy2angle(stop_x-center_x, stop_y-center_y)
                step = -0.025 if codetype == 'CWA' else 0.025
                if codetype == 'CWA' and stop_angle > start_angle:
                    stop_angle = stop_angle - 2*pi
                if codetype == 'CCA' and stop_angle < start_angle:
                    start_angle = start_angle - 2*pi
                for a in frange(start_angle, stop_angle, step):
                    x = center_x + math.cos(a) * radius
                    y = center_y + math.sin(a) * radius
                    lon, lat = transform(srs, pWGS, x, y)
                    g.append([lon, lat])
            elif codetype == 'FNT':
                # geographic borders
                start = geo2coordinates(avx)
                if avx_cur+1 == len(avx_list):
                    stop = g[0]
                else:
                    stop = geo2coordinates(avx_list[avx_cur+1])
                fnt = gbr[avx.gbruid["mid"]]
                start_d = fnt.project(Point(start[0], start[1]), normalized=True)
                stop_d = fnt.project(Point(stop[0], stop[1]), normalized=True)
                geom = substring(fnt, start_d, stop_d, normalized=True)
                for c in geom.coords:
                    lon, lat = c
                    g.append([lon, lat])
            else:
                g.append(geo2coordinates(avx))

        if (len(g)==0):
            print(o.prettify())
            geom = None
        elif len(g) == 1:
            srs = Proj(proj='ortho', lat_0=g[0][1], lon_0=g[0][0])
            geom = {"type": "Polygon", "coordinates": make_circle(g[0][0], g[0][1], 100, srs)}
        else:
            g.append(g[0])
            geom = {"type": "Polygon", "coordinates": [g]}
        
    return {"type": "Feature", "geometry": geom, "properties": prop}

    # <Abd>
    #     <AbdUid mid="1570252">
    #         <AseUid mid="1562867">
    #             <codeType>SECTOR</codeType>
    #             <codeId>LFRRVU</codeId>
    #         </AseUid>
    #     </AbdUid>
    #     <Avx>
    #         <codeType>GRC</codeType>
    #         <geoLat>493400.00N</geoLat>
    #         <geoLong>0042700.00W</geoLong>
    #         <codeDatum>WGE</codeDatum>
    #     </Avx>
    #     <Avx>
    #         <codeType>GRC</codeType>
    #         <geoLat>500000.00N</geoLat>
    #         <geoLong>0020000.00W</geoLong>
    #         <codeDatum>WGE</codeDatum>
    #     </Avx>
    #     <Avx>
    #         <codeType>GRC</codeType>
    #         <geoLat>494343.00N</geoLat>
    #         <geoLong>0015825.00W</geoLong>
    #         <codeDatum>WGE</codeDatum>
    #     </Avx>
    #     <Avx>
    #         <codeType>GRC</codeType>
    #         <geoLat>485404.00N</geoLat>
    #         <geoLong>0024822.00W</geoLong>
    #         <codeDatum>WGE</codeDatum>
    #     </Avx>
    #     <Avx>
    #         <codeType>GRC</codeType>
    #         <geoLat>484607.00N</geoLat>
    #         <geoLong>0025950.00W</geoLong>
    #         <codeDatum>WGE</codeDatum>
    #     </Avx>
    #     <Avx>
    #         <codeType>GRC</codeType>
    #         <geoLat>484746.00N</geoLat>
    #         <geoLong>0040157.00W</geoLong>
    #         <codeDatum>WGE</codeDatum>
    #     </Avx>
    # </Abd>


def gbr2json(o):
    "Geographic borders"

    # geometry
    g = []
    l = []
    for gbv in o.find_all('gbv'):
        if gbv.codetype.string not in ['GRC', 'END']:
            print(gbv)
        g.append(geo2coordinates(gbv))
        l.append((g[-1][0], g[-1][1]))
    geom = { "type":"LineString", "coordinates": g }

    # properties
    prop = dict()
    prop = addfield(prop, getfield(o.gbruid, 'txtname', 'name'))
    prop = addfield(prop, getfield(o, 'codetype', 'type'))
    prop = addfield(prop, getfield(o, 'txtrmk', 'remark'))
    
    return ({"type": "Feature", "geometry": geom, "properties": prop} , l)

    # <Gbr>
    #     <GbrUid mid="1544998">
    #         <txtName>ZR:LE</txtName>
    #     </GbrUid>
    #     <codeType>OTHER</codeType>
    #     <Gbv>
    #         <codeType>GRC</codeType>
    #         <geoLat>424729.76N</geoLat>
    #         <geoLong>0000031.32W</geoLong>
    #         <codeDatum>WGE</codeDatum>
    #     </Gbv>
    #     ...


def tower2json(o):
    "Control towers"
    if o.codetype.string == 'TWR':
        # geometry
        geom = { "type":"Point", "coordinates": geo2coordinates(o) }

        # properties
        prop = dict()
        prop = addfield(prop, getfield(o.uniuid, 'txtname', 'name'))

        return {"type": "Feature", "geometry": geom, "properties": prop}

    # <Uni>
    #     <UniUid mid="1524684">
    #         <txtName>LFBR MURET</txtName>
    #     </UniUid>
    #     <OrgUid mid="1520800">
    #         <txtName>FRANCE</txtName>
    #     </OrgUid>
    #     <AhpUid mid="1521106">
    #         <codeId>LFBR</codeId>
    #     </AhpUid>
    #     <codeType>TWR</codeType>
    #     <codeClass>OTHER</codeClass>
    #     <geoLat>432656.96N</geoLat>
    #     <geoLong>0011549.30E</geoLong>
    #     <codeDatum>WGE</codeDatum>
    # </Uni>
 
def gsd2json(o):
    "Gate stands"
    # geometry
    geom = { "type":"Point", "coordinates": geo2coordinates(o) }

    # properties
    prop = dict()
    prop = addfield(prop, getfield(o.gsduid, 'txtdesig', 'ref'))
    prop = addfield(prop, getfield(o.gsduid.apnuid.ahpuid, 'codeid', 'airport_ref'))

    return {"type": "Feature", "geometry": geom, "properties": prop}

    # <Gsd>
    #     <GsdUid mid="1583952">
    #         <ApnUid mid="1574122">
    #             <AhpUid mid="1520960">
    #                 <codeId>LFMN</codeId>
    #             </AhpUid>
    #             <txtName>LFMN-APRON</txtName>
    #         </ApnUid>
    #         <txtDesig>Y2</txtDesig>
    #     </GsdUid>
    #     <codeType>OTHER</codeType>
    #     <geoLat>433923.85N</geoLat>
    #     <geoLong>0071214.03E</geoLong>
    #     <codeDatum>WGE</codeDatum>
    # </Gsd>


pLocal = Proj(init='epsg:2154')
pWGS = Proj(init='epsg:4326')
nm = 1852   # Nautic Mile to meters
ft = 0.3048 # foot in meter
pi = 3.1415926

print("parsing xml")
aixm = BeautifulSoup(open(sys.argv[1]), 'lxml')

print("extract ahp - aerodromes/heliports")
out = []
for o in aixm.find_all('ahp'):
    out.append(ahp2json(o))

with open('aerodromes.geojson','w') as output:
    output.write(json.dumps({"type":"FeatureCollection", "features": out}, sort_keys=True, ensure_ascii=False))

print("extract obs - obstacles")
out = []
for o in aixm.find_all('obs'):
    out.append(obs2json(o))

with open('obstacles.geojson','w') as output:
    output.write(json.dumps({"type":"FeatureCollection", "features": out}, sort_keys=True, ensure_ascii=False))

print("extract rcp - runway centers")
out = []
for o in aixm.find_all('rcp'):
    out.append(rcp2json(o))

with open('runway_center.geojson','w') as output:
    output.write(json.dumps({"type":"FeatureCollection", "features": out}, sort_keys=True, ensure_ascii=False))

print("extract ase - airspace")
ase = dict()
for o in aixm.find_all('ase'):
    ase[o.aseuid['mid']] = o

print("extract gbr - geographic borders")
gbr = dict()
out = []
for o in aixm.find_all('gbr'):
    j,l = gbr2json(o)
    out.append(j)
    gbr[o.gbruid['mid']] = LineString(l)
with open('border.geojson','w') as output:
    output.write(json.dumps({"type":"FeatureCollection", "features": out}, sort_keys=True, ensure_ascii=False))

print("extract abd - airspace boundaries")
out = []
for o in aixm.find_all('abd'):
    out.append(abd2json(o))

with open('airspace.geojson','w') as output:
    output.write(json.dumps({"type":"FeatureCollection", "features": out}, sort_keys=True, ensure_ascii=False))

print("extract uni - control towers")
out = []
for o in aixm.find_all('uni'):
    twr = tower2json(o)
    if twr:
        out.append(twr)

with open('tower.geojson','w') as output:
    output.write(json.dumps({"type":"FeatureCollection", "features": out}, sort_keys=True, ensure_ascii=False))

print("extract gsd - gate stands")
out = []
for o in aixm.find_all('gsd'):
    out.append(gsd2json(o))

with open('gate_stand.geojson','w') as output:
    output.write(json.dumps({"type":"FeatureCollection", "features": out}, sort_keys=True, ensure_ascii=False))

print("done")
