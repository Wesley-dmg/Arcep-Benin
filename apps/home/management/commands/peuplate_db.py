# apps/home/management/commands/peuplate_db.py
import os
import random
from datetime import date, timedelta
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from PIL import Image, ImageDraw
from io import BytesIO

# Importe tes modèles (ajuste le chemin si nécessaire)
from apps.home.models import (
    Operateur,
    Departement,
    Commune,
    Localite,
    Technologie,
    Emplacement,
    Site,
    SiteTechnologie,
    Conformite,
)


class Command(BaseCommand):
    help = "Peuple la base de données avec 450 sites (150 par opérateur) pour le Bénin"

    def handle(self, *args, **options):
        """Fonction principale exécutée par la commande."""
        self.stdout.write(self.style.SUCCESS("🚀 Début du peuplement des données..."))

        # Étape 1: Créer la hiérarchie géographique (Département > Commune > Localité)
        self.stdout.write("🗺️  Création des départements, communes et localités...")
        localites_dict = self._creer_geographie_benin()

        # Étape 2: Créer les opérateurs, technologies et types d'emplacement
        self.stdout.write("📡 Création des opérateurs, technologies et emplacements...")
        operateurs = self._creer_operateurs()
        technologies = self._creer_technologies()
        emplacements = self._creer_types_emplacement()

        # Étape 3: Créer 450 sites (150 par opérateur)
        self.stdout.write("🏗️  Création de 450 sites (150 par opérateur)...")
        sites_crees = self._creer_sites_telecom(
            operateurs, technologies, emplacements, localites_dict
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"""
✅ Peuplement terminé avec succès !
• Départements : {Departement.objects.count()}
• Communes : {Commune.objects.count()}
• Localités : {Localite.objects.count()}
• Opérateurs : {len(operateurs)}
• Sites créés : {sites_crees} (répartis entre {", ".join([op.nom for op in operateurs])})
"""
            )
        )

    def _creer_geographie_benin(self):
        """Crée la structure administrative du Bénin avec de vraies coordonnées."""
        # Données des 12 départements avec leurs communes principales
        donnees_benin = {
            "Alibori": {
                "lat": 11.0,
                "lon": 2.5,
                "communes": ["Kandi", "Gogounou", "Banikoara"],
            },
            "Atacora": {
                "lat": 10.5,
                "lon": 1.0,
                "communes": ["Natitingou", "Tanguiéta", "Kérou"],
            },
            "Atlantique": {
                "lat": 6.5,
                "lon": 2.25,
                "communes": ["Abomey-Calavi", "Allada", "Ouidah", "Toffo"],
            },
            "Borgou": {
                "lat": 9.5,
                "lon": 2.5,
                "communes": ["Parakou", "Nikki", "Bembèrèkè"],
            },
            "Collines": {
                "lat": 8.0,
                "lon": 2.0,
                "communes": ["Dassa-Zoumè", "Savè", "Glazoué"],
            },
            "Couffo": {
                "lat": 7.0,
                "lon": 1.75,
                "communes": ["Aplahoué", "Djakotomey", "Klouékanmè"],
            },
            "Donga": {
                "lat": 9.0,
                "lon": 1.5,
                "communes": ["Djougou", "Copargo", "Bassila"],
            },
            "Littoral": {"lat": 6.35, "lon": 2.4, "communes": ["Cotonou"]},
            "Mono": {
                "lat": 6.5,
                "lon": 1.75,
                "communes": ["Lokossa", "Athieme", "Comè"],
            },
            "Ouémé": {
                "lat": 6.5,
                "lon": 2.6,
                "communes": ["Porto-Novo", "Adjohoun", "Dangbo"],
            },
            "Plateau": {
                "lat": 7.0,
                "lon": 2.5,
                "communes": ["Sakété", "Kétou", "Pobè"],
            },
            "Zou": {
                "lat": 7.25,
                "lon": 2.0,
                "communes": ["Abomey", "Bohicon", "Za-Kpota"],
            },
        }

        localites_dict = {}

        for nom_dept, infos in donnees_benin.items():
            # Crée le département
            dept, _ = Departement.objects.get_or_create(nom=nom_dept)

            for nom_commune in infos["communes"]:
                # Crée la commune liée au département
                commune, _ = Commune.objects.get_or_create(
                    nom=nom_commune, departement=dept
                )

                # Crée 3 à 5 localités (quartiers) pour cette commune
                for i in range(random.randint(3, 5)):
                    nom_localite = f"Quartier {chr(65+i)}"  # Quartier A, B, C...

                    # Coordonnées basées sur la position du département + variation aléatoire
                    lat = infos["lat"] + random.uniform(-0.15, 0.15)
                    lon = infos["lon"] + random.uniform(-0.15, 0.15)

                    # Crée la localité dans la base de données
                    localite, _ = Localite.objects.get_or_create(
                        localite=f"{nom_localite} ({nom_commune})", commune=commune
                    )

                    # Stocke les infos pour créer les sites plus tard
                    localites_dict[localite.id] = {
                        "objet": localite,
                        "latitude": lat,
                        "longitude": lon,
                        "nom_affichage": f"{nom_localite}, {nom_commune}, {nom_dept}",
                    }

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Géographie créée : {len(donnees_benin)} départements, "
                f'{sum(len(d["communes"]) for d in donnees_benin.values())} communes, '
                f"{len(localites_dict)} localités."
            )
        )
        return localites_dict

    def _creer_operateurs(self):
        """Crée les 3 opérateurs télécoms avec leurs couleurs officielles."""
        operateurs_info = [
            {"nom": "MTN", "couleur": "#FFCC00"},  # Jaune vif
            {"nom": "MOOV", "couleur": "#0055A4"},  # Bleu roi
            {"nom": "Celtiis", "couleur": "#0099CC"},  # Bleu clair
        ]

        operateurs_liste = []
        for info in operateurs_info:
            operateur, cree = Operateur.objects.get_or_create(
                nom=info["nom"], defaults={"couleur": info["couleur"]}
            )
            if cree:
                self._generer_logo_operateur(operateur, info["couleur"])
            operateurs_liste.append(operateur)

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Opérateurs créés : {", ".join([op.nom for op in operateurs_liste])}'
            )
        )
        return operateurs_liste

    def _generer_logo_operateur(self, operateur, couleur_hex):
        """Génère un logo simple pour l'opérateur."""
        try:
            img = Image.new("RGB", (200, 200), color=couleur_hex)
            dessin = ImageDraw.Draw(img)

            # Dessine un cercle avec la première lettre
            dessin.ellipse([40, 40, 160, 160], fill="white", outline="black", width=3)

            # Sauvegarde dans le modèle
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            nom_fichier = f"logo_{operateur.nom.lower()}.png"
            operateur.logo.save(nom_fichier, ContentFile(buffer.getvalue()))
            operateur.save()
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"⚠️  Logo non généré pour {operateur.nom}: {e}")
            )

    def _creer_technologies(self):
        """Crée les technologies réseau (2G, 3G, 4G, 5G)."""
        technologies_noms = ["2G", "3G", "4G", "5G"]
        for nom in technologies_noms:
            Technologie.objects.get_or_create(nom=nom)
        return list(Technologie.objects.all())

    def _creer_types_emplacement(self):
        """Crée les différents types d'emplacements pour les sites."""
        types = [
            "Terrain nu",
            "Bâtiment public",
            "Colline",
            "Zone industrielle",
            "Toit d'immeuble",
        ]
        for nom_type in types:
            Emplacement.objects.get_or_create(type_emplacement=nom_type)
        return list(Emplacement.objects.all())

    def _creer_sites_telecom(
        self, operateurs, technologies, emplacements, localites_dict
    ):
        """Crée 150 sites pour chaque opérateur (450 au total)."""
        if not localites_dict:
            self.stdout.write(self.style.ERROR("❌ Aucune localité disponible."))
            return 0

        sites_crees = 0
        sites_par_operateur = 150  # 150 sites par opérateur
        localites_ids = list(localites_dict.keys())

        for operateur in operateurs:
            self.stdout.write(f"  📶 Création des 150 sites pour {operateur.nom}...")

            for i in range(sites_par_operateur):
                try:
                    # Choisis une localité aléatoire
                    localite_id = random.choice(localites_ids)
                    info_loc = localites_dict[localite_id]

                    # Coordonnées près de la localité (léger décalage)
                    lat_site = info_loc["latitude"] + random.uniform(-0.01, 0.01)
                    lon_site = info_loc["longitude"] + random.uniform(-0.01, 0.01)

                    # CORRECTION : Génère un nom UNIQUE avec timestamp + index
                    timestamp = int(timezone.now().timestamp() * 1000)
                    nom_unique = f"SITE_{operateur.nom}_{timestamp}_{i:04d}"

                    # Crée le site dans la base de données
                    site = Site.objects.create(
                        nom=nom_unique,  # Utilise le nom unique
                        latitude=lat_site,
                        longitude=lon_site,
                        description=f"Site {operateur.nom} à {info_loc['nom_affichage']}",
                        date_mise_en_service=date.today()
                        - timedelta(days=random.randint(0, 1825)),  # 0-5 ans
                        type_pylone=random.choice(
                            ["Monopôle", "Treillis", "Autoportant", "Camouflé"]
                        ),
                        hauteur_antenne=round(random.uniform(25.0, 75.0), 2),
                        camouflage=random.choice([True, False]),
                        proprietaire=random.choice(["État", "Collectivité", "Privé"]),
                        operateur=operateur,
                        emplacement=random.choice(emplacements),
                        localite=info_loc["objet"],
                        num_dossier=f"DOS-{random.randint(2020, 2024)}-{random.randint(1000, 9999)}",
                        contact_proprietaire=f"+229 {random.randint(60, 99)}{random.randint(100000, 999999)}",
                    )

                    # Associe 1 à 3 technologies au site
                    techs_site = random.sample(technologies, random.randint(1, 3))
                    for tech in techs_site:
                        SiteTechnologie.objects.create(site=site, technologie=tech)

                    # Génère une image pour 30% des sites
                    if random.random() < 0.3:
                        self._generer_image_site(site)

                    # Crée un rapport de conformité pour 25% des sites
                    if random.random() < 0.25:
                        Conformite.objects.create(
                            site=site,
                            date_inspection=date.today()
                            - timedelta(days=random.randint(30, 365)),
                            statut=random.choice([True, False]),
                        )

                    sites_crees += 1

                    # Affiche la progression tous les 30 sites
                    if sites_crees % 30 == 0:
                        self.stdout.write(f"    {sites_crees} sites créés au total...")

                except Exception as e:
                    # Si erreur (normalement plus de doublons), on continue
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠️  Erreur sur un site: {e} - on continue..."
                        )
                    )
                    continue

        return sites_crees

    def _generer_image_site(self, site):
        """Génère une image factice d'un site de télécommunication."""
        try:
            img = Image.new("RGB", (800, 600), color=(240, 240, 240))
            dessin = ImageDraw.Draw(img)

            # Dessine un pylône
            dessin.line([400, 550, 400, 250], fill=(100, 100, 100), width=8)
            dessin.line([350, 350, 450, 350], fill=(150, 150, 150), width=6)
            dessin.polygon([380, 250, 420, 250, 400, 200], fill="red")

            # Sauvegarde l'image
            buffer = BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            nom_fichier = f"site_{site.id}.jpg"
            site.photo.save(nom_fichier, ContentFile(buffer.getvalue()))
            site.save(update_fields=["photo"])
        except Exception:
            pass  # Ignore les erreurs de génération d'image
