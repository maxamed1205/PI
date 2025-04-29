# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import asyncio
import os
import csv
import json
from datetime import datetime
from hx711_lgpio import HX711
import numpy as np
import time

app = Flask(__name__)
socketio = SocketIO(app, async_mode="threading")

patient_info = {}

# --- CONFIG CAPTEUR ---
DOUT_PIN = 27
SCK_PIN = 18
SEUIL_VARIATION: np.float32 = np.float32(0.1)
FACTEUR_ETALONNAGE: np.float32 = np.float32(80.65)
OFFSET: np.float32 = np.float32(-149098.0)

assert DOUT_PIN in range(0, 28)
assert SCK_PIN in range(0, 28)

hx = HX711(dout_pin=DOUT_PIN, pd_sck_pin=SCK_PIN)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/start_measurement', methods=['POST'])
def start_measurement():
    global patient_info
    patient_info = request.form.to_dict()
    return render_template('measurement.html', patient=patient_info, no_card=True)

@app.route('/save_patient', methods=['POST'])
def save_patient():
    try:
        data = request.get_json()
        name = data.get('patient_name')
        mode = data.get('mode', 'create')

        if not name:
            return jsonify({"error": "Nom du patient manquant."}), 400

        os.makedirs('static/patients', exist_ok=True)
        filepath = os.path.join('static/patients', name.replace(" ", "_").lower() + ".json")

        # ➡️ Backup s'il s'agit d'une modification
        if mode == 'edit' and os.path.exists(filepath):
            os.makedirs('static/patients/history', exist_ok=True)
            backup_path = os.path.join('static/patients/history', name.replace(" ", "_").lower() + "_ancien.json")
            os.replace(filepath, backup_path)

        # ➡️ Sauvegarde finale
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        return jsonify({"message": "Fiche patient sauvegardée."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/check_patient_exists/<patient_name>', methods=['GET'])
def check_patient_exists(patient_name):
    try:
        print(f"[DEBUG] Vérification de l'existence du patient : {patient_name}")
        filename = patient_name.replace(" ", "_").lower() + ".json"
        filepath = os.path.join('static/patients', filename)
        return jsonify({"exists": os.path.exists(filepath)})
    except Exception as e:
        print(f"[ERREUR] {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/list_patients', methods=['GET'])
def list_patients():
    try:
        folder = 'static/patients'
        os.makedirs(folder, exist_ok=True)
        files = [f for f in os.listdir(folder) if f.endswith('.json')]
        return jsonify(files)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/load_patient/<filename>', methods=['GET'])
def load_patient(filename):
    try:
        filepath = os.path.join('static/patients', filename)
        if not os.path.exists(filepath):
            return jsonify({"error": "Fichier introuvable."}), 404

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@socketio.on('save_data')
def handle_save_data(data):
    try:
        os.makedirs('historique', exist_ok=True)
        patient = data['patient']
        force = data['force']
        angle = data['amplitude']

        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d_%H-%M")
        filename = f"{patient['patient_name']}_{patient['finger']}_{patient['phalange']}_{patient['operator']}_{date_str}.txt"
        filepath = os.path.join('historique', filename)

        max_len = max(len(force['time']), len(angle['time']))
        col_width_time = 18
        col_width_value = 12

        with open(filepath, mode='w', encoding='utf-8-sig') as file:
            file.write(f"Patient : {patient['patient_name']}\n")
            file.write(f"Doigt : {patient['finger']}\n")
            file.write(f"Phalange : {patient['phalange']}\n")
            file.write(f"Opérateur : {patient['operator']}\n")
            file.write(f"Date de sauvegarde : {now.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            header = (
                "Temps (mm:ss) F".ljust(col_width_time) + " | " +
                "Force (N)".ljust(col_width_value) + " | " +
                "Temps (mm:ss) A".ljust(col_width_time) + " | " +
                "Amplitude (°)".ljust(col_width_value) + "\n"
            )
            file.write(header)

            for i in range(max_len):
                f_time = force['time'][i] if i < len(force['time']) else ''
                f_val = force['data'][i] if i < len(force['data']) else ''
                a_time = angle['time'][i] if i < len(angle['time']) else ''
                a_val = angle['data'][i] if i < len(angle['data']) else 'NaN'

                f_val_str = f"{float(f_val):.2f}" if f_val != '' else ''
                a_val_str = f"{float(a_val):.2f}" if a_val not in ('', 'NaN') else 'NaN'

                line = (
                    str(f_time).ljust(col_width_time) + " | " +
                    str(f_val_str).ljust(col_width_value) + " | " +
                    str(a_time).ljust(col_width_time) + " | " +
                    str(a_val_str).ljust(col_width_value) + "\n"
                )
                file.write(line)

        print(f"Données sauvegardées dans {filepath}")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde : {e}")

def lire_force() -> np.float32:
    try:
        valeur_brute = np.float32(hx.get_raw_data_mean(times=3))
        poids_estime = (valeur_brute - OFFSET) / FACTEUR_ETALONNAGE
        force_estimee = (poids_estime / np.float32(1000)) * np.float32(9.81)
        return np.round(force_estimee, 1)
    except Exception as e:
        print(f"Erreur capteur: {e}")
        return np.float32(0)

def read_force_continuously():
    last_force = None
    while True:
        force = lire_force()
        if last_force is None or np.abs(force - last_force) >= SEUIL_VARIATION:
            last_force = force
            socketio.emit('force_update', {'force': float(force)})
        time.sleep(0.1)

def cleanup():
    print("Nettoyage GPIO")
    hx.cleanup()

async def reset():
    print("Reinitialisation du capteur")
    hx.zero()
    await asyncio.sleep(1)
    print("Capteur reinitialise !")

@socketio.on('connect')
def on_connect():
    print("Client connecté")
    socketio.start_background_task(read_force_continuously)

if __name__ == "__main__":
    asyncio.run(reset())
    socketio.run(app, host="0.0.0.0", port=5000)