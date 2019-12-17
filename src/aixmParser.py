#!/usr/bin/env python3

import os
import sys
import json

from bs4 import BeautifulSoup
from shapely.geometry import LineString

from aixm2json.aixm2json import ahp2json, obs2json, rcp2json, gbr2json, abd2json, tower2json, gsd2json
from aixm2openair.aixm2openair import pleasewait

sSrcPath = '../test-data/'
sOutPath = '../out/'

### Initialisations d'environnement
if len(sys.argv) < 2:
    sSrcEncoding = 'utf-8'
    sDstEncoding = 'utf-8'
    #sSrcFile = sSrcPath + 'tst.xml'
    sSrcFile = sSrcPath + 'AIXM4.5_SIA-FR_sample.xml'
    #sSrcFile = sSrcPath + 'AIXM4.5_SIA-FR_2019-12-05.xml'
    #sSrcFile = sSrcPath + 'AIXM4.5_Eurocontrol-EU_2019-11-07.xml'
else:
    sSrcFile = sys.argv[1]

try:
    if not os.path.exists(sOutPath):
        os.mkdir(sOutPath)
except OSError:
    print ("Creation of the directory %s failed" % sOutPath)

print("parsing xml")
#aixm = BeautifulSoup(open(sSrcFile), 'lxml')                                                       #old --encoding error with Eurocontrol files
#aixm = BeautifulSoup(open(sSrcFile, encoding=sSrcEncoding), 'xml', from_encoding=sSrcEncoding)     #std xml solution, with case sensitive elements
aixm = BeautifulSoup(open(sSrcFile, encoding=sSrcEncoding), 'lxml', from_encoding=sSrcEncoding)     #html solution, with lowercase elements


print("extract ahp - aerodromes/heliports")
out = []
for o in aixm.find_all('ahp'):
    out.append(ahp2json(o))

with open(sOutPath + 'aerodromes.geojson', 'w', encoding=sDstEncoding) as output:
    output.write(json.dumps({"type":"FeatureCollection", "features": out}, sort_keys=True, ensure_ascii=False))


print("extract obs - obstacles")
out = []
for o in aixm.find_all('obs'):
    out.append(obs2json(o))

with open(sOutPath + 'obstacles.geojson', 'w' , encoding=sDstEncoding) as output:
    output.write(json.dumps({"type":"FeatureCollection", "features": out}, sort_keys=True, ensure_ascii=False))


print("extract rcp - runway centers")
out = []
for o in aixm.find_all('rcp'):
    out.append(rcp2json(o))

with open(sOutPath + 'runway_center.geojson', 'w', encoding=sDstEncoding) as output:
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
with open(sOutPath + 'border.geojson', 'w', encoding=sDstEncoding) as output:
    output.write(json.dumps({"type":"FeatureCollection", "features": out}, sort_keys=True, ensure_ascii=False))


print("extract abd - airspace boundaries")
out = []
for o in aixm.find_all('abd'):
    out.append(abd2json(o,ase,gbr))

with open(sOutPath + 'airspace.geojson', 'w', encoding=sDstEncoding) as output:
    output.write(json.dumps({"type":"FeatureCollection", "features": out}, sort_keys=True, ensure_ascii=False))


print("extract uni - control towers")
out = []
for o in aixm.find_all('uni'):
    twr = tower2json(o)
    if twr:
        out.append(twr)

with open(sOutPath + 'tower.geojson', 'w', encoding=sDstEncoding) as output:
    output.write(json.dumps({"type":"FeatureCollection", "features": out}, sort_keys=True, ensure_ascii=False))


print("extract gsd - gate stands")
out = []
for o in aixm.find_all('gsd'):
    out.append(gsd2json(o))

with open(sOutPath + 'gate_stand.geojson', 'w', encoding=sDstEncoding) as output:
    output.write(json.dumps({"type":"FeatureCollection", "features": out}, sort_keys=True, ensure_ascii=False))


print("done")
