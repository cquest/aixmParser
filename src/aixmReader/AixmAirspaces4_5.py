#!/usr/bin/env python3

import bpaTools
import aixmReader


#Sauvegarde du catalogue de zones sous forme de CSV
def convertJsonCalalogToCSV(cat) -> str:

    #Phase 2.1 : Header CSV file
    csv = csvCol = csvVal = ""
    oHeader = cat["headerFile"]
    for key,val in oHeader.items():
        if isinstance(val, dict):
            for key2,val2 in val.items():
                csvCol += '{0};'.format(key2)
                csvVal += '{0};'.format(val2)
        else:
            csvCol += '{0};'.format(key)
            csvVal += '{0};'.format(val)
    csv = "<Header file>\n{0}\n{1}\n\n<Content>\n".format(csvCol, csvVal)

    #Phase 2.2 : Construct a global index on columns (collect all columns in contents for complete header of CSV file...)
    #oCols avec initialisation d'une table d'index avec imposition de l'ordonnancement de colonnes choisies
    oCols = {"zoneType":0, "groupZone":0, "vfrZone":0, "freeFlightZone":0, "excludeAirspaceNotCoord":0, "excludeAirspaceNotFfArea":0, "excludeAirspaceByFilter":0, "excludeAirspaceByAlt":0, "excludeAirspaceByRef":0, "potentialFilter4FreeFlightZone":0, "orgName":0, "keySrcFile":0, "GUId":0, "UId":0, "id":0, "srcClass":0, "srcType":0, "srcName":0, "class":0, "type":0, "localType":0, "codeActivity":0, "name":0, "groundEstimatedHeight":0, "ordinalLowerM":0, "lowerM":0, "ordinalUpperM":0, "upperM":0, "nameV":0, "alt":0, "altM":0, "altV":0, "exceptSAT":0, "exceptSUN":0, "exceptHOL":0, "seeNOTAM":0}
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
                csv += '"{0}";'.format(val[colKey])
            else:
                csv += ';'

    csv += "\n\n<EOF>"
    return csv


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
        if not self.oCtrl.oAixm.doc.find(sXmlTag):
            sMsg = "Missing tags {0} - {1}".format(sXmlTag, sTitle)
            self.oCtrl.oLog.info(sMsg, outConsole=False)
        else:
            sMsg = "Indexing {0} - {1}".format(sXmlTag, sTitle)
            self.oCtrl.oLog.info(sMsg)
            oList = self.oCtrl.oAixm.doc.find_all(sXmlTag)
            barre = bpaTools.ProgressBar(len(oList), 20, title=sMsg, isSilent=self.oCtrl.oLog.isSilent)
            idx = 0
            for o in oList:
                idx+=1
                if o.AseUidSameExtent:
                    self.oIdxAseUid2AseUid.update({o.AdgUid.AseUid["mid"]:o.AseUidSameExtent["mid"]})
                if o.AseUidBase:
                    for o2 in o.find_all("AseUidComponent"):
                        self.oIdxAseUid2AseUid2.update({o2["mid"]:o.AseUidBase["mid"]})
                barre.update(idx)
            barre.reset()

        sTitle = "Airspaces Services"
        sXmlTag = "Sae"
        if not self.oCtrl.oAixm.doc.find(sXmlTag):
            sMsg = "Missing tags {0} - {1}".format(sXmlTag, sTitle)
            self.oCtrl.oLog.info(sMsg, outConsole=False)
        else:
            sMsg = "Indexing {0} - {1}".format(sXmlTag, sTitle)
            self.oCtrl.oLog.info(sMsg)
            oList = self.oCtrl.oAixm.doc.find_all(sXmlTag)
            barre = bpaTools.ProgressBar(len(oList), 20, title=sMsg, isSilent=self.oCtrl.oLog.isSilent)
            idx = 0
            for o in oList:
                idx+=1
                self.oIdxAseUid2UniUid.update({o.SaeUid.AseUid["mid"]:o.SaeUid.SerUid.UniUid["mid"]})
                barre.update(idx)
            barre.reset()

        sTitle = "Organizations"
        sXmlTag = "Uni"
        if not self.oCtrl.oAixm.doc.find(sXmlTag):
            sMsg = "Missing tags {0} - {1}".format(sXmlTag, sTitle)
            self.oCtrl.oLog.info(sMsg, outConsole=False)
        else:
            sMsg = "Indexing {0} - {1}".format(sXmlTag, sTitle)
            self.oCtrl.oLog.info(sMsg)
            oList = self.oCtrl.oAixm.doc.find_all(sXmlTag)
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
        if not self.oCtrl.oAixm.doc.find(sXmlTag):
            sMsg = "Missing tags {0} - {1}".format(sXmlTag, sTitle)
            self.oCtrl.oLog.warning(sMsg, outConsole=True)
        else:
            sMsg = "Indexing {0} - {1}".format(sXmlTag, sTitle)
            self.oCtrl.oLog.info(sMsg)
            oList = self.oCtrl.oAixm.doc.find_all(sXmlTag)
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
        #Phase 0: Ecriture des réeferentiels
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
        oList = self.oCtrl.oAixm.doc.find_all(sXmlTag)
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
        groupZone = bool(not ase.valDistVerLower)
        if groupZone:
            theAirspace = self.oCtrl.oAixmTools.initProperty("Grouping zone")
            theAirspace.update({"excludeAirspaceNotCoord":True})
        else:
            theAirspace = self.oCtrl.oAixmTools.initProperty("Airspace Zone")
        theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"groupZone":groupZone})
        theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"UId":sZoneUId})
        theAirspace = self.oCtrl.oAixmTools.addProperty(theAirspace, ase.AseUid, "codeId", "id")

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
            theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"srcName":ase.txtName.string})
        else:
            theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"srcName":""})

        if ase.codeActivity:    theCodeActivity = ase.codeActivity.string
        else:                   theCodeActivity = None

        if ase.txtLocalType:    localTypeZone = ase.txtLocalType.string     #ZIT, TMZ; RMZ ...
        else:                   localTypeZone = None

        #Map 20200715
        #if theAirspace["id"] in ["EBS02"]:
        #    print(theAirspace["id"])

        #Homogénéisation des Classes et Types de zones
        typeZone = ase.AseUid.codeType.string
        if ase.codeClass:
            classZone = ase.codeClass.string

            #Homogénéisation des classe & type de zones aériennes
            if typeZone=="TMA-P":       #TMA-P [Part of TMA.]
                typeZone="TMA"
            elif typeZone=="CTA-P":     #CTA-P [Part of a CTA.]
                typeZone="CTA"
            elif typeZone=="CTR-P":     #CTR-P [Part of CTR.]
                typeZone="CTR"
            elif typeZone=="CLASS":     #CLASS [Airspace having a specified class.]
                typeZone=classZone

            if classZone=="G" and theCodeActivity=="GLIDER":
                classZone = "W"
                typeZone="R"
            elif classZone=="G" and typeZone=="D-OTHER":  #D-OTHER [Activities of dangerous nature (other than a Danger Area).] --> BIRD AREA, GLIDER AREA etc../..
                classZone="Q"           #Q = Danger area in Openair format
                typeZone=classZone

        else:
            classZone = ase.AseUid.codeType.string

            #Homogénéisation des classe & type de zones aériennes
            if classZone=="R-AMC":                  #R-AMC [AMC Manageable Restricted Area.]
                classZone="R"
                typeZone=classZone
            elif classZone in ["D","D-AMC","A","W"]:    #D [Danger Area.] / #D-AMC [AMC Manageable Danger Area.] / #A [Alert Area.] / #W [Warning Area.]
                classZone="Q"                           #Q = Danger area in Openair format / #D-AMC [AMC Manageable Danger Area.]
                typeZone=classZone
            elif classZone in ["FIR","FIR-P"]:      #FIR [Flight Information Region.] / #FIR-P [Part of an FIR.]
                classZone="FIR"
                typeZone=classZone
            elif classZone in ["UTA","UTA-P"]:      #UTA [Upper Control Area.] / #UTA-P [Part of UTA.]
                classZone="UTA"
                typeZone=classZone
            elif classZone in ["UIR","UIR-P"]:      #UIR [Upper Flight Information Region.] / #UIR-P [Part of a UIR.]
                classZone="UIR"
                typeZone=classZone
            elif classZone in ["OCA","OCA-P"]:      #OCA [Oceanic Control Area.] / #OCA-P [Partial OCA.]
                classZone="OCA"
                typeZone=classZone
            elif classZone=="OTA":                  #OTA [Oceanic Transition Area.]
                classZone="OTA"
                typeZone=classZone
            elif classZone=="RAS":                  #RAS [Regulated Airspace (not otherwise covered).]
                classZone="RAS"
                typeZone=classZone
            elif classZone in ["SECTOR","SECTOR-C"]:   #SECTOR [Control Sector.] / #SECTOR-C [Temporarily Consolidated (Collapsed ) Sector.]
                classZone="SECTOR"
                typeZone=classZone
            elif classZone in ["TMA","TMA-P"]:      #TMA [Terminal Control Area.] / #TMA-P [Part of TMA.]
                classZone="C"
                typeZone="TMA"
            elif classZone in ["CTA","CTA-P"]:      #CTA [Control Area.] / #CTA-P [Part of a CTA.]
                classZone="C"
                typeZone="CTA"
            elif classZone in ["CTR","CTR-P"]:      #CTR [Control Zone.] / #CTR-P [Part of CTR.]
                classZone="D"
                typeZone="CTR"
            elif classZone=="CBA":                  #CBA [Cross Border Area (FUA).]
                classZone="R"
                typeZone="CBA"
            elif classZone=="TRA":                  #TRA [Temporary Reserved Area (FUA).]
                classZone="R"
                typeZone="TRA"
            elif classZone=="TSA":                  #TSA [Temporary Segregated Area (FUA).]
                classZone="R"
                typeZone="TSA"
            elif classZone=="PROTECT":              #PROTECT [Airspace protected from specific air traffic.]
                classZone="P"
                typeZone="PROTECT"
            elif classZone=="D-OTHER":              #D-OTHER [Activities of dangerous nature (other than a Danger Area).] --> BIRD AREA, GLIDER AREA etc../..
                classZone="Q"                       #Q = Danger area in Openair format
                if localTypeZone:
                    typeZone=localTypeZone
                else:
                    typeZone=classZone
            elif classZone=="PART":     #PART [Part of an airspace (used in airspace aggregations).]
                classZone="{SpecFilter}"
                typeZone="PART"

        #Specification used for Euroconrol and SIA files
        if typeZone=="ZIT" and (classZone in ["Q"]):
            classZone = "P"
        elif localTypeZone=="TMZ" and (classZone in ["E","G","RAS"]):
            classZone = "P"
            typeZone=localTypeZone
        elif localTypeZone=="RMZ" and (classZone in ["E","G","RAS"]):
            classZone = "R"
            typeZone=localTypeZone
        elif localTypeZone=="LTA" and (typeZone in ["D-OTHER","Q"]):
            typeZone=localTypeZone
        elif localTypeZone=="AER" and (typeZone in ["Q"]):
            typeZone=localTypeZone
        elif localTypeZone=="TRPLA" and (typeZone in ["Q"]):
            typeZone=localTypeZone
        elif localTypeZone=="BAL" and theCodeActivity==None:
            theCodeActivity="BALLOON"
        elif localTypeZone=="TRVL" and (typeZone in ["Q"]):
        #    classZone="{SpecFilter}"
            typeZone=localTypeZone
        elif localTypeZone=="SUR" and (typeZone in ["Q"]):
        #    classZone="{SpecFilter}"
            typeZone=localTypeZone
        elif localTypeZone=="VOL" and (typeZone in ["Q","D-OTHER"]):
        #    classZone="{SpecFilter}"
            typeZone=localTypeZone

        if theCodeActivity=="GLIDER":
            classZone = "W"
            typeZone="R"

        #Cas spécifique initialement non précisés (ex: "EBKT RMZ" ou "EBKT TMZ" de 'KORTRIJK')
        if ase.txtName:     theName = ase.txtName.string.lower()
        else:               theName = ""
        if theName.find("RADIO MANDATORY ZONE".lower()) >= 0:
            classZone="R"
            typeZone="RMZ"
        elif (theName.find("RMZ".lower()) >= 0) and (classZone in ["E","F","G"]):
            classZone="R"
            typeZone="RMZ"
        if theName.find("TRANSPONDER MANDATORY ZONE".lower()) >= 0:
            classZone="P"
            typeZone="TMZ"
        elif (theName.find("TMZ".lower()) >= 0) and (classZone in ["E","F","G"]):
            classZone="P"
            typeZone="TMZ"

        #Filtrage specifique de certaines zones
        if classZone=="{SpecFilter}" and typeZone in ["PART"]:
            if theAirspace["id"] in ["EBR06B"]:
                classZone="P"
            else:
                classZone=typeZone
        #elif classZone=="{SpecFilter}" and typeZone in ["SUR","TRVL","VOL"]:
        #    if theAirspace["id"] in ["NTV010NFP","NTV020NFP","LF225","NTV052TOW","NTV051TOW","NTV053TOW","LF6821","LF6294","LF6055"]:
        #        classZone="Q"
        #    else:
        #        classZone=typeZone
        elif classZone=="{SpecFilter}":
            classZone=typeZone


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


        theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"class":classZone})
        theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"type":typeZone})
        if localTypeZone!=None:
            theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"localType":localTypeZone})
        if theCodeActivity!=None:
            theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"codeActivity":theCodeActivity})

        #--------------------------------
        #Préfiltrage des zones
        aExcludeClassVfrZone = ["PART","SECTOR","FIR","UTA","UIR","OCA","OTA","RAS"]
        aExcludeClassFreeFlightZone = ["E","F","G"]
        aExcludeTypeFreeFlightZone = ["LTA","SIV","TRA","TSA"]  #"AER", "TRPLA"
        aArea4FreeFlightZone = ["","FRANCE"]
        vfrZoneFilter = bool(classZone in aExcludeClassVfrZone)
        freeFlightZoneFilter = bool(vfrZoneFilter or \
                                    (classZone in aExcludeClassFreeFlightZone) or \
                                    (typeZone in aExcludeTypeFreeFlightZone) or \
                                    not(orgName in aArea4FreeFlightZone) )
        if freeFlightZoneFilter:
            theAirspace.update({"excludeAirspaceByFilter":True})
        vfrZone         = bool((not groupZone) and (not vfrZoneFilter))
        freeFlightZone  = bool((not groupZone) and (not freeFlightZoneFilter))
        theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"vfrZone":vfrZone})
        theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"freeFlightZone":freeFlightZone})


        #if typeZone==None:
        #    print(typeZone)

        #--------------------------------
        #Détermination du Nommage de la zone
        if ase.txtName:
            theSrcName = ase.txtName.string
            theName = theSrcName
            if theName[:len(typeZone)] == typeZone:
                theName = (theName[len(typeZone):]).strip()
            if theName[-len(typeZone):] == typeZone:
                theName = (theName[:-len(typeZone)]).strip()
            theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"name":theName})
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
            #theAirspace.update({"groundEstimatedHeight": "?"})
            low, up = self.setAltitudeZone(sZoneUId, ase, theAirspace)

        #--------------------------------
        #Eventuel filtrage complémentaire pour requalification des zones 'vfrZone' & 'freeFlightZone' (zones spécifiques Vol-Libre Parapente/Delta)
        if (theAirspace["vfrZone"]) and ("lowerValue" in theAirspace) and ("upperValue" in theAirspace):
            bFilter0 = bool(low>=3505)                          #Filtrer toutes les zones dont le plancher débute au FL115/3505m
            if bFilter0:
                theAirspace.update({"excludeAirspaceByAlt":True})
                theAirspace.update({"vfrZone":False})

            bPotentialFilter = theAirspace["freeFlightZone"] and bool(low==0 and up>3505)        #Filtre potentiel de zones qui portent sur tous les étages
            if bPotentialFilter:
                theAirspace.update({"potentialFilter4FreeFlightZone":True})

            bFilter1 = False
            sKey = self.oCtrl.oAixmTools.getAirspaceFunctionalKey(theAirspace)
            if sKey in self.oExcludeFilter4FreeFlightZone:
                bFilter1 = self.oExcludeFilter4FreeFlightZone[sKey]
                if bFilter1:
                    theAirspace.update({"excludeAirspaceByRef":True})
                    self.oCtrl.oLog.info("Exclude airspace for Free-Flight-Zone {0}".format(sKey), outConsole=False)
            elif bPotentialFilter:
                self.oPotentialFilter4FreeFlightZone.update({sKey:False})           #Ajoute une zone potentiellement filtrable
                #self.oCtrl.oLog.info("Potential Filter for Free-Flight-Zone {0}".format(sKey), outConsole=False)

            if theAirspace["freeFlightZone"] and (bFilter0 or bFilter1):
                theAirspace.update({"freeFlightZone":False})

            #NE JAMAIS FILTRER: les éventuelles extensions de vol classées "E"; dont le planfond va au delà de FL115/3505m
            if classZone=="E" and up>3505:
                if not theAirspace["vfrZone"]:
                    theAirspace.update({"vfrZone":True})
                if typeZone!="LTA" and not theAirspace["freeFlightZone"]:
                    theAirspace.update({"freeFlightZone":True})


        #--------------------------------
        #Verification des eventuels decalages d'altitudes
        if theAirspace["freeFlightZone"]:
            #Necessité de connaître l'altitude-moyenne du sol
            bFlag = False
            if ase.codeDistVerLower:         #Parfois non précisé dans les fichiers aixm du SIA
                bFlag = bFlag or bool((ase.codeDistVerLower.string == "HEI") and (ase.valDistVerLower.string!="0"))
            if ase.codeDistVerUpper:         #Parfois non précisé dans les fichiers aixm du SIA
                bFlag = bFlag or bool(ase.codeDistVerUpper.string == "HEI")
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
        theAirspace = self.oCtrl.oAixmTools.addProperty(theAirspace, ase, "codeMil", "codeMil", optional=True)              #CIVL
        if ase.Att:
            theAirspace = self.oCtrl.oAixmTools.addProperty(theAirspace, ase.Att, "codeWorkHr", "activationCode", optional=True)
            theAirspace = self.oCtrl.oAixmTools.addProperty(theAirspace, ase.Att, "txtRmkWorkHr", "activationDesc", optional=True)
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
            bExcept = bExcept or bool(activationDesc.find("sauf SAM,DIM et JF".lower()) >= 0)
            bExcept = bExcept or bool(activationDesc.find("sauf WE et JF".lower()) >= 0)
            bExcept = bExcept or bool(activationDesc.find("except SAT,SUN and HOL".lower()) >= 0)
            bExcept = bExcept or bool(activationDesc.find("except SAT,SUN and public HOL".lower()) >= 0)
            bExcept = bExcept or bool(activationDesc.find("MON-TUE except HOL".lower()) >= 0)
            bExcept = bExcept or bool(activationDesc.find("MON-WED except HOL".lower()) >= 0)
            bExcept = bExcept or bool(activationDesc.find("MON-THU except HOL".lower()) >= 0)
            bExcept = bExcept or bool(activationDesc.find("MON-FRI except HOL".lower()) >= 0)
            bExcept = bExcept or bool(activationDesc.find("MON-FRI except public HOL".lower()) >= 0)
            bExcept = bExcept or bool(activationDesc.find("MON-FRI possible activation H24 Except public HOL".lower()) > 0)
            bExcept = bExcept or bool(activationDesc.find("MON to FRI except HOL".lower()) >= 0)
            if bExcept:
                self.oCtrl.oLog.info("except-SDJF: id={0} name={1}".format(sZoneUId, theAirspace["name"]))
                theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"exceptSAT":"Yes"})
                theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"exceptSUN":"Yes"})
                theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"exceptHOL":"Yes"})
        if not bExcept:
            #Non activation = Sauf SAM, DIM // Except SAT and SUN
            bExcept = bool(activationDesc.find("sauf SAM,DIM".lower()) >= 0)
            bExcept = bExcept or bool(activationDesc.find("sauf WE".lower()) >= 0)
            bExcept = bExcept or bool(activationDesc.find("except SAT,SUN".lower()) >= 0)
            bExcept = bExcept or bool(activationDesc.find("except SAT and SUN".lower()) >= 0)
            if bExcept:
                self.oCtrl.oLog.info("except-SD: id={0} name={1}".format(sZoneUId, theAirspace["name"]))
                theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"exceptSAT":"Yes"})
                theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"exceptSUN":"Yes"})
        if not bExcept:
            #Non activation = Sauf DIM et JF // except SUN and public HOL
            bExcept = bool(activationDesc.find("sauf DIM et JF".lower()) >= 0)
            bExcept = bExcept or bool(activationDesc.find("except SUN and HOL".lower()) >= 0)
            bExcept = bExcept or bool(activationDesc.find("except SUN and public HOL".lower()) >= 0)
            bExcept = bExcept or bool(activationDesc.find("MON-SAT except HOL".lower()) >= 0)
            if bExcept:
                self.oCtrl.oLog.info("except-DJF: id={0} name={1}".format(sZoneUId, theAirspace["name"]))
                theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"exceptSUN":"Yes"})
                theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"exceptHOL":"Yes"})
        if not bExcept:
            #Non activation = Sauf SAM // Except SAT
            bExcept = bool(activationDesc.find("sauf SAM".lower()) >= 0)
            bExcept = bExcept or bool(activationDesc.find("except SAT".lower()) >= 0)
            if bExcept:
                self.oCtrl.oLog.info("except-S: id={0} name={1}".format(sZoneUId, theAirspace["name"]))
                theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"exceptSAT":"Yes"})
            #Non activation = Sauf DIM // Except SUN
            bExcept = bool(activationDesc.find("sauf DIM".lower()) >= 0)
            bExcept = bExcept or bool(activationDesc.find("except SUN".lower()) >= 0)
            if bExcept:
                self.oCtrl.oLog.info("except-D: id={0} name={1}".format(sZoneUId, theAirspace["name"]))
                theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"exceptSUN":"Yes"})
            #Non activation = Sauf JF // Except HOL
            bExcept = bool(activationDesc.find("sauf JF".lower()) >= 0)
            bExcept = bExcept or bool(activationDesc.find("except HOL".lower()) >= 0)
            bExcept = bExcept or bool(activationDesc.find("except public HOL".lower()) >= 0)
            bExcept = bExcept or bool(activationDesc.find("EXC HOL".lower()) >= 0)
            if bExcept:
                self.oCtrl.oLog.info("except-JF: id={0} name={1}".format(sZoneUId, theAirspace["name"]))
                theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"exceptHOL":"Yes"})

        #--------------------------------
        #Traitement spécifique pour signaler les zones activable par NOTAM
        bNotam = bool(activationDesc.find("NOTAM".lower()) >= 0)
        if bNotam:
            self.oCtrl.oLog.info("See NOTAM: id={0} name={1}".format(sZoneUId, theAirspace["name"]))
            theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"seeNOTAM":"Yes"})

        #--------------------------------
        #Finalisation avec un libellé complet (type V=Verbose)
        if theAirspace["type"] != theAirspace["class"]:
                finalType = theAirspace["type"]
        else:   finalType = ""
        finalLongName = "[{0}] {1} (".format(theAirspace["class"], theAirspace["name"])
        if finalType:
            finalLongName += finalType + " / "
        if theCodeActivity!=None:
            finalLongName += theCodeActivity + " / "
        if bNotam:
            finalLongName += "SeeNotam / "
        finalLongName +=  "id=" + theAirspace["id"] + ")"
        theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"nameV":finalLongName})

        #--------------------------------
        #Ajout des propriétés pour colorisation de la zone uniquement en mode Draft (car la version finale sous navigateur integre la techno CSS)
        #if self.oCtrl.Draft:
        self.oCtrl.oAixmTools.addColorProperties(theAirspace)

        #--------------------------------
        self.oAirspaces[sZoneUId] = theAirspace         #Store new item in global collection
        return


    def setAltitudeZone(self, sZoneUId, ase, theAirspace, aGroundEstimatedHeight=[0,0,0,0]):

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
        
        #Détermination du plancher de la zone
        sZoneAltL = sZoneAltL_m = sZoneAltL_a = ""
        low = orgLow = 0
        if ase.uomDistVerLower is not None:
            if ase.codeDistVerLower is None:
                if ase.valDistVerLower.string == "0":
                    lowType = "ASFC"
                else:
                    lowType = ""
            elif ase.codeDistVerLower.string == "ALT":
                lowType = "AMSL"
            elif ase.codeDistVerLower.string == "HEI":
                lowType = "ASFC"
            else:
                lowType = ""
            low = None
            if ase.uomDistVerLower.string == "FL":
                low = int(float(ase.valDistVerLower.string) * aixmReader.CONST.ft * 100)
                if low == 0:
                    sTmpLow = "SFC"
                else:
                    if lowType == "":
                        sTmpLow = "{0}{1}".format(ase.uomDistVerLower.string, ase.valDistVerLower.string)
                    else:
                        sTmpLow = "{0}{1} {2}".format(ase.uomDistVerLower.string, ase.valDistVerLower.string, lowType)
                    if ase.codeDistVerLower.string == "HEI":
                        orgLow = low
                        theAirspace.update({"ordinalLowerM": orgLow})
                        low += aGroundEstimatedHeight[1]    #=lAltMed
                sZoneAltL   =  "{0}".format(sTmpLow)
                sZoneAltL_m = "{0}m".format(low)
                sZoneAltL_a = "{0}({1}m)".format(sTmpLow, low)
            elif ase.uomDistVerLower.string == "FT":
                low = int(float(ase.valDistVerLower.string) * aixmReader.CONST.ft)
                if low == 0:
                    sTmpLow = "SFC"
                else:
                    if lowType == "":
                        sTmpLow = "{0}{1}".format(ase.valDistVerLower.string, ase.uomDistVerLower.string)
                    else:
                        sTmpLow = "{0}{1} {2}".format(ase.valDistVerLower.string, ase.uomDistVerLower.string, lowType)
                    if ase.codeDistVerLower.string == "HEI":
                        orgLow = low
                        theAirspace.update({"ordinalLowerM": orgLow})
                        low += aGroundEstimatedHeight[1]    #=lAltMed
                sZoneAltL   = "{0}".format(sTmpLow)
                sZoneAltL_m = "{0}m".format(low)
                sZoneAltL_a = "{0}({1}m)".format(sTmpLow, low)
            elif ase.uomDistVerLower.string in ["M", "SM"]:
                low = int(ase.valDistVerLower.string)
                if low == 0:
                    sTmpLow = "SFC"
                else:
                    if lowType == "":
                        sTmpLow = "{0}M".format(ase.valDistVerLower.string)
                    else:
                        sTmpLow = "{0}M {1}".format(ase.valDistVerLower.string, lowType)
                    if ase.codeDistVerLower.string == "HEI":
                        orgLow = low
                        theAirspace.update({"ordinalLowerM": orgLow})
                        low += aGroundEstimatedHeight[1]    #=lAltMed
                        sZoneAltL_m += "{0}m".format(low)
                sZoneAltL   = "{0}".format(sTmpLow)
                sZoneAltL_m = "{0}m".format(low)
                sZoneAltL_a = "{0}({1}m)".format(sTmpLow, low)
            if low is None:
               self.oCtrl.oLog.error("low is None: id={0} NameV={1} Lower={2}".format(sZoneUId, theAirspace["nameV"], ase.valDistVerLower.string), outConsole=True)
               low=0

        #Détermination du plafond de la zone
        sZoneAltU = sZoneAltU_m = sZoneAltU_a = ""
        up = orgUp = 0
        if ase.uomDistVerUpper is not None:
            if ase.codeDistVerUpper is None:
                if ase.valDistVerUpper.string == "0":
                    upType = "ASFC"
                else:
                    upType = ""
            if ase.codeDistVerUpper.string == "ALT":
                upType = "AMSL"
            elif ase.codeDistVerUpper.string == "HEI":
                upType = "ASFC"
            else:
                upType = ""
            up = None
            if ase.uomDistVerUpper.string == "FL":
                up = int(float(ase.valDistVerUpper.string) * aixmReader.CONST.ft * 100)
                if upType == "":
                    sTmpUp = "{0}{1}".format(ase.uomDistVerUpper.string, ase.valDistVerUpper.string)
                else:
                    sTmpUp = "{0}{1} {2}".format(ase.uomDistVerUpper.string, ase.valDistVerUpper.string, upType)
                if ase.codeDistVerUpper.string == "HEI":
                    orgUp = up
                    theAirspace.update({"ordinalUpperM": orgUp})
                    up += aGroundEstimatedHeight[2]    #=lAltRet
                sZoneAltU   = sTmpUp
                sZoneAltU_m = "{0}m".format(up)
                sZoneAltU_a = "{0}({1}m)".format(sTmpUp, up)
            elif ase.uomDistVerUpper.string == "FT":
                up = int(float(ase.valDistVerUpper.string) * aixmReader.CONST.ft)
                if upType == "":
                    sTmpUp = "{0}{1}".format(ase.valDistVerUpper.string, ase.uomDistVerUpper.string)
                else:
                    sTmpUp = "{0}{1} {2}".format(ase.valDistVerUpper.string, ase.uomDistVerUpper.string, upType)
                if ase.codeDistVerUpper.string == "HEI":
                    orgUp = up
                    theAirspace.update({"ordinalUpperM": orgUp})
                    up += aGroundEstimatedHeight[2]    #=lAltRet
                sZoneAltU   = sTmpUp
                sZoneAltU_m = "{0}m".format(up)
                sZoneAltU_a = "{0}({1}m)".format(sTmpUp, up)
            elif ase.uomDistVerUpper.string in ["M", "SM"]:
                up = int(ase.valDistVerUpper.string)
                if upType == "":
                    sTmpUp = "{0}M".format(ase.valDistVerUpper.string)
                else:
                    sTmpUp = "{0}M {2}".format(ase.valDistVerUpper.string, upType)
                if ase.codeDistVerUpper.string == "HEI":
                    orgUp = up
                    theAirspace.update({"ordinalUpperM": orgUp})
                    up += aGroundEstimatedHeight[2]    #=lAltRet
                sZoneAltU   = "{0}".format(sTmpUp)
                sZoneAltU_m = "{0}m".format(up)
                sZoneAltU_a = "{0}({1}m)".format(sTmpUp, up)
            if up is None:
                self.oCtrl.oLog.error("up is None: id={0} NameV={1} Upper={2}".format(sZoneUId, theAirspace["nameV"], ase.valDistVerUpper.string), outConsole=True)
                up=99999

        #Verrification de conformité des altitudes
        if up <= low:
            #Correction de l'altitude après analyse via référentiel
            if       ("ordinalLowerM" in theAirspace) and     ("ordinalUpperM" in theAirspace):
                low = orgLow + aGroundEstimatedHeight[0]    #=lAltMin
                if up <= low:
                    up = orgUp + aGroundEstimatedHeight[3]    #=lAltMax
                if up <= low:
                    low=0
                    self.oCtrl.oLog.warning("Forced height reset: Upper <= Lower; up={0} low={1} for id={2} NameV={3}".format(up, low, sZoneUId, theAirspace["name"]), outConsole=False)
                sZoneAltL_m = "{0}m".format(low)
                sZoneAltL_a = "{0}({1}m)".format(sTmpLow, low)
                sZoneAltU_m = "{0}m".format(up)
                sZoneAltU_a = "{0}({1}m)".format(sTmpUp, up)
            elif     ("ordinalLowerM" in theAirspace) and not ("ordinalUpperM" in theAirspace):
                low = orgLow + aGroundEstimatedHeight[0]    #=lAltMin
                if up <= low:
                    low=0
                    self.oCtrl.oLog.warning("Forced height reset: Upper <= Lower; up={0} low={1} for id={2} NameV={3}".format(up, low, sZoneUId, theAirspace["name"]), outConsole=False)
                sZoneAltL_m = "{0}m".format(low)
                sZoneAltL_a = "{0}({1}m)".format(sTmpLow, low)
            else:
                self.oCtrl.oLog.error("Height error: Upper <= Lower; up={0} low={1} for id={2} NameV={3}".format(up, low, sZoneUId, theAirspace["name"]), outConsole=True)

        sZoneAlt    = "[" + sZoneAltL   + "/" + sZoneAltU   + "]"
        sZoneAlt_m  = "[" + sZoneAltL_m + "/" + sZoneAltU_m + "]"
        sZoneAlt_a  = "[" + sZoneAltL_a + "/" + sZoneAltU_a + "]"
        
        #Formatage des Plancher/Plafonnd de zone
        if ("ordinalUpperM" in theAirspace):
            theAirspace.update({"ordinalUpperM": theAirspace["ordinalUpperM"]})
        if ("ordinalLowerM" in theAirspace):
            theAirspace.update({"ordinalLowerM": theAirspace["ordinalLowerM"]})
        if ("ordinalLowerM" in theAirspace) or ("ordinalUpperM" in theAirspace):
            theAirspace.update({"groundEstimatedHeight": aGroundEstimatedHeight})
        theAirspace.update({"upperM": up})
        theAirspace.update({"lowerM": low})
        theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"alt"  :sZoneAlt})
        theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"altM":sZoneAlt_m})
        theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"altV":sZoneAlt_a})      #Altitute complète (type V=Verbose)
        
        return low, up
