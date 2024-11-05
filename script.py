import random
from faker import Faker
from apps.home.models import Operateur, Departement, Commune, Localite, Technologie, Site, SiteTechnologie

fake = Faker('fr_FR')
Faker.seed(42)  # Pour garantir la reproductibilité des données

# Création des opérateurs
operateurs = ['MTN', 'MOOV', 'CELTIIS']
couleurs_operateurs = ['#FFCC00', '#009640', '#0074D9']

for nom, couleur in zip(operateurs, couleurs_operateurs):
    Operateur.objects.get_or_create(
        nom=nom,
        defaults={'couleur': couleur}
    )

# Création des départements et communes si nécessaire
departements = ['Atlantique', 'Littoral', 'Ouémé', 'Borgou', 'Alibori']
for dep in departements:
    departement, _ = Departement.objects.get_or_create(nom=dep)
    for i in range(1, 4):  # Ajouter 3 communes par département
        Commune.objects.get_or_create(
            nom=fake.city(),
            departement=departement
        )

# Création des localités
communes = Commune.objects.all()
for commune in communes:
    for _ in range(2):  # Ajouter 2 localités par commune
        Localite.objects.get_or_create(
            commune=commune,
            localite=fake.street_name()
        )

# Création des technologies si elles n'existent pas
technologies_noms = [
    '5G-NR', 'LTE-1800', 'UMTS-900', 'ADSL', 'VDSL',
    'HSPA', 'GPRS', 'EDGE', 'FTTH-GPON', 'WIFI'
]

for tech in technologies_noms:
    Technologie.objects.get_or_create(nom=tech)

# Création des sites
operateurs = Operateur.objects.all()
localites = Localite.objects.all()
technologies = Technologie.objects.all()

for _ in range(50):  # Générer 50 sites
    site = Site.objects.create(
        nom=f'Site {fake.unique.word()}',
        latitude=fake.latitude_between(min_value=6.0, max_value=12.0),  # Coordonnées pour le Bénin
        longitude=fake.longitude_between(min_value=1.0, max_value=4.0),
        description=fake.text(),
        type_pylone=random.choice(['Autostable', 'Haubané', 'Monopôle']),
        hauteur_antenne=round(random.uniform(20.0, 80.0), 2),
        camouflage=random.choice([True, False]),
        proprietaire=fake.company(),
        operateur=random.choice(operateurs),
        localite=random.choice(localites),
    )
    # Ajout de technologies associées au site
    for _ in range(random.randint(1, 3)):
        technologie = random.choice(technologies)
        SiteTechnologie.objects.get_or_create(site=site, technologie=technologie)

print("Données fictives générées avec succès !")
