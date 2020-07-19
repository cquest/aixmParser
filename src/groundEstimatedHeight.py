#!/usr/bin/env python3

import bpaTools
import json
import os
import shutil
import numpy as np
import srtm


### Context applicatif
bpaTools.ctrlPythonVersion()
appName     = bpaTools.getFileName(__file__)
appPath     = bpaTools.getFilePath(__file__)
appVersion  = "1.1.0"
appId       = appName + " v" + appVersion
outPath     = appPath + "../out/"
srcPath     = outPath
refPath     = outPath + "referentials/"
logFile     = outPath + "_" + appName + ".log"
oLog = bpaTools.Logger(appId,logFile)
#oLog.resetFile()


#srtm library documentation - https://pypi.org/project/SRTM.py/
#elevation_data = srtm.get_data()            # srtm.get_data(local_cache_dir="tmp_cache")
#SRTM.py tests
#print('Home (meters):', elevation_data.get_elevation(48.694548, 2.333953))
#print('Place de l avenir (meters):', elevation_data.get_elevation(48.700191, 2.325597))
#print('Attérissage de Doussart (meters):', elevation_data.get_elevation(45.781438, 6.222423))


class GroundEstimatedHeight:
    
    def __init__(self, oLog, srcPath, refPath, headFileName=""):
        bpaTools.initEvent(__file__, oLog)
        self.oLog = oLog
        self.refPath = refPath
        self.srcPath = srcPath
        self.headFileName = headFileName
        
        self.elevation_data = srtm.get_data()
        
        self.sHead = "headerFile"
        self.sProp = "properties"
        self.sGeom = "geometry"
        self.sCoor = "coordinates"
        self.sRefe = "referential"
        self.sFeat = "features"
        
        self.sUnknownGroundHeightFileName = self.headFileName + "refUnknownGroundHeight.json"
        self.sGroundHeightFileName = self.headFileName + "refGroundEstimatedHeight"
        self.sGroundHeightFileNameJson = self.sGroundHeightFileName + ".json"
        self.sGroundHeightFileNameGeoj = self.sGroundHeightFileName + ".geojson"
        return

    def findZone(self, sZoneUId, oFeatures):
        oZone = None
        for o in oFeatures:
            if self.sProp in o:
                oProp = o[self.sProp]
                if oProp["UId"] == sZoneUId:
                    oZone = o
                    #self.oLog.info("Found Data: sZoneUId={0}".format(sZoneUId), outConsole=False)
                    break
        if oZone==None:
            self.oLog.critical("Missing coordinates of area {}".format(sZoneUId))
        return oZone


    def getCoordinates(self, oZone):
        return oZone[self.sGeom][self.sCoor][0]


    def getGroundEstimatedHeight(self, oZone):
        oCoordinates = self.getCoordinates(oZone)
        if type(oCoordinates) != "list":
            #self.oLog.critical("float err: No coordinates found {}".format(oZone))
            return 0,{}
        
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
        #self.oLog.info("Data: sZoneUId={} - lonMin={} - lonMax={} - latMin={} - latMax={}\nCoordinate={}".format(sZoneUId, lonMin, lonMax, latMin, latMax, oCoordinates), outConsole=False)
    
        #Définition d'une suite de coordonnées pour représenter la surface de la zone carré
        step = 10
        latSerial = np.linspace(latMin, latMax, step)   #10 nombres établies entre la valeur mini et maxi
        lonSerial = np.linspace(lonMin, lonMax, step)   #10 nombres établies entre la valeur mini et maxi
        #self.oLog.info("lonMin={} - lonMax={} - latMin={} - latMax={} \nlonSerial={} \nlatSerial={}".format(lonMin, lonMax, latMin, latMax, lonSerial, latSerial), outConsole=False)
    
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
        #self.oLog.info("line={}\n".format(line), outConsole=False)
        
        #Détermination des hauteurs terrain des 100 points (=step*step) qui couvre la zone géographique
        #srtm library documentation - https://pypi.org/project/SRTM.py/
        aElevation = []
        lastElevation = 0
        lCptNullValue = 0
        lCptError = 0
        for o in line:
            #sample: elevation_data.get_elevation(48.694548, 2.333953)
            lElevation = self.elevation_data.get_elevation(o[1], o[0])
            if lElevation==None:
                lCptError += 1
                lElevation = lastElevation
            
            if lElevation>0:
                lastElevation = lElevation
                aElevation.append(lElevation)
            elif lElevation==0 and lCptNullValue==0:
                lCptNullValue += 1
                aElevation.append(lElevation)
    
        #self.oLog.info("aElevation={}".format(aElevation), outConsole=False)
        if lCptError > 40:
             self.oLog.warning("{0} errors in call elevation_data.get_elevation()\nProperties={1}\naElevation{2}".format(lCptError, oZone[self.sProp], aElevation), outConsole=False)
    
        eSortedElevation = sorted(aElevation)
        
        idxMedium = int(len(eSortedElevation)/2)
        idxRetain = int(idxMedium+(idxMedium*(2/3)))
        lAltMin = eSortedElevation[0]
        lAltMax = eSortedElevation[len(eSortedElevation)-1]
        lAltMed = eSortedElevation[idxMedium]
        lAltRet = eSortedElevation[idxRetain]          #Valeur retenue pour l'estimation globale de la hauteur sol
    
        #¤Contruction d'une description geoJSON de la ligne de calcul d'élévations
        #self.oLog.info("oZone=\n{}".format(str(oZone).replace(chr(39),chr(34))), outConsole=False)
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
        #self.oLog.info("geoJSON=\n{}".format(str(geoJSON).replace(chr(39),chr(34))), outConsole=False)
        
        return lAltRet, geoJSON


    def parseUnknownGroundHeightRef(self) -> None:
        #Chargement des éléments inconnus du référetentiel
        sSrcFileName = self.refPath + self.sUnknownGroundHeightFileName
        oUnknownGroundHeight = bpaTools.readJsonFile(sSrcFileName)
        oGroundEstimatedHeight = dict()
        oFeatures = dict()
        
        if len(oUnknownGroundHeight)==0:
            self.oLog.warning("Empty reference file : {0}".format(sSrcFileName), outConsole=False)
        else:
            self.oLog.info("Load reference file : {0}".format(sSrcFileName), outConsole=False)
            
            #Select dataObject in src file
            oUnknownHeader = oUnknownGroundHeight[self.sHead]       #Get the header file
            oUnknownContent = oUnknownGroundHeight[self.sRefe]      #Get the content of referential
            
            #Let specific header file & save the source file
            sHeadFileName = "_{0}_".format(oUnknownHeader["srcAixmOrigin"])
            #Sauvegarde systématique des données manquantes dans le référentiel
            sCpyFileName = "{0}{1}{2}_{3}".format(self.refPath, sHeadFileName, bpaTools.getDateNow(), self.sUnknownGroundHeightFileName)
            shutil.copyfile(sSrcFileName, sCpyFileName)
            
            #Référentiel de destination (.json)
            sRefFileNameJson = "{0}{1}{2}".format(self.refPath, sHeadFileName, self.sGroundHeightFileNameJson)
            #Sauvegarde initiale de la première instance du jour (si pas déjà existant pour ne pas perdre les données en cas réexécution pour mises au point)
            if os.path.exists(sRefFileNameJson):
                sCpyFileName = "{0}{1}{2}_{3}".format(self.refPath, sHeadFileName, bpaTools.getDateNow(), self.sGroundHeightFileNameJson)
                if not os.path.exists(sCpyFileName):
                    shutil.copyfile(sRefFileNameJson, sCpyFileName)
                    self.oLog.info("Save initial reference file : {0} --> {1}".format(sRefFileNameJson, sCpyFileName), outConsole=False)
            
            #Visualiseur du référentiel (.geojson)
            sRefFileNameGeoj = "{0}{1}{2}".format(self.refPath, sHeadFileName, self.sGroundHeightFileNameGeoj)
            #Sauvegarde initiale de la première instance du jour (si pas déjà existant pour ne pas perdre les données en cas réexécution pour mises au point)
            if os.path.exists(sRefFileNameGeoj):
                sCpyFileName = "{0}{1}{2}_{3}".format(self.refPath, sHeadFileName, bpaTools.getDateNow(), self.sGroundHeightFileNameGeoj)
                if not os.path.exists(sCpyFileName):
                    shutil.copyfile(sRefFileNameGeoj, sCpyFileName)
                    self.oLog.info("Save initial reference file : {0} --> {1}".format(sRefFileNameGeoj, sCpyFileName), outConsole=False)
            
            #Chargement du reférentiel initial (si déjà existant ; pour ajout de la complétude des données manquantes)
            oJson = bpaTools.readJsonFile(sRefFileNameJson)
            if self.sRefe in oJson:
                oGroundEstimatedHeight = oJson[self.sRefe]        #Ne récupère que les datas du fichier
            
            #Chargement des zones avec description des bordures
            sGeoJsonFileName = self.srcPath + self.headFileName + "airspaces-vfr.geojson"
            if not os.path.exists(sGeoJsonFileName):
                sGeoJsonFileName = self.srcPath + self.headFileName + "airspaces-freeflight.geojson"
            oGeoJsondata = bpaTools.readJsonFile(sGeoJsonFileName)   
            self.oLog.info("Load source data file : {0}".format(sGeoJsonFileName), outConsole=False)
            if self.sFeat in oGeoJsondata:
                oFeatures = oGeoJsondata[self.sFeat]
            
            #Analyse de toutes les zones manquante du référentiel
            barre = bpaTools.ProgressBar(len(oUnknownContent), 20, title="Unknown Ground Estimated Height")
            geoJSON = []
            idx = 0
            for sZoneUId,sDestKey in oUnknownContent.items():
                idx+=1
                #if sDestKey == "[TMA-P] GENEVE TMA1 (LSGG1)@HEI.1000.FT":
                #    print("stop debug")
                oZone = self.findZone(sZoneUId, oFeatures)
                if oZone:
                    lGroundEstimatedHeight, objJSON = self.getGroundEstimatedHeight(oZone)   #Détermine la hauteur sol moyenne (dessous la zone)
                    if objJSON!={}:
                        oGroundEstimatedHeight.update({sDestKey:lGroundEstimatedHeight})         #Ajoute un point d'entrée attendu
                        #sMsg = "Update Reference Data: sZoneUId={0} - key={1} - {2}m".format(sZoneUId, sDestKey, lGroundEstimatedHeight)
                        #self.oLog.info(sMsg, outConsole=False)
                        for g in objJSON:
                            geoJSON.append(g)
                barre.update(idx)
            barre.reset()
        
        if len(oGroundEstimatedHeight)>0:
            #Contruction du nouveau référentiel
            header = dict()
            header.update({"srcAixmOrigin":oUnknownHeader["srcAixmOrigin"]})
            out = {self.sHead:header, self.sRefe:oGroundEstimatedHeight}
            bpaTools.writeJsonFile(sRefFileNameJson, out)
            self.oLog.info("Write Referential Ground Estimated Height: {0} heights in file {1}".format(len(oGroundEstimatedHeight), sRefFileNameJson), outConsole=True)
            
            #Construction du fichier geojson représentatif du référentiel; y compris la précision du cadrage des zones référencées...
            with open(sRefFileNameGeoj, "w", encoding="utf-8") as output:
                output.write(json.dumps({"type":"FeatureCollection",self.sFeat:geoJSON}, ensure_ascii=False))
            self.oLog.info("Write GeoJSON View of Referential Ground Estimated Height: {0} features in file {1}".format(len(oGroundEstimatedHeight), sRefFileNameGeoj), outConsole=True)
        return
        

if __name__ == '__main__':
    oGEH = GroundEstimatedHeight(oLog, srcPath, refPath)
    oGEH.parseUnknownGroundHeightRef()
    print()
    oLog.Report()
    oLog.closeFile
