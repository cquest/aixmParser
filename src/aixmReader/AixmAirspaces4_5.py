#!/usr/bin/env python3

import bpaTools
import aixmReader
import json
try:
    import xmlSIA
except ImportError:
    xmlSIA = None


#Sauvegarde du catalogue de zones sous forme de CSV
def convertJsonCalalogToCSV(cat:dict) -> str:

    #Phase 2.1 : Header CSV file
    csv = csvCol = csvVal = ""
    oHeader = cat["headerFile"]
    for key,val in oHeader.items():
        if isinstance(val, dict):
            for key2,val2 in val.items():
                csvCol += '"{0}";'.format(key2)
                if isinstance(val2, str):
                    val2 = val2.replace(chr(34), chr(39))
                if isinstance(val2, dict):
                    val2 = json.dumps(val2, ensure_ascii=False)
                    csvVal += '{0};'.format(val2)
                else:
                    csvVal += '"{0}";'.format(val2)
        else:
            csvCol += '"{0}";'.format(key)
            if isinstance(val, str):
                val = val.replace(chr(34), chr(39))
            if isinstance(val, dict):
                val = json.dumps(val, ensure_ascii=False)
                csvVal += '{0};'.format(val)
            else:
                csvVal += '"{0}";'.format(val)
    csv = "<Header file>\n{0}\n{1}\n\n<Content>\n".format(csvCol, csvVal)

    #Phase 2.2 : Construct a global index on columns (collect all columns in contents for complete header of CSV file...)
    #oCols avec initialisation d'une table d'index avec imposition de l'ordonnancement de colonnes choisies
    oCols = {"zoneType":0, "groupZone":0, "vfrZone":0, "vfrZoneExt":0, "freeFlightZone":0, "freeFlightZoneExt":0,
             "excludeAirspaceNotCoord":0,"excludeAirspaceNotFfArea":0, "geometryType":0, "excludeAirspaceByFilter":0, "excludeAirspaceByAlt":0, "excludeAirspaceByRef":0, "deltaExt":0,
             "potentialFilter4FreeFlightZone":0, "orgName":0, "keySrcFile":0, "GUId":0, "UId":0, "id":0,
             "srcClass":0, "srcType":0,
             "class":0, "type":0, "localType":0, "codeActivity":0, "codeMil":0, "codeLocInd":0,
             "srcName":0, "name":0, "nameV":0, "desc":0, "Mhz":0, "activationCode":0, "activationDesc":0, "timeScheduling":0,
             "declassifiable":0, "seeNOTAM":0, "exceptSAT":0, "exceptSUN":0, "exceptHOL":0, "groundEstimatedHeight":0,
             "lowerMin":0, "lower":0, "lowerM":0, "ordinalLowerMinM":0, "ordinalLowerM":0,
             "upperMax":0, "upper":0, "upperM":0, "ordinalUpperMaxM":0, "ordinalUpperM":0,
             "WarningValDistVerLower":0, "WarningValDistVerUpper":0,
             "lowerType":0, "lowerValue":0, "lowerUnit":0,
             "lowerTypeMnm":0,"lowerValueMnm":0,"lowerUnitMnm":0,
             "upperType":0, "upperValue":0, "upperUnit":0,
             "lowerTypeMax":0,"lowerValueMax":0,"lowerUnitMax":0,
             "use4cfd":0 }
    oCatalog = cat["catalog"]
    for key0,val0 in oCatalog.items():
        for key1,val1 in val0.items():
            #Ne pas intégrer les colonnes associées au 'ColorProperties'
            if not key1 in ["stroke", "stroke-width", "stroke-opacity", "fill", "fill-opacity"]:
                oCols.update({key1:0})
    #List all columns in order of the global index on columns
    for colKey,colVal in oCols.items():
        csv += '"{0}";'.format(colKey)

    #Phase 2.3" : Content CSV file
    for key,val in oCatalog.items():
        csv += "\n"
        #Extract columns in order of the global index on columns
        for colKey,colVal in oCols.items():
            if colKey in val:
                utfValue = val[colKey]
                if isinstance(utfValue, str):
                     utfValue = utfValue.replace(chr(34), chr(39))
                if isinstance(utfValue, dict):
                    utfValue = json.dumps(utfValue, ensure_ascii=False)
                    csv += '{0};'.format(utfValue)
                else:
                    csv += '"{0}";'.format(utfValue)
            else:
                csv += ';'

    csv += "\n\n<EOF>"
    return csv

def getSerializeAlt(airspaceProperties:dict, sUppLow:str="") -> str:
    sLower:str = ""
    sUpper:str = ""
    if sUppLow in ["","Low"]:
        if airspaceProperties.get("ordinalLowerMinM", False):
            sLower += airspaceProperties["lowerMin"] + "-"
        if airspaceProperties.get("lower", False):
            sLower += airspaceProperties["lower"]
        else:
            sLower += "SFC"
        ret = sLower
    if sUppLow in ["","Upp"]:
        if airspaceProperties.get("upper", False):
            sUpper += airspaceProperties["upper"]
        else:
            sUpper += "FL999"
        if airspaceProperties.get("ordinalUpperMaxM", False):
            sUpper += "-" + airspaceProperties["upperMax"]
        ret = sUpper
    if sUppLow == "":
        ret = "[{0}/{1}]".format(sLower, sUpper)
    return ret

def getSerializeAltM(airspaceProperties:dict) -> str:
    sLower:str = ""
    if ("lowerM" in airspaceProperties):
        sLower = airspaceProperties["lowerM"]
    sUpper:str = ""
    if ("upperM" in airspaceProperties):
        sUpper = airspaceProperties["upperM"]
    return "[{0}m/{1}m]".format(sLower, sUpper)

def getVerboseName(cat:dict) -> str:
    #Nouveau format fixé le 13/08/2020 - AN <Type> <Nommage> [Frequences] [([<codeActivity>] / [SeeNOTAM])]
    sVerboseName:str = "{0} {1}".format(cat["type"], cat["name"])
    if xmlSIA and ("Mhz" in cat):
        sFreq = xmlSIA.getMasterFrequecy(cat["Mhz"], cat["type"])
        if sFreq:
            sVerboseName += " " + sFreq
    if ("codeActivity" in cat) or ("seeNOTAM" in cat):
        sVerboseName += " ("
    if "codeActivity" in cat:
        sVerboseName += cat["codeActivity"]
        if "seeNOTAM" in cat:
           sVerboseName += " / "
    bNotam:bool = False
    if "seeNOTAM" in cat:
        bNotam = bool(cat["seeNOTAM"])
    if bNotam:
        sVerboseName += "SeeNotam"
    if ("codeActivity" in cat) or ("seeNOTAM" in cat):
        sVerboseName += ")"
    if ("ordinalLowerMinM" in cat) and ("ordinalUpperMaxM" in cat):
        sVerboseName += " " + getSerializeAlt(cat)
    elif cat.get("ordinalLowerMinM", False):
        sVerboseName += " Lower(" + getSerializeAlt(cat, "Low") + ")"
    elif cat.get("ordinalUpperMaxM", False):
        sVerboseName += " Upper(" + getSerializeAlt(cat, "Upp") + ")"
    return sVerboseName


class AixmAirspaces4_5:

    def __init__(self, oCtrl=None):
        bpaTools.initEvent(__file__, oCtrl.oLog)
        self.oCtrl = oCtrl                                              #Référence du contrôleur appelant
        self.oAirspaces = dict()            #Global collection
        self.oAirspacesBorders = dict()     #Global collection
        #self.oDebug = dict()               #Global debug
        self.oIdxAseUid2UniUid = dict()
        self.oIdxUniUid2OrgName = dict()
        self.oIdxAseUid2AseUid = dict()
        self.oIdxAseUid2AseUid2 = dict()
        self.loadRefFiles()                 #Referentials
        self.cleanAirspacesCalalog=False
        return

    def loadRefFiles(self) -> None:
        self.referentialsPath = self.oCtrl.sOutPath + "referentials/"  #Referentials folder
        bpaTools.createFolder(self.referentialsPath)                    #Init dossier si besoin
        sHeadFileName = "_{0}_".format(self.oCtrl.oAixm.srcOrigin)      #Secific header file

        #Referentiel topologique : Nécessaire pour connaissance des hauteurs sols
        self.oUnknownGroundHeight = dict()
        self.sUnknownGroundHeightFile = "{0}{1}{2}".format(self.referentialsPath, self.oCtrl.sOutHeadFile, "refUnknownGroundHeight.json")
        self.oGroundEstimatedHeight = dict()
        self.sGroundEstimatedHeightFile = "{0}{1}{2}{3}".format(self.referentialsPath, sHeadFileName, self.oCtrl.sOutHeadFile, "refGroundEstimatedHeight.json")
        self.oGroundEstimatedHeight = self.loadRefFileData(self.sGroundEstimatedHeightFile)

        #Referentiel d'exclusion de zones : Nécessaire pour la réalisation des filtrages spécifique Vol Libre
        self.oPotentialFilter4FreeFlightZone = dict()
        self.sPotentialFilter4FreeFlightZoneFileName = "{0}{1}{2}".format(self.referentialsPath, self.oCtrl.sOutHeadFile, "refPotentialFilter4FreeFlightZone.json")
        self.oExcludeFilter4FreeFlightZone = dict()
        self.sExcludeFilter4FreeFlightZoneFileName = "{0}{1}{2}{3}".format(self.referentialsPath, sHeadFileName, self.oCtrl.sOutHeadFile, "refExcludeFilter4FreeFlightZone.json")
        self.oExcludeFilter4FreeFlightZone = self.loadRefFileData(self.sExcludeFilter4FreeFlightZoneFileName)
        return

    def loadRefFileData(self, sFileName:str) -> dict:
        oJson = bpaTools.readJsonFile(sFileName)
        if "referential" in oJson:
            dstObject = oJson["referential"]        #Ne récupère que les datas du fichier
            sMsg = "Loading referential: {0} datas in file - {1}".format(len(dstObject), sFileName)
            self.oCtrl.oLog.info(sMsg, outConsole=False)
            return dstObject
        else:
            return {}

    #Controle de cohérence croisée des contenus de référentiels dans le catalogue généré
    def ctrlReferentialContent(self) -> None:
        for sKey,val in self.oGroundEstimatedHeight.items():
            if not self.findAirspaceByFunctionalKey(sKey):
                sMsg = "Referential error: {0} - Unused key {1}".format(self.sGroundEstimatedHeightFile, sKey)
                self.oCtrl.oLog.warning(sMsg, outConsole=False)
        for sKey,val in self.oExcludeFilter4FreeFlightZone.items():
            if not self.findAirspaceByFunctionalKey(sKey):
                sMsg = "Referential error: {0} - Unused key {1}".format(self.sExcludeFilter4FreeFlightZoneFileName, sKey)
                self.oCtrl.oLog.warning(sMsg, outConsole=False)
        return

    #Recherche de présence d'une zone dans le catalogue par le contenu de propriétés
    def findAirspaceByFunctionalKey(self, sFindKey:str) -> bool:
        for oProp in self.oAirspaces.values():
            if oProp["groupZone"]==True:
                return True
            sKey = self.oCtrl.oAixmTools.getAirspaceFunctionalKey(oProp)
            if sKey == sFindKey:
                return True

    def initAirspacesCatalogIdx(self):
        sTitle = "Airspaces Groups"
        sXmlTag = "Adg"
        if not self.oCtrl.oAixm.root.find(sXmlTag, recursive=False):
            sMsg = "Missing tags {0} - {1}".format(sXmlTag, sTitle)
            self.oCtrl.oLog.info(sMsg, outConsole=False)
        else:
            sMsg = "Indexing {0} - {1}".format(sXmlTag, sTitle)
            self.oCtrl.oLog.info(sMsg)
            oList = self.oCtrl.oAixm.root.find_all(sXmlTag, recursive=False)
            barre = bpaTools.ProgressBar(len(oList), 20, title=sMsg, isSilent=self.oCtrl.oLog.isSilent)
            idx = 0
            for o in oList:
                idx+=1
                if o.AseUidSameExtent:
                    self.oIdxAseUid2AseUid.update({o.AdgUid.AseUid["mid"]:o.AseUidSameExtent["mid"]})
                if o.AseUidBase:
                    for o2 in o.find_all("AseUidComponent", recursive=False):
                        self.oIdxAseUid2AseUid2.update({o2["mid"]:o.AseUidBase["mid"]})
                barre.update(idx)
            barre.reset()

        sTitle = "Airspaces Services"
        sXmlTag = "Sae"
        if not self.oCtrl.oAixm.root.find(sXmlTag, recursive=False):
            sMsg = "Missing tags {0} - {1}".format(sXmlTag, sTitle)
            self.oCtrl.oLog.info(sMsg, outConsole=False)
        else:
            sMsg = "Indexing {0} - {1}".format(sXmlTag, sTitle)
            self.oCtrl.oLog.info(sMsg)
            oList = self.oCtrl.oAixm.root.find_all(sXmlTag, recursive=False)
            barre = bpaTools.ProgressBar(len(oList), 20, title=sMsg, isSilent=self.oCtrl.oLog.isSilent)
            idx = 0
            for o in oList:
                idx+=1
                self.oIdxAseUid2UniUid.update({o.SaeUid.AseUid["mid"]:o.SaeUid.SerUid.UniUid["mid"]})
                barre.update(idx)
            barre.reset()

        sTitle = "Organizations"
        sXmlTag = "Uni"
        if not self.oCtrl.oAixm.root.find(sXmlTag, recursive=False):
            sMsg = "Missing tags {0} - {1}".format(sXmlTag, sTitle)
            self.oCtrl.oLog.info(sMsg, outConsole=False)
        else:
            sMsg = "Indexing {0} - {1}".format(sXmlTag, sTitle)
            self.oCtrl.oLog.info(sMsg)
            oList = self.oCtrl.oAixm.root.find_all(sXmlTag, recursive=False)
            barre = bpaTools.ProgressBar(len(oList), 20, title=sMsg, isSilent=self.oCtrl.oLog.isSilent)
            idx = 0
            for o in oList:
                idx+=1
                self.oIdxUniUid2OrgName.update({o.UniUid["mid"]:o.OrgUid.txtName.string})
                barre.update(idx)
            barre.reset()
        return

    def initAirspacesBordersIdx(self):
        sTitle = "Airspaces Borders"
        sXmlTag = "Abd"
        if not self.oCtrl.oAixm.root.find(sXmlTag, recursive=False):
            sMsg = "Missing tags {0} - {1}".format(sXmlTag, sTitle)
            self.oCtrl.oLog.warning(sMsg, outConsole=True)
        else:
            sMsg = "Indexing {0} - {1}".format(sXmlTag, sTitle)
            self.oCtrl.oLog.info(sMsg)
            oList = self.oCtrl.oAixm.root.find_all(sXmlTag, recursive=False)
            barre = bpaTools.ProgressBar(len(oList), 20, title=sMsg, isSilent=self.oCtrl.oLog.isSilent)
            idx = 0
            for o in oList:
                idx+=1
                self.oAirspacesBorders.update({o.AbdUid.AseUid["mid"]:o})
                barre.update(idx)
            barre.reset()
        return

    def clearAirspaceIdx(self):
        #self.oIdxAseUid2AseUid.clear()         #No clear for use...
        #self.oIdxAseUid2AseUid2.clear()        #No clear for use...
        self.oIdxAseUid2UniUid.clear()
        self.oIdxUniUid2OrgName.clear()
        return

    def getExcludeAirspace(self, theAirspace:dict) -> bool:
        if not theAirspace["vfrZone"]:
            return False
        sKey = self.oCtrl.oAixmTools.getAirspaceFunctionalKey(theAirspace)
        if sKey in self.oExcludeFilter4FreeFlightZone:
            return True
        else:
            return False

    def getGroundEstimatedHeight(self, theAirspace:dict) -> list:
        if not theAirspace["vfrZone"]:
            return [0,0,0,0]
        sKey = self.oCtrl.oAixmTools.getAirspaceFunctionalKey(theAirspace)
        aValue:list = None
        if sKey in self.oGroundEstimatedHeight:
            aValue = self.oGroundEstimatedHeight[sKey]                                  #Extract value of Ground Estimated Height
        if aValue==None:
            aValue = [0,0,0,0]
            self.oUnknownGroundHeight.update({theAirspace["UId"]:sKey})                 #Ajoute un point d'entrée attendu
            if theAirspace["freeFlightZone"]:
                self.oCtrl.oLog.warning("Missing Ground Estimated Height UId={0} - Key={1}".format(theAirspace["UId"], sKey), outConsole=False)
        return aValue

    def createAirspacesCatalog(self, sFilename:str) -> dict:
        ret = {"type":"Aeronautical areas catalog", "headerFile":self.oCtrl.oAixmTools.getJsonPropHeaderFile(sFilename), "catalog":self.oAirspaces}
        return ret

    #Modification d'une propriété stocké dans le catalogue
    def changePropertyInAirspacesCalalog(self, UIdZone:str, Property:str, Value:str) -> None:
        self.oAirspaces[UIdZone].update({Property:Value})
        return

    #Sauvegarde du catalogue de zones
    def saveAirspacesCalalog(self) -> None:
        #Phase 0: Ecriture des référentiels
        header = dict()
        header.update({"srcAixmFile":self.oCtrl.srcFile})
        header.update({"srcAixmOrigin":self.oCtrl.oAixm.srcOrigin})
        header.update({"srcAixmVersion": self.oCtrl.oAixm.srcVersion})
        header.update({"srcAixmEffective":self.oCtrl.oAixm.srcEffective})
        if len(self.oUnknownGroundHeight)>0:
            out = {"headerFile":header, "referential":self.oUnknownGroundHeight}
            bpaTools.writeJsonFile(self.sUnknownGroundHeightFile, out)
            self.oCtrl.oLog.critical("Missing Ground Estimated Height: {0} Unknown heights in file {1}".format(len(self.oUnknownGroundHeight), self.sUnknownGroundHeightFile), outConsole=True)
        if len(self.oPotentialFilter4FreeFlightZone)>0:
            out = {"headerFile":header, "referential":self.oPotentialFilter4FreeFlightZone}
            bpaTools.writeJsonFile(self.sPotentialFilter4FreeFlightZoneFileName, out)
            self.oCtrl.oLog.info("Potential Filter for Free Flight Zone: {0} in file {1}".format(len(self.oPotentialFilter4FreeFlightZone), self.sPotentialFilter4FreeFlightZoneFileName), outConsole=False)

        #Phase 1 : JSON calatlog
        sFilename = "airspacesCatalog"
        cat = self.createAirspacesCatalog(sFilename)                                #Construct Catalog
        self.oCtrl.oAixmTools.writeJsonFile(self.referentialsPath, sFilename, cat)  #Save Catalog on Json format

        #Phase 2 : CSV calatlog
        csv = convertJsonCalalogToCSV(cat)
        self.oCtrl.oAixmTools.writeTextFile(self.referentialsPath, sFilename, csv, "csv")    #Save Catalog on CSV format
        return

    #Chargement initial du catalogue de zones
    def loadAirspacesCatalog(self):
        sTitle = "Airspaces Catalog"
        sXmlTag = "Ase"

        sMsg = "Loading {0} - {1}".format(sXmlTag, sTitle)
        self.oCtrl.oLog.info(sMsg)
        oList = self.oCtrl.oAixm.root.find_all(sXmlTag, recursive=False)
        barre = bpaTools.ProgressBar(len(oList), 20, title=sMsg, isSilent=self.oCtrl.oLog.isSilent)
        idx = 0
        for o in oList:
            idx+=1
            self.loadAirspace(o)
            barre.update(idx)
        barre.reset()
        return

    #Recherche de la zone de base (pris en référence)
    def findAixmObjectAirspacesBorders(self, sAseUid):
        oBorder=None
        if sAseUid in self.oAirspacesBorders:
            oBorder = self.oAirspacesBorders[sAseUid]
        return oBorder

    #Recherche de la zone de base (pris en référence)
    def findZoneUIdBase(self, sZoneUId):
        #if sZoneUId == "1566057":
        #    print(sZoneUId)
        sZoneUIdBase = None
        if sZoneUId in self.oIdxAseUid2AseUid:                      #Cas d'une sous-zone: <Adg><AseUidSameExtent mid="1561891">
            sZoneUIdBase = self.oIdxAseUid2AseUid[sZoneUId]         #Identification de la zone de base (dite classique)
        if not bool(sZoneUIdBase):                                  #Not Found
            if sZoneUId in self.oIdxAseUid2AseUid2:                 #Cas d'une sous-zone: <Adg><AseUidBase mid="1561891">
                sZoneUIdBase = self.oIdxAseUid2AseUid2[sZoneUId]    #Identification de la zone de base (dite classique)
        return sZoneUIdBase

    #Détermination du responsable organisationnel de la zone
    def findOrgName(self, sZoneUId):
        #if sZoneUId == "1566057":
        #    print(sZoneUId)
        sUniUid = orgName = ""
        if sZoneUId in self.oIdxAseUid2UniUid:                      #Cas d'une zone classique
            sUniUid = self.oIdxAseUid2UniUid[sZoneUId]              #Extraction de l'id du Service

        if not bool(sUniUid):                                               #Not Found
            if sZoneUId in self.oIdxAseUid2AseUid:                          #Cas d'une sous-zone: <Adg><AseUidSameExtent mid="1561891">
                sZoneUIdBase = self.oIdxAseUid2AseUid[sZoneUId]             #Identification de la zone de base (dite classique)
                if sZoneUIdBase in self.oIdxAseUid2UniUid:
                    sUniUid = self.oIdxAseUid2UniUid[sZoneUIdBase]          #Extraction de l'id du Service
                elif sZoneUIdBase in self.oIdxAseUid2AseUid2:
                    sZoneUIdBase2 = self.oIdxAseUid2AseUid2[sZoneUIdBase]   #Identification de la zone de base (dite classique)
                    if sZoneUIdBase2 in self.oIdxAseUid2UniUid:
                        sUniUid = self.oIdxAseUid2UniUid[sZoneUIdBase2]     #Extraction de l'id du Service

        if not bool(sUniUid):                                               #Not Found
            if sZoneUId in self.oIdxAseUid2AseUid2:                         #Cas d'une sous-zone: <Adg><AseUidBase mid="1561891">
                sZoneUIdBase = self.oIdxAseUid2AseUid2[sZoneUId]            #Identification de la zone de base (dite classique)
                if sZoneUIdBase in self.oIdxAseUid2UniUid:
                    sUniUid = self.oIdxAseUid2UniUid[sZoneUIdBase]          #Extraction de l'id du Service

        if bool(sUniUid):
            if sUniUid in self.oIdxUniUid2OrgName:
                orgName = self.oIdxUniUid2OrgName[sUniUid]                  #Extraction du nom de l'organisation
        return orgName


    def loadAirspace(self, ase):
        #--------------------------------
        #Identifiant et classification globale de la zone
        sZoneUId = ase.AseUid["mid"]
        groupZone = bool((not ase.valDistVerLower) and (not ase.valDistVerUpper))
        if groupZone:
            theAirspace = self.oCtrl.oAixmTools.initProperty("Grouping zone")
            theAirspace.update({"excludeAirspaceNotCoord":True})
        else:
            theAirspace = self.oCtrl.oAixmTools.initProperty("Airspace Zone")
        theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"groupZone":groupZone})
        theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"UId":sZoneUId})
        theAirspace = self.oCtrl.oAixmTools.addProperty(theAirspace, ase.AseUid, "codeId", "id")
        #Partie spécifique
        theAirspace = self.oCtrl.oAixmTools.addProperty(theAirspace, ase.PoaffAdding, "GUId", "srcGUId", optional=True)
        theAirspace = self.oCtrl.oAixmTools.addProperty(theAirspace, ase.PoaffAdding, "UId", "srcUId", optional=True)
        theAirspace = self.oCtrl.oAixmTools.addProperty(theAirspace, ase.PoaffAdding, "Mhz", "Mhz", optional=True)

        #--------------------------------
        #Détermination du responsable organisationnel de la zone
        orgName = self.findOrgName(sZoneUId)
        if bool(orgName):
            theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"orgName":orgName})

        #-- Store srcValues (source values for generate keys in repositories) --------
        if ase.codeClass:
            theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"srcClass":ase.codeClass.string})
        else:
            theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"srcClass":""})

        if ase.AseUid.codeType:
            theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"srcType":ase.AseUid.codeType.string})
        else:
            theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"srcType":""})

        if ase.txtName:
            theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"name":ase.txtName.string})
        else:
            theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"name":""})

        #--------------------------------------------------------
        #Gestion et homogénéisation des Classes et Types de zones
        #--------------------------------------------------------
        typeZone = ase.AseUid.codeType.string
        if ase.codeClass:       classZone = ase.codeClass.string
        else:                   classZone = None
        if ase.codeActivity:    theCodeActivity = ase.codeActivity.string
        else:                   theCodeActivity = None
        if ase.txtLocalType:    localTypeZone = ase.txtLocalType.string     #ZIT, TMZ; RMZ ...
        else:                   localTypeZone = None
        if ase.codeMil:         theCodeMil = ase.codeMil.string             #MIL, CIVIL, OTHER ...
        else:                   theCodeMil = None

        #Map 20200801
        #if theAirspace["id"] in ["LECBFIR_E"]:
        #    self.oCtrl.oLog.critical("just for bug {0}".format(theAirspace["id"]), outConsole=False)

        #Phase 1 via 'type de zone' - Homogénéisation des classe & type de zones aériennes
        if typeZone in ["TMA", "TMA-P"]:        #TMA [Terminal Control Area.] / #TMA-P [Part of TMA.]
            typeZone="TMA"
            if not classZone:   classZone="G"

        elif typeZone in ["CTR","CTR-P"]:       #CTR [Control Zone.] / #CTR-P [Part of CTR.]
            typeZone="CTR"
            if not classZone:   classZone="G"

        elif typeZone in ["CTA","CTA-P"]:       #CTA [Control Area.] / #CTA-P [Part of a CTA.]
            typeZone="CTA"
            if not classZone:   classZone="G"

        elif typeZone=="CBA":                   #CBA [Cross Border Area (FUA).]
            #typeZone="CBA"                     #No change
            if not classZone:   classZone="G"

        #Cases typeZone=="R" - Restricted
        elif typeZone=="R" and localTypeZone in ["ZRT"]:    ##ZRT = Zone Réglementée Temporaire
            classZone = typeZone
            typeZone = localTypeZone
        elif typeZone in ["R","R-AMC"]:         #R [Restricted Area.] / #R-AMC [AMC Manageable Restricted Area.]
            if classZone==None and theCodeActivity in ["NATURE"]:
                typeZone = theCodeActivity
                classZone="GP"                      #GP = Glider-Prohibited in Openair format
            else:
                typeZone="R"                        #R = Restricted in Openair format
                if not classZone:   classZone=typeZone

        elif typeZone in ["D","D-AMC","A","W"]:     #D [Danger Area.] / #D-AMC [AMC Manageable Danger Area.] / #A [Alert Area.] / #W [Warning Area.]
            typeZone="Q"                            #Q = Danger area in Openair format
            if not classZone:   classZone=typeZone

        elif typeZone=="P":                     #P [Prohibited Area.]
            #typeZone="P"                       #P = Prohibited in Openair format
            if not classZone:   classZone=typeZone

        elif typeZone=="ZIT":                   #ZIT [Zone d'Interdiction Temporaire]
            if not classZone:   classZone="P"   #P = Prohibited in Openair format

        #Cases typeZone=="PROTECT" - #PROTECT [Airspace protected from specific air traffic.]
        elif typeZone=="PROTECT" and theCodeActivity in ["IND-NUCLEAR","IND-OIL"]:
            #typeZone="PROTECT"                 #No change
            classZone="P"                       #P = Prohibited in Openair format
        elif typeZone=="PROTECT" and theCodeActivity in ["FAUNA"]:
            #typeZone="PROTECT"                 #No change
            classZone="GP"                      #GP = Glider-Prohibited in Openair format
        elif typeZone in ["ZSM","MSZ"]:         #ZSM or MSZ - Major Sensibility Zone (BPa & LPO France)
            #typeZone="ZSM"                     #ZSM or MSZ - Major Sensibility Zone in new Openair format
            if not classZone:   classZone=typeZone
        elif typeZone=="PROTECT" and theCodeActivity in ["NO-NOISE"]:
            #typeZone="PROTECT"                 #No change
            classZone="ZSM"                     #ZSM or MSZ - Major Sensibility Zone in new Openair format
        elif typeZone in ["PROTECT","PART","RAS","TSA"] and theCodeActivity in ["REFUEL"]:
            #typeZone="PROTECT"                 #No change
            classZone="REFUEL"                  #Special for exclude area
        elif typeZone=="PROTECT":
            #Other case... Use for theCodeActivity in ["","SPORT","PARACHUTE"]
            #typeZone="PROTECT"                 #No change
            classZone="Q"                       #Q = Danger area in Openair format

        #Cases typeZone=="D-OTHER"  -    #D-OTHER [Activities of dangerous nature (other than a Danger Area).] --> BIRD AREA, GLIDER AREA etc../..
        elif typeZone=="D-OTHER" and localTypeZone=="ZIT":  #ZIT [Zone d'Interdiction Temporaire]
            typeZone=localTypeZone
            if not classZone:   classZone="P"               #P = Prohibited in Openair format
        #BPa - 20210111 - Std "Q" affectation for "MILOPS","ARTILERY","BLAST","SHOOT"
        #elif typeZone=="D-OTHER" and theCodeActivity in ["MILOPS","ARTILERY","BLAST","SHOOT"]:
        #    typeZone="R"                        #R = Restricted in Openair format
        #    if not classZone:   classZone=typeZone
        elif typeZone=="D-OTHER" and theCodeActivity in ["BIRD","BIRD-MGR"]:
            typeZone="PROTECT"
            if not classZone:   classZone="ZSM"                    #ZSM or MSZ - Major Sensibility Zone in new Openair format
        elif typeZone=="D-OTHER" and theCodeActivity in ["GLIDER","PARAGLIDER","HANGGLIDER"]:
            typeZone="Q"                        #Q = Danger area in Openair format
            if not classZone:   classZone="W"   #Filtrage spécifique pour : Vol à voile + vol libre
        elif typeZone=="D-OTHER" and localTypeZone=="LTA":
            typeZone=localTypeZone
            if not classZone:   classZone="G"
        elif typeZone=="D-OTHER" and localTypeZone=="SIV":          #SIV - Service d'Information de Vol
            typeZone=localTypeZone
            if not classZone:   classZone=typeZone
        elif typeZone=="D-OTHER":
            #Other case... Use for theCodeActivity in ["","ACROBAT","ANTIHAIL","ASCENT","BALLOON","GLIDER","HANGGLIDER","LASER","PARACHUTE","PARAGLIDER","SPORT","TRG","UAG","ULM"]
            if not classZone:   classZone="Q"   #Q = Danger area in Openair format
            if localTypeZone and len(localTypeZone)<10 and (not bpaTools.isFloat(localTypeZone)):                                     #Exclure cas des: '60020', '8001' etc...
                typeZone=localTypeZone
            else:
                typeZone=classZone

        #Cases typeZone=="RAS"
        if typeZone=="RAS" and localTypeZone in ["TMZ","TMZ-EX","RTMZ"]:    ##TMZ = Transponder Mandatory Zone / "RTMZ" = Radio + Transponder Mandatory Zone
            if  classZone in [None,"E","G"]:
                classZone = "TMZ"
                typeZone = classZone
            elif typeZone in ["PART"]:
                #classZone - No change !
                typeZone = "TMZ"
        elif typeZone=="RAS" and localTypeZone in ["RMZ"]:    #"RMZ" = Radio Mandatory Zone
            if  classZone in [None,"E","G"]:
                classZone = "RMZ"
                typeZone = classZone
        elif localTypeZone and localTypeZone.find("/RMZ")>=0 and localTypeZone.find("TMZ")<0:     #Case: "ATZ/RMZ","EEKA FIZ/RMZ","EEKE FIZ/RMZ", "TIZ/RMZ", "TIA/RMZ"...
            if  classZone in [None,"E","G"]:
                classZone = "RMZ"                           #"RMZ" = Radio Mandatory Zone
                typeZone = classZone
        elif typeZone=="RAS" and localTypeZone in ["FIS"]:    #"FIS" Flight information service
            if  classZone in [None,"E","G"]:
                classZone = "G"
                typeZone = localTypeZone
        elif typeZone=="RAS":                  #RAS [Regulated Airspace (not otherwise covered).]
            #typeZone="RAS"                    #No change
            if not classZone:   classZone=typeZone

        elif typeZone=="PART":                  #PART [Part of an airspace (used in airspace aggregations).]
            #typeZone="PART"                    #No change
            if not classZone:   classZone=typeZone

        elif typeZone in ["FIR","FIR-P"]:       #FIR [Flight Information Region.] / #FIR-P [Part of an FIR.]
            typeZone="FIR"
            if not classZone:   classZone=typeZone

        elif typeZone=="ADIZ":                  #ADIZ [Air Defense Identification Zone.]
            #typeZone="ADIZ"                    #No change
            if not classZone:   classZone=typeZone

        elif typeZone in ["UTA","UTA-P"]:       #UTA [Upper Control Area.] / #UTA-P [Part of UTA.]
            typeZone="UTA"
            if not classZone:   classZone=typeZone

        elif typeZone in ["UIR","UIR-P"]:       #UIR [Upper Flight Information Region.] / #UIR-P [Part of a UIR.]
            typeZone="UIR"
            if not classZone:   classZone=typeZone

        elif typeZone=="AWY":                  #AWY [Airway (corridor)..]
            #typeZone="AWY"                    #No change
            if not classZone:   classZone=typeZone

        elif typeZone in ["OCA","OCA-P"]:       #OCA [Oceanic Control Area.] / #OCA-P [Partial OCA.]
            typeZone="OCA"
            if not classZone:   classZone=typeZone

        elif typeZone=="OTA":                  #OTA [Oceanic Transition Area.]
            #typeZone="OTA"                    #No change
            if not classZone:   classZone=typeZone

        elif typeZone=="TRA":                   #TRA [Temporary Reserved Area (FUA).]
            #typeZone="TRA"                     #No change
            if not classZone:   classZone=typeZone

        elif typeZone=="TSA":                   #TSA [Temporary Segregated Area (FUA).]
            #typeZone="TSA"                     #No change
            if not classZone:   classZone=typeZone

        elif typeZone=="AMA":                  #AMA [Minimum Altitude Area.]
            #typeZone="AMA"                    #No change
            if not classZone:   classZone=typeZone

        elif typeZone in ["SECTOR","SECTOR-C"]: #SECTOR [Control Sector.] / #SECTOR-C [Temporarily Consolidated (Collapsed ) Sector.]
            typeZone="SECTOR"
            if not classZone:   classZone=typeZone

        elif typeZone=="POLITICAL":             #POLITICAL [Political/administrative area.]
            #typeZone="POLITICAL"               #No change
            if not classZone:   classZone=typeZone

        #Cases typeZone=="CLASS"
        elif typeZone=="CLASS":     #CLASS [Airspace having a specified class.]
            typeZone=classZone      #Doubler la classification de zone ds le 'Type' de zone

        #Ramasse miettes
        else:
            if not classZone:   classZone=typeZone


        #Phase 2 via 'code d'activité' - Complétude de donnée
        if theCodeMil=="MIL" and theCodeActivity==None:
            theCodeActivity="MILOPS"


        #Phase 3 via 'code d'activité' - Analyses particulières
        if theCodeActivity in ["GLIDER","PARAGLIDER","HANGGLIDER"]:
            if   classZone=="W" and typeZone=="Q":
                None    #No change - Goog values !
            elif classZone=="R" and typeZone=="R":
                classZone = "W"         #Favoriser la capacité de filtrage/effacement des alertes pour zones: Vol-à-voile & vol-libre
                typeZone = "Q"
            elif classZone=="Q" and typeZone in ["Q","PROTECT"]:
                classZone = "W"         #Favoriser la capacité de filtrage/effacement des alertes pour zones: Vol-à-voile & vol-libre
                typeZone = "Q"
            elif classZone in ["G","PART","RAS","TSA"]:
                classZone = "W"         #Favoriser la capacité de filtrage/effacement des alertes pour zones: Vol-à-voile & vol-libre
            #else:
            #    self.oCtrl.oLog.warning("'GLIDER activity': id={0} Class={1} Type={2} theCodeActivity={3}".format(theAirspace["UId"], classZone, typeZone, theCodeActivity), outConsole=False)


        #Phase 4 - Cleaning du Nommage de la zone
        if ase.txtName:
            theSrcName:str = ase.txtName.string
            cleanName:str = theSrcName
            tmpName = cleanName.lower()

            if typeZone in ["RMZ","TMZ"]:
                if localTypeZone and tmpName.find(localTypeZone.lower())>=0:      #Suppression complémentaire des: 'RTMZ', 'TIZ/RMZ', 'TIA/RMZ' etc...
                    cleanName = cleanName.replace(localTypeZone, "").strip()

            #Sample: "TALLINN FIR CLASS C" --> "TALLINN FIR"
            if cleanName[-(6+len(classZone)):]=="CLASS "+classZone:
                cleanName = (cleanName[:-(6+len(classZone))]).strip()

            #Sample: "FLORENNES TMA" --> "FLORENNES"
            if len(typeZone)>2 and cleanName[-len(typeZone):]==typeZone:
                cleanName = (cleanName[:-len(typeZone)]).strip()

            #Sample: "TMA I KARLOVY VARY" --> "I KARLOVY VARY"
            if len(typeZone)>2 and cleanName[:len(typeZone)]==typeZone:
                cleanName = (cleanName[len(typeZone):]).strip()

            tmpName = cleanName.lower()
        else:
            theSrcName = cleanName = tmpName = ""


        #Phase 5 - Cleaning du Nommage de la zone
        #Phase 5.1 - TMA cleaning
        if tmpName.find(" TMA ".lower()) >= 0:
            if typeZone!="TMA" and (typeZone==classZone or typeZone in ["PART"]):
                typeZone="TMA"
            if typeZone=="TMA":
                cleanName = cleanName.replace(" TMA", "")
        elif tmpName[:4]=="TMA ".lower():
            if typeZone!="TMA" and (typeZone==classZone or typeZone in ["PART"]):
                typeZone="TMA"
            if typeZone=="TMA":
                cleanName = cleanName[4:]
        elif tmpName[-4:]==" TMA".lower():
            if typeZone!="TMA" and (typeZone==classZone or typeZone in ["PART"]):
                typeZone="TMA"
            if typeZone=="TMA":
                cleanName = cleanName[:-4]

        #Phase 5.2 - CTR cleaning
        if tmpName.find(" CTR ".lower()) >= 0:
            if typeZone!="CTR" and (typeZone==classZone or typeZone in ["PART"]):
                typeZone="CTR"
            if typeZone=="CTR":
                cleanName = cleanName.replace(" CTR", "")
        elif tmpName[:4]=="CTR ".lower():
            if typeZone!="CTR" and (typeZone==classZone or typeZone in ["PART"]):
                typeZone="CTR"
            if typeZone=="CTR":
                cleanName = cleanName[4:]
        elif tmpName[-4:]==" CTR".lower():
            if typeZone!="CTR" and (typeZone==classZone or typeZone in ["PART"]):
                typeZone="CTR"
            if typeZone=="CTR":
                cleanName = cleanName[:-4]

        #Phase 5.3 - CTA cleaning
        if tmpName.find(" CTA ".lower()) >= 0:
            if typeZone!="CTA" and (typeZone==classZone or typeZone in ["PART"]):
                typeZone="CTA"
            if typeZone=="CTA":
                cleanName = cleanName.replace(" CTA", "")
        elif tmpName[:4]=="CTA ".lower():
            if typeZone!="CTA" and (typeZone==classZone or typeZone in ["PART"]):
                typeZone="CTA"
            if typeZone=="CTA":
                cleanName = cleanName[4:]
        elif tmpName[-4:]==" CTA".lower():
            if typeZone!="CTA" and (typeZone==classZone or typeZone in ["PART"]):
                typeZone="CTA"
            if typeZone=="CTA":
                cleanName = cleanName[:-4]

        #Phase 5.4 - FIR cleaning
        if tmpName.find(" FIR ".lower()) >= 0:
            if typeZone!="FIR" and (typeZone==classZone or typeZone in ["PART"]):
                typeZone="FIR"
            if typeZone=="FIR":
                cleanName = cleanName.replace(" FIR", "")
        elif tmpName[:4]=="FIR ".lower():
            if typeZone!="FIR" and (typeZone==classZone or typeZone in ["PART"]):
                typeZone="FIR"
            if typeZone=="FIR":
                cleanName = cleanName[4:]
        elif tmpName[-4:]==" FIR".lower():
            if typeZone!="FIR" and (typeZone==classZone or typeZone in ["PART"]):
                typeZone="FIR"
            if typeZone=="FIR":
                cleanName = cleanName[:-4]

        #Phase 5.5 - RMZ cleaning
        if tmpName.find("RADIO MANDATORY ZONE".lower()) >= 0:
            if typeZone in ["RAS"]:
                classZone = "RMZ"
                typeZone = classZone
            if typeZone=="RMZ":
                cleanName = cleanName.replace("RADIO MANDATORY ZONE", "").strip()
        if tmpName.find(" RMZ ".lower()) >= 0:
            if typeZone!="RMZ" and (typeZone==classZone or typeZone in ["RAS"]):
                classZone = "RMZ"
                typeZone = classZone
            if typeZone=="RMZ":
                cleanName = cleanName.replace(" RMZ", "")
        elif tmpName[:4]=="RMZ ".lower():
            if typeZone!="RMZ" and (typeZone==classZone or typeZone in ["RAS"]):
                classZone = "RMZ"
                typeZone = classZone
            if typeZone=="RMZ":
                cleanName = cleanName[4:]
        elif tmpName[-4:]==" RMZ".lower():
            if typeZone!="RMZ" and (typeZone==classZone or typeZone in ["RAS"]):
                classZone = "RMZ"
                typeZone = classZone
            if typeZone=="RMZ":
                cleanName = cleanName[:-4]

        #Phase 5.6 - TMZ cleaning
        if tmpName.find("TRANSPONDER MANDATORY ZONE".lower()) >= 0:
            if typeZone in ["RAS"]:
                classZone = "TMZ"
                typeZone = classZone
            if typeZone=="TMZ":
                cleanName = cleanName.replace("TRANSPONDER MANDATORY ZONE", "").strip()
        if tmpName.find(" TMZ ".lower()) >= 0:
            if typeZone!="TMZ" and (typeZone==classZone or typeZone in ["RAS"]):
                classZone = "TMZ"
                typeZone = classZone
            if typeZone=="TMZ":
                cleanName = cleanName.replace(" TMZ", "")
        elif tmpName[:4]=="TMZ ".lower():
            if typeZone!="TMZ" and (typeZone==classZone or typeZone in ["RAS"]):
                classZone = "TMZ"
                typeZone = classZone
            if typeZone=="TMZ":
                cleanName = cleanName[4:]
        elif tmpName[-4:]==" TMZ".lower():
            if typeZone!="TMZ" and (typeZone==classZone or typeZone in ["RAS"]):
                classZone = "TMZ"
                typeZone = classZone
            if typeZone=="TMZ":
                cleanName = cleanName[:-4]

        #Phase 5.7 - CBA cleaning
        if   typeZone=="CBA" and tmpName.find("CROSS BORDER AREA".lower())>=0:
            cleanName = cleanName.replace("CROSS BORDER AREA", "").strip()
        elif typeZone=="FIR" and tmpName.find("FLIGHT INFORMATION REGION".lower())>=0:
            cleanName = cleanName.replace("FLIGHT INFORMATION REGION", "").strip()
        elif typeZone=="OCA" and tmpName.find("OCEANIC CONTROL AREA".lower())>=0:
            cleanName = cleanName.replace("OCEANIC CONTROL AREA", "").strip()
        elif typeZone=="OTA" and tmpName.find("OCEANIC TRANSITION AREA".lower())>=0:
            cleanName = cleanName.replace("OCEANIC TRANSITION AREA", "").strip()
        elif typeZone in ["SECTOR"]:
            if tmpName.find(typeZone.lower())>=0:           #Suppression complémentaire des: 'SECTOR',
                cleanName = cleanName.replace(typeZone, "").strip()

        #Rectification specifique de certaines zones !
        if classZone==typeZone and typeZone=="PART":
            if theAirspace["id"] in ["EBR06B","EBR07B"]:
                classZone = "R"
        if classZone==typeZone and typeZone=="R":
            if tmpName.find("prohibited for all aircraft".lower()) >= 0:
                classZone = "P"
                typeZone = classZone


        #ase.AseUid.codeType or CODE_TYPE_ASE Format
        #-------------------------------------------
            #P [Prohibited Area.]
            #PROTECT [Airspace protected from specific air traffic.]
            #R [Restricted Area.]
            #R-AMC [AMC Manageable Restricted Area.]
            #D [Danger Area.]
            #D-AMC [AMC Manageable Danger Area.]
            #D-OTHER [Activities of dangerous nature (other than a Danger Area).] --> BIRD AREA, GLIDER AREA etc../..
            #A [Alert Area.]
            #W [Warning Area.]
            #CBA [Cross Border Area (FUA).]
            #CTA [Control Area.]
            #CTA-P [Part of a CTA.]
            #CTR [Control Zone.]
            #CTR-P [Part of CTR.]
            #AWY [Airway (corridor)..]
            #TMA [Terminal Control Area.]
            #TMA-P [Part of TMA.]
            #TRA [Temporary Reserved Area (FUA).]
            #TSA [Temporary Segregated Area (FUA).]
            #RAS [Regulated Airspace (not otherwise covered).]
            #CLASS [Airspace having a specified class.]
            #PART [Part of an airspace (used in airspace aggregations).]
            #OCA [Oceanic Control Area.]
            #OCA-P [Partial OCA.]
            #OTA [Oceanic Transition Area.]
            #SECTOR [Control Sector.]
            #SECTOR-C [Temporarily Consolidated (Collapsed ) Sector.]
            #UIR [Upper Flight Information Region.]
            #UIR-P [Part of a UIR.]
            #FIR [Flight Information Region.]
            #FIR-P [Part of an FIR.]
            #UTA [Upper Control Area.]
            #UTA-P [Part of UTA.]
            #   ICAO DEPRECATED-4.0  [ICAO Region (for example, EUR, NAT, etc).]
            #   ECAC DEPRECATED-4.0  [ECAC Region.]
            #   CFMU DEPRECATED-4.0  [CFMU Area.]
            #   IFPS DEPRECATED-4.0  [IFPS Area.]
            #   TACT DEPRECATED-4.0  [TACT Area.]
            #   ATZ DEPRECATED-4.0  [Aerodrome Traffic Zone.]
            #   ATZ-P DEPRECATED-4.0  [Part of ATZ.]
            #   MNPSA DEPRECATED-4.0  [Minimum Navigation Performance Specifications Area.]
            #   MNPSA-P DEPRECATED-4.0  [Part of MNPSA.]
            #   RTECL DEPRECATED-4.0  [Route Centreline.]
            #   CDA DEPRECATED-4.0  [Client Defined Airspace.]
            #   HTZ DEPRECATED-4.0  [Helicopter Traffic Zone.]
            #   OIL DEPRECATED-4.0  [Oil Field.]
            #   BIRD DEPRECATED-4.0  [Bird Migration Area.]
            #   SPORT DEPRECATED-4.0  [Aerial Sporting/Recreational Area.]
            #   LMA DEPRECATED-4.0  [Limited Airspace (in general).]
            #   MIL DEPRECATED-4.0  [Military Training/Exercise Area.]
            #   NAS-P DEPRECATED-4.0  [A part of a National Airspace System.]
            #NAS [National Airspace System.]
            #RCA [Reduced Co-ordination Airspace Procedure (FUA).]
            #ADIZ [Air Defense Identification Zone.]
            #AMA [Minimum Altitude Area.]
            #ASR [Altimeter Setting Region.]
            #NO-FIR [Airspace for which not even an FIR is defined.]
            #POLITICAL [Political/administrative area.]

        #ase.txtLocalType or ? Format
        #-------------------------------------------
            #TMZ = Transponder Mandatory Zone / "RTMZ" = Radio + Transponder Mandatory Zone
            #SIV - Service d'Information de Vol
            #FIS - Flight information service
            #HPZ is used in some States in order to designate 'Helicopter Protected Zone'


        #ase.codeActivity or CODE_ACTIVITY Format
        #-------------------------------------------
            #TFC-AD [Aerodrome traffic.]
            #TFC-HELI [Helicopter/Gyrocopter traffic.]
            #TRG [Training.]
            #ACROBAT [Acrobatic flights, aerobatics.]
            #AIRSHOW [Air show.]
            #SPORT [Aerial sporting.]
            #ULM [Ultra light flights.]
            #GLIDER [Gliding.]
            #PARAGLIDER [Paragliding.]
            #HANGGLIDER [Hanggliding.]
            #PARACHUTE [Parachute jumping.]
            #DROP [Droppings.]
            #BALLOON [Hot air balloons.]
            #ASCENT [Ascent of radio probe, radiosonde, meteorological balloons.]
            #SPACEFLT [Space flight operations.]
            #UAV [Unmanned aerial vehicle.]
            #WORK [Aerial work.]
            #DUSTING [Seasonal crop dusting.]
            #FIRE [Heavy fire suppression work.]
            #MILOPS [Military operations.]
            #REFUEL [Refuelling.]
            #JETCLIMB [Climb-out sector for jet aircraft.]
            #EXERCISE [Air combat and exercises.]
            #TOWING [Target towing.]
            #NAVAL [Ship exercises.]
            #MISSILES [Flight of guided missiles.]
            #AIRGUN [Aerial gunnery.]
            #ARTILERY [Artillery firing.]
            #SHOOT [Shooting from ground.]
            #BLAST [Blasting operations.]
            #WATERBLAST [Underwater explosions.]
            #ANTIHAIL [Anti-hail rocket firing.]
            #BIRD [Bird hazard.]
            #BIRD-MGR [Bird migration.]
            #FIREWORK [Fireworks.]
            #HI-RADIO [High intensity radio transmission (HIRTA).]
            #HI-LIGHT [High intensity lights.]
            #LASER [Laser light activity.]
            #NATURE [Natural reserve.]
            #FAUNA [Sensitive fauna.]
            #NO-NOISE [Noise abatement.]
            #ACCIDENT [Accident investigation area.]
            #POPULATION [Highly populated area.]
            #VIP [VIP, public figures.]
            #VIP-PRES [President.]
            #VIP-VICE [Vice-President.]
            #OIL [Oil field.]
            #GAZ [Gas field or gasoline vaporization.]
            #IND-OIL [Oil refinery.]
            #IND-CHEM [Chemical plant.]
            #IND-NUCLEAR [Nuclear energy plant/activity.]
            #TECHNICAL [Technical activity.]
            #ATS [Air traffic services.]
            #EQUIPMENT [Special equipment.]
            #PROCEDURE [Special procedure.]
            #EQUIPMENT-RSVM [RSVM equipment required.]
            #EQUIPMENT-RNAV [RNAV equipment required.]
            #EQUIPMENT-833 [8.33 channel equipment required.]
            #OTHER [Other activities/reasons.]


        theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"class":classZone})
        theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"type":typeZone})
        if localTypeZone!=None:
            theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"localType":localTypeZone})
        if theCodeActivity!=None:
            theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"codeActivity":theCodeActivity})
        if theCodeMil!=None:
            theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"codeMil":theCodeMil})


        #--------------------------------
        #Préfiltrage des zones
        aExcludeClassVfrZone           = ["FIR","NO-FIR","ADIZ","UTA","UIR","OTA","SIV","SECTOR","PART","FIS","OCA","AWY","TRA","TSA","RAS","AMA","POLITICAL","REFUEL"]
        aExcludeTypeFreeFlightZone     = ["FIR","NO-FIR","ADIZ","UTA","UIR","OTA","SIV","SECTOR","PART","FIS"]  #OCA+CBA+CTA+RAS a garder!
        aExcludeClassFreeFlightZone    = ["E","F","W"]      #"G" - Preserver les 'G' pour affichage des zones à caractères particuliers
        aExcludeClassFreeFlightZoneExt = ["F"]			    #"G"+"E"   - Preserver 'G' + 'E' pour capacité d'extention de vols au dessus FL115 (et de 0m jusqu'au FL195/5944m)
        vfrZoneFilter = bool(classZone in aExcludeClassVfrZone)
        freeFlightZoneFilter = bool(vfrZoneFilter or \
                                    (classZone in aExcludeClassFreeFlightZone) or \
                                    (typeZone in aExcludeTypeFreeFlightZone) )
        freeFlightZoneExtFilter = bool(vfrZoneFilter or \
                                    (classZone in aExcludeClassFreeFlightZoneExt) or \
                                    (typeZone in aExcludeTypeFreeFlightZone) )
        if freeFlightZoneFilter:
            theAirspace.update({"excludeAirspaceByFilter":True})
        bvfrZone           = bool((not groupZone) and (not vfrZoneFilter))
        bfreeFlightZone 	  = bool((not groupZone) and (not freeFlightZoneFilter))
        bfreeFlightZoneExt = bool((not groupZone) and (not freeFlightZoneExtFilter))
        theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"vfrZone":bvfrZone})
        theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"freeFlightZone":bfreeFlightZone})
        theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"freeFlightZoneExt":bfreeFlightZoneExt})

        #--------------------------------
        #Stockage du Nommage de la zone
        if ase.txtName:
            theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"srcName":theSrcName})
            theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"name":cleanName})
        else:
            theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"name":ase.AseUid.codeId.string})

        #--------------------------------
        #Décodage des plancher/Plafond avec estimlation des altitudes en mètres (exclusion des regroupement de zones qui n'ont pas ces caractéristiques...)
        if not theAirspace["groupZone"]:
            theAirspace = self.oCtrl.oAixmTools.addProperty(theAirspace, ase, "codeDistVerUpper", "upperType", optional=True)
            theAirspace = self.oCtrl.oAixmTools.addProperty(theAirspace, ase, "valDistVerUpper", "upperValue", optional=True)
            theAirspace = self.oCtrl.oAixmTools.addProperty(theAirspace, ase, "uomDistVerUpper", "upperUnit", optional=True)
            #theAirspace = self.oCtrl.oAixmTools.addProperty(theAirspace, ase, "codeDistVerLower", "lowerType", optional=True)
            if ase.codeDistVerLower:    #Parfois non précisé dans les fichiers aixm du SIA
                theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"lowerType":ase.codeDistVerLower.string})
            else:
                theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"lowerType":"ALT"})      #Default fixed at 'AMSL'
            theAirspace = self.oCtrl.oAixmTools.addProperty(theAirspace, ase, "valDistVerLower", "lowerValue", optional=True)
            theAirspace = self.oCtrl.oAixmTools.addProperty(theAirspace, ase, "uomDistVerLower", "lowerUnit", optional=True)
            #Cas particulier des zones ayant des double plancher (ex: [C] GENEVE 1 (TMA / id=TMA16161))
            if ase.valDistVerMnm:
                theAirspace = self.oCtrl.oAixmTools.addProperty(theAirspace, ase, "codeDistVerMnm", "lowerTypeMnm", optional=True)
                theAirspace = self.oCtrl.oAixmTools.addProperty(theAirspace, ase, "valDistVerMnm", "lowerValueMnm", optional=True)
                theAirspace = self.oCtrl.oAixmTools.addProperty(theAirspace, ase, "uomDistVerMnm", "lowerUnitMnm", optional=True)

            #Map 20200801
            #if theAirspace["UId"] in ["1561273"]:
            #    print("map alt")

            #theAirspace.update({"groundEstimatedHeight": "?"})
            low, up = self.setAltitudeZone(sZoneUId, ase, theAirspace)

        #--------------------------------
        #Eventuel filtrage complémentaire pour requalification des zones 'vfrZone' & 'freeFlightZone' (zones spécifiques Vol-Libre Parapente/Delta)
        if bvfrZone and ("lowerValue" in theAirspace) and ("upperValue" in theAirspace):
            bLowInfFL115 = bool(low<3505)       #Plancher strictement en dessous FL115/3505m
            #bLowInfFL175 = bool(low<5334)       #Plancher strictement en dessous FL175/5334m
            bLowInfFL195 = bool(low<5943)       #Plancher strictement en dessous FL195/5944m
            bUppInfFL115 = bool(up<=3505)       #Plafond en dessous, et jusqu'au FL115/3505m

            if not bLowInfFL115:                #Zone dont le plancher débute au dessus le FL115/3505m
                theAirspace.update({"excludeAirspaceByAlt":True})
                theAirspace.update({"vfrZone":False})

            theAirspace.update({"vfrZoneExt":bool(bLowInfFL195 and (not bUppInfFL115))})             #Extension de vol possible jusqu'au FL195/5944m

            bPotentialFilter = bfreeFlightZone and bool(up<=5944)       #Marqueur pour filtrage potentiel de zones jusqu'au FL195/5944m
            if bPotentialFilter:
                theAirspace.update({"potentialFilter4FreeFlightZone":True})

            bExclude:bool = False
            if bfreeFlightZone:
                sKey = self.oCtrl.oAixmTools.getAirspaceFunctionalKey(theAirspace)
                if sKey in self.oExcludeFilter4FreeFlightZone:
                    bExclude = self.oExcludeFilter4FreeFlightZone[sKey]
                    if bExclude:
                        theAirspace.update({"excludeAirspaceByRef":True})
                        self.oCtrl.oLog.info("Exclude airspace for Free-Flight-Zone {0}".format(sKey), outConsole=False)
                elif bPotentialFilter:
                    self.oPotentialFilter4FreeFlightZone.update({sKey:False})           #Ajoute une zone potentiellement filtrable
                    self.oCtrl.oLog.debug("Potential Filter for Free-Flight-Zone {0}".format(sKey), outConsole=False)

                theAirspace.update({"freeFlightZone":bool((not bExclude) and bLowInfFL115)})     #Zone non-exclue et dont le plancher débute en dessous FL115/3505m

            if bfreeFlightZoneExt:
                theAirspace.update({"freeFlightZoneExt":bool((not bExclude) and (bLowInfFL195 and (not bUppInfFL115)))})  #Extension de vol possible jusqu'au FL195/5944m

        #--------------------------------
        #Verification des eventuels decalages d'altitudes
        if theAirspace["vfrZone"]:   #Extend calculs - old freeFlightZone
            #Necessité de connaître l'altitude-moyenne du sol
            bFlag:bool = False
            if ase.codeDistVerLower:         #Parfois non précisé dans les fichiers aixm du SIA
                bFlag = bFlag or bool((ase.codeDistVerLower.string=="HEI") and (ase.valDistVerLower.string!="0"))
                if ase.codeDistVerMnm:
                    bFlag = bFlag or bool((ase.codeDistVerMnm.string=="HEI") and (ase.valDistVerMnm.string!="0"))
            if ase.codeDistVerUpper:         #Parfois non précisé dans les fichiers aixm du SIA
                bFlag = bFlag or bool(ase.codeDistVerUpper.string=="HEI")
                if ase.codeDistVerMax:
                    bFlag = bFlag or bool(ase.codeDistVerMax.string=="HEI")
            if bFlag:
                aGroundEstimatedHeight:list = self.getGroundEstimatedHeight(theAirspace)
                if aGroundEstimatedHeight[3]>0:    #Ctrl lAltMax
                    theAirspace.update({"groundEstimatedHeight": aGroundEstimatedHeight})
                    low, up = self.setAltitudeZone(sZoneUId, ase, theAirspace, aGroundEstimatedHeight)
            #else:
            #    del theAirspace["groundEstimatedHeight"]  #Suppression de la propriété qui est inutile


            if ase.codeDistVerLower in ["W84", "QFE"]:
                self.oCtrl.oLog.critical("codeDistVerLower calculation: id={0} name={1} Lower={2}".format(sZoneUId, theAirspace["name"], ase.codeDistVerLower.string), outConsole=True)
            if ase.codeDistVerUpper in ["W84", "QFE"]:
                self.oCtrl.oLog.critical("codeDistVerUpper calculation: id={0} name={1} Upper={2}".format(sZoneUId, theAirspace["name"], ase.codeDistVerUpper.string), outConsole=True)


        #--------------------------------
        #Zones complémentaire avec remarques et description des activations
        theAirspace = self.oCtrl.oAixmTools.addProperty(theAirspace, ase, "codeLocInd", "codeLocInd", optional=True)        #LFFF, LIMM
        if ase.Att:
            sCodeWorkHr:str=""
            if ase.Att.codeWorkHr:
                sCodeWorkHr = ase.Att.codeWorkHr.string
                theAirspace = self.oCtrl.oAixmTools.addProperty(theAirspace, ase.Att, "codeWorkHr", "activationCode", optional=True)

            if classZone=="D" and typeZone!="LTA" and theAirspace.get("activationCode", None)!="H24":
                theAirspace.update({"declassifiable":True})

            if ase.Att.Timsh:
                #Documentation of <Timsh> content
                #   <codeTimeRef>UTC</codeTimeRef>				#Time reference system
                #   <dateValidWef>01-01</dateValidWef>			#Yearly start date (day and month) | or 'SDLST' [Start of Daylight Saving Time] or 'EDLST' [End of Daylight Saving
                #   <dateValidTil>31-12</dateValidTil>			#Yearly end date | or 'SDLST' [Start of Daylight Saving Time] or 'EDLST' [End of Daylight Saving
                #   <codeDay>ANY</codeDay>						#Affected day or start of affected period | enumeration values(MON,TUE,WED,THU,FRI,SAT,SUN,WD,PWD,AWD,LH,PLH,ALH,ANY)
                #   										    ie.   WD  [Working day] - which is any day except Saturday/Sunday/Legal Holidays
                #   											      PWD [the day preceding a working day]
                #   											      AWD [the day after a working day]
                #   											      LH  [Legal Holiday]
                #   											      PLH [the day preceding a legal holiday]
                #   										  		  ALH [the day after a legal holiday]
                #   									              ANY [Any day]
                #   Optional attributes [
                #       <codeDayTil>SAT</codeDayTil>			#End of affected period | (the same enumeration of <codeDay>)
                #       ##Start time bloc description
                #       <timeWef>08:30</timeWef>				#Start - Time
                #       <codeEventWef>SR</codeEventWef>			#Start - Event
                #       <timeRelEventWef>30</timeRelEventWef>	#Start - Relative to event | enumeration values(SR,SS)
                #       <codeCombWef>E</codeCombWef>			#Start - Interpretation	   | enumeration values(E,L)
                #       ##End time bloc description
                #       <timeTil>16:00</timeTil>				#End - Time
                #       <codeEventTil>SS</codeEventTil>			#End - Event
                #       <timeRelEventTil>30</timeRelEventTil>	#End - Relative to event   | (the same enumeration of <timeRelEventWef>)
                #       <codeCombTil>L</codeCombTil>			#End - Interpretation      | (the same enumeration of <codeCombWef>)
                #   ]
                #Tentative de construction d'un format 'comprehensible par l'humain'...
                #   cas 1 : UTC(01/01->31/12) ANY(08:30->16:00)
                #   cas 2 : UTC(01/01->31/12) MON to FRI(08:30->16:00)
                """ standard aixm-4.5 output samples              // associate to POAF convertion samples
        		<Att>
        			<codeWorkHr>TIMSH</codeWorkHr>
            		<Timsh>                                       '*ATimes {"1": ["UTC(01/01->31/12)", "WD(08:00->18:00)"], "2":...}'
            			<codeTimeRef>UTCW</codeTimeRef>
            			<dateValidWef>01-01</dateValidWef>
            			<dateValidTil>31-12</dateValidTil>
            			<codeDay>WD</codeDay>
            			<codeDayTil>WD</codeDayTil>
            			<timeWef>08:00</timeWef>
            			<timeTil>18:00</timeTil>
            		</Timsh>
            		<Timsh>                                       '*ATimes {{"1":... , "2": ["UTC(EDLST->SDLST)", "SAT to SUN(08:30->16:00)"]}'
            			<codeTimeRef>UTC</codeTimeRef>
            			<dateValidWef>EDLST</dateValidWef>
            			<dateValidTil>SDLST</dateValidTil>
            			<codeDay>SAT</codeDay>
            			<codeDayTil>SUN</codeDayTil>
            			<timeWef>08:30</timeWef>
            			<timeTil>16:00</timeTil>
            		</Timsh>
                    <Timsh>                                       '*ATimes {{"1":... , "2":... , "3": ["UTC(01/01->31/12)", "ANY(SR/30/E->SS/30/L)"]}'
            			<codeTimeRef>UTC</codeTimeRef>
            			<dateValidWef>01-01</dateValidWef>
            			<dateValidTil>31-12</dateValidTil>
            			<codeDay>ANY</codeDay>
            			<codeEventWef>SR</codeEventWef>
            			<timeRelEventWef>30</timeRelEventWef>
            			<codeCombWef>E</codeCombWef>
            			<codeEventTil>SS</codeEventTil>
            			<timeRelEventTil>30</timeRelEventTil>
            			<codeCombTil>L</codeCombTil>
            		</Timsh>
                </Att>
                """
                oGlobTimsh:dict = {}
                #Interprétation de toutes les occurances de <Timsh>
                oLstTsh = ase.Att.find_all("Timsh", recursive=False)
                for oTsh in oLstTsh:
                    sMonthPeriod:str = oTsh.codeTimeRef.string + "("
                    sMonthPeriod += str(oTsh.dateValidWef.string).replace("-", "/") + "->"
                    sMonthPeriod += str(oTsh.dateValidTil.string).replace("-", "/") + ")"
                    sDayPeriod:str = oTsh.codeDay.string
                    if oTsh.codeDayTil:
                        if oTsh.codeDay.string != oTsh.codeDayTil.string:
                            sDayPeriod += " to " + oTsh.codeDayTil.string
                    sDayPeriod += "("
                    ##Start time bloc description
                    if oTsh.timeWef:
                         sDayPeriod += oTsh.timeWef.string
                    if oTsh.codeEventWef:
                        sDayPeriod += oTsh.codeEventWef.string
                    if oTsh.timeRelEventWef:
                        sDayPeriod += "/" + oTsh.timeRelEventWef.string
                    if oTsh.codeCombWef:
                        sDayPeriod += "/" + oTsh.codeCombWef.string
                    sDayPeriod += "->"
                    ##End time bloc description
                    if oTsh.timeTil:
                        sDayPeriod += oTsh.timeTil.string
                    if oTsh.codeEventTil:
                        sDayPeriod += oTsh.codeEventTil.string
                    if oTsh.timeRelEventTil:
                        sDayPeriod += "/"+ oTsh.timeRelEventTil.string
                    if oTsh.codeCombTil:
                        sDayPeriod += "/" + oTsh.codeCombTil.string
                    sDayPeriod += ")"
                    oGlobTimsh.update({len(oGlobTimsh)+1:[sMonthPeriod, sDayPeriod]})
                    theAirspace.update({"timeScheduling": oGlobTimsh})

            if ase.Att.txtRmkWorkHr:
                if ase.Att.txtRmkWorkHr.string != sCodeWorkHr:        #Eviter les doublons de codes ; ex; H24 / H24
                    theAirspace = self.oCtrl.oAixmTools.addProperty(theAirspace, ase.Att, "txtRmkWorkHr", "activationDesc", optional=True)

        if ase.txtRmk:
            if ase.txtRmk.string != ".":              #Clean data
                theAirspace = self.oCtrl.oAixmTools.addProperty(theAirspace, ase, "txtRmk", "desc", optional=True)

        #--------------------------------
        #Traitement spécifique pour signaler les zones non-activables...
        activationDesc=""
        if ase.Att: activationDesc = str(ase.Att.txtRmkWorkHr).lower()
        activationDesc = activationDesc + "/" + str(ase.txtRmk).lower()
        activationDesc = activationDesc.replace("  ", " ")   #Clean...
        activationDesc = activationDesc.replace(", ", ",")
        activationDesc = activationDesc.replace(" ,", ",")
        activationDesc = activationDesc.replace("- ", "-")
        activationDesc = activationDesc.replace(" -", "-")
        bExcept = False
        if not bExcept:
            #Non activation = Sauf SAM, DIM et JF // except SAT, SUN and public HOL
            bExcept = bExcept or bool(activationDesc.find("sauf SAM,DIM et JF".lower())>=0)
            bExcept = bExcept or bool(activationDesc.find("sauf WE et JF".lower())>=0)
            bExcept = bExcept or bool(activationDesc.find("except SAT,SUN and HOL".lower())>=0)
            bExcept = bExcept or bool(activationDesc.find("except SAT,SUN and public HOL".lower())>=0)
            bExcept = bExcept or bool(activationDesc.find("MON-TUE except HOL".lower())>=0)
            bExcept = bExcept or bool(activationDesc.find("MON-WED except HOL".lower())>=0)
            bExcept = bExcept or bool(activationDesc.find("MON-THU except HOL".lower())>=0)
            bExcept = bExcept or bool(activationDesc.find("MON-FRI except HOL".lower())>=0)
            bExcept = bExcept or bool(activationDesc.find("MON-FRI except public HOL".lower())>=0)
            bExcept = bExcept or bool(activationDesc.find("MON-FRI possible activation H24 Except public HOL".lower())>=0)
            bExcept = bExcept or bool(activationDesc.find("MON to FRI except HOL".lower())>=0)
            bExcept = bExcept or bool(activationDesc.find("MON/FRI EXC HOL".lower())>=0)
            bExcept = bExcept or bool(activationDesc.find("MON/THU EXC HOL".lower())>=0)
            bExcept = bExcept or bool(activationDesc.find("MON-FRI (EXC HOL)".lower())>=0)
            bExcept = bExcept or bool((activationDesc.find("MON-FRI".lower())>=0) and (activationDesc.find("EXC HOL".lower())>=0))
            if bExcept:
                self.oCtrl.oLog.debug("except-SDJF: id={0} name={1}".format(sZoneUId, theAirspace["name"]))
                theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"exceptSAT":True})
                theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"exceptSUN":True})
                theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"exceptHOL":True})
        if not bExcept:
            #Non activation = Sauf SAM, DIM // Except SAT and SUN
            bExcept = bool(activationDesc.find("sauf SAM,DIM".lower())>=0)
            bExcept = bExcept or bool(activationDesc.find("sauf WE".lower())>=0)
            bExcept = bExcept or bool(activationDesc.find("except SAT,SUN".lower())>=0)
            bExcept = bExcept or bool(activationDesc.find("except SAT and SUN".lower())>=0)
            if bExcept:
                self.oCtrl.oLog.debug("except-SD: id={0} name={1}".format(sZoneUId, theAirspace["name"]))
                theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"exceptSAT":True})
                theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"exceptSUN":True})
        if not bExcept:
            #Non activation = Sauf DIM et JF // except SUN and public HOL
            bExcept = bool(activationDesc.find("sauf DIM et JF".lower())>=0)
            bExcept = bExcept or bool(activationDesc.find("except SUN and HOL".lower())>=0)
            bExcept = bExcept or bool(activationDesc.find("except SUN and public HOL".lower())>=0)
            bExcept = bExcept or bool(activationDesc.find("MON-SAT except HOL".lower())>=0)
            if bExcept:
                self.oCtrl.oLog.debug("except-DJF: id={0} name={1}".format(sZoneUId, theAirspace["name"]))
                theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"exceptSUN":True})
                theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"exceptHOL":True})
        if not bExcept:
            #Non activation = Sauf SAM // Except SAT
            bExcept = bool(activationDesc.find("sauf SAM".lower())>=0)
            bExcept = bExcept or bool(activationDesc.find("except SAT".lower())>=0)
            if bExcept:
                self.oCtrl.oLog.debug("except-S: id={0} name={1}".format(sZoneUId, theAirspace["name"]))
                theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"exceptSAT":True})
            #Non activation = Sauf DIM // Except SUN
            bExcept = bool(activationDesc.find("sauf DIM".lower())>=0)
            bExcept = bExcept or bool(activationDesc.find("except SUN".lower())>=0)
            if bExcept:
                self.oCtrl.oLog.debug("except-D: id={0} name={1}".format(sZoneUId, theAirspace["name"]))
                theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"exceptSUN":True})
            #Non activation = Sauf JF // Except HOL
            bExcept = bool(activationDesc.find("sauf JF".lower())>=0)
            bExcept = bExcept or bool(activationDesc.find("except HOL".lower())>=0)
            bExcept = bExcept or bool(activationDesc.find("except public HOL".lower())>=0)
            bExcept = bExcept or bool(activationDesc.find("EXC HOL".lower())>=0)
            if bExcept:
                self.oCtrl.oLog.debug("except-JF: id={0} name={1}".format(sZoneUId, theAirspace["name"]))
                theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"exceptHOL":True})

        #--------------------------------
        #Traitement spécifique pour signaler les zones activable par NOTAM
        bNotam = bool(activationDesc.find("NOTAM".lower())>=0)
        if bNotam:
            self.oCtrl.oLog.debug("See NOTAM: id={0} name={1}".format(sZoneUId, theAirspace["name"]))
            theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"seeNOTAM":True})

        #--------------------------------
        #Libellé complet de la zone (V=Verbose)
        theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"nameV":getVerboseName(theAirspace)})

        #--------------------------------
        self.oAirspaces[sZoneUId] = theAirspace         #Store new item in global collection
        return


    #Détermination des caractéristiques d'un plancher ou plafond de zone
    #   inputs: sRefAlt in "Lower", "Upper"
    #   Return format: [orgAltM, altM]
    def getAltitude(self, theAirspace, sRefAlt:str, sRefAltMinMax:str, oValDistVer, oCodeDistVer, oUomDistVer, aGroundEstimatedHeight) -> list:
        #ase.uomDistVerLower, ase.uomDistVerUpper or UOM_DIST_VER format:
        #    FT [Feet.]
        #    M [Metres.]
        #    FL [Flight level in hundreds of feet..]
        #    SM [Standard metres (tens of metres).]
        #ase.codeDistVerLower, ase.codeDistVerUpper or CODE_DIST_VER_UPPER/LOWER format:
        #   Real distance
        #       HEI [The distance measured from ground (GND)]
        #       ALT [The distance from mean sea level (MSL)]
        #       W84 [The distance measured from WGS-84 ellipsoid]
        #   Pressure difference
        #       STD [The altimeter setting is set to standard atmosphere]
        #       QFE [The pressure corrected to the official station/aerodrome elevation]

        cstRefAltLower:str = "Lower"
        cstRefAltUpper:str = "Upper"
        if sRefAlt == cstRefAltLower:
            cstRetError = [-1, 0, None, None, None]
        else:
            cstRetError = [-1, 9999, None, None, None]
        if not sRefAlt in [cstRefAltLower, cstRefAltUpper]:
           self.oCtrl.oLog.error("getAltitude() - Calling error {0}".format(sRefAlt), outConsole=True)
           return cstRetError

        cstRefAltMin:str = "Min"
        cstRefAltMax:str = "Max"
        if not sRefAltMinMax in ["", cstRefAltMin, cstRefAltMax]:
           self.oCtrl.oLog.error("getAltitude() - Calling error {0}".format(sRefAltMinMax), outConsole=True)
           return cstRetError

        if oValDistVer is None:     #old - oUomDistVer
            #Logger une erreur en cas d'absence de valeur du plancher/planfond pour les zones potentiellement utilisable !
            if (sRefAltMinMax=="") and not (theAirspace["class"] in ["RAS","PART","AMA"]):
                #self.oCtrl.oLog.warning("oValDistVer{0} is None: id={1} Class={2} Type={3} Name={4}".format(sRefAlt, theAirspace["UId"], theAirspace["class"], theAirspace["type"], theAirspace["name"]), outConsole=False)
                theAirspace.update({"WarningValDistVer"+sRefAlt:True})
            return cstRetError

        cstKeyAlt    = sRefAlt.lower() + sRefAltMinMax              #samples: 'lower' or 'lowerMin' or 'upper' or 'upperMax'
        cstKeyOrdAlt = "ordinal" + sRefAlt + sRefAltMinMax + "M"    #samples: 'ordinalLowerM' or 'ordinalLowerMinM' or 'ordinalUpperM' or 'ordinalUpperMaxM'

        #Décodage du référencement d'altitude
        sType:str = ""                      #Defualt value
        if oCodeDistVer is None:
            if oValDistVer.string == "0":   sType = "AGL"       #old ASFC
        elif oCodeDistVer.string == "HEI":  sType = "AGL"       #old ASFC
        elif oCodeDistVer.string == "ALT":  sType = "AMSL"
        #elif oCodeDistVer.string == "STD":  sType = "AMSL"  #Default value for 'R T VALLORBE (GLIDER)' or 'R T LE BRASSUS (GLIDER)'

        #Décodage
        altM:int    = None
        orgAltM:int = 0
        sAlt:str    = ""

        if oUomDistVer.string == "FL":
            altM = int(float(oValDistVer.string) * aixmReader.CONST.ft * 100)
            if altM == 0:
                sAlt = "SFC"
            else:
                if sType == "":
                    sAlt = "{0}{1:03d}".format(oUomDistVer.string, int(oValDistVer.string))
                else:
                    sAlt = "{0}{1:03d} {2}".format(oUomDistVer.string, int(oValDistVer.string), sType)
                if oCodeDistVer.string == "HEI":
                    orgAltM = altM
                    theAirspace.update({cstKeyOrdAlt: orgAltM})
                    if sRefAlt == cstRefAltLower:
                        altM += aGroundEstimatedHeight[1]    #=lAltMed
                    else:
                        altM += aGroundEstimatedHeight[2]    #=lAltRet

        elif oUomDistVer.string == "FT":
            altM = int(float(oValDistVer.string) * aixmReader.CONST.ft)
            if altM == 0:
                sAlt = "SFC"
            else:
                if sType == "":
                    sAlt = "{0}{1}".format(oValDistVer.string, oUomDistVer.string)
                else:
                    sAlt = "{0}{1} {2}".format(oValDistVer.string, oUomDistVer.string, sType)
                if oCodeDistVer.string == "HEI":
                    orgAltM = altM
                    theAirspace.update({cstKeyOrdAlt: orgAltM})
                    if sRefAlt == cstRefAltLower:
                        altM += aGroundEstimatedHeight[1]    #=lAltMed
                    else:
                        altM += aGroundEstimatedHeight[2]    #=lAltRet

        elif oUomDistVer.string in ["M", "SM"]:
            altM = int(oValDistVer.string)
            if altM == 0:
                sAlt = "SFC"
            else:
                if sType == "":
                    sAlt = "{0}M AMSL".format(oValDistVer.string)  #'AMSL' is default value
                else:
                    sAlt = "{0}M {1}".format(oValDistVer.string, sType)
                if oCodeDistVer.string == "HEI":
                    orgAltM = altM
                    theAirspace.update({cstKeyOrdAlt: orgAltM})
                    if sRefAlt == cstRefAltLower:
                        altM += aGroundEstimatedHeight[1]    #=lAltMed
                    else:
                        altM += aGroundEstimatedHeight[2]    #=lAltRet

        theAirspace.update({cstKeyAlt: sAlt})

        if altM is None:
            self.oCtrl.oLog.error("altM is None: id={0} Class={1} Type={2} Name={3} ".format(theAirspace["UId"], theAirspace["class"], theAirspace["type"], theAirspace["name"]), outConsole=False)
            return cstRetError

        return [orgAltM, altM]


    def setAltitudeZone(self, sZoneUId, ase, theAirspace, aGroundEstimatedHeight=[0,0,0,0]) -> list:
        sOrdinalLower:str = "ordinalLower"    #samples: 'ordinalLowerM' or 'ordinalLowerMinM'
        aFinalLower:list
        aAltLower    = self.getAltitude(theAirspace, "Lower", "",    ase.valDistVerLower, ase.codeDistVerLower, ase.uomDistVerLower, aGroundEstimatedHeight)
        aAltLowerMin = self.getAltitude(theAirspace, "Lower", "Min", ase.valDistVerMnm, ase.codeDistVerMnm, ase.uomDistVerMnm, aGroundEstimatedHeight)
        #Spécifique pour les fichiers (EuCtrl & SIA France): Ignorer la double référence altimétrique du plancher pour toutes les #LTA FRANCE
        #if theAirspace["type"] == "LTA":
        #    aAltLowerMin = [-1, 0, None, None, None]
        #if aAltLowerMin[0]>=0:
        #    aFinalLower = aAltLowerMin
        #    sOrdinalLower += "MinM"
        #else:
        #    aFinalLower = aAltLower
        #    sOrdinalLower += "M"
        aFinalLower = aAltLower
        sOrdinalLower += "M"

        sOrdinalUpper:str = "ordinalUpper"    #samples: 'ordinalUpperM' or 'ordinalUpperMaxM'
        aFinalUpper:list
        aAltUpper    = self.getAltitude(theAirspace, "Upper", "",    ase.valDistVerUpper, ase.codeDistVerUpper, ase.uomDistVerUpper, aGroundEstimatedHeight)
        aAltUpperMax = self.getAltitude(theAirspace, "Upper", "Max", ase.valDistVerMax, ase.codeDistVerMax, ase.uomDistVerMax, aGroundEstimatedHeight)
        #if aAltUpperMax[0]>=0:
        #    aFinalUpper = aAltUpperMax
        #    sOrdinalUpper += "MaxM"
        #else:
        #    aFinalUpper = aAltUpper
        #    sOrdinalUpper += "M"
        aFinalUpper = aAltUpper
        sOrdinalUpper += "M"

        #Verrification de conformité des altitudes
        low = aFinalLower[1]
        up  = aFinalUpper[1]
        if up < low:
            #Eventuelle correction d'altitude après analyse via référentiel
            if (sOrdinalLower in theAirspace) and (sOrdinalUpper in theAirspace):
                low = aFinalLower[0] + aGroundEstimatedHeight[0]        # orgAlt + AltMin
                if up <= low:
                    up = aFinalUpper[0] + aGroundEstimatedHeight[3]     # orgAlt + AltMax
                if up <= low:
                    low = 0
                    self.oCtrl.oLog.warning("Forced height reset1: Upper <= Lower; up={0} low={1} for id={2} NameV={3}".format(up, low, sZoneUId, theAirspace["name"]), outConsole=False)
                aFinalLower[1] = low
                aFinalUpper[1] = up
            elif (sOrdinalLower in theAirspace) and not (sOrdinalUpper in theAirspace):
                low = aFinalLower[0] + aGroundEstimatedHeight[0]    #=lAltMin
                if up <= low:
                    low = 0
                    self.oCtrl.oLog.warning("Forced height reset2: Upper <= Lower; up={0} low={1} for id={2} NameV={3}".format(up, low, sZoneUId, theAirspace["name"]), outConsole=False)
                aFinalLower[1] = low
                aFinalUpper[1] = up
            elif not (sOrdinalLower in theAirspace) and (sOrdinalUpper in theAirspace):
                up = aFinalUpper[0] + aGroundEstimatedHeight[3]     # orgAlt + AltMax
                if up <= low:
                    up = aAltUpper[1]
                if up <= low:
                    low = 0
                    self.oCtrl.oLog.warning("Forced height reset3: Upper <= Lower; up={0} low={1} for id={2} NameV={3}".format(up, low, sZoneUId, theAirspace["name"]), outConsole=False)
                aFinalLower[1] = low
                aFinalUpper[1] = up
            else:
                self.oCtrl.oLog.error("Height error: Upper <= Lower; up={0} low={1} for id={2} NameV={3}".format(up, low, sZoneUId, theAirspace["name"]), outConsole=True)
        elif up == low:
            self.oCtrl.oLog.warning("Height warning: Upper == Lower; up={0} low={1} for id={2} NameV={3}".format(up, low, sZoneUId, theAirspace["name"]), outConsole=True)

        #Stockage des Plancher/Plafond en catalogue
        if (sOrdinalLower in theAirspace) or (sOrdinalUpper in theAirspace):
            theAirspace.update({"groundEstimatedHeight": aGroundEstimatedHeight})
        theAirspace.update({"lowerM": aFinalLower[1]})
        theAirspace.update({"upperM": aFinalUpper[1]})

        return aFinalLower[1], aFinalUpper[1]
