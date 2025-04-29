function toggleCreatePatientForm() {
    const createForm = document.getElementById('createPatientForm');
    const loadForm = document.getElementById('loadPatientForm');
    const preview = document.getElementById('patientPreview');

    if (createForm.style.display === 'block') {
        createForm.style.display = 'none';
    } else {
        createForm.style.display = 'block';
        loadForm.style.display = 'none';   // 🛠 Cache l'autre
        preview.style.display = 'none';    // 🛠 Cache aussi l'aperçu
    }
}


function toggleLoadPatientForm() {
    const loadForm = document.getElementById('loadPatientForm');
    const createForm = document.getElementById('createPatientForm');
    const preview = document.getElementById('patientPreview');

    if (loadForm.style.display === 'block') {
        loadForm.style.display = 'none';
    } else {
        loadForm.style.display = 'block';
        createForm.style.display = 'none';  // 🛠 Cache l'autre
        preview.style.display = 'none';     // 🛠 Cache aussi l'aperçu
    }

    if (loadForm.style.display === 'block') {
        fetch('/list_patients')
            .then(response => response.json())
            .then(files => {
                const select = document.getElementById('patientFile');
                select.innerHTML = '';
                files.forEach(name => {
                    const option = document.createElement('option');
                    option.value = name;
                    option.text = name;
                    select.appendChild(option);
                });
            })
            .catch(error => {
                console.error("Erreur lors du chargement des patients :", error);
            });
    }
}


function savePatient() {
    const data = {
        patient_name: document.getElementById('patient_name').value, // 🟢 bon id
        birthdate: document.getElementById('birthdate').value,
        age: parseInt(document.getElementById('age').value),
        weight: parseInt(document.getElementById('weight').value),
        height: parseInt(document.getElementById('height').value),
        sex: document.getElementById('sex').value,
        pathology: document.getElementById('pathology').value,
        notes: document.getElementById('notes').value
    };
    

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


// Synchroniser le champ "Nom" à droite avec celui à gauche
document.addEventListener('DOMContentLoaded', () => {
    const leftInput = document.getElementById('patient_name');
    const rightDisplay = document.getElementById('display_patient_name');
    function syncNameToRight() {
        rightDisplay.textContent = leftInput.value || '–';
    }
    // Met à jour le champ de droite à chaque frappe dans celui de gauche
    leftInput.addEventListener('input', syncNameToRight);

    // Initialisation
    syncNameToRight();
});

document.addEventListener('DOMContentLoaded', () => {
    const measureForm = document.getElementById('measureForm');
    measureForm.addEventListener('submit', async function (e) {
        e.preventDefault(); // Empêche l'envoi immédiat

        const patientName = document.getElementById('patient_name').value.trim();
        if (!patientName) {
            alert("Veuillez entrer un nom de patient.");
            return;
        }

        try {
            const response = await fetch(`/check_patient_exists/${encodeURIComponent(patientName)}`);
            const data = await response.json();

            if (data.exists) {
                // Fiche trouvée → on envoie le formulaire
                measureForm.submit();
            } else {
                // Fiche introuvable → message
                alert("⚠️ Ce patient n'existe pas encore dans la base de données. Veuillez lui créer une fiche d'abord.");
            }
        } catch (error) {
            console.error("Erreur lors de la vérification du patient :", error);
            alert("Une erreur est survenue pendant la vérification du patient.");
        }
    });
});
