#!/usr/bin/env python3
from myXml import Xml


def cleanCoords(sCoords:str="") -> str:
    sCoords = sCoords.replace(":","")
    sCoords = sCoords.replace("°","")
    sCoords = sCoords.replace("'","")
    sCoords = sCoords.replace("’","")
    sCoords = sCoords.replace("\"","")
    sCoords = sCoords.replace(" N","N")
    sCoords = sCoords.replace(" S","S")
    sCoords = sCoords.replace(" E","E")
    sCoords = sCoords.replace(" W","W")
    return sCoords

def getCoords(sCoords:str="") -> list:
    aGlobalCoords:list = []
    sCoords = cleanCoords(sCoords)
    aSep:list = [",","-","–"]
    sSep:str = ""
    for sTokenSep in aSep:
        iPos = sCoords.find(sTokenSep)
        if iPos>0:
            sSep = sTokenSep
            break
    if sSep:
        sCoords = sCoords.replace(sSep,"-")
        sCoords = sCoords.replace(" -","-")
        sCoords = sCoords.replace("- ","-")
        aLines = sCoords.split("\n")
        for sLine in aLines:
            sLine = sLine.strip()
            aCoords:list = sLine.split("-")
            if len(aCoords)==2:
                aTocken:list = ["N","S","E","W"]
                sTocken = ".00"
                for iIdx in range(0, len(aCoords)):
                    sCoord = aCoords[iIdx]
                    iPos = sCoord.find(sTocken)
                    iStart = iPos+len(sTocken)
                    if iPos>0 and sCoord[iStart:iStart+1] in aTocken:
                        aCoords[iIdx] = sCoord.replace(sTocken,"")
                if len(aCoords[1])==7:                          #Ctrl format
                    aCoords[1] = "0" + aCoords[1]               #format '032624W' to '0032624W'
                sTocken = "."
                if  (len(aCoords[0])==7 or aCoords[0].find(sTocken)>0) and (len(aCoords[1])==8 or aCoords[1].find(sTocken)>0):
                    aGlobalCoords.append(aCoords)
                else:
                    aGlobalCoords.append(["getCoords() Error in coords: '" + sLine +"'"])
            elif sLine!="":
                aGlobalCoords.append(["getCoords() Comment: '" + sLine +"'"])

    if not aGlobalCoords:
        print("getCoords() Error in coords:", sCoords)
    return aGlobalCoords


def makeAixm(sCircle:str="", sRadius:str="", sAvx:str="") -> None:
    if sCircle:
        #<Circle>
		#	<geoLatCen>450814N</geoLatCen>
		#	<geoLongCen>0010942W</geoLongCen>
		#	<codeDatum>WGE</codeDatum>
		#	<valRadius>16</valRadius>
		#	<uomRadius>NM</uomRadius>
        #</Circle>
        aCoords = getCoords(sCircle)
        if len(aCoords)!=1:
            return

    if sAvx:
		#<Avx>
		#	<codeType>GRC</codeType>
		#	<geoLat>442524N</geoLat>
		#	<geoLong>0010215W</geoLong>
		#	<codeDatum>WGE</codeDatum>
		#</Avx>
		#<Avx> Nota. CWA=ClockWize  & Arc / CCA=Counter Clockwise Arc
		#	<codeType>CWA</codeType>
		#	<geoLat>442705N</geoLat>
		#	<geoLong>0012424W</geoLong>
		#	<codeDatum>WGE</codeDatum>
		#	<geoLatArc>442532N</geoLatArc>
		#	<geoLongArc>0011323W</geoLongArc>
		#	<valRadiusArc>8</valRadiusArc>
		#	<uomRadiusArc>NM</uomRadiusArc>
		#</Avx>
        aCoords = getCoords(sAvx)
        if len(aCoords)==0:
            return

    oXml:Xml = Xml()
    #oRoot = oXml.createRoot("AIXM-Snapshot")
    #oXml.addAttrib(oRoot, "xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    #oXml.addAttrib(oRoot, "xsi:noNamespaceSchemaLocation", "../_aixm_xsd-4.5b/AIXM-Snapshot.xsd")
    #oXml.addAttrib(oRoot, "origin", "BPa")
    #oXml.addAttrib(oRoot, "version", "4.5")
    #oAbd = oXml.addTag(oRoot, "Abd")
    oAbd = oXml.createRoot("Abd")
    oAbdUid = oXml.addTag(oAbd, "AbdUid")
    oXml.addAttrib(oAbdUid, "mid", "BPa-FR-SIA-SUPAIP-2021-???-?name?-?type?")
    oAseUid = oXml.addTag(oAbdUid, "AseUid")
    oXml.addAttrib(oAseUid, "mid", "BPa-FR-SIA-SUPAIP-2021-???-?name?-?type?")
    oXml.addTag(oAseUid, "codeType", sValue="???")
    oXml.addTag(oAseUid, "codeId", sValue="???")

    if sCircle:
        oCircle = oXml.addTag(oAbd, "Circle")
        oXml.addTag(oCircle, "geoLatCen", sValue=aCoords[0][0])
        oXml.addTag(oCircle, "geoLongCen", sValue=aCoords[0][1])
        oXml.addTag(oCircle, "codeDatum", sValue="WGE")
        oXml.addTag(oCircle, "valRadius", sValue=sRadius)
        oXml.addTag(oCircle, "uomRadius", sValue="NM")      #In Miles-Nautic

    if sAvx:
        for oCoords in aCoords:
            if len(oCoords)==1:
                oXml.addComment(oAbd, oCoords)
            elif len(oCoords)==2:
                oAvx = oXml.addTag(oAbd, "Avx")
                oXml.addTag(oAvx, "codeType", sValue="GRC")
                oXml.addTag(oAvx, "geoLat", sValue=oCoords[0])
                oXml.addTag(oAvx, "geoLong", sValue=oCoords[1])
                oXml.addTag(oAvx, "codeDatum", sValue="WGE")

    print(oXml.toString("\t"))
    return



if __name__ == '__main__':

    sRadius:str =   "16"     #In MN Miles Nautic  - https://www.google.com/search?client=firefox-b-d&q=convertion+milenautique
    sCircle:str =   ""#"43°08'19.00'' N, 001°54'23.00'' E"
    sAvx:str    =   """
49°06'50'' N, 006°02'37'' E
49°07'17'' N, 006°03'59'' E
49°07'02'' N, 006°04'19'' E
49°06'53'' N, 006°04'02'' E
49°06'02'' N, 006°04'04'' E
49°05'52'' N, 006°03'16'' E
49°06'50'' N, 006°02'37'' E
                    """

    sCircle = sCircle.strip()
    sAvx = sAvx.strip()
    if sCircle: makeAixm(sCircle=sCircle, sRadius=sRadius)
    if sAvx: makeAixm(sAvx=sAvx)

