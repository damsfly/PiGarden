// Fonction pour ajuster l'heure des données, notamment pour les graphiques
function convertToLocaleStringISO(timestamps) {
    return timestamps.map(ts => {
        const date = new Date(ts + 'Z');  // Assurez-vous que le timestamp est traité comme UTC
        return date.toISOString();  // Retourne au format ISO pour Plotly sans ajustement d'heure
    });
}

// Fonction pour convertir l'heure en chaîne locale
function convertToLocaleString(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString(); // Conversion en chaîne de caractères locale
}

// Exemple : Lorsque le bouton "Arroser le jardin" est cliqué
document.getElementById("btn-water-garden")?.addEventListener("click", function () {
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
document.getElementById("btn-water-tomatoes")?.addEventListener("click", function () {
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
document.getElementById("btn-activate-faucet")?.addEventListener("click", function () {
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
document.getElementById("btn-stop-watering")?.addEventListener("click", function () {
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
    const waterLevelSpan = document.getElementById('water-level');
    if (!waterLevelSpan) return;  // Ajout de vérification d'existence
    fetch('/get-water-level')
        .then(response => response.json())
        .then(data => {
            // Extraire le niveau d'eau des données et le formater
            const waterLevel = parseFloat(data.water_level).toFixed(2); // Formater la valeur à deux chiffres après la virgule

            // Mettre à jour la balise HTML avec le niveau d'eau
            waterLevelSpan.textContent = `${waterLevel} cm`; // Ajouter l'unité
        })
        .catch(error => {
            console.error('Erreur lors de la récupération du niveau d\'eau :', error);
        });
}

// Appeler la fonction pour afficher le niveau d'eau au chargement de la page
getWaterLevel();

// Récupérer la valeur de pluie tombée les 12 dernières heures depuis le serveur Flask et mettre à jour la balise HTML
function getLastRainData() {
    const rainDataSpan = document.getElementById('rain-data');
    if (!rainDataSpan) return;  // Ajout de vérification d'existence
    fetch('/get-last-rain-data')
        .then(response => response.json())
        .then(data => {
            rainDataSpan.textContent = `${data.rain_data} mm`; // Ajouter l'unité de mesure
        })
        .catch(error => {
            console.error('Erreur lors de la récupération des données de pluie:', error);
        });
}

// Appeler cette fonction au chargement de la page
getLastRainData();

// Récupérer les données du niveau d'eau depuis le serveur Flask et générer le graphique
function getWaterLevelChartData(duration) {
    fetch(`/water-level-chart-data?duration=${duration}`)
        .then(response => response.json())
        .then(data => {
            // Convertir les timestamps en format ISO pour Plotly sans ajustement d'heure
            const timestamps = convertToLocaleStringISO(data.timestamps);
            const waterLevels = data.water_levels;

            const chartData = [{
                x: timestamps,
                y: waterLevels,
                type: 'scatter',  // Utilisez 'scatter' pour les graphiques à points et lignes
                mode: 'lines+markers',  // Ligne avec des points à chaque donnée
                name: 'Niveau d\'eau (cm)',
                fill: 'tozeroy',  // Remplissage jusqu'à l'axe des x (zéro)
                fillcolor: 'rgba(173, 216, 230, 0.5)',  // Bleu clair avec une transparence
                line: {  // Définir la couleur et la largeur de la ligne
                    color: 'blue',
                    width: 2
                },
                marker: {  // Style des marqueurs
                    color: 'blue',
                    size: 6
                }
            }];

            const chartLayout = {
                title: 'Évolution du niveau d\'eau de la citerne',
                xaxis: {
                    title: 'Horodatage',
                    type: 'date'
                },
                yaxis: {
                    title: 'Niveau d\'eau (cm)'
                },
                autosize: true,
                margin: {
                    l: 50,
                    r: 50,
                    b: 100,
                    t: 100,
                    pad: 4
                },
                paper_bgcolor: 'white',
                plot_bgcolor: 'white'
            };

            Plotly.newPlot('water-level-chart', chartData, chartLayout, {responsive: true});
        })
        .catch(error => {
            console.error('Erreur lors de la récupération des données du niveau d\'eau :', error);
        });
}

// Script pour le menu hamburger
document.addEventListener('DOMContentLoaded', function () {
    const menuIcon = document.getElementById('menu-icon');
    const navLinks = document.getElementById('nav-links');

    menuIcon.addEventListener('click', function () {
        navLinks.classList.toggle('active');
    });
});