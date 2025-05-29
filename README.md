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

Le système s’appuie sur :
- Un capteur de force **HX711** (lecture via GPIO)
- Deux IMUs **BMI270** (lecture via bus I2C)
- Un microcontrôleur (ex. Raspberry Pi) exécutant le serveur Flask

Un schéma de câblage est disponible dans le dossier `docs/` ou dans le rapport.

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
