#!/usr/bin/env python3

import xml.etree.ElementTree as ET
#from xml.etree.ElementTree import tostring
from xml.dom import minidom

cstCDATA:str = '<![CDATA[{0}]]>'
#Surcharge de fontionnalité - CDATA parsing values -> Sample: '<![CDATA[<root><tag>YourValue</tag></root>]]>'
def _escape_cdata(text):
    try:
        if "&" in text:
            text = text.replace("&", "&amp;")
        # if "<" in text:
            # text = text.replace("<", "&lt;")
        # if ">" in text:
            # text = text.replace(">", "&gt;")
        return text
    except TypeError:
        raise TypeError(
            "cannot serialize %r (type %s)" % (text, type(text).__name__)
        )
#ET._escape_cdata = _escape_cdata       #use setCDATA() Method for apply this fonctionality

#Other CDATA function
#def CDATA(text=None):
#    element = ET.Element(CDATA)
#    element.text = text
#    return element
#
#class ElementTreeCDATA(ET.ElementTree):
#    def _write(self, file, node, encoding, namespaces):
#        if node.tag is CDATA:
#            text = node.text.encode(encoding)
#            file.write("\n<![CDATA[%s]]>\n" % text)
#        else:
#            ET.ElementTree._write(self, file, node, encoding, namespaces)

class Xml:

    def __init__(self)-> None:
        self.oRoot:ET.Element = None
        return

    @property
    def root(self):
        return self.oRoot

    #Define context for use CDATA in your XML files
    def setCDATA(self) -> None:
        ET._escape_cdata = _escape_cdata
        return

    #Method for convert string in CDATA format
    #  sample: in = '<root version="1""><content>value</content></root>' --> out = "'<![CDATA[<root version="1""><content>value</content></root>]]>'"
    def letCDATA(self, sValue:str) -> None:
        self.setCDATA()                         #Swap context in CDATA mode
        sCDATA = cstCDATA.format(sValue)
        return sCDATA

    #Method for get string in CDATA format
    #  sample: in = '<![CDATA[<root version="1""><content>value</content></root>]]>' --> out = '<root version="1""><content>value</content></root>'
    def getCDATA(self, sCDATA:str) -> str:
        sValue:str = sCDATA
        if sCDATA[0:9]==cstCDATA[0:9] and sCDATA[-3:]==cstCDATA[-3:]:
            sValue = sCDATA[10:-4]
        return sValue

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
        #if sValue and sValue[0:9]=="<![CDATA[":
        #    oTag = CDATA(sValue)
        #    oParent.append(oTag)
        #else:
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

