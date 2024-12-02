from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.http import JsonResponse
from django.db import IntegrityError
from django.contrib import messages 
from datetime import datetime

from django.shortcuts import render
# from django.apps import apps
from .models import *
import pandas as pd
import unicodedata
import openpyxl
import logging
import re

logger = logging.getLogger(__name__)

def handle_message(request, message, level='success'):
    if level == 'success':
        messages.success(request, message)
    elif level == 'error':
        messages.error(request, message)

# Vue pour récupérer les données statistiques avec filtrage
@login_required(login_url='authentication:login')
def get_statistics_data(request):
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    operateur_id = request.GET.get('operateur')
    conformite_status = request.GET.get('conformite')

    # Création des requêtes de base pour les sites
    sites_query = Site.objects.all()

    # Filtrage par date pour les sites
    if date_from:
        sites_query = sites_query.filter(date_autorisation__gte=date_from)
    
    if date_to:
        sites_query = sites_query.filter(date_autorisation__lte=date_to)

    # Filtrage par opérateur
    if operateur_id:
        sites_query = sites_query.filter(operateur_id=operateur_id)

    # Création de la requête de base pour les conformités liées aux sites filtrés
    conformite_query = Conformite.objects.filter(site__in=sites_query)

    # Filtrage par statut de conformité
    if conformite_status:
        conformite_filter = Q(statut=True) if conformite_status == 'conforme' else Q(statut=False)
        conformite_query = conformite_query.filter(conformite_filter)

    # Comptage des résultats
    sites_count = sites_query.count()
    conformite_count = conformite_query.count()
    operateurs_count = sites_query.values('operateur').distinct().count()

    # Comptage des sites conformes et non conformes
    conformes_count = conformite_query.filter(statut=True).count()
    non_conformes_count = conformite_query.filter(statut=False).count()

    data = {
        'sites_count': sites_count, 
        'conformite_count': conformite_count, 
        'operateurs_count': operateurs_count, 
        'conformes_count': conformes_count,  
        'non_conformes_count': non_conformes_count,    
}

    return JsonResponse(data)

login_required(login_url='authentication:login')
def get_communes(request):
    """
    Vue pour récupérer les communes en fonction des départements sélectionnés.
    Si un ou plusieurs départements sont sélectionnés, retourne les communes correspondantes.
    """
    departement_ids = request.GET.getlist('departement_id[]')  # Récupère une liste d'IDs des départements
    if departement_ids:  # Si au moins un département est sélectionné
        communes = Commune.objects.filter(departement_id__in=departement_ids).values('id', 'nom')
        return JsonResponse(list(communes), safe=False)
    return JsonResponse([], safe=False)  # Retourne une liste vide si aucun département n'est sélectionné

# Normalisation des noms de colonnes
def normalize_column_name(col_name):
    if col_name is None:
        logger.warning("Nom de colonne vide.")
        return None
    
    col_name = col_name.lower()
    
    # Normalisation des caractères
    col_name = ''.join((c for c in unicodedata.normalize('NFD', col_name) if unicodedata.category(c) != 'Mn'))
    
    # Remplacer les espaces par des underscores, décommentez la ligne ci-dessous
    col_name = col_name.replace(' ', '_')
    
    col_name = re.sub(r"[^a-z0-9_]", '', col_name)
    # Vérifier si le nom est vide après le traitement
    if not col_name:
        logger.error("Nom de colonne vide après normalisation.")
        return None 
    
    return col_name.strip()

def safe_strip(value):
    """
    Supprime les espaces en début et en fin de chaîne, ainsi que les espaces insécables et invisibles.
    Si la valeur est None, elle est renvoyée telle quelle.

    Args:
        value (any): La valeur à nettoyer.

    Returns:
        str or any: La valeur nettoyée si c'est une chaîne, sinon la valeur d'origine.
    """
    if isinstance(value, str):
        # Utilisation d'une expression régulière pour supprimer tous les types d'espaces insécables
        cleaned_value = re.sub(r'\s+', ' ', value.strip())
        return cleaned_value.replace('\xa0', '').replace('\u200b', '')
    return value  # Retourner la valeur telle quelle pour les valeurs None ou autres

def clean_row_values(row):
    """
    Nettoie les valeurs d'une ligne de données en remplaçant les valeurs vides ou NaN par None, 
    et en nettoyant les chaînes de caractères.

    Args:
        row (dict): La ligne de données à nettoyer.

    Returns:
        dict: La ligne nettoyée.
    """
    for key, value in row.items():
        if pd.isna(value) or value == '':
            logger.debug(f"Valeur manquante pour la colonne '{key}', remplacée par None.")
            row[key] = None
        else:
            cleaned_value = safe_strip(value)
            if cleaned_value != value:
                logger.debug(f"Valeur pour la colonne '{key}' nettoyée : '{value}' -> '{cleaned_value}'.")
            row[key] = cleaned_value or None  
    return row

# Nettoyage des valeurs numériques
def clean_numeric_value(value):
    if pd.isna(value) or value == '':
        return None
    value = safe_strip(value)  # Supprimer les espaces insécables s'il y en a
    try:
        return float(value)
    except ValueError:
        logger.warning(f"Valeur numérique invalide : {value}")
        return None

def validate_latitude_longitude(lat, long):
    lat = clean_numeric_value(lat)
    long = clean_numeric_value(long)
    
    if lat is not None and not (-90 <= lat <= 90):
        raise ValidationError(f"Latitude invalide: {lat}")
    if long is not None and not (-180 <= long <= 180):
        raise ValidationError(f"Longitude invalide: {long}")
    
    return lat, long

def validate_date(date_value, formats=["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]):
    if isinstance(date_value, pd.Timestamp):
        return date_value
    
    for fmt in formats:
        try:
            return pd.Timestamp(datetime.strptime(date_value, fmt)) 
        except ValueError:
            continue
    raise ValidationError(f"Format de date incorrect: {date_value}")

# Récupérer ou créer un objet clé étrangère
def get_or_create_foreign_key(model_class, field_name, value):

    """
    Récupère ou crée une instance d'un modèle en fonction d'une clé étrangère.

    Args:
        model_class (Model): La classe de modèle à utiliser.
        field_name (str): Le nom du champ à utiliser pour la recherche.
        value (any): La valeur à rechercher ou à créer.

    Returns:
        tuple: L'instance du modèle et un booléen indiquant si elle a été créée.
    
    Raises:
        ValidationError: Si une erreur se produit lors de la récupération ou de la création.
    """
    
    lookup = {field_name: value}
    
    try:
        instance, created = model_class.objects.get_or_create(**lookup)
        return instance, created
    except IntegrityError as e:
        logger.error(f"Erreur d'intégrité avec {model_class.__name__} ({field_name}={value}): {e}")
        raise ValidationError(f"Erreur d'intégrité avec {model_class.__name__} ({field_name}={value})")
    except Exception as e:
        logger.error(f"Erreur avec {model_class.__name__} ({field_name}={value}): {e}")
        raise ValidationError(f"Erreur avec {model_class.__name__} ({field_name}={value})")

def get_or_create_localite(row):
    departement_nom = safe_strip(row.get('departement').lower())
    commune_nom = safe_strip(row.get('communes').lower())
    localite_nom = safe_strip(row.get('localite').lower())

    logger.debug(f"Département: '{departement_nom}', Commune: '{commune_nom}', Localité: '{localite_nom}'")

    if not departement_nom or not commune_nom or not localite_nom:
        raise ValidationError(f"Département, commune et localité requis (Département: {departement_nom}, Commune: {commune_nom}, Localité: {localite_nom})")

    try:
        # Récupérer ou créer le département
        departement_instance, _ = Departement.objects.get_or_create(nom=departement_nom)

        # Récupérer ou créer la commune
        commune_instance, created_com = Commune.objects.get_or_create(nom=commune_nom, departement=departement_instance)

        # Récupérer ou créer la localité
        localite_instance, created_loc = Localite.objects.get_or_create(localite=localite_nom, commune=commune_instance)

        if created_loc:
            logger.info(f"Nouvelle localité créée: {localite_nom} dans la commune {commune_nom}")
        else:
            logger.debug(f"Localité existante trouvée: {localite_nom} dans la commune {commune_nom}")

        return localite_instance

    except IntegrityError as e:
        logger.error(f"Erreur d'intégrité lors de la création de la localité {localite_nom}: {e}")
        raise ValidationError(f"Erreur d'intégrité: {e}")
    except Exception as e:
        logger.error(f"Erreur inconnue lors de la création de la localité {localite_nom}: {e}")
        raise ValidationError(f"Erreur inconnue: {e}")

# Récupération ou création d'un emplacement
def get_or_create_emplacement(row):
    type_emplacement = row.get("emplacement", "").strip()
    
    # Si type_emplacement est vide, retourner None
    if not type_emplacement:
        return None

    emplacement, created = Emplacement.objects.get_or_create(type_emplacement=type_emplacement)
    return emplacement

def process_excel_file(uploaded_file):
    errors = []
    try:
        df = pd.read_excel(uploaded_file, engine="openpyxl", header=0)
        logger.debug(f"Colonnes dans le fichier Excel avant normalisation : {df.columns.tolist()}")
    
        df.columns = [normalize_column_name(col) for col in df.columns]
        df = df.fillna('')  # Utilise None pour les valeurs manquantes
        
        for index, row in df.iterrows():
            row = clean_row_values(row)
            logger.debug(f"Traitement de la ligne {index + 1}: {row}")

            try:
                localite_instance = get_or_create_localite(row)
                emplacement_instance = get_or_create_emplacement(row)
                operateur_instance, _ = get_or_create_foreign_key(Operateur, 'nom', row.get('operateur'))
                
                latitude, longitude = validate_latitude_longitude(row.get('latitude_du_candidat'), row.get('longitude_du_candidat'))

                # Log pour vérifier la date
                logger.debug(f"Date autorisation brute pour la ligne {index + 1}: {row.get('date_autorisation')}")
                
                date_autorisation = validate_date(row.get('date_autorisation')) if row.get('date_autorisation') else None
                date_mise_en_service = validate_date(row.get('date_mise_en_service')) if row.get('date_mise_en_service') else None
                
                # Dictionnaire de correspondance pour les valeurs booléennes possibles
                camouflage_mapping = {
                    'oui': True, 'yes': True, 'true': True, '1': True,
                    'non': False, 'no': False, 'false': False, '': False, '0': False
                }

                # Obtenir la valeur de 'camouflage' dans la ligne (si None, utilise une chaîne vide '')
                camouflage_value = row.get('camouflage', '') 

                # Assurer qu'il s'agit d'une chaîne de caractères et nettoyer les espaces inutiles
                camouflage_value = str(camouflage_value).replace('\xa0', '').strip().lower()

                # Mapper la valeur selon le dictionnaire ou utiliser False par défaut si la clé est absente
                camouflage = camouflage_mapping.get(camouflage_value, False)


                
                site_data = {
                    'nom': row.get('id_du_site', f"Site_{index + 1}"),
                    'localite': localite_instance,
                    'latitude': latitude,
                    'longitude': longitude,
                    'avis_arcep': row.get('avis_de_larcep_benin'),
                    'observation': row.get('observations'),
                    'emplacement': emplacement_instance,
                    'type_pylone': row.get('type_pylone'),
                    'hauteur_antenne': row.get('hauteur_antenne'),
                    'camouflage': camouflage,
                    'description': row.get('description'),
                    'proprietaire': row.get('proprietaire_site'),
                    'operateur': operateur_instance,
                    'num_dossier': row.get('n_dossier'),
                    'ref_courrier': row.get('ref_courrier'),
                    'date_autorisation': date_autorisation,
                    'date_mise_en_service': date_mise_en_service
                }
                site_data_filtered = {key: value for key, value in site_data.items() if value is not None}
                
                Site.objects.update_or_create(nom=site_data_filtered['nom'], defaults=site_data_filtered)
                logger.info(f"Site '{site_data_filtered['nom']}' créé/mis à jour avec succès.")
                
            except ValidationError as ve:
                logger.warning(f"Erreur de validation à la ligne {index + 1}: {ve}")
                errors.append(f"Ligne {index + 1}: {ve}")
            except Exception as e:
                logger.error(f"Erreur inattendue à la ligne {index + 1}: {e}")
                errors.append(f"Ligne {index + 1}: {e}")
                
    except Exception as e:
        logger.error(f"Erreur lors du traitement du fichier Excel: {e}")
        raise ValidationError(f"Erreur lors du traitement du fichier Excel: {e}")

    return errors

def get_filtered_sites(departements=None, communes=None, operateurs=None, conformite=None):
    
    """
        Récupère les sites filtrés selon les critères spécifiés.

        Args:
            departements (list): Liste des IDs de départements.
            communes (list): Liste des IDs de communes.
            operateurs (list): Liste des IDs d'opérateurs.
            conformite (list): Liste des statuts de conformité (e.g., ['conforme', 'non-conforme', 'sans-rapport']).

        Returns:
            QuerySet: Les sites filtrés.
    """
    
    sites = Site.objects.select_related('operateur', 'localite', 'conformite').all()

    if departements:
        sites = sites.filter(localite__commune__departement_id__in=departements)
    if communes:
        sites = sites.filter(localite__commune_id__in=communes)
    if operateurs:
        sites = sites.filter(operateur_id__in=operateurs)
    
    if conformite:
        conformite_filters = Q()
        if 'conforme' in conformite:
            conformite_filters |= Q(conformite__statut=True)
        if 'non-conforme' in conformite:
            conformite_filters |= Q(conformite__statut=False)
        if 'sans-rapport' in conformite:
            conformite_filters |= Q(conformite__isnull=True)
        sites = sites.filter(conformite_filters)  # Appliquer la condition OR

    return sites

def recherche_ajax(request):
    query = request.GET.get('q', '')
    resultats = []

    if query:
        sites = Site.objects.filter(
            Q(nom__icontains=query) |
            Q(description__icontains=query) |
            Q(proprietaire__icontains=query) |
            Q(operateur__nom__icontains=query) |
            Q(localite__localite__icontains=query) |
            Q(localite__commune__nom__icontains=query) |
            Q(localite__commune__departement__nom__icontains=query)
        ).distinct()

        resultats = [
            {
                'id': site.id,
                'nom': site.nom,
                'description': site.description,
                'localite': str(site.localite),
                'operateur': site.operateur.nom,
            } for site in sites
        ]

    return JsonResponse({'resultats': resultats})

