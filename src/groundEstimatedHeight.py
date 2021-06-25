#!/usr/bin/env python3

import bpaTools
import json
import os
import shutil
import numpy as np
import srtm
#from copy import deepcopy

defEstimHeight:list         = [0, 0, 0, 0]
errNoArea:list              = [-999, -999, -999, -999]
errLocalisationPoint:list   = [-5,45]

class GroundEstimatedHeight:

    def __init__(self, oLog:bpaTools.Logger=None, srcPath:str="", refPath:str="", headFileName:str=""):
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


    def getElevation(self, latitude:float, longitude:float) -> float:
        #test coordinates for get_file()
        try:
            geo_file = self.elevation_data.get_file(latitude, longitude)
        except Exception as e:
            msg:str = str(e)
            if self.oLog:
                self.oLog.error(msg, outConsole=False)
            else:
                print(msg)
            return
        lElevation:float = self.elevation_data.get_elevation(latitude, longitude)
        #Problème durant l'évaluation de la hauteur terrain !?
        #if lElevation==None:
        #    #Bug non référencé sur le net ; contournement pour tentative de récupération d'une 'altitude valide'
        #    for digit in range(8, 1, -1):
        #        lElevation = self.elevation_data.get_elevation(round(latitude,digit), round(longitude,digit))
        #        if lElevation: break
        return lElevation


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


    def getGroundEstimatedHeight(self, oZone) -> list:
        oCoordinates = self.getCoordinates(oZone)
        if not isinstance(oCoordinates, list):
            #self.oLog.critical("float err: No coordinates found {}".format(oZone))
            return 0,{}

        lat = []
        lon = []
        try:
            for o in oCoordinates:
                lat.append(o[0])
                lon.append(o[1])
        except Exception as e:
            sHeader = "[" + bpaTools.getFileName(__file__) + "." + self.getGroundEstimatedHeight.__name__ + "()] "
            sMsg = "/!\ Estimated height Error - AreaRef={0}".format(oZone)
            raise Exception(sHeader + sMsg + " / " + str(e))

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
        aElevation:list = []
        aRet:list = []
        lastElevation = 0
        lCptNullValue = 0
        lCptError = 0
        for o in line:
            #lElevation:float = self.getElevation(o[1], o[0])                   #for map
            lElevation:float = self.elevation_data.get_elevation(o[1], o[0])    #operational
            if lElevation==None:
                lCptError += 1
                lElevation = lastElevation
            elif lElevation>0:
                lastElevation = lElevation
                aElevation.append(lElevation)
            elif lElevation==0 and lCptNullValue==0:
                lCptNullValue += 1
                aElevation.append(lElevation)

        #self.oLog.info("aElevation={}".format(aElevation), outConsole=False)
        #if lCptError > 90:
        #     #print("{0} errors in call elevation_data.get_elevation() - name={1}".format(lCptError, oZone[self.sProp]["nameV"]))
        #     self.oLog.warning("{0} errors in call elevation_data.get_elevation()\nProperties={1}\naElevation={2}".format(lCptError, oZone[self.sProp], aElevation), outConsole=False)

        if not aElevation:
            #Tableau vide ! --> '100 errors in call elevation_data.get_elevation()'
            sMsg:str = "{0} errors in call elevation_data.get_elevation() --> Properties={1}".format(lCptError, oZone[self.sProp])
            sMsg += "\n(debug) --> Area coordinates={0}".format(line)
            self.oLog.error(sMsg, outConsole=False)
            aRet = defEstimHeight
        else:
            eSortedElevation = sorted(aElevation)
            idxMedium = int(len(eSortedElevation)/2)
            idxRetain = int(idxMedium+(idxMedium*(2/3)))
            lAltMin = eSortedElevation[0]
            lAltMax = eSortedElevation[-1]
            lAltMed = eSortedElevation[idxMedium]
            lAltRet = eSortedElevation[idxRetain]          #Valeur retenue pour l'estimation globale de la hauteur sol
            aRet = [lAltMin,lAltMed,lAltRet,lAltMax]

        geoJSON = []
        geoJSON.append(oZone)
        prop = {}
        prop.update({"nameV":"Square line"})
        prop.update({"lAltMin":aRet[0]})
        prop.update({"lAltMed":aRet[1]})
        prop.update({"lAltRet":aRet[2]})
        prop.update({"lAltMax":aRet[3]})
        #prop.update({"elevationArray":aElevation})
        #prop.update({"sortedElevationArray":eSortedElevation})
        geoJSON.append({"type":"Feature", "properties":prop, "geometry":{"type":"LineString", "coordinates":line}})
        return aRet, geoJSON


    def parseUnknownGroundHeightRef(self, sGeoJsonSrcFile:str=None) -> None:
        #Chargement des éléments inconnus du référetentiel
        sSrcFileName = self.refPath + self.sUnknownGroundHeightFileName
        if not os.path.exists(sSrcFileName):
            self.oLog.error("File not found - {0} ".format(sSrcFileName), outConsole=True)
            return
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
            #oNewUnknownContent = deepcopy(oUnknownContent)          #Clone the initial repository for clean

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
            if sGeoJsonSrcFile:
                sGeoJsonFileName:str = sGeoJsonSrcFile
            else:
                sGeoJsonFileName:str = self.srcPath + self.headFileName + "airspaces-all.geojson"
                if not os.path.exists(sGeoJsonFileName):
                    sGeoJsonFileName = self.srcPath + self.headFileName + "airspaces-vfr.geojson"
                if not os.path.exists(sGeoJsonFileName):
                    sGeoJsonFileName = self.srcPath + self.headFileName + "airspaces-freeflight.geojson"
            if not os.path.exists(sGeoJsonFileName):
                self.oLog.error("File not found - {0} ".format(sGeoJsonFileName), outConsole=True)
                return
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
                    #Valid area control (exclude the single point or line)
                    if oZone[self.sGeom]["type"] in ["Point","LineString"]:
                        #del oNewUnknownContent[sZoneUId]                                           #Remove area in new repositoy
                        oGroundEstimatedHeight.update({sDestKey:errNoArea})
                    else:
                        aGroundEstimatedHeight, objJSON = self.getGroundEstimatedHeight(oZone)      #Détermine la hauteur sol moyenne (dessous la zone)
                        if objJSON!={}:
                            oGroundEstimatedHeight.update({sDestKey:aGroundEstimatedHeight})         #Ajoute un point d'entrée attendu
                            #sMsg = "Update Reference Data: sZoneUId={0} - key={1} - {2}m".format(sZoneUId, sDestKey, aGroundEstimatedHeight)
                            #self.oLog.info(sMsg, outConsole=False)
                            for g in objJSON:
                                geoJSON.append(g)
                barre.update(idx)
            barre.reset()

            #if len(oNewUnknownContent) != len(oUnknownContent):
            #    #Generate new repository if clean data
            #    oNewRepository:dict = {}
            #    oNewRepository.update({self.sHead:oUnknownHeader})
            #    oNewRepository.update({self.sRefe:oNewUnknownContent})
            #    bpaTools.writeJsonFile(sSrcFileName, oNewRepository)

        if len(oGroundEstimatedHeight)>0:
            #Contruction du nouveau référentiel
            header = dict()
            header.update({"srcAixmOrigin":oUnknownHeader["srcAixmOrigin"]})
            out = {self.sHead:header, self.sRefe:oGroundEstimatedHeight}
            bpaTools.writeJsonFile(sRefFileNameJson, out)
            self.oLog.info("Written Referential Ground Estimated Height: {0} heights in file {1}".format(len(oGroundEstimatedHeight), sRefFileNameJson), outConsole=True)

            #Construction du fichier geojson représentatif du référentiel; y compris la précision du cadrage des zones référencées...
            with open(sRefFileNameGeoj, "w", encoding="utf-8") as output:
                output.write(json.dumps({"type":"FeatureCollection",self.sFeat:geoJSON}, ensure_ascii=False))
            self.oLog.info("Written GeoJSON View of Referential Ground Estimated Height: {0} features in file {1}".format(len(oGroundEstimatedHeight), sRefFileNameGeoj), outConsole=True)
        return


def basicTest(frmt:str="latlon", aPoints:list=None) -> None:
    #srtm library documentation     - https://pypi.org/project/SRTM.py/
    #srtm file config               - D:\Users\BPascal\Anaconda3\Lib\site-packages\srtm\list.json
    #srtm source files              - https://srtm.kurviger.de/index.html
    #srtm wiki                      - https://wiki.openstreetmap.org/wiki/SRTM
    #srtm maps                      - https://www.usgs.gov/centers/eros/science/usgs-eros-archive-products-overview?qt-science_center_objects=0#qt-science_center_objects
    #srtm (digital elevation)       - https://www.usgs.gov/centers/eros/science/usgs-eros-archive-products-overview?qt-science_center_objects=0#qt-science_center_objects
    if aPoints:
        oGEH = GroundEstimatedHeight()
        if isinstance(aPoints[0], list):
            ret:list=[]
            for aPt in aPoints:
                if frmt!="latlon":
                    aPt = aPt[::-1]     #Invertion des coordonnées
                ret.append(oGEH.getElevation(aPt[0], aPt[1]))
            print("Points (m)", ret)
        else:
            if frmt!="latlon":
                aPoints = aPoints[::-1]     #Invertion des coordonnées
            print("Point (m)", oGEH.getElevation(aPoints[0], aPoints[1]), "m")
    else:
        elevation_data = srtm.get_data()            # srtm.get_data(local_cache_dir="tmp_cache")  // Default cache - D:\Users\BPascal\.cache\srtm
        print("Home (m)", elevation_data.get_elevation(48.694548, 2.333953))
        print("Place de l avenir (m)", elevation_data.get_elevation(48.700191, 2.325597))
        print("Attérissage de Doussart (m)", elevation_data.get_elevation(45.781438, 6.222423))


if __name__ == '__main__':
    """
    #Tests de la librairie SRTM...
    #basicTest()
    #basicTest("latlon", [48.694548, 2.333953])

    basicTest("lonlat", [26.812106, 60.501396])
    basicTest("lonlat", [19.196111, 65.532222])
    basicTest("lonlat", [-18.691121, 65.160185])

    basicTest("lonlat", #Q KOTKA (BLAST)
            [[26.812106, 60.501396], [26.812106, 60.50250555555556], [26.812106, 60.50361511111111], [26.812106, 60.50472466666667], [26.812106, 60.50583422222222], [26.812106, 60.50694377777778], [26.812106, 60.50805333333333], [26.812106, 60.50916288888889], [26.812106, 60.51027244444444], [26.812106, 60.511382], [26.814357666666666, 60.511382], [26.814357666666666, 60.51027244444444], [26.814357666666666, 60.50916288888889], [26.814357666666666, 60.50805333333333], [26.814357666666666, 60.50694377777778], [26.814357666666666, 60.50583422222222], [26.814357666666666, 60.50472466666667], [26.814357666666666, 60.50361511111111], [26.814357666666666, 60.50250555555556], [26.814357666666666, 60.501396], [26.816609333333332, 60.501396], [26.816609333333332, 60.50250555555556], [26.816609333333332, 60.50361511111111], [26.816609333333332, 60.50472466666667], [26.816609333333332, 60.50583422222222], [26.816609333333332, 60.50694377777778], [26.816609333333332, 60.50805333333333], [26.816609333333332, 60.50916288888889], [26.816609333333332, 60.51027244444444], [26.816609333333332, 60.511382], [26.818861, 60.511382], [26.818861, 60.51027244444444], [26.818861, 60.50916288888889], [26.818861, 60.50805333333333], [26.818861, 60.50694377777778], [26.818861, 60.50583422222222], [26.818861, 60.50472466666667], [26.818861, 60.50361511111111], [26.818861, 60.50250555555556], [26.818861, 60.501396], [26.821112666666664, 60.501396], [26.821112666666664, 60.50250555555556], [26.821112666666664, 60.50361511111111], [26.821112666666664, 60.50472466666667], [26.821112666666664, 60.50583422222222], [26.821112666666664, 60.50694377777778], [26.821112666666664, 60.50805333333333], [26.821112666666664, 60.50916288888889], [26.821112666666664, 60.51027244444444], [26.821112666666664, 60.511382], [26.823364333333334, 60.511382], [26.823364333333334, 60.51027244444444], [26.823364333333334, 60.50916288888889], [26.823364333333334, 60.50805333333333], [26.823364333333334, 60.50694377777778], [26.823364333333334, 60.50583422222222], [26.823364333333334, 60.50472466666667], [26.823364333333334, 60.50361511111111], [26.823364333333334, 60.50250555555556], [26.823364333333334, 60.501396], [26.825616, 60.501396], [26.825616, 60.50250555555556], [26.825616, 60.50361511111111], [26.825616, 60.50472466666667], [26.825616, 60.50583422222222], [26.825616, 60.50694377777778], [26.825616, 60.50805333333333], [26.825616, 60.50916288888889], [26.825616, 60.51027244444444], [26.825616, 60.511382], [26.827867666666666, 60.511382], [26.827867666666666, 60.51027244444444], [26.827867666666666, 60.50916288888889], [26.827867666666666, 60.50805333333333], [26.827867666666666, 60.50694377777778], [26.827867666666666, 60.50583422222222], [26.827867666666666, 60.50472466666667], [26.827867666666666, 60.50361511111111], [26.827867666666666, 60.50250555555556], [26.827867666666666, 60.501396], [26.830119333333332, 60.501396], [26.830119333333332, 60.50250555555556], [26.830119333333332, 60.50361511111111], [26.830119333333332, 60.50472466666667], [26.830119333333332, 60.50583422222222], [26.830119333333332, 60.50694377777778], [26.830119333333332, 60.50805333333333], [26.830119333333332, 60.50916288888889], [26.830119333333332, 60.51027244444444], [26.830119333333332, 60.511382], [26.832371, 60.511382], [26.832371, 60.51027244444444], [26.832371, 60.50916288888889], [26.832371, 60.50805333333333], [26.832371, 60.50694377777778], [26.832371, 60.50583422222222], [26.832371, 60.50472466666667], [26.832371, 60.50361511111111], [26.832371, 60.50250555555556], [26.832371, 60.501396]])
    basicTest("lonlat", #TMA VIDSEL
            [[19.196111, 65.532222], [19.196111, 65.60811711111111], [19.196111, 65.68401222222222], [19.196111, 65.75990733333333], [19.196111, 65.83580244444444], [19.196111, 65.91169755555556], [19.196111, 65.98759266666667], [19.196111, 66.06348777777778], [19.196111, 66.13938288888889], [19.196111, 66.215278], [19.407160444444443, 66.215278], [19.407160444444443, 66.13938288888889], [19.407160444444443, 66.06348777777778], [19.407160444444443, 65.98759266666667], [19.407160444444443, 65.91169755555556], [19.407160444444443, 65.83580244444444], [19.407160444444443, 65.75990733333333], [19.407160444444443, 65.68401222222222], [19.407160444444443, 65.60811711111111], [19.407160444444443, 65.532222], [19.618209888888888, 65.532222], [19.618209888888888, 65.60811711111111], [19.618209888888888, 65.68401222222222], [19.618209888888888, 65.75990733333333], [19.618209888888888, 65.83580244444444], [19.618209888888888, 65.91169755555556], [19.618209888888888, 65.98759266666667], [19.618209888888888, 66.06348777777778], [19.618209888888888, 66.13938288888889], [19.618209888888888, 66.215278], [19.829259333333333, 66.215278], [19.829259333333333, 66.13938288888889], [19.829259333333333, 66.06348777777778], [19.829259333333333, 65.98759266666667], [19.829259333333333, 65.91169755555556], [19.829259333333333, 65.83580244444444], [19.829259333333333, 65.75990733333333], [19.829259333333333, 65.68401222222222], [19.829259333333333, 65.60811711111111], [19.829259333333333, 65.532222], [20.040308777777778, 65.532222], [20.040308777777778, 65.60811711111111], [20.040308777777778, 65.68401222222222], [20.040308777777778, 65.75990733333333], [20.040308777777778, 65.83580244444444], [20.040308777777778, 65.91169755555556], [20.040308777777778, 65.98759266666667], [20.040308777777778, 66.06348777777778], [20.040308777777778, 66.13938288888889], [20.040308777777778, 66.215278], [20.25135822222222, 66.215278], [20.25135822222222, 66.13938288888889], [20.25135822222222, 66.06348777777778], [20.25135822222222, 65.98759266666667], [20.25135822222222, 65.91169755555556], [20.25135822222222, 65.83580244444444], [20.25135822222222, 65.75990733333333], [20.25135822222222, 65.68401222222222], [20.25135822222222, 65.60811711111111], [20.25135822222222, 65.532222], [20.462407666666664, 65.532222], [20.462407666666664, 65.60811711111111], [20.462407666666664, 65.68401222222222], [20.462407666666664, 65.75990733333333], [20.462407666666664, 65.83580244444444], [20.462407666666664, 65.91169755555556], [20.462407666666664, 65.98759266666667], [20.462407666666664, 66.06348777777778], [20.462407666666664, 66.13938288888889], [20.462407666666664, 66.215278], [20.67345711111111, 66.215278], [20.67345711111111, 66.13938288888889], [20.67345711111111, 66.06348777777778], [20.67345711111111, 65.98759266666667], [20.67345711111111, 65.91169755555556], [20.67345711111111, 65.83580244444444], [20.67345711111111, 65.75990733333333], [20.67345711111111, 65.68401222222222], [20.67345711111111, 65.60811711111111], [20.67345711111111, 65.532222], [20.884506555555554, 65.532222], [20.884506555555554, 65.60811711111111], [20.884506555555554, 65.68401222222222], [20.884506555555554, 65.75990733333333], [20.884506555555554, 65.83580244444444], [20.884506555555554, 65.91169755555556], [20.884506555555554, 65.98759266666667], [20.884506555555554, 66.06348777777778], [20.884506555555554, 66.13938288888889], [20.884506555555554, 66.215278], [21.095556, 66.215278], [21.095556, 66.13938288888889], [21.095556, 66.06348777777778], [21.095556, 65.98759266666667], [21.095556, 65.91169755555556], [21.095556, 65.83580244444444], [21.095556, 65.75990733333333], [21.095556, 65.68401222222222], [21.095556, 65.60811711111111], [21.095556, 65.532222]])
    basicTest("lonlat", #TMA AKUREYRI
            [[-18.691121, 65.160185], [-18.691121, 65.25546266666666], [-18.691121, 65.35074033333333], [-18.691121, 65.446018], [-18.691121, 65.54129566666667], [-18.691121, 65.63657333333333], [-18.691121, 65.731851], [-18.691121, 65.82712866666667], [-18.691121, 65.92240633333334], [-18.691121, 66.017684], [-18.590530555555553, 66.017684], [-18.590530555555553, 65.92240633333334], [-18.590530555555553, 65.82712866666667], [-18.590530555555553, 65.731851], [-18.590530555555553, 65.63657333333333], [-18.590530555555553, 65.54129566666667], [-18.590530555555553, 65.446018], [-18.590530555555553, 65.35074033333333], [-18.590530555555553, 65.25546266666666], [-18.590530555555553, 65.160185], [-18.48994011111111, 65.160185], [-18.48994011111111, 65.25546266666666], [-18.48994011111111, 65.35074033333333], [-18.48994011111111, 65.446018], [-18.48994011111111, 65.54129566666667], [-18.48994011111111, 65.63657333333333], [-18.48994011111111, 65.731851], [-18.48994011111111, 65.82712866666667], [-18.48994011111111, 65.92240633333334], [-18.48994011111111, 66.017684], [-18.389349666666664, 66.017684], [-18.389349666666664, 65.92240633333334], [-18.389349666666664, 65.82712866666667], [-18.389349666666664, 65.731851], [-18.389349666666664, 65.63657333333333], [-18.389349666666664, 65.54129566666667], [-18.389349666666664, 65.446018], [-18.389349666666664, 65.35074033333333], [-18.389349666666664, 65.25546266666666], [-18.389349666666664, 65.160185], [-18.28875922222222, 65.160185], [-18.28875922222222, 65.25546266666666], [-18.28875922222222, 65.35074033333333], [-18.28875922222222, 65.446018], [-18.28875922222222, 65.54129566666667], [-18.28875922222222, 65.63657333333333], [-18.28875922222222, 65.731851], [-18.28875922222222, 65.82712866666667], [-18.28875922222222, 65.92240633333334], [-18.28875922222222, 66.017684], [-18.188168777777776, 66.017684], [-18.188168777777776, 65.92240633333334], [-18.188168777777776, 65.82712866666667], [-18.188168777777776, 65.731851], [-18.188168777777776, 65.63657333333333], [-18.188168777777776, 65.54129566666667], [-18.188168777777776, 65.446018], [-18.188168777777776, 65.35074033333333], [-18.188168777777776, 65.25546266666666], [-18.188168777777776, 65.160185], [-18.087578333333333, 65.160185], [-18.087578333333333, 65.25546266666666], [-18.087578333333333, 65.35074033333333], [-18.087578333333333, 65.446018], [-18.087578333333333, 65.54129566666667], [-18.087578333333333, 65.63657333333333], [-18.087578333333333, 65.731851], [-18.087578333333333, 65.82712866666667], [-18.087578333333333, 65.92240633333334], [-18.087578333333333, 66.017684], [-17.986987888888887, 66.017684], [-17.986987888888887, 65.92240633333334], [-17.986987888888887, 65.82712866666667], [-17.986987888888887, 65.731851], [-17.986987888888887, 65.63657333333333], [-17.986987888888887, 65.54129566666667], [-17.986987888888887, 65.446018], [-17.986987888888887, 65.35074033333333], [-17.986987888888887, 65.25546266666666], [-17.986987888888887, 65.160185], [-17.886397444444444, 65.160185], [-17.886397444444444, 65.25546266666666], [-17.886397444444444, 65.35074033333333], [-17.886397444444444, 65.446018], [-17.886397444444444, 65.54129566666667], [-17.886397444444444, 65.63657333333333], [-17.886397444444444, 65.731851], [-17.886397444444444, 65.82712866666667], [-17.886397444444444, 65.92240633333334], [-17.886397444444444, 66.017684], [-17.785807, 66.017684], [-17.785807, 65.92240633333334], [-17.785807, 65.82712866666667], [-17.785807, 65.731851], [-17.785807, 65.63657333333333], [-17.785807, 65.54129566666667], [-17.785807, 65.446018], [-17.785807, 65.35074033333333], [-17.785807, 65.25546266666666], [-17.785807, 65.160185]])

    basicTest("lonlat", #Bauges Gresy-Montarbe / Aigle Royal 150m/nid
            [[6.257485, 45.619444], [6.25746, 45.61966], [6.257386, 45.619871], [6.257264, 45.620071], [6.257098, 45.620254], [6.256892, 45.620417], [6.256652, 45.620554], [6.256383, 45.620663], [6.256093, 45.62074], [6.255789, 45.620783], [6.255478, 45.620792], [6.25517, 45.620766], [6.254872, 45.620705], [6.254592, 45.620612], [6.254336, 45.620489], [6.254112, 45.620339], [6.253926, 45.620165], [6.253781, 45.619973], [6.253683, 45.619767], [6.253633, 45.619553], [6.253633, 45.619335], [6.253683, 45.619121], [6.253781, 45.618915], [6.253926, 45.618723], [6.254112, 45.618549], [6.254336, 45.618399], [6.254592, 45.618276], [6.254872, 45.618183], [6.25517, 45.618122], [6.255478, 45.618096], [6.255788, 45.618105], [6.256093, 45.618148], [6.256383, 45.618225], [6.256652, 45.618334], [6.256892, 45.618471], [6.257098, 45.618634], [6.257264, 45.618817], [6.257386, 45.619017], [6.25746, 45.619228], [6.257485, 45.619444]])
    basicTest("lonlat", #Peisey-Nancroix / Lac-de-La-Plagne / Gypaete Barbu 150m/nid
            [[6.835257, 45.486111], [6.835232, 45.486327], [6.835158, 45.486538], [6.835037, 45.486738], [6.834871, 45.486921], [6.834666, 45.487084], [6.834426, 45.487221], [6.834158, 45.48733], [6.833868, 45.487407], [6.833565, 45.48745], [6.833256, 45.487459], [6.832948, 45.487433], [6.832651, 45.487372], [6.832371, 45.487279], [6.832116, 45.487156], [6.831893, 45.487006], [6.831707, 45.486832], [6.831563, 45.48664], [6.831465, 45.486434], [6.831415, 45.48622], [6.831415, 45.486002], [6.831465, 45.485788], [6.831563, 45.485582], [6.831707, 45.48539], [6.831893, 45.485216], [6.832116, 45.485066], [6.832371, 45.484943], [6.832651, 45.48485], [6.832948, 45.484789], [6.833256, 45.484763], [6.833565, 45.484772], [6.833868, 45.484815], [6.834158, 45.484892], [6.834426, 45.485001], [6.834666, 45.485138], [6.834871, 45.485301], [6.835037, 45.485484], [6.835158, 45.485684], [6.835232, 45.485895], [6.835257, 45.486111]])
    basicTest("lonlat", #ZSM Bauges Clarafond Drumettaz / Faucon Pelerin 150m/nid
            [[5.956652, 45.664167], [5.956627, 45.664383], [5.956553, 45.664594], [5.956431, 45.664794], [5.956265, 45.664977], [5.956059, 45.66514], [5.955819, 45.665277], [5.95555, 45.665386], [5.955259, 45.665463], [5.954955, 45.665506], [5.954644, 45.665515], [5.954336, 45.665489], [5.954037, 45.665428], [5.953757, 45.665335], [5.953501, 45.665212], [5.953277, 45.665062], [5.95309, 45.664888], [5.952946, 45.664696], [5.952848, 45.66449], [5.952798, 45.664276], [5.952798, 45.664058], [5.952848, 45.663844], [5.952946, 45.663638], [5.95309, 45.663446], [5.953277, 45.663272], [5.953501, 45.663122], [5.953757, 45.662999], [5.954037, 45.662906], [5.954336, 45.662845], [5.954644, 45.662819], [5.954955, 45.662828], [5.955259, 45.662871], [5.95555, 45.662948], [5.955819, 45.663057], [5.956059, 45.663194], [5.956265, 45.663357], [5.956431, 45.66354], [5.956553, 45.66374], [5.956627, 45.663951], [5.956652, 45.664167]])

    """

    ### Context applicatif
    bpaTools.ctrlPythonVersion()
    appName     = bpaTools.getFileName(__file__)
    appPath     = bpaTools.getFilePath(__file__)
    appVersion  = "1.6.1"
    appId       = appName + " v" + appVersion
    outPath     = appPath + "../out/"
    srcPath     = outPath
    refPath     = outPath + "referentials/"
    logFile     = outPath + "_" + appName + ".log"
    oLog = bpaTools.Logger(appId,logFile)
    #oLog.resetFile()
    oGEH = GroundEstimatedHeight(oLog, srcPath, refPath)
    oGEH.parseUnknownGroundHeightRef()
    print()
    oLog.Report()
    oLog.closeFile
