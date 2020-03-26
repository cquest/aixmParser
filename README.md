# aixmParser

**EN COURS DE DEVELOPPEMENT !!!**  
*ATTENTION: Seules les données d'origine doivent être utilisées pour la navigation aérienne.*  
--> Les Pull-Request et Issues sont les bienvenues :)  

Programme d'extraction et de formatage des données issues du standard AIXM (Aeronautical Information Exchange Modele)  
Les fichiers actuellements générées sont les suivants:  

	a/ Catalogue de zones aériennes, disponible sous deux formats:  
		- airspacesCatalog.json  
		- airspacesCatalog.csv  

	b/ Description des zones aériennes, disponible au format GeoJSON(*):  
		- airspaces-all.geojson			Cartographie complète de l'espace aérien (IFR + VFR)  
		- airspaces-ifr.geojson			Cartographie de l'espace aérien IFR (zones situées au dessus  du niveau FL115)  
		- airspaces-vfr.geojson			Cartographie de l'espace aérien VFR (zones situées en dessous le niveau FL115)  
		- airspaces-ff.geojson			Cartographie de l'espace aérien dédié Vol-Libre (dessous FL115 +filtre +compl.)  
		- (ces fichiers seront bientôt disponible aux formats : Openair et Kml) 

	c/ Description d'informations aéraunautique complémentaires, disponible au format GeoJSON(*):  
		- aerodromes.geojson  
		- towers.geojson  
		- gates-stands.geojson  
		- runwaysCenter.geojson  
		- obstacles.geojson  
		- borders.geojson  

(*) AIXM - Aeronautical Information Exchange Modele.  Est un standard d'échange de données aéronautiques. Basé sur la technologie XML (décrit ici - http://www.aixm.aero/)    
Actuellement, seul l'ancien format AIXM 4.5 est pris en charge. Ultérieurement, ce programme évoluera pour prendre en charge la version AIXM 5.1  

(*) GeoJSON - Geographic JSON.  Est un format ouvert d'encodage d'ensemble de données géospatiales simples utilisant la norme JSON (JavaScript Object Notation). Issu du projet OpenStreetMap, il est compatible avec le système : https://www.google.fr/maps  
Les données au format GeoJSON sont visualisables par des outils tels que : http://geojson.tools/   ou   http://geojson.io/  

## Installation
```
pip install -r requirements.txt
```

## Utilisation

Selon le choix des options de génération; le programme produira un log et les fichiers dans le dossier ./out/  
Les options d'utilisations s'auto décrivent avec l'aide en ligne "aixmParser -h":  

aixmParser v2.3.0  
-----------------  
Aeronautical Information Exchange Model (AIXM) Converter  
Call: aixmParser <[drive:][path]filename> <Format> <Type> [<Type2> ... <TypeN>] [<Option(s)>]  
With:  
  <[drive:][path]filename>       AIXM source file  

  <Format> - Output formats:  
    -Fgeojson        GeoJSON for GoogleMap  
    -Fkml            KML for GoogleEatrh  
    -Fopenair        OpenAir for aeronautical software  
    -Fall            All output formats (simultaneously)  

  <Type(s)> - Data to export:  
    -Airspaces  
    -GeoBorders  
    -Obstacles  
    -Aerodromes  
    -RunwayCenter  
    -ControlTowers  
    -GateStands  
    -Tall           All exported type (simultaneously)  

  <Option(s)> - Complementary Options:  
    -h              Help syntax  
    -CleanLog       Clean log file before exec  
    -IFR            Specific upper vues of aeronautic maps (IFR areas)  
    -VFR            Specific lower vues of aeronautic maps (only IFR areas, without IFR areas)  
    -FreeFlight     Specific Paragliding/Hanggliding maps (out E,F,G,W areas and others...)  
    -Draft          Size limitation for geojson output  

  Samples: aixmParser ../tst/aixm4.5_SIA-FR_2019-12-05.xml -Fall -Tall -CleanLog  
           aixmParser ../tst/aixm4.5_SIA-FR_2019-12-05.xml -Fgeojson -Airspaces -Obstacles -ControlTowers -CleanLog  
           aixmParser ../tst/aixm4.5_SIA-FR_2019-12-05.xml -Fall -Airspaces -FreeFlight -CleanLog  

  Resources  
     GeoJSON test format: http://geojson.tools/  -or-  http://geojson.io  
     OpenAir test format: http://xcglobe.com/cloudapi/browser  -or-  http://cunimb.net/openair2map.php  
