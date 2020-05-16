#!/usr/bin/env python3

import bpaTools

class Aixm2openair:
    
    def __init__(self, oCtrl):
        bpaTools.initEvent(__file__, oCtrl.oLog)
        self.oCtrl = oCtrl
        return        
    
    def parseAirspace(self):
        self.oCtrl.oLog.info("/!\ Traitement interrompu car actuellement non implémenté...", outConsole=True)
        return
