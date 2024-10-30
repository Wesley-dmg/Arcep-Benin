from django.core.exceptions import ValidationError
from django.db import models
import PyPDF2

# Models pour les opérateurs
class Operateur(models.Model):
    """Modèle représentant un opérateur de télécommunication."""
    nom = models.CharField(max_length=255, unique=True, verbose_name="Nom de l'opérateur")
    logo = models.ImageField(upload_to='Operateurs/', blank=True, null=True, verbose_name="Logo de l'opérateur")
    couleur = models.CharField(max_length=50, blank=True, null=True, verbose_name="Couleur de l'opérateur")

    def __str__(self):
        return self.nom

    class Meta:
        ordering = ['nom']
        verbose_name = "Opérateur"
        verbose_name_plural = "Opérateurs"

# Modèle pour les emplacements
class Emplacement(models.Model):
    """Modèle représentant un type d'emplacement."""
    type_emplacement = models.CharField(max_length=255, verbose_name="Type d'emplacement")

    def __str__(self):
        return self.type_emplacement

    class Meta:
        verbose_name = "Emplacement"
        verbose_name_plural = "Emplacements"

class Departement(models.Model):
    """Modèle représentant un département."""
    nom = models.CharField(max_length=255, unique=True, verbose_name="Nom du département")

    def __str__(self):
        return self.nom
    
class Commune(models.Model):
    """Modèle représentant une commune."""
    # The line `# nom = models.CharField(max_length=255, verbose_name="Nom de la commune")` is a
    # commented-out line in the `Commune` model class definition. This means that this line of code is
    # not active or used in the model definition.
    nom = models.CharField(max_length=255, verbose_name="Nom de la commune")
    departement = models.ForeignKey(Departement, on_delete=models.CASCADE, verbose_name="Département")
    
    def __str__(self):
        return self.nom

# Modèle pour les Localité
class Localite(models.Model):
    commune = models.ForeignKey(Commune, on_delete=models.CASCADE, verbose_name="Commune")
    localite = models.CharField(max_length=255, verbose_name="Localité")

    def clean(self):
        super().clean()
        if self.commune and not self.commune.departement:
            raise ValidationError(f"La commune {self.commune} n'est pas associée à un département valide.")

    def __str__(self):
        return f"{self.localite}, {self.commune.nom}, {self.commune.departement.nom}"

    class Meta:
        verbose_name = "Localité"
        verbose_name_plural = "Localités"

# Modèle pour les Technologies
class Technologie(models.Model):
    TECHNOLOGY_CHOICES = [
        ('5G-MMWAVE', '5G mmWave'),
        ('5G-NR', '5G NR'),
        ('5G-SUB_6', '5G Sub-6 GHz'),
        ('ADSL', 'ADSL'),
        ('BLUETOOTH-4', 'Bluetooth 4.0 (LE)'),
        ('BLUETOOTH-5', 'Bluetooth 5.0'),
        ('CABLE-DOCSIS', 'Cable DOCSIS'),
        ('EDGE', 'EDGE'),
        ('FEMTOCELL', 'Femtocell'),
        ('FTTH-EPON', 'FTTH EPON'),
        ('FTTH-GPON', 'FTTH GPON'),
        ('GPRS', 'GPRS'),
        ('GSM-1800', 'GSM 1800'),
        ('GSM-900', 'GSM 900'),
        ('HSPA', 'HSPA'),
        ('HSPA-PLUS', 'HSPA+'),
        ('LORA', 'LoRa'),
        ('LORAWAN', 'LoRaWAN'),
        ('LTE-1800', 'LTE 1800'),
        ('LTE-2600', 'LTE 2600'),
        ('LTE-800', 'LTE 800'),
        ('LTE-A', 'LTE-A'),
        ('LTE-M', 'LTE-M'),
        ('MICRO-CELL', 'Micro Cell'),
        ('MICROWAVE-PTP', 'Microwave Point-to-Point'),
        ('MICROWAVE-PTMP', 'Microwave Point-to-Multipoint'),
        ('MPLS', 'MPLS'),
        ('NB-IOT', 'NB-IoT'),
        ('P25', 'P25'),
        ('PICO-CELL', 'Pico Cell'),
        ('SAT-VSAT', 'Satellite VSAT'),
        ('SIGFOX', 'Sigfox'),
        ('TETRA', 'TETRA'),
        ('UMTS-2100', 'UMTS 2100'),
        ('UMTS-900', 'UMTS 900'),
        ('VDSL', 'VDSL'),
        ('VPN', 'VPN'),
        ('WIFI', 'Wi-Fi'),
        ('Z-WAVE', 'Z-Wave'),
        ('ZIGBEE', 'Zigbee'),
    ]
    
    nom = models.CharField(max_length=255, choices=TECHNOLOGY_CHOICES, verbose_name="Nom de la technologie")

    def __str__(self):
        return dict(self.TECHNOLOGY_CHOICES).get(self.nom, self.nom).replace("_", " ")

    class Meta:
        ordering = ['nom']
        verbose_name = "Technologie"
        verbose_name_plural = "Technologies"

# Modèle pour les sites
class Site(models.Model):
    nom = models.CharField(max_length=255, blank=False, null=False, verbose_name="Nom du site")
    photo = models.ImageField(upload_to='Sites/', blank=True, null=True, verbose_name="Photo du site")
    latitude = models.DecimalField(max_digits=15, decimal_places=12, blank=True, null=True, verbose_name="Latitude")
    longitude = models.DecimalField(max_digits=15, decimal_places=12, blank=True, null=True, verbose_name="Longitude")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    date_mise_en_service = models.DateField(blank=True, null=True, verbose_name="Date de mise en service")
    type_pylone = models.CharField(max_length=255, blank=True, null=True, verbose_name="Type de pylône")
    hauteur_antenne = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="Hauteur de l'antenne")
    camouflage = models.BooleanField(default=False, verbose_name="Camouflage")
    proprietaire = models.CharField(max_length=255, blank=True, null=True, verbose_name="Propriétaire")
    operateur = models.ForeignKey(Operateur, blank=False, null=False, on_delete=models.PROTECT, verbose_name="Opérateur")
    emplacement = models.ForeignKey(Emplacement, blank=True, null=True, on_delete=models.PROTECT, verbose_name="Emplacement")
    localite = models.ForeignKey(Localite, blank=True, null=True, on_delete=models.PROTECT, verbose_name="Localité")
    technologies = models.ManyToManyField(Technologie, through='SiteTechnologie')
    num_dossier = models.CharField(max_length=255, blank=True, null=True, verbose_name="Numéro de dossier")
    # contact_proprietaire = models.CharField(max_length=255, null=True, blank=True)
    add_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'ajout")
    
    ref_courrier = models.CharField(max_length=255, blank=True, null=True, verbose_name="Référence de courrier")
    observation = models.TextField(blank=True, null=True, verbose_name="Observation")
    avis_arcep = models.TextField(blank=True, null=True, verbose_name="Avis ARCEP")
    date_autorisation = models.DateField(blank=True, null=True, verbose_name="Date d'autorisation")

    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = "Site"
        verbose_name_plural = "Sites"

def validate_pdf(value):
    if not value.name.endswith('.pdf'):
        raise ValidationError("Le fichier doit être un PDF.")
    
    try:
        with value.open('rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            if len(pdf_reader.pages) == 0:
                raise ValidationError("Le fichier PDF est vide ou corrompu.")
    except PyPDF2.errors.PdfReadError:
        raise ValidationError("Le fichier doit être un PDF valide.")
    
# Modèle pour la conformité des sites
class Conformite(models.Model):
    site = models.OneToOneField(Site, on_delete=models.CASCADE, verbose_name="Site conforme", related_name="conformite")
    rapport = models.FileField(upload_to='Uploads/pdf/', validators=[validate_pdf], verbose_name="Rapport(PDF)")
    date_inspection = models.DateField(verbose_name="Date d'inspection")
    statut = models.BooleanField(verbose_name="Statut de conformité")
    
    def __str__(self):
        return f"{'Conforme' if self.statut else 'Non conforme'} ({self.date_inspection})"

    class Meta:
        verbose_name = "Conformité"
        verbose_name_plural = "Conformités"

# Modèle intermédiaire pour les technologies des sites
class SiteTechnologie(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, verbose_name="Site")
    technologie = models.ForeignKey(Technologie, on_delete=models.CASCADE, verbose_name="Technologie")
    date_ajout = models.DateTimeField(auto_now_add=True, verbose_name="Date d'ajout de la technologie")
    
    class Meta:
        constraints = [
        models.UniqueConstraint(fields=['site', 'technologie'], name='unique_site_technologie')
        ]
        verbose_name = "Technologie du site"
        verbose_name_plural = "Technologies des sites"
        
# Modèle pour les fichiers téléchargés
class UploadedFile(models.Model):
    file = models.FileField(upload_to='Uploads/excel/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    