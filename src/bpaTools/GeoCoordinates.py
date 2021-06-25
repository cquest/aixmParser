#!/usr/bin/env python3

#import math

# Val parameter is a string or float value
#   print(cleanNumber("1.0"))           #-> "1"
#   print(cleanNumber("1.001200", 2))   #-> "01.0012"
#   print(cleanNumber("1.0", 2))        #-> "01"
#   print(cleanNumber("1.0", 4))        #-> "01"
#   print(cleanNumber(1.0))             #-> 1
#   print(cleanNumber(1.000000))        #-> 1
#   print(cleanNumber(1.1))             #-> 1.1
#   print(cleanNumber(1.001200))        #-> 1.0012
def cleanNumber(val, headdigits:int=0) -> str:
    aSplit:list = str(val).split(".")
    #Numeral part
    iTmp:int = int(float(aSplit[0]))
    sFormat:str = "{0}"
    if headdigits>0:
        sFormat = "{0:0=" + str(headdigits) + "d}"      #samples: "{0:0=2d}" or "{0:0=3d}"
    ret:str = sFormat.format(iTmp)
    #Decimal part
    sDec:str = ""
    if len(aSplit)>1:
        #Netoyage des zéros non-significatif (en fin de chaine)
        for char in reversed(aSplit[1]):
            if (char!="0") or (char=="0" and len(sDec)>0):
                sDec = char + sDec
        if len(sDec)>0:
            ret += "." + sDec
    if isinstance(val, float):
        if "." in ret:
            ret = float(ret)
        else:
            ret = int(ret)
    return ret


def getRef(degrees:float, ref:str) -> str:
    if not isinstance(degrees, float):
        degrees = float(degrees)
    if ref:
        if ref=="lat" and degrees>=0:  direction:str = "N"
        if ref=="lat" and degrees< 0:  direction:str = "S"
        if ref=="lon" and degrees>=0:  direction:str = "E"
        if ref=="lon" and degrees< 0:  direction:str = "W"
    return direction


#Convert DMS (degrees minutes seconds) to DD (decimal degrees)
#   print(dms2dd(45, 30, 1, "S"))   #->  45.500277777777775
#   print(dms2dd(45, 30, 1, "N"))   #-> -45.500277777777775
def dms2dd(degrees, minutes, seconds, direction:str="", digit:int=8) -> float:
    dd = float(degrees) + float(minutes)/60 + float(seconds)/(60*60)
    if direction in ["S","W","O"]:
        dd *= -1
    return round(dd, digit)


#Convert (DM.d or DM.m) (degrees decimal minutes) to DD (decimal degrees)
#   print(dmd2dd(13, 14.012, "N"))   #->  13.23353333
#   print(dmd2dd(13, 14.012, "S"))   #-> -13.2335333
#   print(dmd2dd(1, 1.034,   "E"))   #->  1.01723333
#   print(dmd2dd(1, 1.034,   "O"))   #-> -1.01723333
#   print(dmd2dd(1, 1.034,   "W"))   #-> -1.01723333
def dmd2dd(degrees, minutesd, direction:str="", digit:int=8) -> float:
    dd = abs(float(degrees)) + abs(float(minutesd)/60)
    if direction=="" and degrees<0:
        dd *= -1
    if direction in ["S","W","O"]:
        dd *= -1
    return round(dd, digit)


#Convert DD (decimal degrees) to (DM.d or DM.m) (degrees decimal minutes)
#   dd = 45.0 + 30.0/60 + 1.0/3600  #-> 45.500277777777775
#   print(dd2dmd(dd))               #-> (45, 30.0167)
#   print(dd2dmd(dd*-1))            #-> (-45, 30.0167)
#   print(dd2dmd(dd, "lat"))        #-> (45, 30.0167, 'N')
#   print(dd2dmd(dd*-1, "lat"))     #-> (45, 30.0167, 'S')
#   print(dd2dmd(dd, "lon"))        #-> (45, 30.0167, 'E')
def dd2dmd(dd, ref:str="") -> tuple:
    newDD = abs(dd)
    deg = int(newDD)
    mind = (newDD - deg) * 60
    if ref:
        return abs(int(deg)), round(cleanNumber(mind),8), getRef(dd, ref)
    else:
        if dd<0:
            deg *= -1
        return int(deg), round(cleanNumber(mind),8)


#Convert DMS (degrees minutes seconds) to (DM.d or DM.m) (degrees decimal minutes)
#   print(dms2dmd(45, 30, 1))        #-> (45, 30.01666667)
#   print(dms2dmd(45, 30, 1, "S"))   #-> (45, 30.01666667, 'S')
#   print(dms2dmd(45, 30, 1, "N"))   #-> (45, 30.01666667, 'N')
def dms2dmd(degrees, minutes, seconds, direction:str="") -> tuple:
    if not isinstance(degrees, float):
        degrees = float(degrees)
    md = float(minutes) + float(seconds)/(60)
    if direction:
    #    if direction in ["S","W","O"]:
    #        degrees *= -1
        return degrees, round(md,8), direction
    else:
        return degrees, round(md,8)


#Convert DD (decimal degrees) to DMS (degrees minutes seconds)
#   dd = 45.0 + 30.0/60 + 1.0/3600  #-> 45.500277777777775
#   print(dd2dms(dd))               #-> (45, 30, 1)
#   print(dd2dms(dd*-1))            #-> (-45, 30, 1)
#   print(dd2dms(dd, "lat"))        #-> (45, 30, 1, 'N')
#   print(dd2dms(dd*-1, "lat"))     #-> (45, 30, 1, 'S')
#   print(dd2dms(dd, "lon"))        #-> (45, 30, 1, 'E')
def dd2dms(dd, ref:str="") -> tuple:
    newDD = abs(dd)
    mnt,sec = divmod(newDD*3600,60)
    deg,mnt = divmod(mnt,60)
    deg = int(deg)
    mnt = int(mnt)
    sec = round(cleanNumber(sec),4)
    if sec==60 and min==60:
        deg+=1
        mnt =1
        sec =0
    elif sec==60 and min==59:
        deg+=1
        mnt =0
        sec =0
    elif sec==60:
        mnt+=1
        sec =0
    if min==60:
        deg+=1
        mnt =0
    if ref:
        return abs(deg), mnt, sec, getRef(dd, ref)
    else:
        if dd<0:
            deg *= -1
        return deg, mnt, sec

#No use beacause Err in Convert DD (decimal degrees) to DMS (degrees minutes seconds)
#   dd = 45.0 + 30.0/60 + 1.0/3600
#   print(dd2dms2(dd))   #-> (45, 30, 0.999999999990564)
#def dd2dms2(deg) -> tuple:
#    d = int(deg)
#    md = abs(deg - d) * 60
#    m = int(md)
#    sd = (md - m) * 60
#    return d, m, sd


#Convert (DM.d or DM.m) (degrees decimal minutes) to DMS (degrees minutes seconds)
#   print(dmd2coords("4500", "lat", "dd"))          #->  45.0
#   print(dmd2coords("4500N", "lat", "dd"))         #->  45.0
#   print(dmd2coords("4500S", "lat", "dd"))         #-> -45.0
#   print(dmd2coords("-4500", "lat", "dd"))         #-> -45.0
#   print(dmd2coords("4501N", "lat", "dd"))         #->  45.01666667
#   print(dmd2coords("4501S", "lat", "dd"))         #-> -45.01666667 !!! -44.98333333
#   print(dmd2coords("1314.0000", "lat", "dd"))     #->  13.23333333
#   print(dmd2coords("-1314.0000", "lat", "dd"))    #-> -13.23333333 !!! -12.76666667
def dmd2coords(dmd, ref:str, outFrmt:str) -> tuple:
    if not outFrmt in ["dms", "dmd", "dd"]:
        raise Exception("dmd2coords() Invalid parameter outFrmt: '" + outFrmt +"'")
    if not isinstance(dmd, str):
        dmd = str(dmd)
    sSign:str = ""
    sDir:str = ""
    if dmd[0]=="-":
        sSign = dmd[0]
        dmd = dmd[1:]
    if dmd[0] in ["N","S","E","W","O"]:
        sDir = dmd[0]
        dmd = dmd[1:]
    if dmd[-1] in ["N","S","E","W","O"]:
        sDir = dmd[-1]
        dmd = dmd[:-1]
    if ref=="lat":
        deg = float(sSign + dmd[0:2])
        md  = float(dmd[2:])
    elif ref=="lon":
        deg = float(sSign + dmd[0:3])
        md  = float(dmd[3:])
    if outFrmt == "dms":
        return dmd2dms(deg, md, ref)
    elif outFrmt == "dd":
        if sDir in ["S","W","O"] and sSign!="-":
            deg *= -1
        return dmd2dd(deg, md, sDir)
    elif outFrmt == "dmd":
        return abs(int(deg)), md, getRef(deg, ref)


#Convert (DM.d or DM.m) (degrees decimal minutes) to DMS (degrees minutes seconds)
#   print(dmd2dms(45, 30.016666666666666))    #-> (45, 30, 1)
def dmd2dms(degrees, mindec, ref:str="") -> tuple:
    if not isinstance(degrees, float):
        degrees = float(degrees)
    if isinstance(mindec, str):
        mindec = float(mindec)
    mnt,sec = divmod(mindec*60,60)
    if ref:
        return abs(int(degrees)), int(mnt), round(cleanNumber(sec),4), getRef(degrees, ref)
    else:
        return int(degrees), int(mnt), round(cleanNumber(sec),4)



#Les coordonnées géographiques peuvent êtres présentés selon plusieurs formats
#   1/ (DMS) en Degrés, Minutes, Secondes (ex: 47° 36' 04" N)                   - latitude format: DDMMSS / longitude format: DDDMMSS
#       format long  "47:36:04 N"       (standard sous Openair --> DP 47:36:04 N 000:25:56 W)
#       format court "473604N"
#   2/ (DMS.d) en Degrés, Minutes, Secondes.décimales (ex: 47° 36' 04.123" N)   - latitude format: DDMMSS[.ssss] / longitude format: DDDMMSS[.ssss]
#       format long  "47:36:04.00 N"
#       format court "473604.00N"      (standard sous Aixm --> <geoLat>473604.00N</geoLat>)
#   3/ (DM.d or DM.m) en degrés et minutes décimales (ex: 45° 13.18333' N)              - latitude format: DDMM[.mmmm] / longitude format: DDDMM[.mmmm]
#       format long  "44:14.4667 N"       (parfois existant en Openair --> DP 44:14.4667 N 3:25.7667 E)
#       format court "4414.4667N"
#   4/ (D.d) en degrés décimaux -     (ex: 45.219722)                           - latitude format: DD[.dddd] / longitude format: DDD[.dddd]
#       Convertion des structures sources de type String en Float permet
#       Exemple de conversion (DMS) "473604N" = (D.d) 47.601111
#   Paramètres
#       [latitude], [longitude] : paramètres de Coordonnées optionnelles qui acceptent les types de formats : (DMS), (DMS.d), (DM.d) et (D.d)(comme précisé ci-dessus...)
#       [outFrmt] : Output format parmis les valeurs suivantes: "std"=Standardise l'entrée (sans modification de référence), "dms"=degrees minutes seconds, "dmd"=degrees decimal minutes, "dd"=decimal degrees
#       [sep1] : Séparateur de valeurs  en sortie                  Ex: "DDMMSS.ssssN" sep1=":" -> "DD:MM:SS.ssssN"
#       [sep2] : Séparateur de référence géographique en sortie    Ex: "DDMMSS.ssssN" sep2=" " -> "DDMMSS.ssss N"
#       [bOptimize] : Indicateur pour demande d'optimisation des formats de sortie (DMS / DMS.d) uniquement si [sep1] est précisé. Ex: "0030405.01N" -> (="3:4:5.01N" default=Tue) or (="003:04:05.01N" si=False)
#       [digit] : Optimisation de la valeur décimale pour les sorties "dms". Default=-1 sans aucune modification; 0=Arrondie à l'entier; n=Arrondi au nombre de décimal précisé
#   Sorties
#       Cette fonction retourne les valeurs sous forme d'une liste de str ; conformément au format : (DMS) ou (DMS.d) - latitude: DDMMSS[.ssss] / longitude DDDMMSS[.ssss]
#       Le format de sortie peut être surchargé par les séparateurs [sep1] et/ou [sep2]
#   Appels & Rappels
#       ex1: lat, lon = geoStr2coords("47:36:04 N", "000:25:56 W")
#       ex2: lat, lon = geoStr2coords("473604N", "0002556W")
#       ex3: lat, lon = geoStr2coords("47.601111 N", "000.432222 W")
#   Contrôle de coordonnées
#       http://family.mayer.free.fr/bateau/conversion_DMS_DMM_DD/Copie%20de%20calculators.htm
#       https://www.guide-plaisance-mobile.fr/convertisseur-de-coordonnees-gps-degres-minutes-secondes-decimales
def geoStr2coords(latitude=None, longitude=None, outFrmt:str="std", sep1="", sep2="", bOptimize:bool=True, digit:int=-1) -> tuple:     #tuple(str)
    ##############################
    # Aixm Normalisation
    # Aixm LATITUDE native format:
    #    •DDMMSS.ssX: ‘000000.00N’, ‘131415.5S’, ’455959.9988S’, ‘900000.00N’.
    #    •DDMMSSX: ‘000000S’, ’261356N’, ‘900000S’.
    #    •DDMM.mm...X : ‘0000.0000S’, ’1313.12345678S’, ‘1234.9S’, ‘9000.000S’.
    #    •DDMMX: ‘0000N’, ’1313S’, ‘1234N’, ‘9000S’.
    #    •DD.dd...X : ‘00.00000000N’, ’13.12345678S’, ‘34.9N’, ‘90.000S’.
    # Aixm LONGITUDE native format:
    #    •DDDMMSS.ssY: ‘0000000.00E’, ‘0010101.1E’, ’1455959.9967W’, ‘1800000.00W’.
    #    •DDDMMSSY: ‘0000000W’, ’1261356E’, ‘1800000E’.
    #    •DDDMM.mm...Y : ‘00000.0000W’, ’01313.12345678E’, ‘11234.9E’, ‘18000.000W’.
    #    •DDDMMY: ‘00000E’, ’01313W’, ‘11234E’, ‘18000W’.
    #    •DDD.dd...Y : ‘000.00000000W’, ’113.12345678E’, ‘134.9W’, ‘180.000W’.
    ##############################

    if sep1 in [None, ""]:
        sep1=""
        bOptimize = False
    if sep2 in [None]:
        sep2=""

    if not outFrmt in ["std", "dms", "dmd", "dd"]:
        raise Exception("geoStr2coords() Invalid parameter outFrmt: '" + outFrmt +"'")

    def toConvert(val:str, ref:str) -> str:
        if val == None:
            return val

        sRet:str = ""                           #Init
        sCoord:str = str(val).replace(" ","")   #Cleaning
        sCoord = sCoord.replace(",","")         #Cleaning

        #Eventuelle présence des délimiteurs à la source
        aCoord = sCoord.split(":")
        bSepInSrc:bool = bool(len(aCoord) > 1)

        #Cas specifique pour les formats: "47° 36' 04" N" ou "47°:36':04" N"
        if not bSepInSrc and sCoord.find("°")>=0:
            sCoord = sCoord.replace("°",":")    #Create separator
        else:
            sCoord = sCoord.replace("°","")     #Cleaning
        if not bSepInSrc and sCoord.find("'")>=0:
            sCoord = sCoord.replace("'",":")    #Create separator
        else:
            sCoord = sCoord.replace("'","")     #Cleaning
        sCoord = sCoord.replace('"',"")         #Cleaning

        #type de référence
        sCoordRef:str = ""
        if sCoord[-1].upper() in ["N","S","E","W","O"]:
            sCoordRef = sCoord[-1].upper()
            sCoord = sCoord[:-1]
        elif sCoord[0].upper() in ["N","S","E","W","O"]:
            sCoordRef = sCoord[0].upper()
            sCoord = sCoord[1:]

        if sCoordRef:
            if ref=="lat" and not sCoordRef in ["N","S"]:
                raise Exception("geoStr2coords() Invalid input: " + sCoord)
            if ref=="lon" and not sCoordRef in ["E","W","O"]:
                raise Exception("geoStr2coords() Invalid input: " + sCoord)
            if ref=="lon" and sCoordRef == "O":
                sCoordRef = "W"     #Normilise value

        #Eventuelle présence des délimiteurs dans la source
        aCoord = sCoord.split(":")
        if not len(aCoord) in [1,2,3]:
            raise Exception("geoStr2coords() Invalid delimiter input: " + sCoord)

        #Cleaning pour cas particulier réception d'un format (DM.d ou DM.m) '13:14.0000S'
        if len(aCoord)==2:
            sCoord = sCoord.replace(":","")         #Cleaning
            aCoord = sCoord.split(":")
        bSepInSrc:bool = bool(len(aCoord)>1)

        #Séparateur dans la source, donc exclusivement format (DMS ou DMS.d) en entrée
        if bSepInSrc:
            if outFrmt in ["std","dms"] and bOptimize:
                #Sortie optimisé en taille. Ex: "07:03:04.0 N" -> "7:3:4N"
                if len(aCoord)==3:
                    tmp = round(float(aCoord[2]), 4)
                    if tmp>=60:
                        aCoord[1] = str(int(aCoord[1])+1)                   #Ajout des 60 sec
                        aCoord[2] = str(round(float(aCoord[2])-60,8))       #Suppression des 60 sec
                        #aCoord[2] = cleanNumber(aCoord[2], headdigits=0)
                    if "." in aCoord[2] and digit>=0:
                        aCoord[2] = str(round(float(aCoord[2]), digit))
                    aCoord[2] = cleanNumber(aCoord[2], headdigits=0)
                    if aCoord[2]=="60" and aCoord[1]=="60":
                        aCoord[0] = str(int(aCoord[0])+1)   #Ajout des 60 min
                        aCoord[1] = "1"                     #Ajout des 60 sec
                        aCoord[2] = "0"
                    elif aCoord[2]=="60" and aCoord[1]=="59":
                        aCoord[0] = str(int(aCoord[0])+1)   #Ajout des 60 min
                        aCoord[1] = "0"
                        aCoord[2] = "0"
                    elif aCoord[2]=="60":
                        aCoord[1] = str(int(aCoord[1])+1)   #Ajout des 60 sec
                        aCoord[2] = "0"
                    aCoord[2] = cleanNumber(aCoord[2], headdigits=0)
                tmp = round(float(aCoord[1]), 4)
                if tmp>=60:
                    aCoord[0] = str(int(aCoord[0])+1)                   #Ajout des 60 min
                    aCoord[1] = str(round(float(aCoord[1])-60,8))       #Suppression des 60 min
                if "." in aCoord[1] and digit>=0:
                    aCoord[1] = str(round(float(aCoord[1]), digit))
                aCoord[1] = cleanNumber(aCoord[1], headdigits=0)
                aCoord[0] = "{0}".format(int(aCoord[0]))
                sRet = sep1.join(aCoord) + sep2 + sCoordRef
            elif outFrmt in ["std","dms"] and not bOptimize:
                #Sortie non-optimisé en taille
                if len(aCoord)==3:
                    tmp = round(float(aCoord[2]), 4)
                    if tmp>=60:
                        aCoord[1] = str(int(aCoord[1])+1)                   #Ajout des 60 sec
                        aCoord[2] = str(round(float(aCoord[2])-60,8))       #Suppression des 60 sec
                        #aCoord[2] = cleanNumber(aCoord[2], headdigits=0)
                    if "." in aCoord[2] and digit>=0:
                        aCoord[2] = str(round(float(aCoord[2]), digit))
                    aCoord[2] = cleanNumber(aCoord[2], headdigits=2)
                    if aCoord[2]=="60" and aCoord[1]=="60":
                        aCoord[0] = str(int(aCoord[0])+1)   #Ajout des 60 min
                        aCoord[1] = "1"                     #Ajout des 60 sec
                        aCoord[2] = "0"
                    elif aCoord[2]=="60" and aCoord[1]=="59":
                        aCoord[0] = str(int(aCoord[0])+1)   #Ajout des 60 min
                        aCoord[1] = "0"
                        aCoord[2] = "0"
                    elif aCoord[2]=="60":
                        aCoord[1] = str(int(aCoord[1])+1)   #Ajout des 60 sec
                        aCoord[2] = "0"
                    aCoord[2] = cleanNumber(aCoord[2], headdigits=2)
                tmp = round(float(aCoord[1]), 4)
                if tmp>=60:
                    aCoord[0] = str(int(aCoord[0])+1)                   #Ajout des 60 min
                    aCoord[1] = str(round(float(aCoord[1])-60,8))       #Suppression des 60 min
                if "." in aCoord[1] and digit>=0:
                    aCoord[1] = str(round(float(aCoord[1]), digit))
                aCoord[1] = cleanNumber(aCoord[1], headdigits=2)
                if ref == "lat":
                    if len(aCoord[0]) < 2:      aCoord[0] = "{0:0=2d}".format(int(aCoord[0]))
                elif ref == "lon":
                    if len(aCoord[0]) < 3:      aCoord[0] = "{0:0=3d}".format(int(aCoord[0]))
                sRet = sep1.join(aCoord) + sep2 + sCoordRef
            elif outFrmt=="dmd":
                degrees, md, direction = dms2dmd(aCoord[0], aCoord[1], aCoord[2], direction=sCoordRef)
                if not sCoordRef:       #Priorisation a la référence réceptionné (donc négligence de la signature nulérique '+/-')
                    sCoordRef = direction
                if ref == "lat":
                    degrees = cleanNumber(str(degrees), headdigits=0 if bOptimize else 2)
                elif ref == "lon":
                    degrees = cleanNumber(str(degrees), headdigits=0 if bOptimize else 3)
                if digit>=0:
                    md = round(md, digit)
                md = cleanNumber(str(md), headdigits=0 if bOptimize else 2)
                sRet = sep1.join([degrees, md]) + sep2 + sCoordRef
            elif outFrmt=="dd":
                dd = dms2dd(aCoord[0], aCoord[1], aCoord[2], direction=sCoordRef)
                if digit>=0:
                    dd = round(dd, digit)
                sRet = dd

        #Décodage des formats (pas de séparateur dans la source)
        if not bSepInSrc:
            sSign:str = ""
            if sCoord[0]=="-":
                sSign = sCoord[0]
                sCoord = sCoord[1:]

            if isinstance(val, float):
                bDDLatFrmt = True           #Lat or Lon - D[.dddd] or DD[.dddd] DDD[.dddd] or -D[.dddd] or -DD[.dddd] -DDD[.dddd]
            else:
                bDDLatFrmt:bool   = bool(ref=="lat" and len(sCoord)==2 or (len(sCoord)>2 and sCoord[2]=="."))     #  DD[.dddd]  or  -DD[.dddd]
                bDDLonFrmt:bool   = bool(ref=="lon" and len(sCoord)==3 or (len(sCoord)>3 and sCoord[3]=="."))     # DDD[.dddd]  or -DDD[.dddd]
                bDMdLatFrmt:bool  = bool(ref=="lat" and len(sCoord)==4 or (len(sCoord)>4 and sCoord[4]=="."))     #  DDMM[.mmmm]  or   -DDMM[.mmmm]
                bDMdLonFrmt:bool  = bool(ref=="lon" and len(sCoord)==5 or (len(sCoord)>5 and sCoord[5]=="."))     # DDDMM[.mmmm]  or  -DDDMM[.mmmm]
                bDMSdLatFrmt:bool = bool(ref=="lat" and len(sCoord)==6 or (len(sCoord)>6 and sCoord[6]=="."))     #  DDMMSS[.mmmm]  or   -DDMMSS[.mmmm]
                bDMSdLonFrmt:bool = bool(ref=="lon" and len(sCoord)==7 or (len(sCoord)>7 and sCoord[7]=="."))     # DDDMMSS[.mmmm]  or  -DDDMMSS[.mmmm]

            if bDDLatFrmt or bDDLonFrmt:
                dd = float(sSign + sCoord)
                if outFrmt=="std":
                    if ref == "lat":
                        sRet = cleanNumber(sCoord, headdigits=2)
                    elif ref == "lon":
                        sRet = cleanNumber(sCoord, headdigits=3)
                    if sCoordRef:       #Priorisation a la référence réceptionné (donc négligence de la signature nulérique '+/-')
                        sRet += sCoordRef
                    else:
                        sRet = sSign + sRet
                elif outFrmt=="dms":
                    degrees, minutes, seconds,  direction = dd2dms(dd, ref)
                    if not sCoordRef:       #Priorisation a la référence réceptionné (donc négligence de la signature nulérique '+/-')
                        sCoordRef = direction
                    if digit>=0:
                        seconds = round(seconds, digit)
                    if seconds==60 and minutes==60:
                        degrees+= 1
                        minutes = 1
                        seconds = 0
                    elif seconds==60 and minutes==59:
                        degrees+= 1
                        minutes = 0
                        seconds = 0
                    elif seconds==60:
                        minutes +=1
                        seconds = 0
                    seconds = cleanNumber(str(seconds), headdigits=0 if bOptimize else 2)
                    if ref == "lat":
                        degrees = cleanNumber(str(degrees), headdigits=0 if bOptimize else 2)
                    elif ref == "lon":
                        degrees = cleanNumber(str(degrees), headdigits=0 if bOptimize else 3)
                    minutes = cleanNumber(str(minutes), headdigits=0 if bOptimize else 2)
                    sRet = sep1.join([degrees, minutes, seconds]) + sep2 + sCoordRef
                elif outFrmt=="dmd":
                    degrees, md, direction = dd2dmd(dd, ref)
                    if not sCoordRef:       #Priorisation a la référence réceptionné (donc négligence de la signature nulérique '+/-')
                        sCoordRef = direction
                    if ref == "lat":
                        degrees = cleanNumber(str(degrees), headdigits=0 if bOptimize else 2)
                    elif ref == "lon":
                        degrees = cleanNumber(str(degrees), headdigits=0 if bOptimize else 3)
                    if digit>=0:
                        md = round(md, digit)
                    md = cleanNumber(str(md), headdigits=0 if bOptimize else 2)
                    sRet = sep1.join([degrees, md]) + sep2 + sCoordRef
                elif outFrmt=="dd":
                    if digit>=0:
                        dd = round(dd, digit)
                    sRet = dd
            elif bDMdLatFrmt or bDMdLonFrmt:
                dmd = sCoordRef + str(sSign + sCoord)
                if outFrmt=="std":
                    if ref == "lat":
                        sRet = cleanNumber(sCoord, headdigits=4)
                    elif ref == "lon":
                        sRet = cleanNumber(sCoord, headdigits=5)
                    if sCoordRef:       #Priorisation a la référence réceptionné (donc négligence de la signature nulérique '+/-')
                        sRet += sCoordRef
                    else:
                        sRet = sSign + sRet
                elif outFrmt=="dms":
                    degrees, minutes, seconds, direction = dmd2coords(dmd, ref, outFrmt)
                    if not sCoordRef:       #Priorisation a la référence réceptionné (donc négligence de la signature nulérique '+/-')
                        sCoordRef = direction
                    if ref == "lat":
                        degrees = cleanNumber(str(degrees), headdigits=0 if bOptimize else 2)
                    elif ref == "lon":
                        degrees = cleanNumber(str(degrees), headdigits=0 if bOptimize else 3)
                    minutes = cleanNumber(str(minutes), headdigits=0 if bOptimize else 2)
                    if digit>=0:
                        seconds = round(seconds, digit)
                    seconds = cleanNumber(str(seconds), headdigits=0 if bOptimize else 2)
                    sRet = sep1.join([degrees, minutes, seconds]) + sep2 + sCoordRef
                elif outFrmt=="dmd":
                    degrees, md, direction = dmd2coords(dmd, ref, outFrmt)
                    if not sCoordRef:       #Priorisation a la référence réceptionné (donc négligence de la signature nulérique '+/-')
                        sCoordRef = direction
                    if ref == "lat":
                        degrees = cleanNumber(str(degrees), headdigits=0 if bOptimize else 2)
                    elif ref == "lon":
                        degrees = cleanNumber(str(degrees), headdigits=0 if bOptimize else 3)
                    if digit>=0:
                        md = round(md, digit)
                    md = cleanNumber(str(md), headdigits=0 if bOptimize else 2)
                    sRet = sep1.join([degrees, md]) + sep2 + sCoordRef
                elif outFrmt=="dd":
                    dd = dmd2coords(dmd, ref, outFrmt)
                    if digit>=0:
                        dd = round(dd, digit)
                    sRet = dd
            elif bDMSdLatFrmt or bDMSdLonFrmt:
                #Sortie optimisé en taille.     Ex: "070304.0N" -> "7:3:4N"
                #Sortie non-optimisé en taille. Ex: "070304.0N" -> "07:03:04N"
                if ref == "lat":
                    degrees = cleanNumber(sCoord[0:2], headdigits=0 if bOptimize else 2)
                    minutes = cleanNumber(sCoord[2:4], headdigits=0 if bOptimize else 2)
                    seconds = cleanNumber(sCoord[4:] , headdigits=0 if bOptimize else 2)
                elif ref == "lon":
                    degrees = cleanNumber(sCoord[0:3], headdigits=0 if bOptimize else 3)
                    minutes = cleanNumber(sCoord[3:5], headdigits=0 if bOptimize else 2)
                    seconds = cleanNumber(sCoord[5:] , headdigits=0 if bOptimize else 2)
                if outFrmt in ["std","dms"]:
                    if "." in seconds and digit>=0:
                        seconds = str(round(float(seconds), digit))
                        seconds = cleanNumber(seconds, headdigits=0 if bOptimize else 2)
                    if seconds=="60" and minutes in ["59", "60"]:
                        if ref == "lat":
                            degrees = cleanNumber(int(degrees)+1, headdigits=0 if bOptimize else 2)     #Ajout des 60 min
                        elif ref == "lon":
                            degrees = cleanNumber(int(degrees)+1, headdigits=0 if bOptimize else 3)     #Ajout des 60 min
                        if minutes=="60":
                            minutes = cleanNumber(1, headdigits=0 if bOptimize else 2)                  #Ajout des 60 sec
                        else:
                            minutes = cleanNumber(0, headdigits=0 if bOptimize else 2)
                        seconds = "0"
                    elif seconds=="60":
                        minutes = cleanNumber(int(minutes)+1, headdigits=0 if bOptimize else 2)         #Ajout des 60 sec
                        seconds = "0"
                    elif minutes=="60":
                        if ref == "lat":
                            degrees = cleanNumber(int(degrees)+1, headdigits=0 if bOptimize else 2)     #Ajout des 60 min
                        elif ref == "lon":
                            degrees = cleanNumber(int(degrees)+1, headdigits=0 if bOptimize else 3)     #Ajout des 60 min
                        minutes = cleanNumber(0, headdigits=0 if bOptimize else 2)
                    sRet = sep1.join([degrees, minutes, seconds]) + sep2 + sCoordRef
                elif outFrmt=="dmd":
                    degrees, md, direction = dms2dmd(degrees, minutes, seconds, sCoordRef)
                    if not sCoordRef:       #Priorisation a la référence réceptionné (donc négligence de la signature nulérique '+/-')
                        sCoordRef = direction
                    if ref == "lat":
                        degrees = cleanNumber(str(degrees), headdigits=0 if bOptimize else 2)
                    elif ref == "lon":
                        degrees = cleanNumber(str(degrees), headdigits=0 if bOptimize else 3)
                    if digit>=0:
                        md = round(md, digit)
                    md = cleanNumber(str(md), headdigits=0 if bOptimize else 2)
                    sRet = sep1.join([degrees, md]) + sep2 + sCoordRef
                elif outFrmt=="dd":
                    dd = dms2dd(degrees, minutes, seconds, sCoordRef)
                    if digit>=0:
                        dd = round(dd, digit)
                    sRet = dd
            else:
               raise Exception("geoStr2coords() Invalid input: '{0}' [lat:{1} lon:{2}] outFrmt={3}".format(ref, latitude, longitude, outFrmt))
        return sRet
    try:
        return toConvert(latitude, "lat"), toConvert(longitude, "lon")
    except:
        raise


if __name__ == '__main__':
    ddlat1 = 13.0
    ddlon1 = 3.0
    sDdLat1:str = cleanNumber(str(ddlat1), headdigits=2)
    sDdLon1:str = cleanNumber(str(ddlon1), headdigits=3)
    #print(sDdLat1, sDdLon1)

    ddlat2 = 13.0 + 14.0/60 + 5.002/3600
    ddlon2 = 3.0 + 4.0/60 + 5.0/3600
    sDdLat2:str = cleanNumber(str(ddlat2), headdigits=2)
    sDdLon2:str = cleanNumber(str(ddlon2), headdigits=3)
    #print(sDdLat2, sDdLon2)

    aPoints:list = [
                    #Format D.d sous différentes formes (Aixm: DD, DD.dd...X and DDD, DDD.dd...Y)
                    [(sDdLat1, sDdLon1)                                     , ("130000N", "0030000E")           , ("1300N", "00300E")                       , (13.0, 3.0)],
                    [("-"+sDdLat1, "-"+sDdLon1)                             , ("130000S", "0030000W")           , ("1300S", "00300W")                       , (-13.0, -3.0)],
                    [(sDdLat1+".000", sDdLon1+".000")                       , ("130000N", "0030000E")           , ("1300N", "00300E")                       , (13.0, 3.0)],
                    [(sDdLat1+".0001", sDdLon1+".0001")                     , ("130000.36N", "0030000.36E")     , ("1300.006N", "00300.006E")               , (13.0001, 3.0001)],
                    [(sDdLat1+".0120", sDdLon1+".0340")                     , ("130043.2N", "0030202.4E")       , ("1300.72N", "00302.04E")                 , (13.012, 3.034)],
                    [(sDdLat2, sDdLon2)                                     , ("131405.002N", "0030405E")       , ("1314.08336667N", "00304.08333333E")     , (13.234722777777778, 3.068055555555556)],
                    [("-"+sDdLat2, "-"+sDdLon2)                             , ("131405.002S", "0030405W")       , ("1314.08336667S", "00304.08333333W")     , (-13.234722777777778, -3.068055555555556)],

                    #Format DMS et DMS.d sans séparateurs et sous différentes formes (Aixm: DDMMSSX, DDMMSS.ssX and DDDMMSSY, DDDMMSS.ssY)
                    [("131415N", "0010101E")                                , ("131415N", "0010101E")           , ("1314.25N", "00101.01666667E")           , (13.2375, 1.01694444)],
                    [("131415S", "0010101E")                                , ("131415S", "0010101E")           , ("1314.25S", "00101.01666667E")           , (-13.2375, 1.01694444)],
                    [("131415 S", "0010101 E")                              , ("131415S", "0010101E")           , ("1314.25S", "00101.01666667E")           , (-13.2375, 1.01694444)],
                    [("030405.0000S", "0010203.0000E")                      , ("030405S", "0010203E")           , ("0304.08333333S", "00102.05E")           , (-3.06805556, 1.03416667)],
                    [("N030405.001200", "E0010203.003400")                  , ("030405.0012N", "0010203.0034E") , ("0304.08335333N", "00102.05005667E")     , (3.06805589, 1.03416761)],
                    [("S030405.001200", "W0010203.003400")                  , ("030405.0012S", "0010203.0034W") , ("0304.08335333S", "00102.05005667W")     , (-3.06805589, -1.03416761)],
                    [("S030405.001200", "O0010203.003400")                  , ("030405.0012S", "0010203.0034W") , ("0304.08335333S", "00102.05005667W")     , (-3.06805589, -1.03416761)],
                    [("030405.001200S", "0010203.003400O")                  , ("030405.0012S", "0010203.0034W") , ("0304.08335333S", "00102.05005667W")     , (-3.06805589, -1.03416761)],
                    [("030405.1200S", "0010203.3400O")                      , ("030405.12S", "0010203.34W")     , ("0304.08533333S", "00102.05566667W")     , (-3.06808889, -1.03426111)],

                    #Format DMS et DMS.d avec séparateurs et sous différentes formes (Aixm: DDMMSSX, DDMMSS.ssX and DDDMMSSY, DDDMMSS.ssY)
                    [("13:14:15N", "001:01:01E")                            , ("131415N", "0010101E")           , ("1314.25N", "00101.01666667E")           , (13.2375, 1.01694444)],
                    [("13:14:15S", "001:01:01E")                            , ("131415S", "0010101E")           , ("1314.25S", "00101.01666667E")           , (-13.2375, 1.01694444)],
                    [("13:14:15 S", "001:01:01 E")                          , ("131415S", "0010101E")           , ("1314.25S", "00101.01666667E")           , (-13.2375, 1.01694444)],
                    [("3:4:5S", "1:2:3E")                                   , ("030405S", "0010203E")           , ("0304.08333333S", "00102.05E")           , (-3.06805556, 1.03416667)],
                    [("3:4:5 S", "1:2:3 E")                                 , ("030405S", "0010203E")           , ("0304.08333333S", "00102.05E")           , (-3.06805556, 1.03416667)],
                    [("3:4:5.0S", "1:2:3.0E")                               , ("030405S", "0010203E")           , ("0304.08333333S", "00102.05E")           , (-3.06805556, 1.03416667)],
                    [("3:4:5.0000S", "1:2:3.0000E")                         , ("030405S", "0010203E")           , ("0304.08333333S", "00102.05E")           , (-3.06805556, 1.03416667)],
                    [("3:4:5.1S", "1:2:3.5E")                               , ("030405.1S", "0010203.5E")       , ("0304.085S", "00102.05833333E")          , (-3.06808333, 1.03430556)],
                    [("3:4:5.1234S", "1:2:3.1234E")                         , ("030405.1234S", "0010203.1234E") , ("0304.08539S", "00102.05205667E")        , (-3.06808983, 1.03420094)],
                    [("3:4:5.1200S", "1:2:3.3400E")                         , ("030405.12S", "0010203.34E")     , ("0304.08533333S", "00102.05566667E")     , (-3.06808889, 1.03426111)],
                    [("3:4:5.001200S", "1:2:3.003400E")                     , ("030405.0012S", "0010203.0034E") , ("0304.08335333S", "00102.05005667E")     , (-3.06805589, 1.03416761)],
                    [("S 13°14'15\"", "E 001°01'01\"")                      , ("131415S", "0010101E")           , ("1314.25S", "00101.01666667E")           , (-13.2375, 1.01694444)],
                    [("13°14'15\"S", "001°01'01\"E")                        , ("131415S", "0010101E")           , ("1314.25S", "00101.01666667E")           , (-13.2375, 1.01694444)],
                    [(" 13°  14' 15.00\"  S ", "001°  01'  01.00\"  O  ")   , ("131415S", "0010101W")           , ("1314.25S", "00101.01666667W")           , (-13.2375, -1.01694444)],
                    [("13°:14':15.001\" S ", "001°:01':01.001\" O")         , ("131415.001S", "0010101.001W")   , ("1314.25001667S", "00101.01668333W")     , (-13.23750028, -1.01694472)],
                    [("13°:14':15 .0120\" S ", "001°:01':01 .0340\" O")     , ("131415.012S", "0010101.034W")   , ("1314.2502S", "00101.01723333W")         , (-13.23750333, -1.01695389)],

                    #Format DM.d ou DM.m avec séparateurs et sous différentes formes (Aixm: DDMMX, DDMM.mm...X and DDDMMY, DDDMM.mm...Y)
                    [(" 1300       ", " 00100     ")                        , ("130000N", "0010000E")           , ("1300N", "00100E")                       , (13.0, 1.0)],
                    [(" 13:00      ", " 001:00     ")                       , ("130000N", "0010000E")           , ("1300N", "00100E")                       , (13.0, 1.0)],
                    [("-13:00.0000 ", "-001:00.0000")                       , ("130000S", "0010000W")           , ("1300S", "00100W")                       , (-13.0, -1.0)],
                    [(" 13:00.0000 ", " 001:00.0000")                       , ("130000N", "0010000E")           , ("1300N", "00100E")                       , (13.0, 1.0)],
                    [(" 13:14.0000 ", " 001:01.0000")                       , ("131400N", "0010100E")           , ("1314N", "00101E")                       , (13.23333333, 1.01666667)],
                    [("-13:14.0000 ", "-001:01.0000")                       , ("131400S", "0010100W")           , ("1314S", "00101W")                       , (-13.23333333, -1.01666667)],
                    [(" 13:14.0000N", " 001:01.0000E")                      , ("131400N", "0010100E")           , ("1314N", "00101E")                       , (13.23333333, 1.01666667)],
                    [(" N13:14.0000", "E001:01.0000")                       , ("131400N", "0010100E")           , ("1314N", "00101E")                       , (13.23333333, 1.01666667)],
                    [(" S13:14.0000", "W001:01.0000")                       , ("131400S", "0010100W")           , ("1314S", "00101W")                       , (-13.23333333, -1.01666667)],
                    [(" S13:14.0000", "O001:01.0000")                       , ("131400S", "0010100W")           , ("1314S", "00101W")                       , (-13.23333333, -1.01666667)],
                    [(" 13:14.0000S", " 001:01.0000W")                      , ("131400S", "0010100W")           , ("1314S", "00101W")                       , (-13.23333333, -1.01666667)],
                    [(" 13:14.0120N", " 001:01.0340E")                      , ("131400.72N", "0010102.04E")     , ("1314.012N", "00101.034E")               , (13.23353333, 1.01723333)],
                    [(" 13:14.0120S", " 001:01.0340W")                      , ("131400.72S", "0010102.04W")     , ("1314.012S", "00101.034W")               , (-13.23353333, -1.01723333)],
                    [(" 13:14.0120 ", " 001:01.0340")                       , ("131400.72N", "0010102.04E")     , ("1314.012N", "00101.034E")               , (13.23353333, 1.01723333)],
                    [("-13:14.0120 ", "-001:01.0340")                       , ("131400.72S", "0010102.04W")     , ("1314.012S", "00101.034W")               , (-13.23353333, -1.01723333)],

                    #Format DM.d ou DM.m sans séparateurs et sous différentes formes  (Aixm: DDMMX, DDMM.mm...X and DDDMMY, DDDMM.mm...Y)
                    [(" 1314.0000 ", " 00101.0000")                         , ("131400N", "0010100E")           , ("1314N", "00101E")                       , (13.23333333, 1.01666667)],
                    [("-1314.0000 ", "-00101.0000")                         , ("131400S", "0010100W")           , ("1314S", "00101W")                       , (-13.23333333, -1.01666667)],
                    [(" 1314.0000N", " 00101.0000E")                        , ("131400N", "0010100E")           , ("1314N", "00101E")                       , (13.23333333, 1.01666667)],
                    [(" N1314.0000", "E00101.0000")                         , ("131400N", "0010100E")           , ("1314N", "00101E")                       , (13.23333333, 1.01666667)],
                    [(" S1314.0000", "W00101.0000")                         , ("131400S", "0010100W")           , ("1314S", "00101W")                       , (-13.23333333, -1.01666667)],
                    [(" 1314.0000S", " 00101.0000W")                        , ("131400S", "0010100W")           , ("1314S", "00101W")                       , (-13.23333333, -1.01666667)],
                    [(" 1314.0120N", " 00101.0340E")                        , ("131400.72N", "0010102.04E")     , ("1314.012N", "00101.034E")               , (13.23353333, 1.01723333)],
                    [(" 1314.0120S", " 00101.0340W")                        , ("131400.72S", "0010102.04W")     , ("1314.012S", "00101.034W")               , (-13.23353333, -1.01723333)],
                    [(" 1314.0120 ", " 00101.0340")                         , ("131400.72N", "0010102.04E")     , ("1314.012N", "00101.034E")               , (13.23353333, 1.01723333)],
                    [("-1314.0120 ", "-00101.0340")                         , ("131400.72S", "0010102.04W")     , ("1314.012S", "00101.034W")               , (-13.23353333, -1.01723333)]
                ]


    for aPt in aPoints:
        source = aPt[0]
        cible1 = aPt[1]
        cible2 = aPt[2]
        cible3 = aPt[3]

        print("Source         ", source)
        print("Standardization", geoStr2coords(source[0], source[1], "std"))      #Clean ans normalyse source

        res1 = geoStr2coords(source[0], source[1], "dms")       #Output DMS ou DMS.d
        res2 = geoStr2coords(source[0], source[1], "dmd")       #Output DM.d
        res3 = geoStr2coords(source[0], source[1], "dd" )       #Output D.d
        if res1!=cible1:
            raise Exception("/!\Err: {0} - {1}!={2}".format(source, res1, cible1))
        if res2!=cible2:
            raise Exception("/!\Err: {0} - {1}!={2}".format(source, res2, cible2))
        if res3!=cible3:
            raise Exception("/!\Err: {0} - {1}!={2}".format(source, res3, cible3))

        print("DMS.d output   ", res1)
        print("DMS.d not-opti ", geoStr2coords(source[0], source[1], "dms", sep1=":", sep2=" ", bOptimize=False))
        print("DMS.d opti     ", geoStr2coords(source[0], source[1], "dms", sep1=":" , sep2=""))
        print("DM.d  output   ", res2)
        print("D.d   output   ", res3)

        #Test d'optimisation des décimaux
        if any(sRes.find(".")>0 for sRes in res1):
            print("(digit) DMS.d output   ", res1)
            print("(digit) DMS.d opti d=3 ", geoStr2coords(source[0], source[1], "dms", digit=3))
            print("(digit) DMS.d opti d=2 ", geoStr2coords(source[0], source[1], "dms", digit=2))
            print("(digit) DMS.d opti d=1 ", geoStr2coords(source[0], source[1], "dms", digit=1))
            print("(digit) DMS.d opti d=0 ", geoStr2coords(source[0], source[1], "dms", digit=0))

            print("(digit) DM.d  output   ", res2)
            print("(digit) DM.d  opti d=3 ", geoStr2coords(source[0], source[1], "dmd", digit=3))
            print("(digit) DM.d  opti d=2 ", geoStr2coords(source[0], source[1], "dmd", digit=2))
            print("(digit) DM.d  opti d=1 ", geoStr2coords(source[0], source[1], "dmd", digit=1))
            print("(digit) DM.d  opti d=0 ", geoStr2coords(source[0], source[1], "dmd", digit=0))

            print("(digit) D.d   output   ", res3)
            print("(digit) D.d   opti d=6 ", geoStr2coords(source[0], source[1], "dd", digit=6))
            print("(digit) D.d   opti d=5 ", geoStr2coords(source[0], source[1], "dd", digit=5))
            print("(digit) D.d   opti d=4 ", geoStr2coords(source[0], source[1], "dd", digit=4))
            print("(digit) D.d   opti d=3 ", geoStr2coords(source[0], source[1], "dd", digit=3))

        print()



    aDegs = ["9","1"]
    aMins = ["60"]                      #["0","59","60","61","62"]
    aSecs = ["60"]                      #["0","59","60","61","62"]
    aDecs = [".1",".9"]                 #["",".1",".9"]
    aRefs = [["N","E"]]                 #[["N","E"], ["S","W"]]
    for aRef in aRefs:
        for sMin in aMins:
            print("--", aRef, "Min="+sMin)
            for sSec in aSecs:
                for sDec in aDecs:
                    sLatSrc:str = "{0}:{1}:{2}{3}{4}".format(aDegs[0], sMin, sSec, sDec, aRef[0])
                    sLonSrc:str = "{0}:{1}:{2}{3}{4}".format(aDegs[1], sMin, sSec, sDec, aRef[1])
                    print("---- src", (sLatSrc, sLonSrc))
                    resDmsSep = geoStr2coords(sLatSrc, sLonSrc, "dms", sep1=":", sep2="")
                    print(" dms-sep", resDmsSep)

                    resDd0 = geoStr2coords(sLatSrc, sLonSrc, "dd")
                    #print("  dms2dd", resDd0)
                    resDd2dms = (dd2dms(resDd0[0], "lat"), dd2dms(resDd0[1], "lon"))
                    print("  dd2dms", resDd2dms)
                    tmpLat = ":".join([str(resDd2dms[0][0]), str(resDd2dms[0][1]), str(resDd2dms[0][2])]) + resDd2dms[0][3]
                    tmpLon = ":".join([str(resDd2dms[1][0]), str(resDd2dms[1][1]), str(resDd2dms[1][2])]) + resDd2dms[1][3]
                    print("     tmp", (tmpLat, tmpLon))
                    resDms8 = geoStr2coords(tmpLat, tmpLon, "dms")
                    print(" dd-dms2", resDms8)
                    resDms9 = geoStr2coords(tmpLat, tmpLon, "dms", digit=0)
                    print("     d=0", resDms9)

                    resDmsSepOpt = geoStr2coords(sLatSrc, sLonSrc, "dms", sep1=":", sep2="", bOptimize=False)
                    print(" no Opti", resDmsSepOpt)
                    resStd = geoStr2coords(sLatSrc, sLonSrc, "std")      #Clean ans normalyse source
                    print("     std", resStd)
                    resDmsUnSep = geoStr2coords(sLatSrc, sLonSrc, "dms")
                    print("     dms", resDmsUnSep)
                    resDmsSepOptDig1 = geoStr2coords(sLatSrc, sLonSrc, "dms", sep1=":", sep2="", bOptimize=False, digit=1)
                    print("     d=1", resDmsSepOptDig1)
                    resDmsSepOptDig0 = geoStr2coords(sLatSrc, sLonSrc, "dms", sep1=":", sep2="", bOptimize=False, digit=0)
                    print("     d=0", resDmsSepOptDig0)
                    resDmsSepOptDig0 = geoStr2coords(sLatSrc, sLonSrc, "dms", sep1=":", sep2="", bOptimize=True, digit=0)
                    print("opti d=0", resDmsSepOptDig0)

                    print()
