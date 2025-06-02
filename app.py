# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-  # Définition de l'encodage du fichier (UTF-8)
from flask import Flask, render_template, request, jsonify  # Importation des modules Flask pour créer l'application web
from flask_socketio import SocketIO, emit  # SocketIO pour gérer les communications en temps réel
import asyncio  # Module pour opérations asynchrones
import os  # Pour interagir avec le système d'exploitation (gestion de fichiers)
import csv  # Gestion des fichiers CSV
import json  # Gestion des fichiers JSON
from datetime import datetime  # Pour gérer les dates et heures
from hx711_lgpio import HX711  # Pilote du capteur HX711 (amplificateur de cellule de charge)
import numpy as np  # Librairie pour calcul numérique
import time  # Pour gérer les temps et délais
from bmi270.BMI270 import *  # Importation des fonctions relatives au capteur d'accélération BMI270
from accelerometer.lib.read_angle import ReadAngle_IMU  # Importation du module personnalisé pour lire l'angle IMU

app = Flask(__name__)  # Création de l'application Flask
socketio = SocketIO(app, async_mode="threading")  # Initialisation de SocketIO avec mode threading

patient_info = {}  # Dictionnaire pour stocker les informations du patient

# --- CONFIGURATION DU CAPTEUR HX711 ---
DOUT_PIN = 27  # Broche GPIO de sortie de données du capteur HX711
SCK_PIN = 18   # Broche GPIO pour l'horloge du capteur HX711
SEUIL_VARIATION: np.float32 = np.float32(0.1)  # Seuil minimal de variation du signal pour considérer une mesure valide
FACTEUR_ETALONNAGE: np.float32 = np.float32(80.65)  # Facteur d'étalonnage spécifique au capteur de force
OFFSET: np.float32 = np.float32(-149098.0)  # Décalage (offset) initial déterminé par calibration

SEUIL_VARIATION_ANGLE_DISTAL: np.int32 = np.int32(1)  # Seuil minimal de variation angulaire en degrés

# Vérification de la validité des broches utilisées (0 à 27 pour Raspberry Pi)
assert DOUT_PIN in range(0, 28)
assert SCK_PIN in range(0, 28)

# Initialisation du capteur HX711 avec les broches spécifiées
hx = HX711(dout_pin=DOUT_PIN, pd_sck_pin=SCK_PIN)

# Numéros de bus I2C utilisés pour les capteurs IMU (BMI270)
bus_num = [0, 1, 2]
# Initialisation de la lecture des angles articulaires via IMU sur le bus I2C primaire
ang = ReadAngle_IMU(bus_num, I2C_PRIM_ADDR)
# Calibration des capteurs IMU pour la partie gyroscopique
ang.calibrate_gyro_bias()
# Calibration des offsets pour les capteurs IMU
ang.calibrate_offsets(100)  

@app.route('/')  # Route principale (accueil)
def home():
    return render_template('index.html')  # Affichage du modèle HTML principal

@app.route('/start_measurement', methods=['POST'])  # Route pour démarrer une mesure
def start_measurement():
    global patient_info
    patient_info = request.form.to_dict()  # Récupère et stocke les informations patient envoyées par formulaire
    return render_template('measurement.html', patient=patient_info, no_card=True)  # Affiche la page mesure

@app.route('/save_patient', methods=['POST'])  # Route pour sauvegarder les données du patient
def save_patient():
    try:
        data = request.get_json()  # Récupération des données JSON envoyées par le client
        name = data.get('patient_name')  # Nom du patient
        mode = data.get('mode', 'create')  # Mode : création ou modification, défaut à 'create'

        if not name:  # Vérifie que le nom est bien présent
            return jsonify({"error": "Nom du patient manquant."}), 400

        os.makedirs('static/patients', exist_ok=True)  # Crée le dossier patients si inexistant
        filepath = os.path.join('static/patients', name.replace(" ", "_").lower() + ".json")  # Chemin vers fichier JSON du patient

        # Sauvegarde de backup si modification d'un fichier existant
        if mode == 'edit' and os.path.exists(filepath):
            os.makedirs('static/patients/history', exist_ok=True)  # Crée dossier backup si inexistant
            backup_path = os.path.join('static/patients/history', name.replace(" ", "_").lower() + "_ancien.json")
            os.replace(filepath, backup_path)  # Déplace l'ancien fichier en backup

        # Sauvegarde finale des données du patient au format JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        return jsonify({"message": "Fiche patient sauvegardée."}), 200  # Réponse positive en cas de succès

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Retourne une erreur en cas d'exception


# Route pour vérifier l'existence d'un fichier patient par nom
@app.route('/check_patient_exists/<patient_name>', methods=['GET'])
def check_patient_exists(patient_name):
    try:
        print(f"[DEBUG] Vérification de l'existence du patient : {patient_name}")  # Message de debug
        filename = patient_name.replace(" ", "_").lower() + ".json"  # Génération du nom de fichier
        filepath = os.path.join('static/patients', filename)  # Chemin complet vers le fichier patient
        return jsonify({"exists": os.path.exists(filepath)})  # Vérifie l'existence du fichier
    except Exception as e:
        print(f"[ERREUR] {e}")  # Affiche l'erreur dans la console
        return jsonify({"error": str(e)}), 500  # Retourne une erreur HTTP 500

# Route pour lister tous les fichiers patients existants
@app.route('/list_patients', methods=['GET'])
def list_patients():
    try:
        folder = 'static/patients'  # Dossier où se trouvent les fichiers patients
        os.makedirs(folder, exist_ok=True)  # Crée le dossier s'il n'existe pas
        files = [f for f in os.listdir(folder) if f.endswith('.json')]  # Liste tous les fichiers JSON du dossier
        return jsonify(files)  # Retourne la liste des fichiers JSON
    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Retourne une erreur HTTP 500

# Route pour charger les données d'un patient depuis un fichier JSON
@app.route('/load_patient/<filename>', methods=['GET'])
def load_patient(filename):
    try:
        filepath = os.path.join('static/patients', filename)  # Chemin complet vers le fichier spécifié
        if not os.path.exists(filepath):  # Vérifie si le fichier existe
            return jsonify({"error": "Fichier introuvable."}), 404  # Retourne une erreur HTTP 404

        with open(filepath, 'r', encoding='utf-8') as f:  # Ouvre le fichier en lecture
            data = json.load(f)  # Charge les données JSON du fichier
            return jsonify(data)  # Retourne les données JSON
    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Retourne une erreur HTTP 500

# Gestion de l'événement 'save_data' envoyé via SocketIO
@socketio.on('save_data')
def handle_save_data(data):
    try:
        os.makedirs('historique', exist_ok=True)  # Crée un dossier historique s'il n'existe pas
        patient = data['patient']  # Récupère les informations du patient
        force = data['force']  # Récupère les données de force
        angle_prox = data['amplitude_proximal']  # Récupère les données d'angle proximal
        angle_dist = data['amplitude_distal']  # Récupère les données d'angle distal

        now = datetime.now()  # Timestamp actuel
        date_str = now.strftime("%Y-%m-%d_%H-%M")  # Formatage du timestamp pour le nom de fichier
        filename = f"{patient['patient_name']}_{patient['finger']}_{patient['phalange']}_{patient['operator']}_{date_str}.txt"  # Génération du nom du fichier
        filepath = os.path.join('historique', filename)  # Chemin complet du fichier à créer

        max_len = max(len(force['time']), len(angle_prox['time']), len(angle_dist['time']))  # Taille maximale des listes de données
        col_width_time = 18  # Largeur des colonnes de temps
        col_width_value = 12  # Largeur des colonnes de valeurs numériques


        # Ouvre le fichier spécifié en mode écriture avec encodage UTF-8
        with open(filepath, mode='w', encoding='utf-8-sig') as file:
            # Écriture des informations du patient
            file.write(f"Patient : {patient['patient_name']}\n")  # Nom du patient
            file.write(f"Doigt : {patient['finger']}\n")  # Doigt concerné par la mesure
            file.write(f"Phalange : {patient['phalange']}\n")  # Phalange concernée par la mesure
            file.write(f"Opérateur : {patient['operator']}\n")  # Opérateur ayant effectué la mesure
            file.write(f"Date de sauvegarde : {now.strftime('%Y-%m-%d %H:%M:%S')}\n\n")  # Date et heure de sauvegarde

            # Écriture de l'en-tête des colonnes
            header = (
                "Temps (mm:ss) F".ljust(col_width_time) + " | " +  # Temps associé à la force mesurée
                "Force (N)".ljust(col_width_value) + " | " +  # Valeur de la force en Newton
                "Temps Aprox".ljust(col_width_time) + " | " +  # Temps associé à l'angle proximal
                "Angle PIP (°)".ljust(col_width_value) + " | " +  # Angle proximal (PIP)
                "Temps Adist".ljust(col_width_time) + " | " +  # Temps associé à l'angle distal
                "Angle DIP (°)".ljust(col_width_value) + "\n"  # Angle distal (DIP)
            )
            file.write(header)  # Écriture de l'en-tête dans le fichier

            # Boucle pour écrire les données ligne par ligne
            for i in range(max_len):
                # Récupération du temps et de la valeur de la force (ou chaîne vide si absent)
                f_time = force['time'][i] if i < len(force['time']) else ''
                f_val = force['data'][i] if i < len(force['data']) else ''

                # Récupération du temps et de la valeur de l'angle proximal (ou NaN si absent)
                p_time = angle_prox['time'][i] if i < len(angle_prox['time']) else ''
                p_val = angle_prox['data'][i] if i < len(angle_prox['data']) else 'NaN'

                # Récupération du temps et de la valeur de l'angle distal (ou NaN si absent)
                d_time = angle_dist['time'][i] if i < len(angle_dist['time']) else ''
                d_val = angle_dist['data'][i] if i < len(angle_dist['data']) else 'NaN'

                # Formatage des valeurs numériques avec deux décimales
                f_val_str = f"{float(f_val):.2f}" if f_val != '' else ''  # Force en format chaîne
                p_val_str = f"{float(p_val):.2f}" if p_val not in ('', 'NaN') else 'NaN'  # Angle proximal formaté
                d_val_str = f"{float(d_val):.2f}" if d_val not in ('', 'NaN') else 'NaN'  # Angle distal formaté

                # Création de la ligne à écrire dans le fichier
                line = (
                    str(f_time).ljust(col_width_time) + " | " +  # Temps force
                    str(f_val_str).ljust(col_width_value) + " | " +  # Valeur force
                    str(p_time).ljust(col_width_time) + " | " +  # Temps angle proximal
                    str(p_val_str).ljust(col_width_value) + " | " +  # Valeur angle proximal
                    str(d_time).ljust(col_width_time) + " | " +  # Temps angle distal
                    str(d_val_str).ljust(col_width_value) + "\n"  # Valeur angle distal
                )
                file.write(line)  # Écriture de la ligne de données dans le fichier

        print(f"Données sauvegardées dans {filepath}")  # Confirmation de sauvegarde dans la console

    except Exception as e:
        print(f"Erreur lors de la sauvegarde : {e}")  # Affiche l'erreur en cas d'exception


# Fonction pour lire la force du capteur HX711
def lire_force() -> np.float32:
    try:
        valeur_brute = np.float32(hx.get_raw_data_mean(times=3))  # Lecture moyenne brute du capteur HX711 (3 mesures)
        poids_estime = (valeur_brute - OFFSET) / FACTEUR_ETALONNAGE  # Conversion de la valeur brute en poids estimé
        force_estimee = (poids_estime / np.float32(1000)) * np.float32(9.81)  # Conversion du poids en force (Newton)
        return np.round(force_estimee, 1)  # Arrondi de la force estimée à un chiffre après la virgule
    except Exception as e:
        print(f"Erreur capteur: {e}")  # Affichage de l'erreur dans la console
        return np.float32(0)  # Retourne 0 en cas d'erreur

# Fonction pour lire la force en continu
def read_force_continuously():
    last_force = None  # Initialisation de la dernière valeur de force
    while True:
        force = lire_force()  # Lecture de la force
        if last_force is None or np.abs(force - last_force) >= SEUIL_VARIATION:  # Vérification de la variation minimale
            last_force = force  # Mise à jour de la dernière force enregistrée
            socketio.emit('force_update', {'force': float(force)})  # Envoi de la valeur de force via socket
        time.sleep(0.1)  # Délai entre deux lectures (100 ms)

# Fonction pour lire l'angle via capteur IMU
def lire_angle() -> np.int32:
    try:
        angle_distal, angle_proximal = ang.read_angle()  # Lecture des angles distal et proximal
        return angle_distal, angle_proximal  # Retourne les deux valeurs d'angle
    except Exception as e:
        print(f"Erreur capteur: {e}")  # Affichage de l'erreur
        return np.int32(0)  # Retourne 0 en cas d'erreur

# Fonction pour lire les angles distal et proximal en continu
def read_angle_distal_continuously():
    last_angle_distal = None  # Dernière valeur de l'angle distal
    last_angle_proximal = None  # Dernière valeur de l'angle proximal
    while True:
        angle_distal, angle_proximal = lire_angle()  # Lecture des angles
        if last_angle_distal is None or np.abs(angle_distal - last_angle_distal) >= SEUIL_VARIATION_ANGLE_DISTAL:
            last_angle_distal = angle_distal  # Mise à jour dernière valeur angle distal
            socketio.emit('angle_distal_update', {'Angle distale': float(angle_distal)})  # Envoi angle distal via socket

        if last_angle_proximal is None or np.abs(angle_proximal - last_angle_proximal) >= SEUIL_VARIATION_ANGLE_DISTAL:
            last_angle_proximal = angle_proximal  # Mise à jour dernière valeur angle proximal
            socketio.emit('angle_proximal_update', {'Angle proximal': float(angle_proximal)})  # Envoi angle proximal via socket

        time.sleep(0.1)  # Délai entre deux lectures (100 ms)

# Fonction pour nettoyer les ressources GPIO utilisées par le capteur HX711
def cleanup():
    print("Nettoyage GPIO")  # Affiche un message indiquant le nettoyage des GPIO
    hx.cleanup()  # Nettoyage des broches GPIO utilisées par le HX711

# Fonction asynchrone pour réinitialiser le capteur HX711
async def reset():
    print("Réinitialisation du capteur")  # Affiche un message indiquant le début de la réinitialisation
    hx.zero()  # Réinitialisation du capteur à zéro (calibration)
    await asyncio.sleep(1)  # Attente d'une seconde pour stabiliser la réinitialisation
    print("Capteur réinitialisé !")  # Message confirmant la réinitialisation

# Gestionnaire d'événement SocketIO lorsqu'un client se connecte
@socketio.on('connect')
def on_connect():
    print("Client connecté")  # Affiche un message lors de la connexion d'un client
    # Lance les tâches de lecture continue de force et d'angle en arrière-plan
    socketio.start_background_task(read_force_continuously)
    socketio.start_background_task(read_angle_distal_continuously)

# Point d'entrée principal du script
if __name__ == "__main__":
    asyncio.run(reset())  # Exécute la fonction de réinitialisation de manière asynchrone
    socketio.run(app, host="0.0.0.0", port=5000)  # Lance l'application Flask avec SocketIO sur toutes les interfaces réseau disponibles