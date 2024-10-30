import os
import django
import random
from faker import Faker
from django.core.files.uploadedfile import InMemoryUploadedFile
import io

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.home.models import (
    Operateur,
    Emplacement,
    Departement,
    Commune,
    Localite,
    Technologie,
    Site,
    SiteTechnologie,
    Conformite,
)

fake = Faker('fr_FR')

def generate_random_latitude():
    return round(random.uniform(6.142, 12.396), 6)

def generate_random_longitude():
    return round(random.uniform(0.773, 3.839), 6)

def populate_initial_data():
    # Ajout des opérateurs
    if Operateur.objects.count() == 0:
        print("Ajout des opérateurs...")
        Operateur.objects.bulk_create([
            Operateur(nom="MTN", couleur="#FFDD00"),
            Operateur(nom="MOOV", couleur="#00A859"),
            Operateur(nom="CELTIIS", couleur="#002244")
        ])
    
    # Ajout des emplacements
    if Emplacement.objects.count() == 0:
        print("Ajout des emplacements...")
        Emplacement.objects.bulk_create([
            Emplacement(type_emplacement="Rural"),
            Emplacement(type_emplacement="Urbain"),
            Emplacement(type_emplacement="Suburbain")
        ])

    # Ajout des départements et communes
    if Departement.objects.count() == 0:
        print("Ajout des départements et communes...")
        departement_commune = {
            'Alibori': ['Banikoara', 'Gogounou', 'Kandi', 'Karimama', 'Malanville', 'Segbana'],
            'Atacora': ['Boukoumbé', 'Cobly', 'Kérou', 'Kouandé', 'Matéri', 'Natitingou', 'Péhunco', 'Tanguiéta', 'Toucountouna'],
            'Atlantique': ['Abomey-Calavi', 'Allada', 'Kpomassè', 'Ouidah', 'Sô-Ava', 'Toffo', 'Tori-Bossito', 'Zè'],
            'Borgou': ['Bembéréké', 'Kalalé', 'N\'Dali', 'Nikki', 'Parakou', 'Pèrèrè', 'Sinendé', 'Tchaourou'],
            'Collines': ['Bantè', 'Dassa-Zoumé', 'Glazoué', 'Ouèssè', 'Savalou', 'Savè'],
            'Couffo': ['Aplahoué', 'Djakotomey', 'Dogbo', 'Klouékanmè', 'Lalo', 'Toviklin'],
            'Donga': ['Bassila', 'Copargo', 'Djougou', 'Ouaké'],
            'Littoral': ['Cotonou'],
            'Mono': ['Athiémé', 'Bopa', 'Comè', 'Grand-Popo', 'Houéyogbé', 'Lokossa'],
            'Oueme': ['Adjarra', 'Adjohoun', 'Aguégués', 'Akpro-Missérété', 'Avrankou', 'Bonou', 'Dangbo', 'Porto-Novo', 'Sèmè-Kpodji'],
            'Plateau': ['Adja-Ouèrè', 'Ifangni', 'Kétou', 'Pobè', 'Sakété'],
            'Zou': ['Abomey', 'Agbangnizoun', 'Bohicon', 'Covè', 'Djidja', 'Ouinhi', 'Za-Kpota', 'Zagnanado', 'Zogbodomey'],
        }

        for departement, communes in departement_commune.items():
            depart = Departement.objects.create(nom=departement)
            for commune in communes:
                Commune.objects.create(nom=commune, departement=depart)

    # Ajout des localités
    if Localite.objects.count() == 0:
        print("Ajout des localités...")
        for commune in Commune.objects.all():
            Localite.objects.create(
                commune=commune,
                localite=fake.city()
            )

    # Ajout des technologies
    if Technologie.objects.count() == 0:
        print("Ajout des technologies...")
        technology_choices = [
            '5G mmWave', '5G NR', '5G Sub-6 GHz', 'ADSL', 'Bluetooth 4.0 (LE)', 
            'Bluetooth 5.0', 'Cable DOCSIS', 'EDGE', 'Femtocell', 'FTTH EPON', 
            'FTTH GPON', 'GPRS', 'GSM 1800', 'GSM 900', 'HSPA', 'HSPA+', 'LoRa', 
            'LoRaWAN', 'LTE 1800', 'LTE 2600', 'LTE 800', 'LTE-A', 'LTE-M', 
            'Micro Cell', 'Microwave Point-to-Point', 'Microwave Point-to-Multipoint', 
            'MPLS', 'NB-IoT', 'P25', 'Pico Cell', 'Satellite VSAT', 'Sigfox', 
            'TETRA', 'UMTS 2100', 'UMTS 900', 'VDSL', 'VPN', 'Wi-Fi', 'Z-Wave', 'Zigbee'
        ]
        Technologie.objects.bulk_create([Technologie(nom=tech) for tech in technology_choices])

def populate_sites(n):
    operateurs = list(Operateur.objects.all())
    emplacements = list(Emplacement.objects.all())
    localites = list(Localite.objects.all())
    technologies = list(Technologie.objects.all())

    if not operateurs or not emplacements or not localites or not technologies:
        print("Assurez-vous que les tables Operateur, Emplacement, Localite, et Technologie sont remplies avant d'exécuter ce script.")
        return

    sites_to_create = []
    site_technologies_to_create = []
    conformites_to_create = []

    for _ in range(n):
        site_nom = fake.company()
        site_latitude = generate_random_latitude()
        site_longitude = generate_random_longitude()

        if Site.objects.filter(nom=site_nom, latitude=site_latitude, longitude=site_longitude).exists():
            continue

        try:
            with open('/Users/macbookpro/Downloads/istockphoto-154932576-612x612.jpg', 'rb') as img_file:
                img_content = img_file.read()
                img_io = io.BytesIO(img_content)
                photo = InMemoryUploadedFile(
                    img_io, None, f'site_{fake.word()}.jpg', 'image/jpeg', len(img_content), None
                )

                site = Site(
                    nom=site_nom,
                    photo=photo,
                    latitude=site_latitude,
                    longitude=site_longitude,
                    description=fake.text(),
                    date_mise_en_service=fake.date_this_decade(),
                    type_pylone=fake.word(),
                    hauteur_antenne=round(random.uniform(10.00, 100.00), 2),
                    camouflage=fake.boolean(),
                    observation=fake.text(),
                    avis_arcep=fake.text(),
                    proprietaire=fake.name(),
                    num_dossier=fake.bothify(text='??####'),
                    ref_courrier=fake.bothify(text='???-###'),
                    date_autorisation=fake.date_this_decade(),
                    operateur=random.choice(operateurs),
                    emplacement=random.choice(emplacements),
                    localite=random.choice(localites),
                )

                sites_to_create.append(site)

                selected_technologies = random.sample(technologies, k=random.randint(1, 5))
                site_technologies_to_create.extend(
                    SiteTechnologie(site=site, technologie=tech)
                    for tech in selected_technologies
                )

                conformite = Conformite(
                    site=site,
                    rapport=None,  # Remplir si nécessaire
                    date_inspection=fake.date_this_decade(),
                    statut=fake.boolean()
                )
                conformites_to_create.append(conformite)

        except Exception as e:
            print(f"Erreur lors de la création du site : {e}")

    if sites_to_create:
        Site.objects.bulk_create(sites_to_create)
        SiteTechnologie.objects.bulk_create(site_technologies_to_create)
        Conformite.objects.bulk_create(conformites_to_create)

if __name__ == "__main__":
    populate_initial_data()
    print("Données initiales peuplées.")
    populate_sites(1568)
    print("Sites peuplés.")
