# aixmParser

Script d'extraction de données à partir de fichiers XML au standard AIXM 4.5.

AIXM 4.5 est un standard (ancien) d'échange de données aéronautiques au format XML.
Il est par exemple utilisé par le SIA (Services de l'Information Aéronautique) de la DGAC en France.

**EN COURS DE DEVELOPPEMENT !!!**

*ATTENTION: Seules les données d'origine doivent être utilisées pour la navigation aérienne.*


## Installation

```
pip install -r requirements.txt
```

# Utilisation

./src/aixmParser.py <nom_de_fichier_xml>.xml
(Exp: ./src/aixmParser.py ./test-data/AIXM4.5_SIA-FR_sample.xml)

Le script produira les fichiers dans le dossier ./out/

Les fichiers générées sont au format geojson:
- aerodromes.geojson
- airspace.geojson
- border.geojson
- gate_stand.geojson
- obstacles.geojson
- runway_center.geojson
- tower.geojson

# Todo...

Extraire plus d'attributs en lien avec les données déjà extraites.
Extraire de nouveaux type de données.

Les PR et issues sont les bienvenues :)
