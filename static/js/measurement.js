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
// var forceVsAngleX = [];       // Liste des angles (x) pour graphique force vs angle
// var forceVsAngleY = [];       // Liste des forces (y) pour graphique force vs angle

let latestDistal = null;      // Dernière valeur d'angle distal reçue
let latestProximal = null;    // Dernière valeur d'angle proximal reçue
let blockedPhalange = null;   // Variable indiquant la phalange bloquée sélectionnée par l’utilisateur

let color = '#17a2b8'; // Couleur par défaut pour les points du graphique Force vs Angle

// Liste des séries enregistrées et série en cours
const measurementSeries = []; // Tableau pour stocker toutes les séries de mesure terminées (chacune avec force, angle, horodatage, etc.)
let currentSeries = null;    // Variable temporaire utilisée pour stocker les données de la série en cours de capture (avant validation finale)

// Générateur de couleurs dynamiques par angle
const angleColorMap = {};    // Dictionnaire (objet JavaScript) associant chaque angle (ex: '30°', '45°') à une couleur unique pour le graphique
let colorIndex = 0;          // Compteur pour suivre la progression dans la palette de couleurs disponibles

// Fonction pour générer une couleur unique pour chaque nouvel angle rencontré
function generateColor(angleLabel) {
    // Vérifie si une couleur est déjà attribuée à cet angle — si oui, la retourne
    if (angleColorMap[angleLabel]) {
        return angleColorMap[angleLabel]; // Renvoie la couleur déjà assignée à cet angle
    }

    // Palette de 10 couleurs prédéfinies (choisies pour être facilement distinguables dans un graphique)
    const palette = [
        '#1f77b4', // bleu
        '#ff7f0e', // orange
        '#2ca02c', // vert
        '#d62728', // rouge
        '#9467bd', // violet
        '#8c564b', // brun
        '#e377c2', // rose
        '#7f7f7f', // gris
        '#bcbd22', // jaune verdâtre
        '#17becf'  // cyan
    ];

    // Sélectionne une couleur de la palette en fonction de l’indice courant (avec modulo pour boucler après 10 couleurs)
    const color = palette[colorIndex % palette.length];

    // Associe cette couleur au label d’angle (ex: '60°') dans le dictionnaire
    angleColorMap[angleLabel] = color;

    // Incrémente l’indice pour la prochaine couleur
    colorIndex++;

    // Retourne la couleur assignée
    return color;
}

function generateUniqueLabel(baseLabel) {
    let existingLabels = measurementSeries.map(s => s.label);
    if (currentSeries) {
        existingLabels.push(currentSeries.label);
    }

    if (!existingLabels.includes(`Blocage D-I à ${baseLabel}`)) {
        return `Blocage D-I à ${baseLabel}`;
    }

    let suffix = 1;
    while (existingLabels.includes(`Blocage D-I à ${baseLabel} #${suffix}`)) {
        suffix++;
    }
    return `Blocage D-I à ${baseLabel} #${suffix}`;
}



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

document.addEventListener('DOMContentLoaded', () => { // Déclenché lorsque le HTML est complètement chargé (hors images, CSS)
    blockedPhalange = window.blockedPhalange; // Récupère la variable globale transmise depuis le HTML (via template Jinja2)
    console.log("🚀 JS ready — blockedPhalange =", blockedPhalange); // Affiche dans la console la phalange bloquée (utile pour déboguer)

    plotForceGraph(); // Affiche dès le départ le graphique Force vs Temps (vide mais présent)
    plotAmplitudeGraph(); // Affiche dès le départ le graphique Amplitude vs Temps (vide aussi)
    // plotForceVsAngleEmpty(); // Initialise le graphe Force vs Angle avec des tableaux vides
    renderForceVsAnglePlot(); // ⬅️ Affiche le graphique vide au chargement

    // Ajoute un écouteur de changement de sélection dans la liste déroulante
    const selector = document.getElementById("seriesSelector");
    if (selector) {
        selector.addEventListener("change", () => {
            renderForceVsAnglePlot(); // Met à jour le graphique selon la sélection
        });
    }

    setTimeout(() => { // Délai pour laisser le temps au DOM/CSS de se stabiliser avant de forcer le redimensionnement
        Plotly.Plots.resize(document.getElementById('graph-force')); // Force Plotly à recalculer la taille du graphe de force
        Plotly.Plots.resize(document.getElementById('graph-amplitude')); // Force Plotly à redimensionner le graphe d’amplitude
        Plotly.Plots.resize(document.getElementById('graph-force-vs-angle')); // Force Plotly à redimensionner le graphe force/angle
    }, 200); // Délai en millisecondes (0.2 seconde) pour que tout soit bien prêt avant d’ajuster les graphes

    const startBtn = document.getElementById("startSeriesButton"); // ➤ Récupère le bouton HTML correspondant à l’ID "startSeriesButton" (bouton 'Démarrer la mesure')

    if (startBtn) { // ➤ Vérifie que le bouton existe bien dans le DOM (évite les erreurs si l’élément est introuvable)

        startBtn.disabled = true; // 🔒 Désactive le bouton par défaut au chargement de la page, tant que les données (angles) ne sont pas encore disponibles

        startBtn.addEventListener("click", () => { // ➤ Ajoute un écouteur d’événement : quand l’utilisateur clique sur le bouton...
            onStartMeasurementSeries(); // ➤ ... on appelle la fonction qui lance une nouvelle série de mesure avec l’angle détecté automatiquement
        });

    }
    const stopBtn = document.getElementById("stopSeriesButton"); // 🔴 Bouton "Interrompre la mesure"

    if (stopBtn) { // ✅ Vérifie si le bouton existe réellement dans le DOM (évite des erreurs si l’élément est absent)

        console.log("🛑 Bouton 'Interrompre la mesure' détecté dans le DOM"); // 🪵 Log informatif : confirme que le bouton est bien présent dans la page

        stopBtn.addEventListener("click", () => { // ➕ Ajoute un écouteur d’événement : exécute la fonction ci-dessous lorsqu’un clic est effectué sur le bouton

            console.log("🧨 Clic détecté sur le bouton 'Interrompre la mesure'"); // 🪵 Log : confirme que le clic sur le bouton a bien été détecté

            if (currentSeries) { // ✅ Vérifie s’il existe actuellement une série de mesure en cours
                console.log("📊 Série en cours trouvée :", currentSeries.label); // 🪵 Log : affiche le nom (label) de la série active
            } else {
                console.warn("⚠️ Aucune série active au moment de l'interruption !"); // ⚠️ Avertit qu’aucune série n’était en cours (rien à interrompre)
            }

            if (currentSeries && !currentSeries.stopped) { // ✅ Double condition : vérifie qu’une série est active ET qu’elle n’est pas encore marquée comme arrêtée

                currentSeries.stopped = true; // 🛑 Marque explicitement la série comme arrêtée (évite que de nouveaux points soient ajoutés)
                measurementSeries.push(currentSeries); // 📥 Ajoute cette série complète à la liste globale des séries enregistrées (pour affichage ou export)
                console.log("📥 Série ajoutée à la liste des séries enregistrées :", currentSeries.label); // 🪵 Log de confirmation de l’enregistrement

                currentSeries = null; // 🔄 Réinitialise la variable (plus de série active à ce stade, on attend une nouvelle série si besoin)
                renderForceVsAnglePlot(); // 🔄 Met à jour le graphique "Force vs Angle" pour refléter l’arrêt de la série actuelle
                alert("Série interrompue manuellement !"); // 🔔 Message utilisateur : feedback visuel que la série a été bien arrêtée

            } else {
                console.log("⏸️ Série déjà arrêtée ou inexistante — aucune action nécessaire."); // ℹ️ Cas où soit la série est déjà arrêtée, soit aucune n’a été démarrée : rien à faire
            }

        });

    } else {
        console.warn("❌ Bouton 'stopSeriesButton' introuvable dans le DOM !"); // ⚠️ Avertissement si le bouton n’est pas trouvé dans la page HTML (problème potentiel d’intégration ou de chargement)
    }


});

function updateStartButtonState() {
    const startBtn = document.getElementById("startSeriesButton"); // ➤ Récupère le bouton HTML 'Démarrer la mesure' via son ID

    if (!startBtn) return; // ➤ Si le bouton n’existe pas dans la page, on quitte immédiatement la fonction (sécurité)

    // --------------------------------------------------
    // Vérifie si la donnée nécessaire est disponible
    // --------------------------------------------------

    const ready = // ➤ Variable booléenne : indique si le bouton peut être activé
        (blockedPhalange === "proximale" && latestDistal !== null) || // ➤ Cas 1 : si la phalange bloquée est proximale, alors on attend un angle distal valide
        (blockedPhalange === "distale" && latestProximal !== null);   // ➤ Cas 2 : si la phalange bloquée est distale, alors on attend un angle proximal valide

    startBtn.disabled = !ready; // ➤ Active le bouton si `ready` est vrai, sinon le désactive (inversion logique avec `!`)
}


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
    // console.log("📡 distal reçu:", data); // Affiche dans la console pour vérification
    updateStartButtonState(); // ✅ Vérifie si bouton peut être activé
    maybePlotNewPoint(); // Tente de tracer un point dans force vs angle (à condition que les deux angles soient dispo)
});

// --------------------------------------------------
// Réception des données d’angle proximal depuis le serveur
// --------------------------------------------------

socket.on('angle_proximal_update', function(data) {
    latestProximal = parseFloat(data['Angle proximal']).toFixed(1); // Convertit l’angle en nombre à 1 décimale
    document.getElementById('angle-proximal').textContent = latestProximal; // Affiche l’angle dans l’interface
    // console.log("📡 proximal reçu:", data); // Affiche dans la console pour vérification
    updateStartButtonState(); // ✅ Vérifie si bouton peut être activé
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
            color = '#d9534f'; // Rouge = distal (car c’est l’angle libre)
            angleLibre = latestDistal; // L’angle libre est distal
        } else if (blockedPhalange === "distale") { // Si la phalange distale est bloquée
            color = '#007bff'; // Bleu = proximal (car c’est l’angle libre)
            angleLibre = latestProximal; // L’angle libre est proximal
        }

        // ⛔ Ce bloc est indépendant — ajoute au graphique force vs angle SEULEMENT si une série est active
        if (lastForce !== undefined && angleLibre !== null && currentSeries && !currentSeries.stopped) {
            console.log("🧪 Point ajouté à la série :", lastForce, angleLibre);
            appendToCurrentSeries(parseFloat(lastForce), parseFloat(angleLibre));
        }
    }
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
        },
        series: measurementSeries.map(serie => {
            return {
                label: serie.label,           // "Blocage D-I à 30°"
                color: serie.color,           // Couleur de la série
                dataX: serie.dataX,           // Angles libres
                dataY: serie.dataY            // Forces correspondantes
            };
        })

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
// Affiche ou cache les graphiques dynamiquementa
// --------------------------------------------------

let graphsVisible = true; // État initial : graphes visibles

document.getElementById('toggleGraphsButton').addEventListener('click', function () {
    const container = document.getElementById('graphs-container'); // Sélectionne le conteneur des graphes
    graphsVisible = !graphsVisible; // Inverse l’état (visible ↔ caché)

    // Bascule la classe 'hidden' pour masquer ou afficher les graphes
    container.classList.toggle('hidden');

    // Met à jour le texte du bouton
    this.textContent = graphsVisible ? "Cacher les graphiques" : "Afficher les graphiques";

    // 🔧 Force Plotly à redimensionner les graphes après un court délai
    if (graphsVisible) {
        setTimeout(() => {
            Plotly.Plots.resize(document.getElementById('graph-force'));
            Plotly.Plots.resize(document.getElementById('graph-amplitude'));
        }, 300); // Attendre que l'animation CSS soit terminée
    }
});

function onStartMeasurementSeries() {
    // Fonction appelée lorsqu'on clique sur le bouton "Démarrer une nouvelle mesure"
    // Elle détermine automatiquement quel angle utiliser en fonction de la phalange bloquée
    // Puis elle démarre une nouvelle série de mesure si un angle valide est disponible
    console.log("🟢 Nouvelle mesure démarrée — angleDistal:", latestDistal, "angleProximal:", latestProximal);
    
    let angleMesure = null; // Initialisation d'une variable qui contiendra la valeur de l’angle libre à utiliser
    let angleBlocage = null; // Initialise la variable qui contiendra l’angle de blocage détecté

    // Si la phalange bloquée est la proximale (côté paume)
    if (blockedPhalange === "proximale") {
        angleBlocage = latestProximal;   // ➤ Alors l’angle de blocage est celui mesuré au niveau de la phalange proximale
    } 
    // Si la phalange bloquée est la distale (au bout du doigt)
    else if (blockedPhalange === "distale") {
        angleBlocage = latestDistal;     // ➤ Alors l’angle de blocage est celui mesuré au niveau de la phalange distale
    }

    angleMesure = angleBlocage; // ✅ ➕ Ajoute cette ligne
    
    document.getElementById("autoAngleDisplay").textContent = `${parseInt(angleBlocage)}°`; // ⬅️ Met à jour l'affichage de l’angle de blocage détecté (ex : "45°") en le convertissant en entier puis en l'affichant dans l’élément HTML d’ID "autoAngleDisplay"

    // Vérifie si un angle a bien été détecté
    if (angleMesure === null || angleMesure === undefined || isNaN(parseFloat(angleMesure))) {
        alert("Aucun angle détecté pour démarrer la mesure.");
        return;
    }


    // Convertit l’angle en entier (ex. 45.6 devient 45), puis ajoute le symbole °
    // Cela permet de créer une étiquette lisible pour l’interface utilisateur
    const angleLabel = `${parseInt(angleMesure)}°`;

    // Démarre une nouvelle série de mesure avec l’étiquette construite à partir de l’angle détecté
    startNewMeasurementSeries(angleLabel);
}


function startNewMeasurementSeries(angleLabel) {
    // Vérifie si une série est en cours avec des données déjà présentes
    if (currentSeries && currentSeries.dataX.length > 0) {
        // Ajoute l’ancienne série à la liste globale
        measurementSeries.push(currentSeries);

        // Crée une option pour le <select> avec couleur
        const option = document.createElement("option");
        option.value = currentSeries.label;              // ➤ la valeur permet d’identifier la série (filtrage)
        option.textContent = currentSeries.label;        // ➤ le texte affiché
        option.style.color = currentSeries.color;        // ➤ applique la couleur dans le menu
        document.getElementById("seriesSelector").appendChild(option);
    }

    // Génére un label unique du type "Blocage D-I à 60° #2"
    const uniqueLabel = generateUniqueLabel(angleLabel);

    // Associe une couleur unique à ce label (et non juste à l’angle)
    const color = generateColor(uniqueLabel);

    // Met à jour l'affichage de l'angle
    const angleSpan = document.getElementById("autoAngleDisplay");
    angleSpan.textContent = angleLabel;

    if (blockedPhalange === "proximale") {
        angleSpan.style.color = "#d9534f"; // Rouge (D-I)
    } else if (blockedPhalange === "distale") {
        angleSpan.style.color = "#007bff"; // Bleu (I-P)
    } else {
        angleSpan.style.color = "black"; // Valeur par défaut
    }


    // Crée une nouvelle série vide
    currentSeries = {
        label: uniqueLabel, // Label identifiant la série (ex : "Blocage D-I à 60°")
        color: color,                           // Couleur spécifique
        dataX: [],                              // Liste des angles
        dataY: [],                              // Liste des forces
        startForce: null,                       // Valeur de force initiale
        stopped: false,                          // Indique si la série est terminée
         };
}


// --------------------------------------------------
// Ajoute une mesure (force + angle) à la série en cours
// --------------------------------------------------

function appendToCurrentSeries(force, angle) {
    // Si aucune série n’est active OU si la série est marquée comme terminée, on ne fait rien
    if (!currentSeries || currentSeries.stopped) return;

    // --------------------------------------------------
    // 1️⃣ Initialisation de la force de départ
    // --------------------------------------------------

    // Si c’est la toute première mesure, on enregistre la valeur de force comme référence initiale
    if (currentSeries.startForce === null) {
        currentSeries.startForce = force;
    }

    // --------------------------------------------------
    // 6️⃣ Ajout du point (angle + force) à la série en cours
    // --------------------------------------------------

    currentSeries.dataX.push(angle); // Ajoute la valeur d’angle à la liste X (abscisses)
    currentSeries.dataY.push(force); // Ajoute la valeur de force à la liste Y (ordonnées)

    renderForceVsAnglePlot(); // Met à jour le graphique avec tous les points présents
}


function renderForceVsAnglePlot() {
    // Récupère la série sélectionnée dans la liste déroulante (ou "all" si aucune)
    const selected = document.getElementById("seriesSelector")?.value || "all";

    // Prépare un tableau pour les courbes (traces) à afficher
    const traces = [];

    // Parcourt toutes les séries enregistrées pour construire les courbes
    for (const serie of measurementSeries) {
        // Si une série spécifique est sélectionnée, on saute les autres
        if (selected !== "all" && serie.label !== selected) continue;

        // Ajoute une trace au graphique pour cette série
        traces.push({
            x: serie.dataX,                     // Liste des angles
            y: serie.dataY,                     // Liste des forces
            mode: 'markers',              // Lignes reliées avec des points visibles
            name: serie.label,                  // Nom affiché dans la légende
            line: { color: serie.color }        // Couleur spécifique à cette série
        });
    }

    // Si une série est encore en cours et doit être affichée
    if (currentSeries && (selected === "all" || selected === currentSeries.label)) {
        traces.push({
            x: currentSeries.dataX,                  // Angles en cours
            y: currentSeries.dataY,                  // Forces en cours
            mode: 'lines+markers',                   // Points + ligne pointillée
            name: currentSeries.label + " (en cours)", // Légende avec indication que c'est une série active
            line: { color: currentSeries.color, dash: 'dot' } // Ligne pointillée pour la distinguer
        });
    }

    // Utilise Plotly pour tracer ou mettre à jour le graphique avec les séries sélectionnées
    Plotly.newPlot('graph-force-vs-angle', traces, {
        xaxis: { title: 'Angle libre (°)' },         // Titre de l’axe X
        yaxis: { title: 'Force (N)' },               // Titre de l’axe Y
        margin: { l: 50, r: 30, t: 20, b: 50 }       // Marges autour du graphique
    }, { responsive: true });                        // Rend le graphique adaptatif à la taille de l’écran
}


// --------------------------------------------------
// Simuler des valeurs d'angles
// --------------------------------------------------

function simulateFakeMeasurementSeries(angleLabel = "45°") {
    startNewMeasurementSeries(angleLabel); // Crée la série avec un nom unique

    const numPoints = 20;
    const baseForce = 10;
    const amplitude = 5;

    for (let i = 0; i < numPoints; i++) {
        const fakeForce = baseForce + Math.sin(i / 2) * amplitude + (Math.random() - 0.5);
        const fakeAngle = angleLabel === "30°"
            ? 40 + Math.random() * 5
            : 60 + Math.random() * 5;

        appendToCurrentSeries(fakeForce, fakeAngle);
    }

    appendToCurrentSeries(baseForce, angleLabel === "30°" ? 42 : 63);
    console.log("✅ currentSeries (nouvelle):", currentSeries);
}
