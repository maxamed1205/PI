// --- CONNEXION AVEC LE SERVEUR VIA SOCKET.IO ---
var socket = io();

// --- VARIABLES POUR STOCKER LES DONNEES RECUES EN TEMPS REEL ---
var forceTime = [];
var forceData = [];
var angleTime = [];
var angleData = [];
var angleDataProximal = [];
var forceVsAngleX = [];
var forceVsAngleY = [];

let latestDistal = null;
let latestProximal = null;
let blockedPhalange = null;

// Assigne blockedPhalange quand le DOM est prêt
document.addEventListener('DOMContentLoaded', () => {
    blockedPhalange = window.blockedPhalange;
    console.log("🚀 JS ready — blockedPhalange =", blockedPhalange);
    plotForceVsAngleEmpty();
});

function getFormattedTime() {
    var now = new Date();
    return now.getMinutes().toString().padStart(2, '0') + ":" + now.getSeconds().toString().padStart(2, '0');
}

function plotForceGraph() {
    Plotly.newPlot('graph-force', [{
        x: forceTime,
        y: forceData,
        mode: 'markers',
        name: 'Force (N)',
        line: {color: '#009640'}
    }], {
        xaxis: {title: 'Temps (mm:ss)'},
        yaxis: {title: 'Force (N)'},
        margin: {l: 50, r: 30, t: 20, b: 50},
        autosize: true
    }, {responsive: true});
}

function plotAmplitudeGraph() {
    Plotly.newPlot('graph-amplitude', [
        {
            x: angleTime,
            y: angleData,
            mode: 'markers',
            name: 'Distal (°)',
            line: { color: '#d9534f' }
        },
        {
            x: angleTime,
            y: angleDataProximal,
            mode: 'markers',
            name: 'Proximal (°)',
            line: { color: '#007bff' }
        }
    ], {
        xaxis: { title: 'Temps (mm:ss)' },
        yaxis: { title: 'Amplitude (°)' },
        margin: { l: 50, r: 30, t: 20, b: 50 },
        autosize: true
    }, { responsive: true });
}

socket.on('force_update', function(data) {
    var now = getFormattedTime();
    forceTime.push(now);
    forceData.push(data.force);
    plotForceGraph();
});

socket.on('angle_distal_update', function(data) {
    latestDistal = parseFloat(data['Angle distale']).toFixed(1);
    document.getElementById('angle-distal').textContent = latestDistal;
    console.log("📡 distal reçu:", data);
    maybePlotNewPoint();
});

socket.on('angle_proximal_update', function(data) {
    latestProximal = parseFloat(data['Angle proximal']).toFixed(1);
    document.getElementById('angle-proximal').textContent = latestProximal;
    console.log("📡 proximal reçu:", data);
    maybePlotNewPoint();
});

function maybePlotNewPoint() {
    if (latestDistal !== null && latestProximal !== null) {
        const now = getFormattedTime();
        angleTime.push(now);
        angleData.push(parseFloat(latestDistal));
        angleDataProximal.push(parseFloat(latestProximal));

        plotAmplitudeGraph();

        const lastForce = forceData[forceData.length - 1];
        let angleLibre = null;

        if (blockedPhalange === "proximale") {
            angleLibre = latestDistal;
        } else if (blockedPhalange === "distale") {
            angleLibre = latestProximal;
        }

        if (lastForce !== undefined && angleLibre !== null) {
            updateForceVsAngle(lastForce, angleLibre);
            console.log("✅ Donnée ajoutée au graphique Force vs Angle:", lastForce, angleLibre);
        }

        latestDistal = null;
        latestProximal = null;
    }
}

function updateForceVsAngle(forceValue, angleLibre) {
    forceVsAngleX.push(parseFloat(angleLibre));
    forceVsAngleY.push(parseFloat(forceValue));

    console.log("📈 Tracé Force vs Angle:", forceVsAngleX, forceVsAngleY);

    Plotly.newPlot('graph-force-vs-angle', [{
        x: forceVsAngleX,
        y: forceVsAngleY,
        mode: 'markers',
        name: 'Force vs Angle libre',
        line: { color: '#17a2b8' }
    }], {
        xaxis: { title: 'Angle libre (°)' },
        yaxis: { title: 'Force (N)' },
        margin: { l: 50, r: 30, t: 20, b: 50 },
        title: "Force en fonction de l'angle mesuré (libre)"
    }, { responsive: true });
}

function plotForceVsAngleEmpty() {
    Plotly.newPlot('graph-force-vs-angle', [{
        x: [],
        y: [],
        mode: 'markers',
        name: 'Force vs Angle libre',
        line: { color: '#17a2b8' }
    }], {
        xaxis: { title: 'Angle libre (°)' },
        yaxis: { title: 'Force (N)' },
        margin: { l: 50, r: 30, t: 20, b: 50 },
        title: "Force en fonction de l'angle mesuré (libre)"
    }, { responsive: true });
}

window.addEventListener('resize', function() {
    plotForceGraph();
    plotAmplitudeGraph();
});

document.getElementById('saveButton').addEventListener('click', function() {
    socket.emit('save_data', {
        patient: {
            patient_name: patientData.patient_name,
            finger: patientData.finger,
            phalange: patientData.phalange,
            operator: patientData.operator
        },
        force: {
            time: forceTime,
            data: forceData
        },
        amplitude_proximal: {
            time: angleTime,
            data: angleDataProximal
        },
        amplitude_distal: {
            time: angleTime,
            data: angleData
        }
    });
    alert('Donnees envoyees pour sauvegarde !');
});

document.getElementById('newMeasureButton').addEventListener('click', function() {
    window.location.href = "/";
});

document.getElementById('toggleGraphsButton').addEventListener('click', function() {
    const container = document.getElementById('graphs-container');
    graphsVisible = !graphsVisible;
    container.style.display = graphsVisible ? 'flex' : 'none';
    this.textContent = graphsVisible ? "Cacher les graphiques" : "Afficher les graphiques";
});
