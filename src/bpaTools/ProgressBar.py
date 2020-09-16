#!/usr/bin/env python3

import sys
import time

class ProgressBar:

    def __init__ (self, valmax, maxbar, mod=10, title="", isSilent:bool=False) -> None:
        self.isSilent = isSilent            # Set as 'True' for Silent mode (no ProgressBar message!
        if valmax == 0:  valmax = 1
        if maxbar > 200: maxbar = 200
        self.valmax = valmax
        self.maxbar = maxbar
        self.mod = mod
        self.title = title
        return
    
    def update(self, val:int=0) -> None:
        if self.isSilent or (val<self.valmax and val%self.mod==0):
            return
        if val > self.valmax: val = self.valmax     # format
        perc  = round((float(val) / float(self.valmax)) * 100)
        scale = 100.0 / float(self.maxbar)
        bar   = int(perc / scale)
        #Retour début de ligne avec écruture de la suite
        out = '\r[%s%s] %3d %% - %s' % ('=' * bar, ' ' * (self.maxbar - bar), perc, self.title)
        sys.stdout.write(out)
        self.setCursor("off")                   #Extinction du curseur
        sys.stdout.flush()                      #Rafraichissement de la barre
        return

    def reset(self) -> None:
        if self.isSilent:
                return
        self.update(self.valmax)
        print("")
        self.setCursor("on")                    #Redemarrage du curseur
        return
    
    #val='off' - Extinction du curseur
    #val='on' - Redemarrage du curseur
    def setCursor(self, val:str) -> None:
        #if self.isSilent:
        #    return
        #Nota: Suppression de la gestion curseur car implique une grosse consamation de ressource !
        #os.system("setterm -cursor" + val)      #Extinction du curseur
        return


## Test
if __name__ == "__main__":
    i = 1                                               #Variable surveillée
    barre = ProgressBar(40, 20, title="Traitement")     #Objet barre de progression
    for x in range(40):
         barre.update(i)
         time.sleep(0.30)
         i = i+1
    barre.reset()

