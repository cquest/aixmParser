#!/usr/bin/env python3

import bpaTools
import aixmReader

class AixmAirspaces4_5:
    
    def __init__(self, oCtrl=None):
        bpaTools.initEvent(__file__, oCtrl.oLog)
        self.oCtrl = oCtrl                  #Référence du contrôleur appelant
        self.oAirspaces = dict()            #Global collection
        self.oAirspacesBorders = dict()     #Global collection
        #self.oDebug = dict()               #Global debug
        self.oIdxAseUid2UniUid = dict()
        self.oIdxUniUid2OrgName = dict()
        self.oIdxAseUid2AseUid = dict()
        self.oIdxAseUid2AseUid2 = dict()
        return


    def initAirspaceIdx(self):
        sTitle = "Airspaces Groups"
        sXmlTag = "Adg"
        if not self.oCtrl.oAixm.doc.find(sXmlTag):
            sMsg = "Missing tags {0} - {1}".format(sXmlTag, sTitle)
            self.oCtrl.oLog.warning(sMsg, outConsole=True)
        else:
            sMsg = "Indexing {0} - {1}".format(sXmlTag, sTitle)
            self.oCtrl.oLog.info(sMsg)
            oList = self.oCtrl.oAixm.doc.find_all(sXmlTag)
            barre = bpaTools.ProgressBar(len(oList), 20, title=sMsg)
            idx = 0
            for o in oList:
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
            self.oCtrl.oLog.warning(sMsg, outConsole=True)
        else:
            sMsg = "Indexing {0} - {1}".format(sXmlTag, sTitle)
            self.oCtrl.oLog.info(sMsg)
            oList = self.oCtrl.oAixm.doc.find_all(sXmlTag)
            barre = bpaTools.ProgressBar(len(oList), 20, title=sMsg)
            idx = 0
            for o in oList:
                self.oIdxAseUid2UniUid.update({o.SaeUid.AseUid["mid"]:o.SaeUid.SerUid.UniUid["mid"]})
                barre.update(idx)
            barre.reset()
        
        sTitle = "Organizations"
        sXmlTag = "Uni"
        if not self.oCtrl.oAixm.doc.find(sXmlTag):
            sMsg = "Missing tags {0} - {1}".format(sXmlTag, sTitle)
            self.oCtrl.oLog.warning(sMsg, outConsole=True)
        else:
            sMsg = "Indexing {0} - {1}".format(sXmlTag, sTitle)
            self.oCtrl.oLog.info(sMsg)
            oList = self.oCtrl.oAixm.doc.find_all(sXmlTag)
            barre = bpaTools.ProgressBar(len(oList), 20, title=sMsg)
            idx = 0
            for o in oList:
                self.oIdxUniUid2OrgName.update({o.UniUid["mid"]:o.OrgUid.txtName.string})
                barre.update(idx)
            barre.reset()
            
        sTitle = "Airspaces Borders"
        sXmlTag = "Abd"
        if not self.oCtrl.oAixm.doc.find(sXmlTag):
            sMsg = "Missing tags {0} - {1}".format(sXmlTag, sTitle)
            self.oCtrl.oLog.warning(sMsg, outConsole=True)
        else:
            sMsg = "Indexing {0} - {1}".format(sXmlTag, sTitle)
            self.oCtrl.oLog.info(sMsg)
            oList = self.oCtrl.oAixm.doc.find_all(sXmlTag)
            barre = bpaTools.ProgressBar(len(oList), 20, title=sMsg)
            idx = 0
            for o in oList:
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
    
    
    def getAirspacesCatalog(self, sFilename):
        ret = {"type":"Aeronautical areas catalog", "headerFile":self.oCtrl.oAixmTools.getJsonPropHeaderFile(sFilename), "catalog":self.oAirspaces}
        return ret


    def saveAirspacesCalalog(self):
        #Phase 1 : JSON calatlog
        sFilename = "airspacesCatalog"
        cat = self.getAirspacesCatalog(sFilename)              #Construct Catalog on CSV format
        self.oCtrl.oAixmTools.writeJsonFile(sFilename, cat)    #Save Catalog on Json format
        
        #Phase 2 : CSV calatlog
        #Phase 2.1 : Header CSV file
        csv = csvCol = csvVal = ""
        oHeader = cat["headerFile"]
        for key,val in oHeader.items():
            csvCol += '{0};'.format(key)
            csvVal += '{0};'.format(val)
        csv = "<Header file>\n{0}\n{1}\n\n<Content>\n".format(csvCol, csvVal)
        
        #Phase 2.2 : Construct a global index on columns (collect all columns in contents for complete header of CSV file...)
        #oCols avec initialisation d'une table d'index avec imposition de l'ordonnancement de colonnes choisies
        oCols = {"zoneType":0, "groupZone":0, "vfrZone":0, "freeFlightZone":0, "orgName":0, "UId":0, "id":0, "type":0, "class":0, "name":0, "lowerM":0, "upperM":0, "nameV":0, "alt":0, "altM":0, "altV":0, "exceptSAT":0, "exceptSUN":0, "exceptHOL":0}
        oCatalog = cat["catalog"]
        for key0,val0 in oCatalog.items():
            for key1,val1 in val0.items():
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
        self.oCtrl.oAixmTools.writeTextFile(sFilename, csv, "csv")    #Save Catalog on CSV format
        return
    
    
    def loadAirspacesCatalog(self):
        sTitle = "Airspaces Catalog"
        sXmlTag = "Ase"
        
        sMsg = "Loading {0} - {1}".format(sXmlTag, sTitle)
        self.oCtrl.oLog.info(sMsg)
        oList = self.oCtrl.oAixm.doc.find_all(sXmlTag)
        barre = bpaTools.ProgressBar(len(oList), 20, title=sMsg)
        idx = 0
        for o in oList:
            self.loadAirspace(o)
            barre.update(idx)
        barre.reset()
        return


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
        sUniUid = orgName = None
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
            
        #--------------------------------
        #Détermination de la Classe de la zone
        if ase.codeClass:
            classZone = ase.codeClass.string
        else:
            classZone = ase.AseUid.codeType.string
        typeZone = ase.AseUid.codeType.string
        theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"type":typeZone})
        theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"class":classZone})
        
        #ase.AseUid.codeType or CODE_TYPE_ASE Format
        #ICAO DEPRECATED-4.0  [ICAO Region (for example, EUR, NAT, etc).]
        #ECAC DEPRECATED-4.0  [ECAC Region.]
        #CFMU DEPRECATED-4.0  [CFMU Area.]
        #IFPS DEPRECATED-4.0  [IFPS Area.]
        #TACT DEPRECATED-4.0  [TACT Area.]
        #NAS [National Airspace System.]
        #NAS-P DEPRECATED-4.0  [A part of a National Airspace System.]
        #FIR [Flight Information Region.]
        #FIR-P [Part of an FIR.]
        #UIR [Upper Flight Information Region.]
        #UIR-P [Part of a UIR.]
        #CTA [Control Area.]
        #CTA-P [Part of a CTA.]
        #OCA [Oceanic Control Area.]
        #OCA-P [Partial OTA.]
        #UTA [Upper Control Area.]
        #UTA-P [Part of UTA.]
        #TMA [Terminal Control Area.]
        #TMA-P [Part of TMA.]
        #CTR [Control Zone.]
        #CTR-P [Part of CTR.]
        #CLASS [Airspace having a specified class.]
        #ATZ DEPRECATED-4.0  [Aerodrome Traffic Zone.]
        #ATZ-P DEPRECATED-4.0  [Part of ATZ.]
        #MNPSA DEPRECATED-4.0  [Minimum Navigation Performance Specifications Area.]
        #MNPSA-P DEPRECATED-4.0  [Part of MNPSA.]
        #OTA [Oceanic Transition Area.]
        #SECTOR [Control Sector.]
        #SECTOR-C [Temporarily Consolidated (Collapsed ) Sector.]
        #TSA [Temporary Segregated Area (FUA).]
        #TRA [Temporary Reserved Area (FUA).]
        #CBA [Cross Border Area (FUA).]
        #RCA [Reduced Co-ordination Airspace Procedure (FUA).]
        #RAS [Regulated Airspace (not otherwise covered).]
        #CDA DEPRECATED-4.0  [Client Defined Airspace.]
        #AWY [Airway (corridor)..]
        #RTECL DEPRECATED-4.0  [Route Centreline.]
        #P [Prohibited Area.]
        #R [Restricted Area.]
        #R-AMC [AMC Manageable Restricted Area.]
        #D [Danger Area.]
        #D-AMC [AMC Manageable Danger Area.]
        #D-OTHER [Activities of dangerous nature (other than a Danger Area).] --> BIRD AREA, GLIDER AREA etc../..
        #MIL DEPRECATED-4.0  [Military Training/Exercise Area.]
        #ADIZ [Air Defense Identification Zone.]
        #HTZ DEPRECATED-4.0  [Helicopter Traffic Zone.]
        #OIL DEPRECATED-4.0  [Oil Field.]
        #BIRD DEPRECATED-4.0  [Bird Migration Area.]
        #SPORT DEPRECATED-4.0  [Aerial Sporting/Recreational Area.]
        #LMA DEPRECATED-4.0  [Limited Airspace (in general).]
        #A [Alert Area.]
        #W [Warning Area.]
        #PROTECT [Airspace protected from specific air traffic.]
        #AMA [Minimum Altitude Area.]
        #ASR [Altimeter Setting Region.]
        #NO-FIR [Airspace for which not even an FIR is defined.]
        #POLITICAL [Political/administrative area.]
        #PART [Part of an airspace (used in airspace aggregations).]

        #--------------------------------
        #Classification détaillée pour préfiltrage des zones
        #if sZoneUId == "1563421":
        #    print(theAirspace["vfrZone"], theAirspace["freeFlightZone"])        
        aFreeFlightZone = ["A","B","C","D","R","P","D","W","CTA","CTA-P","CTR","CTR-P","TMA","TMA-P"]   #Pour cartographie Vol-Libre / For FreeFlight map
        aVfrZone = aFreeFlightZone + ["E","F","G"]                                              #Pour cartographie VFR / For VFR map
        #aVfrTypeZone = ["CTA","CTA-P","CTR","CTR-P","TMA","TMA-P"]                                  #Pour cartographie VFR / For VFR map
        vfrZone = bool((not groupZone) and typeZone in aVfrZone)
        vfrZone = bool((vfrZone) and classZone in aVfrZone)
        freeFlightZone = bool((vfrZone) and classZone in aFreeFlightZone)
        #theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"ifrZone":(not vfrZone)})       #No use ../..
        theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"vfrZone":vfrZone})
        theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"freeFlightZone":freeFlightZone})

            #Case of vfrZone=False: Enumeration of <ase.AseUid.codeType.string> values
            #    SIA-FRA - dict_values(['TMA', 'D-OTHER', 'CTA', 'UTA', 'CTR', 'OCA', 'SECTOR', 'R-AMC', 'SECTOR-C', 'CBA', 'TSA', 'TRA', 'RAS'])
            #    Eur-FRA - dict_values(['UIR', 'FIR', 'RAS', 'CTR', 'TMA', 'D-AMC', 'SECTOR', 'PART', 'TMA-P', 'D-OTHER', 'CBA', 'OCA', 'CTA', 'PROTECT', 'TSA', 'TRA', 'R-AMC', 'SECTOR-C', 'UTA'])
            #    Eur-Europe -   dict_values(['PART', 'D-OTHER', 'CTA', 'UIR', 'OCA-P', 'OCA', 'FIR', 'FIR-P', 'RAS', 'SECTOR', 'UTA', 'TMA', 'TMA-P', 'TRA', 'CTR', 'CBA', 'PROTECT', 'TSA', 'R-AMC', 'SECTOR-C', 'D-AMC', 'AMA', 'CTR-P', 'POLITICAL', 'ADIZ', 'CTA-P', 'NO-FIR', 'AWY', 'UIR-P'])
            #if (not ase.codeClass) and (not ase.AseUid.codeType.string in ["A","B","C","D","E","F","G","R","P","W"]):
            #    self.oDebug[ase.AseUid.codeType.string] = ase.AseUid.codeType.string

        #--------------------------------
        #Détermination du Nommage de la zone
        if ase.txtName:
            theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"name":ase.txtName.string})
        else:
            theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"name":ase.AseUid.codeId.string})

        #Précision d'un libellé complet (type V=Verbose)
        sLongName = "[{0}]".format(theAirspace["class"])
        if theAirspace["type"] != theAirspace["class"]:
            sLongName = "{0} {1}".format(sLongName, theAirspace["type"])
        sLongName = "{0} {1} ({2})".format(sLongName, theAirspace["name"], theAirspace["id"])
        theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"nameV":sLongName})

        #--------------------------------
        #Décodage des plancher/Plafond avec estimlation des altitudes en mètres (exclusion des regroupement de zones qui n'ont pas ces caractéristiques...)
        if not theAirspace["groupZone"]:
            theAirspace = self.oCtrl.oAixmTools.addProperty(theAirspace, ase, "codeDistVerUpper", "upperType", optional=True)
            theAirspace = self.oCtrl.oAixmTools.addProperty(theAirspace, ase, "valDistVerUpper", "upperValue", optional=True)
            theAirspace = self.oCtrl.oAixmTools.addProperty(theAirspace, ase, "uomDistVerUpper", "upperUnit", optional=True)
            theAirspace = self.oCtrl.oAixmTools.addProperty(theAirspace, ase, "codeDistVerLower", "lowerType", optional=True)
            theAirspace = self.oCtrl.oAixmTools.addProperty(theAirspace, ase, "valDistVerLower", "lowerValue", optional=True)
            theAirspace = self.oCtrl.oAixmTools.addProperty(theAirspace, ase, "uomDistVerLower", "lowerUnit", optional=True)

            sZoneAlt = sZoneAlt_m = sZoneAlt_a = "["
            low=0
            #ase.uomDistVerLower or UOM_DIST_VER format:
            #    FT [Feet.]  
            #    M [Metres.]
            #    FL [Flight level in hundreds of feet..]  
            #    SM [Standard metres (tens of metres).]  
            if ase.uomDistVerLower is not None:
                low = None
                if ase.uomDistVerLower.string == "FL":
                    low = int(float(ase.valDistVerLower.string) * aixmReader.CONST.ft * 100)
                    if low == 0:
                        sTmp = "SFC"
                    else:
                        sTmp = "{0}{1}".format(ase.uomDistVerLower.string, ase.valDistVerLower.string)
                    sZoneAlt   +=  "{0}/".format(sTmp)
                    sZoneAlt_m += "{0}m/".format(low)
                    sZoneAlt_a += "{0}({1}m)/".format(sTmp, low)
                elif ase.uomDistVerLower.string == "FT":
                    low = int(float(ase.valDistVerLower.string) * aixmReader.CONST.ft)
                    if low == 0:
                        sTmp = "SFC"
                    else:
                        sTmp = "{1}{0}".format(ase.uomDistVerLower.string, ase.valDistVerLower.string)
                    sZoneAlt   += "{0}/".format(sTmp)
                    sZoneAlt_m += "{0}m/".format(low)
                    sZoneAlt_a += "{0}({1}m)/".format(sTmp, low)
                elif ase.uomDistVerLower.string in ["M", "SM"]:
                    low = int(ase.valDistVerLower.string)
                    sZoneAlt   += "{0}m/".format(low)
                    sZoneAlt_m += "{0}m/".format(low)
                    sZoneAlt_a += "{0}m/".format(low)
                if low is None:
                   self.oCtrl.oLog.error("low is None: id={0} NameV={1} Lower={2}".format(sZoneUId, theAirspace["nameV"], ase.valDistVerLower.string), outConsole=True)
                   low=0
                else:
                     theAirspace.update({"lowerM": low})

            if ase.uomDistVerUpper is not None:
                up = None
                if ase.uomDistVerUpper.string == "FL":
                    up = int(float(ase.valDistVerUpper.string) * aixmReader.CONST.ft * 100)
                    sTmp = "{0}{1}".format(ase.uomDistVerUpper.string, ase.valDistVerUpper.string)
                    sZoneAlt   += sTmp
                    sZoneAlt_m += "{0}m".format(up)
                    sZoneAlt_a += "{0}({1}m)".format(sTmp, up)
                elif ase.uomDistVerUpper.string == "FT":
                    up = int(float(ase.valDistVerUpper.string) * aixmReader.CONST.ft)
                    sTmp = "{1}{0}".format(ase.uomDistVerUpper.string, ase.valDistVerUpper.string)
                    sZoneAlt   += sTmp
                    sZoneAlt_m += "{0}m".format(up)
                    sZoneAlt_a += "{0}({1}m)".format(sTmp, up)
                elif ase.uomDistVerUpper.string in ["M", "SM"]:
                    up = int(ase.valDistVerUpper.string)
                    sZoneAlt   += "{0}m".format(up)
                    sZoneAlt_m += "{0}m".format(up)
                    sZoneAlt_a += "{0}m".format(up)
                if up is None:
                    self.oCtrl.oLog.error("up is None: id={0} NameV={1} Upper={2}".format(sZoneUId, theAirspace["nameV"], ase.valDistVerUpper.string), outConsole=True)
                    up=99999
                else:
                    theAirspace.update({"upperM": up})

            sZoneAlt   += "]"
            sZoneAlt_m += "]"
            sZoneAlt_a += "]"
            theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"alt"  :sZoneAlt})
            theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"altM":sZoneAlt_m})
            theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"altV":sZoneAlt_a})      #Altitute complète (type V=Verbose)

        #--------------------------------
        #Eventuel filtrage complémentaire pour requalification des zones 'vfrZone' & 'freeFlightZone' (zones spécifiques Vol-Libre Parapente/Delta)
        #if sZoneUId == "1563421":
        #    print(theAirspace["vfrZone"], theAirspace["freeFlightZone"])
        if (theAirspace["vfrZone"]) and ("lowerValue" in theAirspace) and ("upperValue" in theAirspace):
            bFilter = low>=3505                                             #Filtrer toutes les zones dont le plancher débute au dessus FL115/3505m
            bFilter = bFilter or (low==0 and up>=3505)                      #Filtrer les zones qui portent sur tous les étages
            #theAirspace.update({"altFilter":bFilter})
            if theAirspace["vfrZone"] and bFilter:
                theAirspace.update({"vfrZone":False})
            if theAirspace["freeFlightZone"] and bFilter:
                theAirspace.update({"freeFlightZone":False})
            #NE JAMAIS FILTRER: les éventuelles extensions de vol classées "E"; dont le planfond va au delà de FL115/3505m               
            if classZone=="E" and up>3505:
                #theAirspace.update({"altAddE":True})
                if not theAirspace["vfrZone"]:
                    theAirspace.update({"vfrZone":True})
                if not theAirspace["freeFlightZone"]:
                    theAirspace.update({"freeFlightZone":True})
                    
        #--------------------------------
        #Zones complémentaire avec remarques et description des activations
        if ase.Att:
            theAirspace = self.oCtrl.oAixmTools.addProperty(theAirspace, ase.Att, "codeWorkHr", "activationCode", optional=True)
            theAirspace = self.oCtrl.oAixmTools.addProperty(theAirspace, ase.Att, "txtRmkWorkHr", "activationDesc", optional=True)
        theAirspace = self.oCtrl.oAixmTools.addProperty(theAirspace, ase, "txtRmk", "desc", optional=True)

        #--------------------------------
        #Traitement spécifique pour signaler les zones non-activables...
        activationDesc=""
        if ase.Att: activationDesc = str(ase.Att.txtRmkWorkHr).lower()
        activationDesc = activationDesc + str(ase.txtRmk).lower()
        bExcept = False
        if not bExcept:
            #Non activation = Sauf SAM, DIM et JF // except SAT, SUN and public HOL
            bExcept = bool(activationDesc.find("sauf SAM, DIM et JF".lower()) > 0)
            bExcept = bExcept or bool(activationDesc.find("sauf WE et JF".lower()) > 0)
            bExcept = bExcept or bool(activationDesc.find("except SAT, SUN and HOL".lower()) > 0)
            bExcept = bExcept or bool(activationDesc.find("except SAT, SUN and public HOL".lower()) > 0)
            if bExcept:
                self.oCtrl.oLog.info("except-SDJF: id={0} NameV={1}".format(sZoneUId, theAirspace["nameV"]))
                theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"exceptSAT":"Yes"})
                theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"exceptSUN":"Yes"})
                theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"exceptHOL":"Yes"})
        if not bExcept:
            #Non activation = Sauf SAM, DIM // Except SAT and SUN
            bExcept = bool(activationDesc.find("sauf SAM, DIM".lower()) > 0)
            bExcept = bExcept or bool(activationDesc.find("sauf WE".lower()) > 0)
            bExcept = bExcept or bool(activationDesc.find("except SAT, SUN".lower()) > 0)
            bExcept = bExcept or bool(activationDesc.find("except SAT and SUN".lower()) > 0)
            if bExcept:
                self.oCtrl.oLog.info("except-SD: id={0} NameV={1}".format(sZoneUId, theAirspace["nameV"]))
                theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"exceptSAT":"Yes"})
                theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"exceptSUN":"Yes"})
        if not bExcept:
            #Non activation = Sauf DIM et JF // except SUN and public HOL
            bExcept = bool(activationDesc.find("sauf DIM et JF".lower()) > 0)
            bExcept = bExcept or bool(activationDesc.find("except SUN and HOL".lower()) > 0)
            bExcept = bExcept or bool(activationDesc.find("except SUN and public HOL".lower()) > 0)
            if bExcept:
                self.oCtrl.oLog.info("except-DJF: id={0} NameV={1}".format(sZoneUId, theAirspace["nameV"]))
                theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"exceptSUN":"Yes"})
                theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"exceptHOL":"Yes"})                   
        if not bExcept:
            #Non activation = Sauf SAM // Except SAT
            bExcept = bool(activationDesc.find("sauf SAM".lower()) > 0)
            bExcept = bExcept or bool(activationDesc.find("except SAT".lower()) > 0)
            if bExcept:
                self.oCtrl.oLog.info("except-S: id={0} NameV={1}".format(sZoneUId, theAirspace["nameV"]))
                theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"exceptSAT":"Yes"})
            #Non activation = Sauf DIM // Except SUN
            bExcept = bool(activationDesc.find("sauf DIM".lower()) > 0)
            bExcept = bExcept or bool(activationDesc.find("except SUN".lower()) > 0)
            if bExcept:
                self.oCtrl.oLog.info("except-D: id={0} NameV={1}".format(sZoneUId, theAirspace["nameV"]))
                theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"exceptSUN":"Yes"})           
            #Non activation = Sauf JF // Except HOL
            bExcept = bool(activationDesc.find("sauf JF".lower()) > 0)
            bExcept = bExcept or bool(activationDesc.find("except HOL".lower()) > 0)
            bExcept = bExcept or bool(activationDesc.find("except public HOL".lower()) > 0)
            if bExcept:
                self.oCtrl.oLog.info("except-JF: id={0} NameV={1}".format(sZoneUId, theAirspace["nameV"]))
                theAirspace = self.oCtrl.oAixmTools.addField(theAirspace, {"exceptHOL":"Yes"})   
        
        #--------------------------------    
        #Ajout des propriétés pour colorisation de la zone uniquement en mode Draft (car la version finale sous navigateur integre la techno CSS)
        #if self.oCtrl.Draft:
        self.oCtrl.oAixmTools.addColorProperties(theAirspace)
        
        self.oAirspaces[sZoneUId] = theAirspace         #Store new item in global collection
        return

