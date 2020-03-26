# -*- coding: utf-8 -*-

import sys
import time
import os

class ProgressBar:

    def __init__ (self, valmax, maxbar, mod=10, title=""):
        if valmax == 0:  valmax = 1
        if maxbar > 200: maxbar = 200
        self.valmax = valmax
        self.maxbar = maxbar
        self.mod = mod
        self.title  = title
    
    def update(self, val=0):
        if val<self.valmax and val%self.mod == 0:
            return
        if val > self.valmax: val = self.valmax     # format
        perc  = round((float(val) / float(self.valmax)) * 100)
        scale = 100.0 / float(self.maxbar)
        bar   = int(perc / scale)
        out = '\r%s [%s%s] %3d %% ' % (self.title, '=' * bar, ' ' * (self.maxbar - bar), perc)
        sys.stdout.write(out)
        self.setCursor('off')                   #Extinction du curseur
        sys.stdout.flush()                      #Rafraichissement de la barre
        return

    def reset(self):
        self.update(self.valmax)
        print("")
        self.setCursor('on')                    #Redemarrage du curseur
        return
    
    #val='off' - Extinction du curseur
    #val='on' - Redemarrage du curseur
    def setCursor(self, val):
        os.system('setterm -cursor' + val)      #Extinction du curseur
        return


## Test
if __name__ == '__main__':
    i = 1                                       #Variable surveillée
    barre = ProgressBar(40, 20, title="Traitement")   #Objet barre de progression
    for x in range(40):
         barre.update(i)
         time.sleep(0.30)
         i = i+1
    barre.reset()


