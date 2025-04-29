// --------------------------------------------------
// Gérer l'affichage des sections
// --------------------------------------------------

function hideAllForms() {
    document.getElementById('createPatientForm').style.display = 'none';
    document.getElementById('loadPatientForm').style.display = 'none';
    document.getElementById('editPatientForm').style.display = 'none';
    document.getElementById('patientPreview').style.display = 'none';
}

// --------------------------------------------------
// Créer une nouvelle fiche patient
// --------------------------------------------------

function toggleCreatePatientForm() {
    hideAllForms();

    const createForm = document.getElementById('createPatientForm');
    createForm.style.display = 'flex';
    createForm.dataset.mode = 'create'; // 🟢 Mode création

    // Titre
    document.getElementById('formTitle').innerText = "Créer une nouvelle fiche patient";

    // Remise à zéro des champs
    document.getElementById('patient_name').value = '';
    document.getElementById('birthdate').value = '';
    document.getElementById('age').style.display = 'block';
    document.getElementById('age').value = '';
    document.getElementById('ageDisplay').style.display = 'none';
    document.getElementById('ageDisplay').innerText = '–';
    document.getElementById('weight').value = '';
    document.getElementById('height').value = '';
    document.getElementById('sex').value = '';
    document.getElementById('pathology').value = '';
    document.getElementById('notes').value = '';
    document.getElementById('display_patient_name').innerText = '–';

    // Rendre les champs modifiables
    document.getElementById('patient_name').readOnly = false;
    document.getElementById('birthdate').readOnly = false;
}

// --------------------------------------------------
// Modifier une fiche existante
// --------------------------------------------------

function toggleEditPatientForm() {
    hideAllForms();

    const editForm = document.getElementById('editPatientForm');
    editForm.style.display = 'block'; // Affiche la liste déroulante

    // Vide et recharge la liste
    fetch('/list_patients')
        .then(response => response.json())
        .then(files => {
            const select = document.getElementById('editPatientSelect');
            select.innerHTML = '<option value="">-- Choisir un patient --</option>';
            files.forEach(name => {
                const option = document.createElement('option');
                option.value = name;
                option.text = name.replace('.json', '').replace('_', ' ');
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error("Erreur lors du chargement des patients :", error);
        });
}

// Stock global pour l'historique du patient sélectionné
let currentHistory = [];

function onSelectPatientToEdit() {
    // 🔒 On cache tout (y compris patientPreview)
    hideAllForms();

    const selectedFile = document.getElementById('editPatientSelect').value;
    if (!selectedFile) {
        return;
    }

    fetch(`/load_patient/${selectedFile}`)
        .then(response => response.json())
        .then(data => {
            // 🧠 Stocker l'historique globalement pour sauvegarde
            currentHistory = data.history || [];

            // 🔄 Afficher le formulaire d'édition
            const createForm = document.getElementById('createPatientForm');
            createForm.style.display = 'flex';
            createForm.dataset.mode = 'edit'; // 🔵 mode édition
            createForm.dataset.filename = selectedFile; // 📂 stocker le nom du fichier

            // 🏷️ Mettre à jour le titre du formulaire
            document.getElementById('formTitle').innerText = "Modifier la fiche du patient";

            // 🖊️ Remplir les champs
            document.getElementById('patient_name').value = data.patient_name || '';
            document.getElementById('display_patient_name').innerText = data.patient_name || '–';

            document.getElementById('birthdate').value = data.birthdate || '';

            document.getElementById('age').style.display = 'none';
            document.getElementById('ageDisplay').style.display = 'block';
            document.getElementById('ageDisplay').innerText = calculateAge(data.birthdate) + " ans";

            document.getElementById('weight').value = data.weight || '';
            document.getElementById('height').value = data.height || '';
            document.getElementById('sex').value = data.sex || '';
            document.getElementById('pathology').value = data.pathology || '';
            document.getElementById('notes').value = data.notes || '';

            // 🔐 Rendre nom et naissance non modifiables
            document.getElementById('patient_name').readOnly = true;
            document.getElementById('birthdate').readOnly = true;
        })
        .catch(error => {
            console.error("Erreur lors du chargement du patient :", error);
            alert("Impossible de charger la fiche du patient.");
        });
}


// --------------------------------------------------
// Charger une fiche pour consultation
// --------------------------------------------------

function toggleLoadPatientForm() {
    hideAllForms();

    const loadForm = document.getElementById('loadPatientForm');
    loadForm.style.display = 'block';

    fetch('/list_patients')
        .then(response => response.json())
        .then(files => {
            const select = document.getElementById('patientFile');
            select.innerHTML = '';
            files.forEach(name => {
                const option = document.createElement('option');
                option.value = name;
                option.text = name.replace('.json', '').replace('_', ' ');
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error("Erreur lors du chargement des patients :", error);
        });
}

function loadPatient() {
    const selectedFile = document.getElementById('patientFile').value;
    if (!selectedFile) {
        alert("Veuillez sélectionner un patient !");
        return;
    }

    fetch(`/load_patient/${selectedFile}`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('patient_name').value = data.patient_name || '';
            document.getElementById('previewName').innerText = data.patient_name || '';
            document.getElementById('previewBirthdate').innerText = data.birthdate || '';
            document.getElementById('previewAge').innerText = data.age || '';
            document.getElementById('previewWeight').innerText = data.weight || '';
            document.getElementById('previewHeight').innerText = data.height || '';
            document.getElementById('previewSex').innerText = data.sex || '';
            document.getElementById('previewPathology').innerText = data.pathology || '';
            document.getElementById('previewNotes').innerText = data.notes || '';

            const preview = document.getElementById('patientPreview');
            preview.classList.add('active');
        })
        .catch(error => {
            console.error("Erreur lors du chargement du patient :", error);
            alert("Impossible de charger la fiche du patient.");
        });
}

// --------------------------------------------------
// Enregistrer une fiche patient (création ou édition)
// --------------------------------------------------

function savePatient() {
    const form = document.getElementById('createPatientForm');
    const mode = form.dataset.mode || 'create';
    const filename = form.dataset.filename || null;

    const todayStr = new Date().toISOString().split('T')[0];

    const patientName = document.getElementById('patient_name').value;
    const birthdate = document.getElementById('birthdate').value;
    const weight = parseInt(document.getElementById('weight').value) || 0;
    const height = parseInt(document.getElementById('height').value) || 0;
    const sex = document.getElementById('sex').value;
    const pathology = document.getElementById('pathology').value;
    const notes = document.getElementById('notes').value;

    const data = {
        patient_name: patientName,
        birthdate: birthdate,
        age: calculateAge(birthdate),
        weight: weight,
        height: height,
        sex: sex,
        pathology: pathology,
        mode: mode
    };

    if (mode === 'edit') {
        const newEntry = {
            date: todayStr,
            weight: weight,
            pathology: pathology,
            notes: notes // ✅ seulement ici
        };

        data.history = currentHistory || [];
        data.history.push(newEntry);
        data.filename = filename;
    }

    if (mode === 'create') {
        // ✅ En mode création, la note va dans la fiche principale
        data.notes = notes;
    }

    fetch('/save_patient', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    })
    .then(response => {
        if (response.ok) {
            alert("Fiche patient enregistrée !");
            toggleCreatePatientForm();
        } else {
            alert("Erreur lors de l'enregistrement.");
        }
    })
    .catch(error => {
        console.error("Erreur lors de l'enregistrement :", error);
    });
}



// --------------------------------------------------
// Outils complémentaires
// --------------------------------------------------

function calculateAge(birthdateStr) {
    const today = new Date();
    const birthDate = new Date(birthdateStr);
    let age = today.getFullYear() - birthDate.getFullYear();
    const m = today.getMonth() - birthDate.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
        age--;
    }
    return age;
}

// --------------------------------------------------
// Synchroniser le nom du patient (input ↔ affichage)
// --------------------------------------------------

document.addEventListener('DOMContentLoaded', () => {
    const leftInput = document.getElementById('patient_name');
    const rightDisplay = document.getElementById('display_patient_name');
    function syncNameToRight() {
        rightDisplay.textContent = leftInput.value || '–';
    }
    leftInput.addEventListener('input', syncNameToRight);

    // Initialiser
    syncNameToRight();
});
