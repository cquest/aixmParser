#!/usr/bin/env python3

import math

#Les coordonnées géographiques peuvent êtres présentés selon plusieurs formats
#   1/ (DMS) en Degrés, Minutes, Secondes   ex: 47° 36' 04" N
#       format long  "47:36:04 N"       (standard sous Openair --> DP 47:36:04 N 000:25:56 W)
#       format court "473604N"
#   2/ (DMS.d) en Degrés, Minutes, Secondes.décimales   ex: 47° 36' 04.123" N
#       format long  "47:36:04.00 N"
#       format court "473604.00N"      (standard sous Aixm --> <geoLat>473604.00N</geoLat>)
#   3/ (DM.d) en degrés et minutes décimales   : 45° 13.18333' N
#       format long  "44:14.4667 N"       (parfois existant en Openair --> DP 44:14.4667 N 3:25.7667 E)
#       format court "4414.4667N"
#   4/ (D.d) en degrés décimaux     ex: 45,219722
#       Convertion des structures sources de type String en Float permet 
#       Exemple de conversion (DMS) "473604N" = (D.d) 47.601111
#   Paramètres
#       [latitude], [longitude] : paramètres de Coordonnées optionnelles qui acceptent les types de formats : (DMS), (DMS.d) et (DM.d) (comme précisé ci-dessus...)
#       [digit] ; paramètre optionnel pour préciser la taille de l'arrondi (défaut = 8 digits)
#   Sorties
#       Cette fonction retourne les valeurs sous forme d'une liste de float ; conformément au format : (D.d) en degrés décimaux  (comme précisé ci-dessus...)
#   Appels & Rappels
#       ex1: lat, lon = geoStr2dd("47:36:04 N", "000:25:56 W")
#       ex2: lat, lon = geoStr2dd("473604N", "0002556W")
#       ex3: lat, lon = geoStr2dd("47.601111 N", "000.432222 W")
#       une latitude  s'exprime en référence : 'N' (Deg*1) ; ou 'S' (Deg*-1)
#       une longitude s'exprime en référence : 'E' (Deg*1) ; ou 'W' ou 'O' (Deg*-1)
#       Contrôle de coordonnées - https://www.guide-plaisance-mobile.fr/convertisseur-de-coordonnees-gps-degres-minutes-secondes-decimales
def geoStr2dd(latitude=None, longitude=None, digit:int=8) -> float:
    try:
        #-- latitude --
        if latitude == None:
            lat = latitude
        else:
            lat = latitude.replace(" ","")      #Cleaning
            lat = lat.replace(",","")           #Cleaning
            latRef = lat[-1].upper()
            lat = lat[:-1]
            aLat = lat.split(":")               #Ctrl format
            if len(aLat) > 1:
                if len(aLat[0]) < 2:        aLat[0] = "{0:0=2d}".format(int(aLat[0]))
                if not "." in aLat[1]:
                    if len(aLat[1]) < 2:    aLat[1] = "{0:0=2d}".format(int(aLat[1]))
                else:
                    if len(str(int(float(aLat[1])))) == 1:
                        aLat[1] = "0" + str(aLat[1])
                lat = "".join(aLat)             #Cleaning
            if not latRef in ["N","S"]:
                raise Exception("Invalid input - latitude")
            else:
                if len(lat)==2 or lat[2]==".":              # DD[.dddd]
                    lat = float(lat)
                elif len(lat)==4 or lat[4]==".":            # DDMM[.mmmm]
                    lat = int(lat[0:2])+float(lat[2:])/60
                else:                                       # DDMMSS[.sss]
                    lat = int(lat[0:2])+int(lat[2:4])/60+float(lat[4:])/3600
                if latRef == "S":
                    lat = -lat
            lat = round(lat, digit)
        
        #-- longitude --
        if longitude == None:
            lon = longitude
        else:        
            lon = longitude.replace(" ","")     #Cleaning
            lon = lon.replace(",","")           #Cleaning
            lonRef = lon[-1].upper()
            lon = lon[:-1]
            aLon = lon.split(":")               #Ctrl format
            if len(aLon) > 1:
                if len(aLon[0]) < 3:    aLon[0] = "{0:0=3d}".format(int(aLon[0]))
                if not "." in aLon[1]:
                    if len(aLon[1]) < 2:    aLon[1] = "{0:0=2d}".format(int(aLon[1]))
                else:
                    if len(str(int(float(aLon[1])))) == 1:
                        aLon[1] = "0" + str(aLon[1])
                lon = "".join(aLon)             #Cleaning
            if not lonRef in ["E","W","O"]:
                raise Exception("Invalid input - longitude")
            else:
                if len(lon) == 3 or lon[3] == ".":          # DDD[.dddd]
                    lon = float(lon)
                elif len(lon) == 5 or lon[5] == ".":        # DDDMM[.dddd]
                    lon = int(lon[0:3])+float(lon[3:])/60
                else:                                       # DDDMMSS[.sss]
                    lon = int(lon[0:3])+int(lon[3:5])/60+float(lon[5:])/3600
                if lonRef in ["W","O"]:
                    lon = -lon
            lon = round(lon, digit)
                
        return lat, lon
    except:
        raise


def geoDd2dms(dd1,ref1, dd2,ref2, sep1="", sep2="", digit:int=0) -> str:  
    if not ref1 in ["lat","lon"]:   raise Exception("Invalid input - ref1")
    if not ref2 in ["lat","lon"]:   raise Exception("Invalid input - ref2")
    def toDMS(dd, ref) -> str:
        dd1 = abs(float(dd))
        ldeg = int(dd1)
        lmind = (dd1 - ldeg) * 60
        lmin = int(lmind)
        lsecd = (lmind - lmin) * 60
        lsec = round(lsecd, digit)
        if lsec >= 60:
            lsec = 0
            lmin +=1
        if lmin >= 60:
            lmin = 0
            ldeg +=1
        aRes = math.modf(lsec)
        if digit == 0 or aRes[0] < 0.00001 :
            sSec = "{0:0=2d}".format(int(lsec))
        else:
            frmtDigit = "{0:." + str(digit) + "f}"    #ex: "{0:.6f}" si digit=6
            aDig = (frmtDigit.format(aRes[0])).split(".")
            sSec = "{0:0=2d}.{1}".format(int(aRes[1]), aDig[1])
        if ref == "lat":
            ret = "{0:0=2d}{1}{2:0=2d}{3}{4}".format(ldeg, sep1, lmin, sep1, sSec)
            if dd < 0:
                sRef = "S"
            else:
                sRef = "N"
            ret = "{0}{1}{2}".format(ret, sep2, sRef)
        elif ref == "lon":
            ret = "{0:0=3d}{1}{2:0=2d}{3}{4}".format(ldeg, sep1, lmin, sep1, sSec)
            if dd < 0:
                sRef = "W"
            else:
                sRef = "E"
            ret = "{0}{1}{2}".format(ret, sep2, sRef)
        else:
            raise Exception("Invalid input")
        return ret
    try:
        return toDMS(dd1,ref1), toDMS(dd2,ref2)   
    except:
        raise


def geoDd2dmd(dd1,ref1, dd2,ref2, sep1="", sep2="", digit:int=8) -> str:  
    def toDMD(dd, ref) -> str:
        dd1 = abs(float(dd))
        ldeg = int(dd1)
        lmind = (dd1 - ldeg) * 60
        frmtDigit = "{2:." + str(digit) + "f}"    #ex: "{2:.8f}"
        if ref == "lat":
            msg = "{0:0=2d}{1}" + frmtDigit
            ret = msg.format(ldeg, sep1, lmind)
            if dd < 0:
                sRef = "S"
            else:
                sRef = "N"
            ret = "{0}{1}{2}".format(ret, sep2, sRef)
        elif ref == "lon":
            msg = "{0:0=3d}{1}" + frmtDigit
            ret = msg.format(ldeg, sep1, lmind)
            if dd < 0:
                sRef = "W"
            else:
                sRef = "E"
            ret = "{0}{1}{2}".format(ret, sep2, sRef)
        else:
            raise Exception("Invalid input")
        return ret
    try:
        return toDMD(dd1,ref1), toDMD(dd2,ref2)   
    except:
        raise


if __name__ == '__main__':
    #(DMS)  DP 47:36:04 N 000:25:56 W           dms2dd --> 47.601111, -0.432222  /  dmd --> 47:36.0666660 N, 0:25.9333320 W
    
    lat, lon = geoStr2dd(" 7:7.4833333N ", " 0:5.15W ")
    print("( D.d-->D.d)", lat, lon)
    
    lat0 = "473604N"
    lon0 = "0002556W"
    
    lat1, lon1 = geoStr2dd(lat0)
    print("(DMS--->D.d)", lat0, "-->", lat1, lon1)
    
    lat1, lon1 = geoStr2dd(None,lon0)
    print("(DMS--->D.d)", lon0, "-->", lat1, lon1)

    lat1, lon1 = geoStr2dd(lat0, lon0)
    print("(DMS--->D.d)", lat0, lon0, "-->", lat1, lon1)

    #test autres formats d'entrées
    lat, lon = geoStr2dd("4736.0666660 N", "00025.9333320 W")
    print("(DM.d-->D.d)", lat, lon)
    
    lat, lon = geoStr2dd("47.601111 N", "000.432222 W")
    print("( D.d-->D.d)", lat, lon)
    
    lat3, lon3 = geoDd2dmd(lat1,"lat", lon1,"lon")
    print("( D.d->DM.d)", lat1, lon1, "-->", lat3, lon3)
    lat3, lon3 = geoDd2dmd(lat1,"lat", lon1,"lon", ":", ",", 2)
    print("( D.d->DM.d)", lat1, lon1, "-->", lat3, lon3)
    
    print()
    
    lat2, lon2 = geoDd2dms(lat1,"lat", lon1,"lon")
    print("(D.d->DMS short)", lat1, lon1, "-->", lat2, lon2)
    
    lat2, lon2 = geoDd2dms(lat1,"lat", lon1,"lon", ":"," ")
    print("(D.d->DMS long )", lat1, lon1, "-->", lat2, lon2)

    lat2, lon2 = geoDd2dms(lat1,"lat", lon1,"lon", digit=4)
    print("(D.d->DMS digit=4)", lat1, lon1, "-->", lat2, lon2)
    
    print()
    
    lat, lon = geoStr2dd("47: 36: 04n", "000 :25 : 56, w")
    print("( D.d-->D.d)", lat, lon)
    lat, lon = geoStr2dd(" 47 :36:04,  N", "0: 25:56 , o")
    print("( D.d-->D.d)", lat, lon)
    lat, lon = geoStr2dd("7: 5: 04,  s", " 0:5: 56, e")
    print("( D.d-->D.d)", lat, lon)
    


