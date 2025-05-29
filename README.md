# PI – Application de mesure biomécanique en temps réel

## 📌 Présentation

Cette application permet d’acquérir et de visualiser en temps réel des mesures biomécaniques (force et angles articulaires) à l’aide de capteurs connectés à une interface web. Elle repose sur une architecture client-serveur construite avec Flask, Socket.IO, HTML, CSS et JavaScript.

Elle a été développée dans le cadre du projet P.I. à la HES-SO, avec une approche modulaire pensée pour la recherche clinique et l’analyse du mouvement.

---

## 🖥️ Architecture logicielle

L’architecture suit un modèle client-serveur :

- **Frontend** : interface utilisateur en HTML/CSS/JavaScript
- **Backend** : serveur Flask + Socket.IO pour la lecture capteur, la transmission des données et la sauvegarde

Le système fonctionne en boucle temps réel :
1. L'utilisateur saisit une fiche patient
2. Le serveur lit les capteurs HX711 (force) et BMI270 (angles)
3. Les mesures sont transmises en direct à l'interface via WebSocket
4. À la fin, un fichier texte structuré est généré automatiquement

---

## 📂 Organisation du code

### 1. `templates/` — Pages HTML

- `base.html` : structure de base commune (en-tête, styles, bloc `content`)
- `index.html` : page d’accueil (création et chargement de fiche patient)
- `measurement.html` : page de mesure avec graphiques en temps réel

### 2. `templates/components/` — Fragments HTML réutilisables

- `create_patient_form.html` : création d’un nouveau patient
- `editpatientform.html` : modification d’une fiche existante
- `load_patient_form.html` : chargement d’un patient
- `measure_form.html` : formulaire de métadonnées de la session
- `patient_buttons.html` : boutons de commande de la session

### 3. `static/css/` — Feuilles de style

- `base.css` : styles globaux
- `index.css` : mise en page de l’accueil
- `measurement.css` : styles pour les mesures et courbes dynamiques

### 4. `static/js/` — Scripts JavaScript

- `index.js` : gestion des formulaires sur la page d’accueil
- `measurement.js` : 
  - Connexion à Socket.IO
  - Réception des données en temps réel
  - Affichage avec Plotly.js
  - Sauvegarde des mesures
  - Gestion des boutons

---

## ⚙️ Backend — `app.py`

Le fichier `app.py` joue un rôle central :

- Affichage des pages web via Flask
- Lecture des capteurs HX711 et BMI270
- Transmission des données avec Socket.IO
- Sauvegarde automatique dans un fichier texte structuré
- Fiches patient stockées en local au format JSON

Deux tâches de fond sont exécutées à la connexion :
- Lecture continue de la force (`read_force_continuously`)
- Lecture continue des angles (`read_angle_distal_continuously`)

Les données sont transmises uniquement en cas de variation significative.

---

## 📷 Schéma de câblage

![Schéma de câblage complet](https://raw.githubusercontent.com/maxamed1205/PI/main/Solution_finale.png)

Le système s’appuie sur :
- Un capteur de force **HX711** (lecture via GPIO)
- Trois IMUs **BMI270** (lecture via bus I2C)
- Un microcontrôleur **Raspberry Pi 5** qui exécute le serveur Flask

### 🔧 Conception électronique

Le système est conçu pour mesurer trois types de données biomécaniques :
- La **force** exercée par l’utilisateur
- L’**angle de la phalange distale**
- L’**angle de la phalange proximale**

#### ➤ Mesure d’angle (IMU)

Les angles articulaires sont obtenus à l’aide d’IMU (accéléromètre + gyroscope).  
- L’accéléromètre fournit une mesure de l’orientation relative au sol.
- Le gyroscope donne la vitesse de rotation.  
Pour éviter les dérives dans le temps, un **filtre de Kalman** est utilisé. Il ajuste les données en continu, ce qui améliore la stabilité des résultats.

L’angle entre deux phalanges est calculé par la différence entre les mesures de deux IMUs placés de part et d’autre de l’articulation.

#### ➤ Mesure de force (HX711)

La mesure de force repose sur un **capteur de déformation**, relié à un module **HX711**. Ce module convertit les données analogiques du capteur en signaux numériques lisibles par le Raspberry Pi via GPIO.

---

### 🧷 Connexions GPIO (Raspberry Pi 5)

Voici le tableau de câblage utilisé pour connecter tous les capteurs au Raspberry Pi 5 :

| N° Connecteur | GPIO | Fonction                          |
|---------------|------|-----------------------------------|
| 1             | -    | 3.3V alimentation IMU 1           |
| 2             | -    | 5V alimentation HX711             |
| 3             | 2    | SDA IMU 1                         |
| 5             | 3    | SCL IMU 1                         |
| 6             | -    | GND IMU 1                         |
| 9             | -    | GND HX711                         |
| 12            | 18   | CLK HX711                         |
| 13            | 27   | DATA HX711                        |
| 17            | -    | 3.3V alimentation IMU 2–3         |
| 27            | 0    | SDA IMU 2                         |
| 28            | 1    | SCL IMU 2                         |
| 30            | -    | GND IMU 2                         |
| 32            | 12   | SDA IMU 3                         |
| 33            | 13   | SCL IMU 3                         |
| 34            | -    | GND IMU 3                         |

---

## 📁 Dossier de sauvegarde

Les mesures sont exportées au format `.txt` :
- Incluent les informations patient, opérateur, doigt et phalange
- Format horodaté pour chaque ligne
- Enregistrées automatiquement dans un dossier historique

---

## 🧪 Objectifs pédagogiques

Ce projet vise à :

- Développer une application biomédicale interactive en temps réel
- Maîtriser Flask, WebSocket, Plotly.js et la lecture de capteurs physiques
- Fournir un outil fiable pour la recherche clinique ou l’expérimentation en biomécanique

---

## 👤 Auteurs

Projet réalisé par :  
**Maxamed Nuur Maxamed**,  
en collaboration avec **Favario M.**, **Loup O.** et **Di Benedetto A.**

Encadrement : Sciences de l'information médicale – HUG  
HES-SO Master – 2024–2025

---

## 📜 Licence

Ce projet est partagé à des fins éducatives. Pour toute utilisation hors cadre académique, merci de contacter l’auteur.
