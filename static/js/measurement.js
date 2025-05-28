// --------------------------------------------------
// Connexion avec le serveur via Socket.IO
// --------------------------------------------------

var socket = io(); // Initialise la connexion en temps réel avec le serveur via Socket.IO

// --------------------------------------------------
// Variables pour stocker les données reçues en temps réel
// --------------------------------------------------

var forceTime = [];            // Liste des horodatages associés aux mesures de force
var forceData = [];           // Liste des valeurs de force reçues
var angleTime = [];           // Liste des horodatages associés aux mesures d'angle
var angleData = [];           // Liste des angles distaux mesurés
var angleDataProximal = [];   // Liste des angles proximaux mesurés
var forceVsAngleX = [];       // Liste des angles (x) pour graphique force vs angle
var forceVsAngleY = [];       // Liste des forces (y) pour graphique force vs angle

let latestDistal = null;      // Dernière valeur d'angle distal reçue
let latestProximal = null;    // Dernière valeur d'angle proximal reçue
let blockedPhalange = null;   // Variable indiquant la phalange bloquée sélectionnée par l’utilisateur

// --------------------------------------------------
// Fonction utilitaire pour formater l'heure (mm:ss)
// --------------------------------------------------

function getFormattedTime() {
    var now = new Date(); // Récupère l’instant actuel
    return now.getMinutes().toString().padStart(2, '0') + ":" + now.getSeconds().toString().padStart(2, '0'); // Formate mm:ss
}


// --------------------------------------------------
// Initialisation des éléments une fois le DOM chargé
// --------------------------------------------------

document.addEventListener('DOMContentLoaded', () => {
    blockedPhalange = window.blockedPhalange; // Récupère la variable JS globale définie dans le template HTML
    console.log("🚀 JS ready — blockedPhalange =", blockedPhalange); // Affiche la phalange bloquée pour débogage
    plotForceVsAngleEmpty(); // Initialise un graphique vide pour force vs angle (fonction à définir)
});

// --------------------------------------------------
// Réception des données de force depuis le serveur
// --------------------------------------------------

socket.on('force_update', function(data) {
    var now = getFormattedTime();   // Récupère l’heure actuelle au format mm:ss
    forceTime.push(now);            // Ajoute le temps à la liste des temps
    forceData.push(data.force);     // Ajoute la valeur de force reçue à la liste
    plotForceGraph();               // Met à jour le graphique avec les nouvelles données
});

// --------------------------------------------------
// Réception des données d’angle distal depuis le serveur
// --------------------------------------------------

socket.on('angle_distal_update', function(data) {
    latestDistal = parseFloat(data['Angle distale']).toFixed(1); // Convertit l’angle en nombre à 1 décimale
    document.getElementById('angle-distal').textContent = latestDistal; // Affiche l’angle dans l’interface
    console.log("📡 distal reçu:", data); // Affiche dans la console pour vérification
    maybePlotNewPoint(); // Tente de tracer un point dans force vs angle (à condition que les deux angles soient dispo)
});

// --------------------------------------------------
// Réception des données d’angle proximal depuis le serveur
// --------------------------------------------------

socket.on('angle_proximal_update', function(data) {
    latestProximal = parseFloat(data['Angle proximal']).toFixed(1); // Convertit l’angle en nombre à 1 décimale
    document.getElementById('angle-proximal').textContent = latestProximal; // Affiche l’angle dans l’interface
    console.log("📡 proximal reçu:", data); // Affiche dans la console pour vérification
    maybePlotNewPoint(); // Tente de tracer un point dans force vs angle
});

// --------------------------------------------------
// Tracer le graphique de la force en fonction du temps
// --------------------------------------------------

function plotForceGraph() {
    Plotly.newPlot('graph-force', [{ // Crée un graphique avec Plotly dans l’élément HTML 'graph-force'
        x: forceTime,                // Axe des abscisses : temps
        y: forceData,               // Axe des ordonnées : valeurs de force
        mode: 'markers',            // Mode "points"
        name: 'Force (N)',          // Nom de la courbe
        line: {color: '#009640'}    // Couleur verte
    }], {
        xaxis: {title: 'Temps (mm:ss)'},    // Titre de l’axe X
        yaxis: {title: 'Force (N)'},        // Titre de l’axe Y
        margin: {l: 50, r: 30, t: 20, b: 50},// Marges du graphe
        autosize: true                       // Redimensionnement automatique
    }, {responsive: true});                  // Rend le graphe adaptatif à la taille de l’écran
}

// --------------------------------------------------
// Tracer le graphique de l’amplitude en fonction du temps
// --------------------------------------------------

function plotAmplitudeGraph() {
    Plotly.newPlot('graph-amplitude', [
        {
            x: angleTime,                   // Axe X : temps
            y: angleData,                   // Axe Y : angle distal
            mode: 'markers',                // Mode "points"
            name: 'Distal (°)',             // Nom de la série
            line: { color: '#d9534f' }      // Couleur rouge
        },
        {
            x: angleTime,                   // Axe X : temps (le même)
            y: angleDataProximal,           // Axe Y : angle proximal
            mode: 'markers',
            name: 'Proximal (°)',
            line: { color: '#007bff' }      // Couleur bleue
        }
    ], {
        xaxis: { title: 'Temps (mm:ss)' },  // Titre de l’axe X
        yaxis: { title: 'Amplitude (°)' },  // Titre de l’axe Y
        margin: { l: 50, r: 30, t: 20, b: 50 },
        autosize: true
    }, { responsive: true });
}

// --------------------------------------------------
// Ajoute un point sur les graphiques si les deux angles sont disponibles
// --------------------------------------------------
function maybePlotNewPoint() {
    if (latestDistal !== null && latestProximal !== null) { // Vérifie que les deux mesures d'angles ont été reçues
        const now = getFormattedTime(); // Récupère l’heure actuelle
        angleTime.push(now); // Enregistre l’instant de mesure
        angleData.push(parseFloat(latestDistal)); // Ajoute l’angle distal au tableau
        angleDataProximal.push(parseFloat(latestProximal)); // Ajoute l’angle proximal au tableau

        plotAmplitudeGraph(); // Met à jour le graphique d’amplitude

        const lastForce = forceData[forceData.length - 1]; // Récupère la dernière valeur de force reçue
        let angleLibre = null; // Initialisation de la variable angle libre (celui non bloqué)

        if (blockedPhalange === "proximale") { // Si la phalange proximale est bloquée
            angleLibre = latestDistal; // L’angle libre est distal
        } else if (blockedPhalange === "distale") { // Si la phalange distale est bloquée
            angleLibre = latestProximal; // L’angle libre est proximal
        }

        if (lastForce !== undefined && angleLibre !== null) { // Si la force et l’angle libre sont valides
            updateForceVsAngle(lastForce, angleLibre); // Ajoute le point au graphe force vs angle
            console.log("✅ Donnée ajoutée au graphique Force vs Angle:", lastForce, angleLibre);
        }

        latestDistal = null; // Réinitialise la dernière valeur reçue
        latestProximal = null;
    }
}

// --------------------------------------------------
// Initialise un graphique vide Force vs Angle libre
// --------------------------------------------------

function plotForceVsAngleEmpty() { // Fonction pour initialiser un graphique vide Force vs Angle
    Plotly.newPlot('graph-force-vs-angle', [{ // Crée un nouveau tracé Plotly dans l’élément HTML avec l’ID spécifié
        x: [], // Initialise la série d’abscisses (angle libre) comme un tableau vide
        y: [], // Initialise la série d’ordonnées (force) comme un tableau vide
        mode: 'markers', // Mode d’affichage : uniquement des points (pas de lignes)
        name: 'Force vs Angle libre', // Légende de la courbe dans l’interface graphique
        line: { color: '#17a2b8' } // Couleur utilisée pour les points
    }], {
        xaxis: { title: 'Angle libre (°)' }, // Titre affiché pour l’axe horizontal
        yaxis: { title: 'Force (N)' }, // Titre affiché pour l’axe vertical
        margin: { l: 50, r: 30, t: 20, b: 50 }, // Marges autour du graphique
        title: "Force en fonction de l'angle mesuré (libre)" // Titre du graphique
    }, { responsive: true }); // Rend le graphique adaptatif au redimensionnement de l’écran
}

// --------------------------------------------------
// Met à jour le graphique Force en fonction de l’Angle libre
// --------------------------------------------------
function updateForceVsAngle(forceValue, angleLibre) {
    forceVsAngleX.push(parseFloat(angleLibre)); // Ajoute l’angle à la liste des abscisses
    forceVsAngleY.push(parseFloat(forceValue)); // Ajoute la force à la liste des ordonnées

    console.log("📈 Tracé Force vs Angle:", forceVsAngleX, forceVsAngleY); // Affiche les données actuelles en console

    Plotly.newPlot('graph-force-vs-angle', [{ // Crée un nouveau graphique dans la div avec l’ID donné
        x: forceVsAngleX, // Axe des abscisses : angles libres
        y: forceVsAngleY, // Axe des ordonnées : forces
        mode: 'markers', // Type de graphique : nuage de points
        name: 'Force vs Angle libre', // Légende de la courbe
        line: { color: '#17a2b8' } // Couleur de la courbe
    }], {
        xaxis: { title: 'Angle libre (°)' }, // Titre de l’axe des abscisses
        yaxis: { title: 'Force (N)' }, // Titre de l’axe des ordonnées
        margin: { l: 50, r: 30, t: 20, b: 50 }, // Marges du graphique
        title: "Force en fonction de l'angle mesuré (libre)" // Titre du graphique
    }, { responsive: true }); // Rend le graphique adaptatif à la taille de l’écran
}


// --------------------------------------------------
// Rend les graphiques adaptatifs au redimensionnement de la fenêtre
// --------------------------------------------------
window.addEventListener('resize', function() {
    plotForceGraph(); // Met à jour le graphe de force
    plotAmplitudeGraph(); // Met à jour le graphe d’amplitude
});

// --------------------------------------------------
// Événement de sauvegarde des données
// --------------------------------------------------
document.getElementById('saveButton').addEventListener('click', function() { // Ajoute un écouteur de clic sur le bouton de sauvegarde
    socket.emit('save_data', { // Envoie les données au serveur via Socket.IO sous l'événement 'save_data'
        patient: { // Données d’identification du patient
            patient_name: patientData.patient_name, // Nom du patient (extrait d’un objet global patientData)
            finger: patientData.finger, // Doigt mesuré
            phalange: patientData.phalange, // Phalange concernée (distale ou proximale)
            operator: patientData.operator // Nom de l’opérateur ou expérimentateur
        },
        force: { // Données de force mesurée
            time: forceTime, // Liste des instants de mesure de la force
            data: forceData // Liste des valeurs de force en Newtons
        },
        amplitude_proximal: { // Données d’amplitude pour la phalange proximale
            time: angleTime, // Liste des instants correspondants
            data: angleDataProximal // Valeurs angulaires mesurées pour la phalange proximale
        },
        amplitude_distal: { // Données d’amplitude pour la phalange distale
            time: angleTime, // Liste des instants correspondants (mêmes que ci-dessus)
            data: angleData // Valeurs angulaires mesurées pour la phalange distale
        }
    });
    alert('Donnees envoyees pour sauvegarde !'); // Affiche une alerte pour confirmer l’envoi des données à l’utilisateur
});

// --------------------------------------------------
// Bouton pour démarrer une nouvelle mesure
// --------------------------------------------------
document.getElementById('newMeasureButton').addEventListener('click', function() {
    window.location.href = "/"; // Redirige l’utilisateur vers la page d’accueil (nouvelle mesure)
});

// --------------------------------------------------
// Affiche ou cache les graphiques dynamiquement
// --------------------------------------------------
document.getElementById('toggleGraphsButton').addEventListener('click', function() {
    const container = document.getElementById('graphs-container'); // Récupère le conteneur des graphiques
    graphsVisible = !graphsVisible; // Inverse l’état d’affichage
    container.style.display = graphsVisible ? 'flex' : 'none'; // Affiche ou masque le bloc
    this.textContent = graphsVisible ? "Cacher les graphiques" : "Afficher les graphiques"; // Met à jour le texte du bouton
});
