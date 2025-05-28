// --------------------------------------------------
// Gérer l'affichage des sections
// --------------------------------------------------

function hideAllForms() {
    document.getElementById('createPatientForm').style.display = 'none';  // Cache le formulaire de création de fiche patient
    document.getElementById('loadPatientForm').style.display = 'none';    // Cache le formulaire de chargement d'une fiche existante
    document.getElementById('editPatientForm').style.display = 'none';    // Cache le formulaire d'édition
    document.getElementById('patientPreview').style.display = 'none';     // Cache l'aperçu de la fiche patient sélectionnée
}


// --------------------------------------------------
// Créer une nouvelle fiche patient
// --------------------------------------------------

function toggleCreatePatientForm() {
    hideAllForms(); // Commence par cacher tous les autres formulaires ou aperçus

    const createForm = document.getElementById('createPatientForm'); // Récupère le formulaire de création de fiche patient
    createForm.style.display = 'flex';                               // L'affiche en mode flex pour empiler verticalement les champs
    createForm.dataset.mode = 'create';                              // Ajoute une information personnalisée indiquant le mode "création"

    // Titre
    document.getElementById('formTitle').innerText = "Créer une nouvelle fiche patient"; // Change dynamiquement le titre du formulaire

    // Remise à zéro des champs
    document.getElementById('patient_name').value = '';       // Vide le champ du nom
    document.getElementById('birthdate').value = '';          // Vide le champ de date de naissance
    document.getElementById('ageDisplay').style.display = 'block'; // Assure que le champ de l'âge est visible
    document.getElementById('ageDisplay').innerText = '–';    // Remet un tiret dans l'affichage de l'âge
    document.getElementById('weight').value = '';             // Vide le champ du poids
    document.getElementById('height').value = '';             // Vide le champ de la taille
    document.getElementById('sex').value = '';                // Réinitialise la sélection du sexe
    document.getElementById('pathology').value = '';          // Vide le champ de la pathologie
    document.getElementById('notes').value = '';              // Vide le champ des remarques
    document.getElementById('display_patient_name').innerText = '–'; // Réinitialise l'affichage du nom du patient

    // Rendre les champs modifiables
    document.getElementById('patient_name').readOnly = false; // Rend le champ nom éditable
    document.getElementById('birthdate').readOnly = false;    // Rend la date de naissance éditable également
}

// --------------------------------------------------
// Modifier une fiche existante
// --------------------------------------------------

function toggleEditPatientForm() {
    hideAllForms(); // Cache tous les autres formulaires ou blocs affichés actuellement

    const editForm = document.getElementById('editPatientForm'); // Récupère le conteneur du formulaire d'édition
    editForm.style.display = 'block'; // Affiche le formulaire d'édition (il contient une liste déroulante)

    // Vide et recharge dynamiquement la liste déroulante des patients depuis le serveur
    fetch('/list_patients') // Fait une requête GET à l’URL /list_patients pour obtenir la liste des fichiers patients
        .then(response => response.json()) // Convertit la réponse en format JSON (liste de noms de fichiers)
        .then(files => { // Une fois les fichiers reçus :
            const select = document.getElementById('editPatientSelect'); // Récupère l’élément <select> où injecter les options
            select.innerHTML = '<option value="">-- Choisir un patient --</option>'; // Initialise la liste avec une option par défaut

            files.forEach(name => { // Pour chaque nom de fichier dans la liste :
                const option = document.createElement('option'); // Crée un nouvel élément <option>
                option.value = name; // Définit la valeur réelle comme le nom du fichier
                option.text = name.replace('.json', '').replace('_', ' '); // Nettoie l'affichage : supprime l'extension .json et remplace les underscores par des espaces
                select.appendChild(option); // Ajoute cette option à la liste déroulante
            });
        })
        .catch(error => { // En cas d’erreur lors de la requête :
            console.error("Erreur lors du chargement des patients :", error); // Affiche l’erreur dans la console pour débogage
        });
}


// --------------------------------------------------
// Sélectionner un patient pour modification
// --------------------------------------------------

// Stock global pour l'historique du patient sélectionné (utilisé plus tard lors de l’enregistrement ou l'affichage)
let currentHistory = [];

// Fonction appelée lorsqu’on choisit un patient dans la liste déroulante d'édition
function onSelectPatientToEdit() {
    hideAllForms(); // Cache tous les formulaires et aperçus pour commencer sur une base propre

    const selectedFile = document.getElementById('editPatientSelect').value; // Récupère le nom du fichier sélectionné dans la liste
    if (!selectedFile) { // Si aucun patient n’a été choisi (option vide), on arrête la fonction
        return;
    }

    // Requête pour charger les données du patient depuis le backend (en JSON)
    fetch(`/load_patient/${selectedFile}`)
        .then(response => response.json()) // Convertit la réponse en objet JSON
        .then(data => { // Lorsque les données du patient sont disponibles :
            currentHistory = data.history || []; // Stocke son historique dans la variable globale (ou tableau vide s’il n’y a rien)

            const createForm = document.getElementById('createPatientForm'); // Récupère le formulaire de création (réutilisé ici pour l'édition)
            createForm.style.display = 'flex'; // L’affiche en mode flex (vertical)
            createForm.dataset.mode = 'edit'; // Change le mode du formulaire pour indiquer qu’il est en "édition"
            createForm.dataset.filename = selectedFile; // Stocke le nom du fichier sélectionné dans les attributs HTML

            document.getElementById('formTitle').innerText = "Modifier la fiche du patient"; // Change le titre pour "modifier"

            // 🖊️ Remplit chaque champ avec les données du patient
            document.getElementById('patient_name').value = data.patient_name || ''; // Nom
            document.getElementById('display_patient_name').innerText = data.patient_name || '–'; // Affichage du nom en haut

            document.getElementById('birthdate').value = data.birthdate || ''; // Date de naissance

            document.getElementById('ageDisplay').style.display = 'block'; // Affiche le champ de l’âge
            document.getElementById('ageDisplay').innerText = calculateAge(data.birthdate) + " ans"; // Calcule et affiche l'âge

            document.getElementById('weight').value = data.weight || ''; // Poids
            document.getElementById('height').value = data.height || ''; // Taille
            document.getElementById('sex').value = data.sex || ''; // Sexe
            document.getElementById('pathology').value = data.pathology || ''; // Pathologie
            document.getElementById('notes').value = data.notes || ''; // Notes/remarques

            // Le nom et la date de naissance ne sont **pas** modifiables en mode édition
            document.getElementById('patient_name').readOnly = true;
            document.getElementById('birthdate').readOnly = true;
        })
        .catch(error => {
            console.error("Erreur lors du chargement du patient :", error); // Affiche une erreur dans la console si le chargement échoue
            alert("Impossible de charger la fiche du patient."); // Alerte l’utilisateur via une fenêtre pop-up
        });
}



// --------------------------------------------------
// Charger une fiche pour consultation
// --------------------------------------------------

function toggleLoadPatientForm() {
    hideAllForms(); // Masque tous les autres formulaires ou aperçus affichés à l'écran

    const loadForm = document.getElementById('loadPatientForm'); // Récupère le formulaire de chargement d'une fiche patient
    loadForm.style.display = 'block'; // Affiche le formulaire de chargement

    fetch('/list_patients') // Envoie une requête GET à l'URL /list_patients pour obtenir la liste des fichiers patients disponibles
        .then(response => response.json()) // Convertit la réponse en JSON (attendu : liste de noms de fichiers .json)
        .then(files => {
            const select = document.getElementById('patientFile'); // Récupère l'élément <select> qui affichera les noms des patients
            select.innerHTML = ''; // Vide complètement la liste avant d'ajouter les nouvelles options

            files.forEach(name => { // Pour chaque fichier dans la liste reçue :
                const option = document.createElement('option'); // Crée une nouvelle balise <option> pour le menu déroulant
                option.value = name; // Attribue le nom du fichier comme valeur de l'option
                option.text = name.replace('.json', '').replace('_', ' '); // Nettoie le nom pour affichage : enlève l'extension .json et remplace les "_" par des espaces
                select.appendChild(option); // Ajoute cette option à la liste déroulante
            });
        })
        .catch(error => {
            console.error("Erreur lors du chargement des patients :", error); // Affiche une erreur dans la console si la requête échoue
        });
}

function loadPatient() {
    const selectedFile = document.getElementById('patientFile').value; // Récupère le fichier sélectionné dans le menu déroulant
    if (!selectedFile) { // Si aucun fichier n'est sélectionné :
        alert("Veuillez sélectionner un patient !"); // Affiche une alerte à l'utilisateur
        return; // Interrompt la fonction
    }

    fetch(`/load_patient/${selectedFile}`) // Envoie une requête pour charger le fichier JSON du patient sélectionné
        .then(response => response.json()) // Convertit la réponse en objet JSON contenant les données du patient
        .then(data => {
            document.getElementById('patient_name').value = data.patient_name || ''; // Remplit le champ 'patient_name' avec la donnée reçue
            document.getElementById('previewName').innerText = data.patient_name || ''; // Affiche le nom du patient dans la zone d’aperçu
            document.getElementById('previewBirthdate').innerText = data.birthdate || ''; // Affiche la date de naissance
            document.getElementById('previewAge').innerText = data.age || ''; // Affiche l’âge
            document.getElementById('previewWeight').innerText = data.weight || ''; // Affiche le poids
            document.getElementById('previewHeight').innerText = data.height || ''; // Affiche la taille
            document.getElementById('previewSex').innerText = data.sex || ''; // Affiche le sexe
            document.getElementById('previewPathology').innerText = data.pathology || ''; // Affiche la pathologie
            document.getElementById('previewNotes').innerText = data.notes || ''; // Affiche les remarques

            const preview = document.getElementById('patientPreview'); // Récupère le bloc d’aperçu du patient
            preview.classList.add('active'); // Rend le bloc visible (lui applique une classe qui change le style d’affichage)
        })
        .catch(error => {
            console.error("Erreur lors du chargement du patient :", error); // Affiche une erreur technique dans la console
            alert("Impossible de charger la fiche du patient."); // Affiche une alerte à l’utilisateur
        });
}

// --------------------------------------------------
// Enregistrer une fiche patient (création ou édition)
// --------------------------------------------------

function savePatient() {
    const form = document.getElementById('createPatientForm'); // Récupère le formulaire de création/édition
    const mode = form.dataset.mode || 'create'; // Récupère le mode actuel (création ou édition), par défaut "create"
    const filename = form.dataset.filename || null; // Si en édition, récupère le nom du fichier existant à modifier

    const todayStr = new Date().toISOString().split('T')[0]; // Formate la date du jour en "YYYY-MM-DD"

    // Récupération des valeurs depuis les champs du formulaire
    const patientName = document.getElementById('patient_name').value; // Nom du patient
    const birthdate = document.getElementById('birthdate').value; // Date de naissance
    const weight = parseInt(document.getElementById('weight').value) || 0; // Poids converti en entier (ou 0 si vide)
    const height = parseInt(document.getElementById('height').value) || 0; // Taille convertie en entier (ou 0 si vide)
    const sex = document.getElementById('sex').value; // Sexe sélectionné
    const pathology = document.getElementById('pathology').value; // Pathologie renseignée
    const notes = document.getElementById('notes').value; // Notes éventuelles

    // Structure des données principales du patient
    const data = {
        patient_name: patientName,          // Nom
        birthdate: birthdate,               // Date de naissance
        age: calculateAge(birthdate),       // Âge calculé à partir de la date de naissance
        weight: weight,                     // Poids
        height: height,                     // Taille
        sex: sex,                           // Sexe
        pathology: pathology,               // Pathologie
        mode: mode                          // Mode (create ou edit)
    };

    // Si on est en mode édition, on ajoute une entrée à l’historique
    if (mode === 'edit') {
        const newEntry = {
            date: todayStr,         // Date actuelle
            weight: weight,         // Poids actuel
            height: height,         // Taille actuelle
            pathology: pathology,   // Pathologie actuelle
            notes: notes            // Remarques (ajoutées uniquement ici en mode historique)
        };

        data.history = currentHistory || []; // Récupère l’historique déjà existant (ou tableau vide)
        data.history.push(newEntry);         // Ajoute la nouvelle entrée à l’historique
        data.filename = filename;            // Ajoute le nom du fichier à modifier
    }

    // Si on est en mode création, on met les notes dans la fiche principale directement
    if (mode === 'create') {
        data.notes = notes; // Attribue la note au niveau de la fiche (et non l’historique)
    }

    // Envoie les données au backend Flask via une requête POST
    fetch('/save_patient', {
        method: 'POST',                               // Méthode HTTP POST
        headers: {'Content-Type': 'application/json'}, // Indique que les données envoyées sont en JSON
        body: JSON.stringify(data)                    // Convertit l'objet JS en chaîne JSON
    })
    .then(response => {
        if (response.ok) {
            alert("Fiche patient enregistrée !"); // Alerte si l'enregistrement a réussi
            toggleCreatePatientForm();            // Recharge le formulaire vide
        } else {
            alert("Erreur lors de l'enregistrement."); // Alerte en cas de réponse non OK
        }
    })
    .catch(error => {
        console.error("Erreur lors de l'enregistrement :", error); // Log de l'erreur si l’envoi a échoué
    });
}



// --------------------------------------------------
// Outils complémentaires
// --------------------------------------------------

// --------------------------------------------------
// Fonction de calcul de l'âge à partir d'une date de naissance
// --------------------------------------------------
function calculateAge(birthdateStr) { // Fonction qui reçoit une date de naissance (au format texte AAAA-MM-JJ)
    const today = new Date(); // Crée un objet Date correspondant à aujourd’hui
    const birthDate = new Date(birthdateStr); // Convertit la date de naissance en objet Date
    let age = today.getFullYear() - birthDate.getFullYear(); // Calcule l’écart entre les années
    const m = today.getMonth() - birthDate.getMonth(); // Compare les mois actuels avec ceux de naissance
    if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) { // Si l'anniversaire n'est pas encore passé
        age--; // Réduit l'âge d'un an
    }
    return age; // Renvoie l'âge final
}

// --------------------------------------------------
// Exécuter une fois que la page HTML est complètement chargée
// --------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {

    // --------------------------------------------------
    // Calcul dynamique de l'âge et mise à jour dans l'affichage
    // --------------------------------------------------
    const birthdateInput = document.getElementById('birthdate'); // Récupère le champ de date de naissance
    const ageDisplay = document.getElementById('ageDisplay');     // Élément affichant "xx ans"
    const ageInput = document.getElementById('age');              // Champ caché (si utilisé) pour transmettre l’âge au backend

    birthdateInput.addEventListener('input', () => { // À chaque modification du champ de naissance
        const birthdateStr = birthdateInput.value; // Lit la date saisie

        if (birthdateStr) { // Si une date a bien été entrée
            const age = calculateAge(birthdateStr); // Calcul de l'âge
            if (!isNaN(age)) { // Vérifie que l'âge est bien un nombre
                ageDisplay.innerText = age + " ans"; // Met à jour l’affichage
                if (ageInput) ageInput.value = age;  // Si le champ existe, on lui donne la même valeur
            }
        } else { // Si la date a été effacée
            ageDisplay.innerText = '–'; // Réinitialise l'affichage de l'âge
            if (ageInput) ageInput.value = ''; // Vide aussi le champ caché
        }
    });

    // --------------------------------------------------
    // Vérifie si la fiche patient existe avant de soumettre le formulaire
    // --------------------------------------------------
    const measureForm = document.getElementById('measureForm'); // Récupère le formulaire de mesure s’il est présent
    if (measureForm) {
        measureForm.addEventListener('submit', async function (e) { // Ajoute un écouteur à la soumission
            e.preventDefault(); // Empêche le rechargement de la page

            const patientName = document.getElementById('patient_name').value.trim(); // Récupère le nom saisi
            if (!patientName) { // Si le champ est vide
                alert("Veuillez entrer un nom de patient."); // Message d’alerte
                return;
            }

            try {
                const response = await fetch(`/check_patient_exists/${encodeURIComponent(patientName)}`); // Requête GET au serveur
                const data = await response.json(); // On convertit la réponse en JSON

                if (data.exists) { // Si le patient est trouvé
                    measureForm.submit(); // On soumet le formulaire
                } else {
                    alert("Ce patient n'existe pas encore dans la base de données.\n\nVeuillez lui créer une fiche d'abord, s'il vous plaît !");
                }
            } catch (error) { // En cas de problème serveur
                console.error("Erreur lors de la vérification du patient :", error); // Affiche l’erreur en console
                alert("Une erreur est survenue pendant la vérification du patient."); // Message utilisateur
            }
        });
    }

    // --------------------------------------------------
    // Synchroniser automatiquement le champ "Nom" (input ↔ affichage)
    // --------------------------------------------------
    const patientNameInput = document.getElementById('patient_name');         // Champ de texte où l'utilisateur écrit le nom
    const displayPatientName = document.getElementById('display_patient_name'); // Élément HTML où le nom est affiché

    function syncPatientName() { // Fonction pour synchroniser les deux
        displayPatientName.textContent = patientNameInput.value.trim() || '–'; // Met à jour l'affichage (ou un tiret si vide)
    }

    if (patientNameInput && displayPatientName) { // Vérifie que les deux éléments existent
        patientNameInput.addEventListener('input', syncPatientName); // À chaque saisie, met à jour l'affichage
        syncPatientName(); // Mise à jour initiale lors du chargement de la page
    }
});
