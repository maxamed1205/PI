// --- CONNEXION AVEC LE SERVEUR VIA SOCKET.IO ---
var socket = io(); // Initialise une connexion en temps reel avec le serveur en utilisant la librairie Socket.IO

// --- VARIABLES POUR STOCKER LES DONNEES RECUES EN TEMPS REEL ---

var forceTime = []; // Liste vide pour stocker les instants (temps) ou on recoit les mesures de force
var forceData = []; // Liste vide pour stocker les valeurs de force (en Newtons)

var angleTime = []; // Liste vide pour stocker les instants (temps) ou on recoit les mesures d'angle
var angleData = []; // Liste vide pour stocker les valeurs d'amplitude (en degres)

// --- FONCTION POUR AFFICHER LE GRAPHIQUE DE FORCE EN TEMPS REEL ---

function plotForceGraph() { // Declaration de la fonction plotForceGraph
    Plotly.newPlot('graph-force', [{ // Cree un nouveau graphique dans l element HTML avec l id 'graph-force'
        x: forceTime, // Les points sur l'axe horizontal (temps)
        y: forceData, // Les points sur l'axe vertical (force)
        mode: 'lines+markers', // Affiche a la fois les lignes reliees et des points marques
        name: 'Force (N)', // Nom de la courbe
        line: {color: '#009640'} // Couleur de la ligne (vert fonce)
    }], {
        xaxis: {title: 'Temps (mm:ss)'}, // Donne un titre a l'axe horizontal
        yaxis: {title: 'Force (N)'}, // Donne un titre a l'axe vertical
        margin: {l: 50, r: 30, t: 20, b: 50}, // Definit les marges autour du graphe (left, right, top, bottom)
        autosize: true // Adapte automatiquement la taille du graphe a l'espace disponible
    }, {responsive: true}); // Rend le graphe adaptable a la taille de la fenetre
}

// --- FONCTION POUR AFFICHER LE GRAPHIQUE D'AMPLITUDE EN TEMPS REEL ---

function plotAmplitudeGraph() { // Declaration de la fonction plotAmplitudeGraph
    Plotly.newPlot('graph-amplitude', [{ // Cree un nouveau graphique dans l element HTML avec l id 'graph-amplitude'
        x: angleTime, // Les points sur l'axe horizontal (temps)
        y: angleData, // Les points sur l'axe vertical (amplitude)
        mode: 'lines+markers', // Affiche lignes + points marques
        name: 'Amplitude (deg)', // Nom de la courbe
        line: {color: '#d9534f'} // Couleur de la ligne (rouge vif)
    }], {
        xaxis: {title: 'Temps (mm:ss)'}, // Titre de l'axe horizontal
        yaxis: {title: 'Amplitude (deg)'}, // Titre de l'axe vertical
        margin: {l: 50, r: 30, t: 20, b: 50}, // Marges autour du graphe
        autosize: true // Adapte automatiquement la taille
    }, {responsive: true}); // Rend adaptable a la taille de la fenetre
}

// --- RECEPTION DES NOUVELLES DONNEES DE FORCE EN TEMPS REEL ---

socket.on('force_update', function(data) { // Quand un message de type 'force_update' est recu depuis le serveur
    var now = new Date(); // Cree un nouvel objet Date avec l'heure actuelle
    var formattedTime = now.getMinutes().toString().padStart(2, '0') + ":" + now.getSeconds().toString().padStart(2, '0'); 
    // Formate l'heure actuelle en mm:ss avec ajout de zeros si necessaire
    forceTime.push(formattedTime); // Ajoute le temps formate dans la liste forceTime
    forceData.push(data.force); // Ajoute la valeur de force recue dans la liste forceData
    plotForceGraph(); // Redessine le graphique avec les nouvelles donnees
});

// --- RECEPTION DES NOUVELLES DONNEES D'AMPLITUDE EN TEMPS REEL ---

socket.on('amplitude_update', function(data) { // Quand un message de type 'amplitude_update' est recu depuis le serveur
    var now = new Date(); // Cree un nouvel objet Date avec l'heure actuelle
    var formattedTime = now.getMinutes().toString().padStart(2, '0') + ":" + now.getSeconds().toString().padStart(2, '0');
    // Formate l'heure actuelle en mm:ss avec ajout de zeros si necessaire
    angleTime.push(formattedTime); // Ajoute le temps formate dans la liste angleTime
    angleData.push(data.amplitude); // Ajoute la valeur d'amplitude recue dans la liste angleData
    plotAmplitudeGraph(); // Redessine le graphique avec les nouvelles donnees
});

// --- ADAPTE LES GRAPHES QUAND ON CHANGE LA TAILLE DE LA FENETRE ---

window.addEventListener('resize', function() { // Ajoute un ecouteur sur l'evenement resize (redimensionnement)
    plotForceGraph(); // Redessine le graphe de force
    plotAmplitudeGraph(); // Redessine le graphe d'amplitude
});

// --- DONNEES DU PATIENT PREPAREES A PARTIR DES VARIABLES JINJA ---

var patientData = { // Objet contenant les informations sur le patient
    patient_name: "{{ patient.patient_name }}", // Nom du patient (injecte par Flask/Jinja)
    finger: "{{ patient.finger }}", // Doigt mesure
    phalange: "{{ patient.phalange }}", // Partie de doigt mesuree
    operator: "{{ patient.operator }}" // Nom de l'operateur
};

// --- EVENEMENT QUAND ON CLIQUE SUR LE BOUTON DE SAUVEGARDE ---

document.getElementById('saveButton').addEventListener('click', function() { // Detecte le clic sur le bouton 'Sauvegarder'
    socket.emit('save_data', { // Envoie un message 'save_data' au serveur avec les donnees suivantes :
		patient: { // Debut de l'objet qui contient toutes les informations du patient
			patient_name: patientData.patient_name, // Le nom du patient (prend la valeur stockee dans patientData)
			finger: patientData.finger, // Le doigt mesure (exemple : index, pouce, majeur, etc.)
			phalange: patientData.phalange, // La phalange mesuree (exemple : proximale, intermediaire, distale)
			operator: patientData.operator // Le nom de l'operateur qui effectue la mesure
		},
		force: { // Debut de l'objet qui contient toutes les donnees de force
			time: forceTime, // La liste de tous les instants (temps) ou une mesure de force a ete enregistree
			data: forceData // La liste de toutes les valeurs de force mesurees (en Newtons) correspondant aux instants
		},
		amplitude: { // Debut de l'objet qui contient toutes les donnees d'amplitude (angle)
			time: angleTime, // La liste de tous les instants (temps) ou une mesure d'amplitude a ete enregistree
			data: angleData // La liste de toutes les valeurs d'amplitude mesurees (en degres) correspondant aux instants
		}
    });
    alert('Donnees envoyees pour sauvegarde !'); // Affiche une alerte pour confirmer que l'envoi a ete fait
});

// --- EVENEMENT QUAND ON CLIQUE SUR LE BOUTON NOUVELLE MESURE ---

document.getElementById('newMeasureButton').addEventListener('click', function() { // Detecte le clic sur le bouton 'Nouvelle mesure'
    window.location.href = "/"; // Redirige vers la page d'accueil pour lancer une nouvelle mesure
});
