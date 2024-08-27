// Exemple : Lorsque le bouton "Arroser le jardin" est cliqué
document.getElementById("btn-water-garden").addEventListener("click", function () {
    // Envoyer une demande au serveur Flask pour démarrer l'arrosage du jardin
    fetch("/water-garden")
        .then(response => response.json())
        .then(data => {
            // Traitez la réponse du serveur si nécessaire
            console.log(data);
        })
        .catch(error => {
            console.error("Erreur lors de la demande au serveur :", error);
        });
});


// Lorsque le bouton "Arroser les tomates" est cliqué
document.getElementById("btn-water-tomatoes").addEventListener("click", function () {
    // Envoyer une demande au serveur Flask pour démarrer l'arrosage des tomates
    fetch("/water-tomatoes")
        .then(response => response.json())
        .then(data => {
            // Traitez la réponse du serveur si nécessaire
            console.log(data);
        })
        .catch(error => {
            console.error("Erreur lors de la demande au serveur :", error);
        });
});


// Lorsque le bouton "Activer le robinet auxiliaire" est cliqué
document.getElementById("btn-activate-faucet").addEventListener("click", function () {
    // Envoyer une demande au serveur Flask pour activer le robinet auxiliaire
    fetch("/activate-faucet")
        .then(response => response.json())
        .then(data => {
            // Traitez la réponse du serveur si nécessaire
            console.log(data);
        })
        .catch(error => {
            console.error("Erreur lors de la demande au serveur :", error);
        });
});


// Exemple : Lorsque le bouton "Arrêter tous les arrosages" est cliqué
document.getElementById("btn-stop-watering").addEventListener("click", function () {
    // Envoyer une demande au serveur Flask pour arrêter tous les arrosages
    fetch("/stop-watering")
        .then(response => response.json())
        .then(data => {
            // Traitez la réponse du serveur si nécessaire
            console.log(data);
        })
        .catch(error => {
            console.error("Erreur lors de la demande au serveur :", error);
        });
});


// Récupérer le niveau d'eau depuis le serveur Flask et mettre à jour la balise HTML
function getWaterLevel() {
    fetch('/get-water-level')
        .then(response => response.json())
        .then(data => {
            // Extraire le niveau d'eau des données et le formater
            const waterLevel = parseFloat(data.water_level).toFixed(2); // Formater la valeur à deux chiffres après la virgule

            // Mettre à jour la balise HTML avec le niveau d'eau
            const waterLevelSpan = document.getElementById('water-level');
            waterLevelSpan.textContent = `${waterLevel} cm`; // Ajouter l'unité
        })
        .catch(error => {
            console.error('Erreur lors de la récupération du niveau d\'eau :', error);
        });
}


// Appeler la fonction pour afficher le niveau d'eau au chargement de la page
getWaterLevel();


// Ecoutes via socketio
const socket = io(); // Cette ligne établit la connexion avec le serveur Socket.IO

// Écoute pour les mises à jour du niveau d'eau
socket.on('update_water_level', function(data) {
    document.getElementById('water-level').textContent = `${parseFloat(data.water_level).toFixed(2)} cm`;
});

// Écoute pour les mises à jour de l'humidité du sol
socket.on('update_moisture', function(data) {
    document.getElementById(`${data.zone.toLowerCase()}-moisture`).textContent = `${data.level}%`;
});

// Écoute pour les mises à jour de l'état du système
socket.on('update_system_state', function(data) {
    document.getElementById('system-state').textContent = `État: ${data.state}, Zone: ${data.zone}, Source: ${data.source}, Mode: ${data.mode}`;
});

// Écoute pour les changements d'état des relais
socket.on('relay_change', function(data) {
    console.log('Relay Change:', data);
    var element = document.getElementById('relay-status-' + data.pin);
    if (data.state) {
        element.classList.add('active');  // Ajoute la classe 'active' pour l'état actif
        element.textContent = element.textContent.replace('Inactif', 'Actif'); // Optionnel: Changez le texte si nécessaire
    } else {
        element.classList.remove('active');  // Supprime la classe 'active' pour revenir à l'état inactif
        element.textContent = element.textContent.replace('Actif', 'Inactif'); // Optionnel: Changez le texte si nécessaire
    }
});

