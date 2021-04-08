#!/usr/bin/env python3

import bpaTools

from bs4 import BeautifulSoup

class AixmReader:

    def __init__(self, oCtrl=None, openType='xml'):
        bpaTools.initEvent(__file__, oCtrl.oLog)
        self.oCtrl = oCtrl                  #Référence du contrôleur appelant
        self.openType = openType            #openType in ["xml"(default) or "lxml"(html solution, with lowercase elements)]
        self.doc:BeautifulSoup = None
        self.root:BeautifulSoup = None
        self.OpenFile()
        return

    def OpenFile(self):
        self.oCtrl.oLog.info("Reading source file: " + self.oCtrl.srcFile, outConsole=True)

        #Ouverture du fichier source
        self.doc = BeautifulSoup(open(self.oCtrl.srcFile, encoding=self.oCtrl.sEncoding), self.openType, from_encoding=self.oCtrl.sEncoding)

        #Extract xml root attributes
        self.root = self.doc.find("AIXM-Snapshot", recursive=False)
        self.srcVersion = self.root['version']
        self.srcOrigin = self.root['origin']            #SIA="Sia-France"; Eurocontrol="EAD-SDO"
        self.srcCreated = self.root['created']
        self.srcEffective = self.root['effective']
        return

