# Posts LinkedIn : OpenGeoData France pour QGIS (v1.0.2)

---

## 🌟 Version Principale : Storytelling Vécu & Pain Points (Recommandée)
*Cette version capte immédiatement l'attention des géomaticiens, urbanistes et agents territoriaux en décrivant leur quotidien réel.*

On va se le dire franchement : qui n'a jamais perdu 45 minutes sur QGIS à chercher l'URL exacte d'un flux WMS qui a encore changé d'adresse ?

Ou à télécharger un zip de 600 Mo sur data.gouv juste pour récupérer les parcelles d'une seule commune ?

Entre :
- les endpoints de l'IGN qui évoluent,
- le Géoportail de l'Urbanisme qu'il faut aller fouiller à part,
- les adresses BAN à géocoder dans un tableur,
- et les flux Géorisques ou DREAL éparpillés sur 10 sites différents...

On passe souvent plus de temps à chercher et nettoyer la donnée qu'à faire de la vraie analyse territoriale.

C'est exactement pour ça que j'ai développé **OpenGeoData France**.

L'idée de base est bête et méchante : 
Vous restez dans QGIS. Vous ouvrez le panneau. Vous tapez ce que vous voulez. Vous cliquez. La couche est dans votre projet.

Ce qu'on a mis sous le capot :

1. Le Cadastre et la BAN en 1 clic
Parcelles, bâti, sections du Parcellaire Express et points d'adresses. Fini les archives par département à dézipper.

2. Les documents d'urbanisme (GPU)
Zonages, prescriptions et servitudes du Géoportail de l'Urbanisme chargés directement sur votre zone d'étude.

3. Plus de 1 200 dataservices connectés
IGN, BRGM, INPN, INSEE, DREAL, réseaux de transport (GTFS, NeTEx, SNCF), bornes IRVE, et les portails régionaux (CRIGE).

4. Le découpage territorial automatique
Vous sélectionnez votre commune ou votre EPCI : le plugin découpe et cadre directement vos couches sur votre territoire. Plus besoin de créer un polygone de masque à la main.

5. Les petits plus pour les curieux
Les photos aériennes historiques de 1950-1965 pour comparer l'urbanisation en 2 secondes, et le radar de pluie en temps réel.

L'extension est 100 % gratuite, open-source, et compatible avec QGIS 3.22 jusqu'à QGIS 4.

👉 Le plugin est disponible sur le dépôt officiel QGIS (recherchez simplement "OpenGeoData France") et le code complet est ouvert sur GitHub :
https://github.com/mwjouini/OpenGeoData-France

J'ai passé pas mal d'heures dessus pour que ce soit fluide, robuste et sans prise de tête pour les agents et les pros du SIG.

Testez-le dans vos projets du quotidien, poussez-le dans ses retranchements, et dites-moi en commentaire les couches ou fonctionnalités que vous aimeriez voir arriver !

#QGIS #SIG #Geomatique #OpenData #DataGouv #Cartographie #Urbanisme #Territoires #Collectivites #OpenSource

---

## ⚡ Option 2 : Format Court & Impactant (Avant / Après)
*Idéal si vous préférez un format ultra-dynamique qui se lit en 45 secondes chrono.*

Avant d'avoir cette extension dans QGIS :
1. Aller sur data.gouv ou le Géoportail.
2. Télécharger une archive de 800 Mo.
3. Dézipper.
4. Trouver le bon shapefile dans 12 sous-dossiers.
5. Reprojecter en Lambert-93.
6. Cliquer sur "Découper selon l'emprise".
⏱️ Temps perdu : 20 minutes.

Maintenant, avec OpenGeoData France :
1. Taper "cadastre" ou "plu".
2. Cliquer sur Importer.
⏱️ Temps : 3 secondes.

En tant qu'utilisateur de QGIS, j'en avais marre de refaire ces mêmes manipulations tous les jours.

Alors j'ai créé **OpenGeoData France**, un moteur de recherche et d'importation unifié directement intégré à QGIS :
- 1 200+ flux et jeux de données ouverts français (IGN, BAN, GPU, INSEE, BRGM, DREAL, Transport).
- Import en 1 clic de vos couches (WMS, WFS, GeoJSON, Parquet, Shapefile).
- Découpage territorial instantané à la commune ou à l'intercommunalité.
- Photos historiques 1950 et radar météo en direct.

C'est open-source, gratuit, et déjà en ligne :
👉 https://github.com/mwjouini/OpenGeoData-France

Les collègues géomaticiens et urbanistes : faites le test aujourd'hui, vous ne reviendrez plus en arrière !

#SIG #QGIS #Geomatique #DataGouv #OpenData #Python #Productivité

---

## 🎬 Option 3 : Format Accompagnant la Démo Vidéo (Spécial Post Médias)
*Conçu spécifiquement pour accompagner le GIF ou la vidéo MP4 (`opengeodata_france_demo.mp4`).*

Regardez la vidéo : en 15 secondes, tout est dans QGIS.

Pas de navigateur ouvert. Pas de téléchargement de ZIP. Pas de token ou de clé d'API à renseigner.

Dans ce court extrait, vous voyez :
- La recherche directe dans le catalogue français
- Le chargement instantané des données
- Le calage automatique sur le territoire sélectionné

J'ai conçu **OpenGeoData France** pour régler une frustration universelle en collectivité et en bureau d'études : l'éparpillement de l'Open Data français.

Que vous ayez besoin d'un zonage PLU, d'une parcelle cadastrale, d'un zonage ZNIEFF ou des bornes de recharge de votre département, tout est accessible dans une seule fenêtre.

Le plugin est disponible gratuitement dans le gestionnaire d'extensions QGIS et sur GitHub :
https://github.com/mwjouini/OpenGeoData-France

Prenez 2 minutes pour l'installer et partagez vos retours en commentaire !

#QGIS #SIG #Geospatial #OpenData #Territoires #Geomatique
