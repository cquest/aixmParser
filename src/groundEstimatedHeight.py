#!/usr/bin/env python3

import bpaTools
import json
import os
import shutil
import numpy as np
import srtm


### Context applicatif
bpaTools.ctrlPythonVersion()
__AppName__     = bpaTools.getFileName(__file__)
__AppPath__     = bpaTools.getFilePath(__file__)
__AppVers__     = "1.0.0"
___AppId___     = __AppName__ + " v" + __AppVers__
__SrcPath__     = __AppPath__ + "../out/"
__OutPath__     = "referentials/"                       #__AppPath__ + "referentials/"
__LogFile__     = __OutPath__ + __AppName__ + ".log"
oLog = bpaTools.Logger(___AppId___,__LogFile__)
#oLog.resetFile()


#srtm library documentation - https://pypi.org/project/SRTM.py/
elevation_data = srtm.get_data()            # srtm.get_data(local_cache_dir="tmp_cache")
#SRTM.py tests
#print('Home (meters):', elevation_data.get_elevation(48.694548, 2.333953))
#print('Place de l avenir (meters):', elevation_data.get_elevation(48.700191, 2.325597))
#print('Attérissage de Doussart (meters):', elevation_data.get_elevation(45.781438, 6.222423))


sProp = "properties"
sGeom = "geometry"
sCoor = "coordinates"


def findZone(sZoneUId, oFeatures):
    oZone = None
    for o in oFeatures:
        if sProp in o:
            oProp = o[sProp]
            if oProp["UId"] == sZoneUId:
                oZone = o
                #oLog.info("Found Data: sZoneUId={0}".format(sZoneUId), outConsole=False)
                break
    if oZone==None:
        oLog.critical("Missing coordinates of area {}".format(sZoneUId))
    return oZone


def getCoordinates(oZone):
    return oZone[sGeom][sCoor][0]


def getGroundEstimatedHeight(oZone):
    oCoordinates = getCoordinates(oZone)
    lon = []
    lat = []
    for o in oCoordinates:
        lat.append(o[0])
        lon.append(o[1])
        
    #Estimation d'un carré représentatif de la zone
    latMin = min(lat)   #Bottom segment of square
    latMax = max(lat)   #Top segment of square
    lonMin = min(lon)   #Left segment of square
    lonMax = max(lon)   #Right segment of square
    #oLog.info("Data: sZoneUId={} - lonMin={} - lonMax={} - latMin={} - latMax={}\nCoordinate={}".format(sZoneUId, lonMin, lonMax, latMin, latMax, oCoordinates), outConsole=False)

    #Définition d'une suite de coordonnées pour représenter la surface de la zone carré
    step = 10
    latSerial = np.linspace(latMin, latMax, step)   #10 nombres établies entre la valeur mini et maxi
    lonSerial = np.linspace(lonMin, lonMax, step)   #10 nombres établies entre la valeur mini et maxi
    #oLog.info("lonMin={} - lonMax={} - latMin={} - latMax={} \nlonSerial={} \nlatSerial={}".format(lonMin, lonMax, latMin, latMax, lonSerial, latSerial), outConsole=False)

    #Définition d'une ligne (type serpentin) qui parcours la surface de la zone
    line = []
    switch=True
    for latIdx in range(0, step):
        if switch:
            for lonIdx in range(0, step, 1):
                line.append([latSerial[latIdx], lonSerial[lonIdx]])
        else:
            for lonIdx in range(step, 0, -1):
                line.append([latSerial[latIdx], lonSerial[lonIdx-1]])
        switch = not switch
    #oLog.info("line={}\n".format(line), outConsole=False)
    
    #Détermination des hauteurs terrain des 100 points (=step*step) qui couvre la zone géographique
    #srtm library documentation - https://pypi.org/project/SRTM.py/
    aElevation = []
    lastElevation = 0
    lCptNullValue = 0
    lCptError = 0
    for o in line:
        #sample: elevation_data.get_elevation(48.694548, 2.333953)
        lElevation = elevation_data.get_elevation(o[1], o[0])
        if lElevation==None:
            lCptError += 1
            lElevation = lastElevation
        
        if lElevation>0:
            lastElevation = lElevation
            aElevation.append(lElevation)
        elif lElevation==0 and lCptNullValue==0:
            lCptNullValue += 1
            aElevation.append(lElevation)

    #oLog.info("aElevation={}".format(aElevation), outConsole=False)
    if lCptError > 40:
         oLog.warning("{0} errors in call elevation_data.get_elevation()\nProperties={1}\naElevation{2}".format(lCptError, oZone[sProp], aElevation), outConsole=False)

    eSortedElevation = sorted(aElevation)
    
    idxMedium = int(len(eSortedElevation)/2)
    idxRetain = int(idxMedium+(idxMedium*(2/3)))
    lAltMin = eSortedElevation[0]
    lAltMax = eSortedElevation[len(eSortedElevation)-1]
    lAltMed = eSortedElevation[idxMedium]
    lAltRet = eSortedElevation[idxRetain]          #Valeur retenue pour l'estimation globale de la hauteur sol

    #¤Contruction d'une description geoJSON de la ligne de calcul d'élévations
    #oLog.info("oZone=\n{}".format(str(oZone).replace(chr(39),chr(34))), outConsole=False)
    geoJSON = []
    geoJSON.append(oZone)
    prop = {}
    prop.update({"name":"Square line"})
    prop.update({"lAltMin":lAltMin})
    prop.update({"lAltMax":lAltMax})
    prop.update({"lAltMed":lAltMed})
    prop.update({"lAltRet":lAltRet})
    prop.update({"elevationArray":aElevation})
    prop.update({"sortedElevationArray":eSortedElevation})
    geoJSON.append({"type":"Feature", "properties":prop, "geometry":{"type":"LineString", "coordinates":line}})
    #oLog.info("geoJSON=\n{}".format(str(geoJSON).replace(chr(39),chr(34))), outConsole=False)
    
    return lAltRet, geoJSON



if __name__ == '__main__':
    #Chargement des éléments inconnus du référetentiel
    sUnknownGroundHeightFileName = "refUnknownGroundHeight.json"
    sGroundHeightFileName = "refGroundEstimatedHeight.json"
    sSrcFileName = __OutPath__ + sUnknownGroundHeightFileName
    oUnknownGroundHeight = bpaTools.readJsonFile(sSrcFileName)
    oGroundEstimatedHeight = {}
    
    if len(oUnknownGroundHeight)==0:
        oLog.warning("Empty reference file : {0}".format(sSrcFileName), outConsole=True)
    else:
        
        #Select dataObject in src file
        oUnknownHeader = oUnknownGroundHeight["headerFile"]      #Get the header file
        oUnknownContent = oUnknownGroundHeight["referential"]     #Get the content of referential
        
        #Let specific header file & save the source file
        sHeadFileName = "_{0}_".format(oUnknownHeader["srcAixmOrigin"])
        sCpyFileName = "{0}{1}{2}_{3}".format(__OutPath__, sHeadFileName, bpaTools.getDateNow(), sUnknownGroundHeightFileName)
        shutil.copyfile(sSrcFileName, sCpyFileName)
        
        #Initialisation du référentiel de destination
        sDstFileName = "{0}{1}{2}".format(__OutPath__, sHeadFileName, sGroundHeightFileName)
        #Sauvegarde initiale de la première instence du jour (si pas déjà existant pour ne pas perdre les données en cas réexécution pour mises au point)
        if os.path.exists(sDstFileName):
            sCpyFileName = "{0}{1}{2}_{3}".format(__OutPath__, sHeadFileName, bpaTools.getDateNow(), sGroundHeightFileName)
            if not os.path.exists(sCpyFileName):
                shutil.copyfile(sDstFileName, sCpyFileName)
                oLog.info("Save initial reference file : {0} --> {1}".format(sDstFileName, sCpyFileName), outConsole=False)
        
        #Chargement du reférentiel initial (si déjà existant ; pour ajout de la complétude des données manquantes)
        oJson = bpaTools.readJsonFile(sDstFileName)
        if "referential" in oJson:
            oGroundEstimatedHeight = oJson["referential"]        #Ne récupère que les datas du fichier
        
        #Chargement des zones avec description des bordures
        sGeoJsonFileName = __SrcPath__ + "airspaces-freeflight.geojson"
        oGeoJsondata = bpaTools.readJsonFile(sGeoJsonFileName)   
        oFeatures = oGeoJsondata["features"]
        
        #Analyse de toutes les zones manquante du référentiel
        barre = bpaTools.ProgressBar(len(oUnknownContent), 20, title="Unknown Ground Estimated Height")
        geoJSON = []
        idx = 0
        for sZoneUId,sDestKey in oUnknownContent.items():
            idx+=1
            #if sDestKey == "[TMA-P] GENEVE TMA1 (LSGG1)@HEI.1000.FT":
            #    print("stop debug")
            oZone = findZone(sZoneUId, oFeatures)
            if oZone:
                lGroundEstimatedHeight, objJSON = getGroundEstimatedHeight(oZone)   #Détermine la hauteur sol moyenne (dessous la zone)
                oGroundEstimatedHeight.update({sDestKey:lGroundEstimatedHeight})    #Ajoute un point d'entrée attendu
                #sMsg = "Update Reference Data: sZoneUId={0} - key={1} - {2}m".format(sZoneUId, sDestKey, lGroundEstimatedHeight)
                #oLog.info(sMsg, outConsole=False)
                for g in objJSON:
                    geoJSON.append(g)
            barre.update(idx)
        barre.reset()
    
    
    if len(oGroundEstimatedHeight)>0:
    
        #Contruction du nouveau référentiel
        header = dict()
        header.update({"srcAixmOrigin":oUnknownHeader["srcAixmOrigin"]})
        out = {"headerFile":header, "referential":oGroundEstimatedHeight}
        bpaTools.writeJsonFile(sDstFileName, out)
        oLog.info("Write Referential Ground Estimated Height: {0} heights in file {1}".format(len(oGroundEstimatedHeight), sDstFileName), outConsole=True)
        
        #Construction du fichier geojson représentatif du référentiel; y compris la précision du cadrage des zones référencées...
        sGeoJsonFileName = str(sDstFileName).replace(".json",".geojson")
        #bpaTools.writeJsonFile(sGeoJsonFileName, json.dumps(out, ensure_ascii=True))
        with open(sGeoJsonFileName, "w", encoding="utf-8") as output:
            output.write(json.dumps({"type":"FeatureCollection","features":geoJSON}, ensure_ascii=False))
        oLog.info("Write GeoJSON View of Referential Ground Estimated Height: {0} features in file {1}".format(len(oGroundEstimatedHeight), sGeoJsonFileName), outConsole=True)
    
    print()
    oLog.Report()
    oLog.closeFile
    
