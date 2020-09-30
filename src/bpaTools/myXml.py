#!/usr/bin/env python3

import xml.etree.ElementTree as ET
from xml.etree.ElementTree import tostring
from xml.dom import minidom

class Xml:
     
    def __init__(self)-> None:
        self.oRoot:ET.Element = None
        return    

    @property
    def root(self):
        return self.oRoot

    def dump(self):
        return ET.dump(self.oRoot)
    
    def toString(self):
        ET.tostring(self.oRoot, method='xml')

    def createRoot(self, sTagName:str, sXmlns:str=None, sId:str=None, sValue:str=None):
        self.oRoot = ET.Element(sTagName)
        if sXmlns:
            self.oRoot.set("xmlns", sXmlns)
        if sId:
            self.oRoot.set("id", sId)
        if sValue:
            self.oRoot.text = sValue
        return self.oRoot

    def addAttrib(self, oTag, sAttName:str, sValue:str=None):
        if sAttName:
            oTag.set(sAttName, sValue)
        return

    def addTag(self, oParent, sTagName:str, sXmlns:str=None, sId:str=None, sValue:str=None):
        oTag = ET.SubElement(oParent, sTagName)
        if sXmlns:
            oTag.set("xmlns", sXmlns)
        if sId:
            oTag.set("id", sId)
        if sValue:
            oTag.text = sValue
        return oTag

    def write(self, sFileName:str, sEncoding:str="utf-8", bExpand=0):
        oTree = ET.ElementTree(self.oRoot)
        if bExpand:
            oXmlStr = minidom.parseString(ET.tostring(self.oRoot)).toprettyxml(indent="  ")
            with open(sFileName, "w", encoding=sEncoding) as file:
                file.write(oXmlStr)
        else:
            oTree.write(sFileName, encoding=sEncoding, xml_declaration=True)
        return


if __name__ == '__main__':
    sPath = "../../output/Tests/"
    oXml:Xml = Xml()
    sXmlns = "www:yournamespace.com"
    oRoot = oXml.createRoot("kml", sXmlns=sXmlns)
    oXml.addAttrib(oRoot, "xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    oXml.addAttrib(oRoot, "xsi:schemaLocation", sXmlns + " http://yournamespace.com/1.1.0/yourschemer.xsd")
    oDoc = oXml.addTag(oRoot, "doc", sId="5612a")
    oXml.addAttrib(oDoc, "att1", "value1")
    oXml.addAttrib(oDoc, "att2", "value2")
    oXml.addTag(oDoc, "name", sId="123", sValue="Frist")
    oXml.addTag(oDoc, "name", sId="456").text = "Two"
    oXml.write(sPath + "__Test.xml", bExpand=1)

