# -*- encoding: utf-8 -*-
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Q
from django.http import JsonResponse
from django.contrib import messages 
from datetime import datetime
from decimal import Decimal
from .models import *
import logging

# Importations de utils après les autres
from .utils import handle_message, process_excel_file, get_communes, get_statistics_data

logger = logging.getLogger(__name__)

def custom_page_not_found_view(request, exception):
    return render(request, 'home/page-404.html', status=404)

def custom_error_view(request):
    return render(request, 'home/page-500.html', status=500)


#Vue dashbord
@login_required(login_url='authentication:login')
def index(request):
    # Récupérer tous les sites
    sites = Site.objects.select_related('operateur', 'localite', 'emplacement').prefetch_related( 'conformite').all()

    site_data = [
        {
            'site': site,
            'has_conformite': hasattr(site, 'conformite'),
        }
        
        for site in sites
    ]
    # Calcul du nombre total de sites
    total_sites = sites.count()

    current_year = datetime.now().year
    new_sites_per_month = {month: 0 for month in range(1, 13)}  # Initialise le dictionnaire pour chaque mois

    new_sites = Site.objects.filter(date_mise_en_service__year=current_year)
    for site in new_sites:
        new_sites_per_month[site.date_mise_en_service.month] += 1

    # Calcul du total de conformités et du nombre de conformités réussies
    # total_conformite = Conformite.objects.count()
    total_conforme = Conformite.objects.filter(statut=True).count()

    # Calcul du pourcentage de conformité
    compliance_percentage = (total_conforme / total_sites) * 100 if total_sites > 0 else 0

    # Récupération de tous les opérateurs
    operateurs = Operateur.objects.all()

    # Préparation des données pour le graphique des statistiques des opérateurs
    operateur_statistics_labels = [operateur.nom for operateur in operateurs]
    operateur_statistics_counts = [sites.filter(operateur=operateur).count() for operateur in operateurs]
    operateur_statistics_non_conform_counts = [sites.filter(operateur=operateur, conformite__statut=False).count() for operateur in operateurs]
    operateur_statistics_colors = [operateur.couleur for operateur in operateurs]

    # Calcul du nombre total de sites non conformes
    non_compliant_sites_count = sites.filter(conformite__statut=False).count()

    # Préparation du contexte pour le template
    context = {
        'total_sites': total_sites,
        'new_sites': new_sites,        'compliance_percentage': compliance_percentage,
        'non_compliant_sites_count': non_compliant_sites_count,
        'operator_statistics_labels': operateur_statistics_labels,
        'operator_statistics_counts': operateur_statistics_counts,
        'operator_statistics_non_conform_counts': operateur_statistics_non_conform_counts,
        'operator_statistics_colors': operateur_statistics_colors,
        'new_sites_per_month': new_sites_per_month, 
        'site_data': site_data, 
    }

    return render(request, 'home/index.html', context)

# Vue pour l'affichage des sites sur la carte
@login_required
def map_view(request):
    # Récupère tous les sites avec une latitude et une longitude valides
    sites = Site.objects.filter(latitude__isnull=False, longitude__isnull=False)

    # Optionnel : Imprimer les détails de chaque site dans la console (à retirer en production)
    for site in sites:
        print(f"Site: {site.id}, {site.nom}, Latitude: {site.latitude}, Longitude: {site.longitude}")

    # Passer les sites au contexte du template
    context = {'sites': sites}
    return render(request, 'home/map.html', context)

# Vues CRUD pour les opérateurs
# Listes des opérateurs
@login_required(login_url='authentication:login')
def operateur_list(request):
    operateurs = Operateur.objects.annotate(
        total_sites=Count('site'),
        conforming_sites=Count('site__conformite', filter=Q(site__conformite__statut=True))
    )

    context = {
        'operateurs': operateurs
    }
    return render(request, 'home/operateurs.html', context)

# Vue pour mettre ajouter un opérateur
@login_required(login_url='authentication:login')
def operateur_create(request):
    if request.method == 'POST':
        try:
            nom = request.POST.get('nom')
            logo = request.FILES.get('logo')
            couleur = request.POST.get('couleur')

            operateur = Operateur.objects.create(nom=nom, logo=logo, couleur=couleur)

            # Créer un message flash
            handle_message(request, "Opérateur créé avec succès.")
            
            return redirect('home:operateur_list')
        except Exception as e:
            handle_message(request, f"Erreur lors de la création de l'opérateur : {e}")
            return redirect('home:operateur_create')

    return render(request, 'home/operateur_form.html')

# Vue pour mettre à jour  un opérateur
@login_required(login_url='authentication:login')
def operateur_update(request, pk):
    operateur = get_object_or_404(Operateur, pk=pk)
    if request.method == 'POST':
        try:
            nom = request.POST.get('nom')
            logo = request.FILES.get('logo')
            couleur = request.POST.get('couleur')

            # Mise à jour des champs de l'opérateur
            operateur.nom = nom
            if logo:
                operateur.logo = logo
            operateur.couleur = couleur
            operateur.save()

            # Créer un message flash et une notification
            handle_message(request, "Opérateur mis à jour avec succès.")
            
            # Redirection vers la liste des opérateurs
            return redirect('home:operateur_list')
        except Exception as e:
            handle_message(request, f"Erreur lors de la mise à jour de l'opérateur : {e}")
            return redirect('home:operateur_update', pk=pk)

    context = {
        'operateur': operateur
    }
    
    return render(request, 'home/operateur_form_upload.html', context)

# Vue pour supprimer un opérateur
@login_required(login_url='authentication:login')
def operateur_delete(request, pk):
    operateur = get_object_or_404(Operateur, pk=pk)
    if request.method == 'POST':
        try:
            # Supprimer l'opérateur
            operateur.delete()

            # Créer un message flash et une notification
            handle_message(request, "Opérateur supprimé avec succès.")
            
            # Redirection vers la liste des opérateurs après suppression
            return redirect('home:operateur_list')
        except Exception as e:
            handle_message(request, f"Erreur lors de la suppression de l'opérateur : {e}")
            return redirect('home:operateur_delete', pk=pk)

    context = {
        'operateur': operateur
    }
    return render(request, 'home/operateur_delete_confirm.html', context)

# Vues CRUD Emplacements
# Vues ajout et liste des emplacements
@login_required(login_url='authentication:login')
def emplacement_create(request):
    if request.method == 'POST':
        try:
            type_emplacement = request.POST.get('type_emplacement')
            Emplacement.objects.create(type_emplacement=type_emplacement)
            
            handle_message(request, "Emplacement créé avec succès.")
            
            return redirect('home:site_create')
        except Exception as e:
            
            handle_message(request, f"Erreur lors de la création de l'emplacement : {e}")
            return redirect('home:emplacement_create')
    
    return render(request, 'home/emplacement_create.html')

# Vues pour mettre à jour des emplacements
@login_required(login_url='authentication:login')
def emplacement_update(request, pk):
    emplacement = get_object_or_404(Emplacement, pk=pk)
    if request.method == 'POST':
        try:
            type_emplacement = request.POST.get('type_emplacement')
            emplacement.type_emplacement = type_emplacement
            emplacement.save()
            
            handle_message(request, "Emplacement mis à jour avec succès.")
            return redirect('home:site_create')
        except Exception as e:
            
            handle_message(request, f"Erreur lors de la mise à jour de l'emplacement : {e}")
            return redirect('home:emplacement_update', pk=pk)
    context = {'emplacement': emplacement}
    return render(request, 'home/emplacement_form.html', context)

# Vues pour supprimer des emplacements
@login_required(login_url='authentication:login')
def emplacement_delete(request, pk):
    emplacement = get_object_or_404(Emplacement, pk=pk)
    if request.method == 'POST':
        try:
            emplacement.delete()
            
            handle_message(request, "Emplacement supprimé avec succès.")
            return redirect('home:site_create')
        except Exception as e:
            
            handle_message(request, f"Erreur lors de la suppression de l'emplacement : {e}")
            return redirect('home:site_create', pk=pk)
    context = {
        'emplacement': emplacement
        }
    
    return render(request, 'home/emplacement_delete_confirm.html', context)

# Vues CRUD pour  Commune
@login_required(login_url='authentication:login')
def commune_list(request):
    communes = Commune.objects.all().order_by('nom')
    context = {
        'communes': communes
    }
    return render(request, 'home/commune_list.html', context)

@login_required(login_url='authentication:login')
def commune_create(request):
    departements = Departement.objects.all()

    if request.method == 'POST':
        departement_id = request.POST.get('departement')
        nom_commune = request.POST.get('nom')

        if departement_id and nom_commune:
            departement = get_object_or_404(Departement, id=departement_id)
            Commune.objects.create(nom=nom_commune, departement=departement)
            handle_message(request, "Commune ajoutée avec succès.")
            return redirect('home:commune_list')

        handle_message(request, "Tous les champs sont requis.")

    context = {
        'departements': departements
    }
    return render(request, 'home/commune_form.html', context)

@login_required(login_url='authentication:login')
def commune_update(request, pk):
    commune = get_object_or_404(Commune, pk=pk)
    departements = Departement.objects.all()

    if request.method == 'POST':
        departement_id = request.POST.get('departement')
        nom_commune = request.POST.get('nom')

        if departement_id and nom_commune:
            departement = get_object_or_404(Departement, id=departement_id)
            commune.nom = nom_commune
            commune.departement = departement
            commune.save()
            handle_message(request, "Commune mise à jour avec succès.")
            return redirect('home:commune_list')

        handle_message(request, "Tous les champs sont requis.")

    context = {
        'commune': commune,
        'departements': departements
    }
    return render(request, 'home/commune_form_update.html', context)

@login_required(login_url='authentication:login')
def commune_delete(request, pk):
    commune = get_object_or_404(Commune, pk=pk)

    if request.method == 'POST':
        commune.delete()
        handle_message(request, "Commune supprimée avec succès.")
        return redirect('home:commune_list')

    context = {
        'commune': commune
    }
    return render(request, 'home/commune_delete_confirm.html', context)

# Vues CRUD pour  Localite

# Vues pour ajouter une Localite
@login_required(login_url='authentication:login')
def localite_create(request):
    query = request.GET.get('q', '')
    if query:
        localites = Localite.objects.filter(
            Q(localite__icontains=query) | 
            Q(commune__nom__icontains=query) | 
            Q(commune__departement__nom__icontains=query)
        ).order_by('localite')
    else:
        localites = Localite.objects.all().order_by('localite')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        localites_data = [
            {
                'localite': localite.localite,
                'commune': localite.commune.nom,
                'departement': localite.commune.departement.nom,
                'id': localite.id
            } 
            for localite in localites
        ]
        return JsonResponse(localites_data, safe=False)

    # Récupérer les départements et les communes
    departements = Departement.objects.all()
    communes = Commune.objects.all()

    if request.method == 'POST':
        departement_id = request.POST.get('departement')
        commune_id = request.POST.get('commune')
        localite_name = request.POST.get('localite')

        if departement_id and commune_id and localite_name:
            try:
                commune = Commune.objects.get(id=commune_id)
                Localite.objects.create(commune=commune, localite=localite_name)
                handle_message(request, "La localité a été ajoutée avec succès.")
                return redirect('home:site_create')
            except Exception as e:
                handle_message(request, f"Erreur lors de l'ajout de la localité : {e}")
        else:
            handle_message(request, "Tous les champs sont requis.")

    context = {
        'departements': departements,
        'communes': communes,
        'localites': localites,
        'query': query,
    }
    
    return render(request, 'home/localite_form.html', context)
    
# Vue pour mettre à jour une localité
@login_required(login_url='authentication:login')
def localite_update(request, pk):
    localite = get_object_or_404(Localite, pk=pk)
    departements = Departement.objects.all()
    communes = Commune.objects.filter(departement=localite.commune.departement)

    if request.method == 'POST':
        commune_id = request.POST.get('commune')
        localite_name = request.POST.get('localite')
        commune = get_object_or_404(Commune, id=commune_id)

        localite.commune = commune
        localite.localite = localite_name
        localite.save()

        handle_message(request, "Localité mise à jour avec succès.")
        return redirect('home:localite_create')

    context = {
        'localite': localite,
        'departements': departements,
        'communes': communes,
    }
    return render(request, 'home/localite_form_update.html', context)

# Vue pour supprimer une localité
@login_required(login_url='authentication:login')
def localite_delete(request, pk):
    localite = get_object_or_404(Localite, pk=pk)
    if request.method == 'POST':
        try:
            localite.delete()
            
            handle_message(request, "Localité supprimée avec succès.")
            return redirect('home:localite_create')
        except Exception as e:
            
            handle_message(request, f"Erreur lors de la suppression de la localité : {e}")
            return redirect('home:site_create')
    
    context= {
        'localite':localite
        }  
    return render(request, 'home/localite_delete_confirm.html', context)

# Vues pour  CRUD les sites
# Vue pour lister les sites
@login_required(login_url='authentication:login')
def site_list(request):
    if ids := request.POST.getlist('ids'):
        if request.method == 'POST':
            try:
                Site.objects.filter(id__in=ids).delete()
                handle_message(request, "Les sites sélectionnés ont été supprimés avec succès.")
            except Exception as e:
                handle_message(request, f"Erreur lors de la suppression des sites : {e}")
            return redirect('home:site_list')

    sites = Site.objects.all()

    site_data = [
        {
            'site': site,
            'has_conformite': hasattr(site, 'conformite'),
        }
        for site in sites
    ]
    context = {
        'sites': site_data,
        'messages': messages.get_messages(request),
    }

    return render(request, 'home/site_list.html', context)

# Vue pour afficher les détails d'un site
@login_required(login_url='authentication:login')
def site_detail(request, pk):
    site = get_object_or_404(Site, pk=pk)
    conformite = Conformite.objects.filter(site=site).first()  # Récupère la première conformité associée au site

    context = {
        'site': site,
        'conformite': conformite,
    }
    return render(request, 'home/site_detail.html', context)

# Vue pour créer un site
@login_required(login_url='authentication:login')
def site_create(request):
    if request.method == 'POST':
        try:
            # Récupération des valeurs du formulaire
            operateur_id = request.POST.get('operateur')
            localite_id = request.POST.get('localite')
            emplacement_id = request.POST.get('emplacement')
            nom = request.POST.get('nom')
            photo = request.FILES.get('photo')
            latitude = float(request.POST.get('latitude', 0))
            longitude = float(request.POST.get('longitude', 0))
            description = request.POST.get('description')
            date_mise_en_service_str = request.POST.get('date_mise_en_service')
            type_pylone = request.POST.get('type_pylone')
            hauteur_antenne = Decimal(request.POST.get('hauteur_antenne', 0))
            camouflage = 'camouflage' in request.POST
            proprietaire = request.POST.get('proprietaire')
            num_dossier = request.POST.get('num_dossier')
            technologies_codes = request.POST.getlist('technologies')

            # Traitement de la date de mise en service
            try:
                date_mise_en_service = datetime.strptime(date_mise_en_service_str, '%Y-%m-%d').date() if date_mise_en_service_str else None
            except ValueError as e:
                raise ValidationError("La date de mise en service est invalide.") from e

            # Création du site
            site = Site.objects.create(
                nom=nom,
                photo=photo,
                latitude=latitude,
                longitude=longitude,
                description=description,
                date_mise_en_service=date_mise_en_service,
                type_pylone=type_pylone,
                hauteur_antenne=hauteur_antenne,
                camouflage=camouflage,
                proprietaire=proprietaire,
                num_dossier=num_dossier,
                operateur_id=operateur_id,
                localite_id=localite_id,
                emplacement_id=emplacement_id,
            )

            # Ajout des technologies
            for code in technologies_codes:
                try:
                    # Vérifie si la technologie existe dans la base de données
                    technologie = Technologie.objects.get(nom=code)
                except Technologie.DoesNotExist:
                    # Si la technologie n'existe pas, ajoute-la d'abord
                    if code in dict(Technologie.TECHNOLOGY_CHOICES):
                        # Crée la nouvelle technologie
                        technologie = Technologie.objects.create(nom=code)
                    else:
                        # Si la technologie n'est pas dans les choix, log l'erreur et passe à la suivante
                        logger.error(f"Technologie avec nom '{code}' non trouvée dans les choix.")
                        handle_message(request, f"Technologie '{code}' non trouvée dans les choix.")
                        continue

                # Associe la technologie au site
                SiteTechnologie.objects.create(site=site, technologie=technologie)
                logger.info(f"Technologie ajoutée : {technologie}")

            handle_message(request, "Le site a été ajouté avec succès.")
            return redirect('/site/')
        except ValidationError as e:
            handle_message(request, f"Erreur de validation : {e}")
        except Exception as e:
            handle_message(request, f"Erreur lors de l'ajout du site : {e}")

    # Préparation des données pour le formulaire
    operateurs = Operateur.objects.all()
    localites = Localite.objects.all()
    emplacements = Emplacement.objects.all()
    technologies = Technologie.TECHNOLOGY_CHOICES

    context = {
        'operateurs': operateurs,
        'localites': localites,
        'emplacements': emplacements,
        'technologies': technologies,
    }
    return render(request, 'home/site_form.html', context)

# Vue pour mise a jour de site
@login_required(login_url='authentication:login')
def site_update(request, pk):
    site = get_object_or_404(Site, pk=pk)
    if request.method == 'POST':
        try:
            # Récupération et validation des données
            nom = request.POST.get('nom')
            description = request.POST.get('description')
            emplacement = get_object_or_404(Emplacement, pk=request.POST.get('emplacement'))
            localite = get_object_or_404(Localite, pk=request.POST.get('localite'))
            operateur = get_object_or_404(Operateur, pk=request.POST.get('operateur'))
            photo = request.FILES.get('photo')
            latitude = float(request.POST.get('latitude', 0))
            longitude = float(request.POST.get('longitude', 0))
            date_mise_en_service_str = request.POST.get('date_mise_en_service')
            type_pylone = request.POST.get('type_pylone')
            hauteur_antenne = Decimal(request.POST.get('hauteur_antenne', 0))
            camouflage = 'camouflage' in request.POST
            proprietaire = request.POST.get('proprietaire')
            num_dossier = request.POST.get('num_dossier')
            technologies_codes = request.POST.getlist('technologies')

            # Validation de la date
            try:
                date_mise_en_service = datetime.strptime(date_mise_en_service_str, '%Y-%m-%d').date() if date_mise_en_service_str else None
            except ValueError as e:
                raise ValidationError("La date de mise en service est invalide.") from e

            # Mise à jour des valeurs dans l'objet site
            site.nom = nom
            site.description = description
            site.emplacement = emplacement
            site.localite = localite
            site.operateur = operateur

            if photo:
                site.photo = photo

            site.latitude = latitude
            site.longitude = longitude
            site.date_mise_en_service = date_mise_en_service
            site.type_pylone = type_pylone
            site.hauteur_antenne = hauteur_antenne
            site.camouflage = camouflage
            site.proprietaire = proprietaire
            site.num_dossier = num_dossier

            # Enregistrement des modifications
            site.save()
            handle_message(request, "Site mise à avec succès.")
            # Mise à jour des technologies associées
            existing_technologies = set(site.technologies.values_list('nom', flat=True))
            new_technologies = set(technologies_codes)

            # Ajoute les nouvelles technologies qui ne sont pas encore dans la base
            for code in new_technologies:
                if code not in existing_technologies:
                    if code in dict(Technologie.TECHNOLOGY_CHOICES):
                        technologie, created = Technologie.objects.get_or_create(nom=code)
                        if created:
                            logger.info(f"Technologie ajoutée : {technologie}")
                    else:
                        logger.error(f"Technologie avec nom '{code}' non trouvée dans les choix.")
                        handle_message(request, f"Technologie '{code}' non trouvée dans les choix.")
                        continue

            # Synchronisation des technologies associées au site
            site.technologies.set(Technologie.objects.filter(nom__in=new_technologies))
            logger.info(f"Technologies mises à jour pour le site : {site}")

            # Message de succès et redirection
            handle_message(request, "Site mis à jour avec succès.")
            return redirect('home:site_detail', pk=site.id)



        except (ValueError, Emplacement.DoesNotExist, Localite.DoesNotExist, Operateur.DoesNotExist) as e:
            handle_message(request, f"Erreur lors de la mise à jour du site : {str(e)}")
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du site: {str(e)}")
            handle_message(request, f"Erreur lors de la mise à jour du site : {e}")

    # Contexte pour le formulaire de mise à jour
    context = {
        'site': site,
        'emplacements': Emplacement.objects.all(),
        'localites': Localite.objects.all(),
        'operateurs': Operateur.objects.all(),
        'technologies': Technologie.TECHNOLOGY_CHOICES,
        'selected_technologies': site.technologies.values_list('nom', flat=True),
        'formatted_date_mise_en_service': site.date_mise_en_service.strftime('%Y-%m-%d') if site.date_mise_en_service else ''
    }

    return render(request, 'home/site_update.html', context)

# Vue pour supprimer un site
@login_required(login_url='authentication:login')
def site_delete(request, pk):
    site = get_object_or_404(Site, pk=pk)
    if request.method == 'POST':
        try:
            site.delete()
            handle_message(request, "Site supprimé avec succès.")
            return redirect('home:site_list')
        except Exception as e:
            handle_message(request, f"Erreur lors de la suppression du site : {e}")

    context = {
        'site': site
        }
    
    return render(request, 'home/site_confirm_delete.html', context)

@login_required(login_url='authentication:login')
def delete_multiple_sites(request):
    if request.method == 'POST':
        ids = request.POST.get('ids', '').split(',')
        if ids := [id for id in ids if id.isdigit()]:
            try:
                Site.objects.filter(id__in=ids).delete()
                handle_message(request, "Les sites sélectionnés ont été supprimés avec succès.")
                return JsonResponse({'success': True})
            except Exception as e:
                handle_message(request, f"Erreur lors de la suppression des sites : {e}")
                return JsonResponse({'success': False, 'error': str(e)})
        else:
            handle_message(request, "Aucun site sélectionné.")
            return JsonResponse({'success': False, 'error': "Aucun site sélectionné."})
    return redirect('home:site_list')

# Vue pour afficher les statistiques
@login_required(login_url='authentication:login')
def statistics(request):
    operateurs = Operateur.objects.all()
    context = {
        'operateurs': operateurs
    }
    return render(request, 'home/statistics.html', context)

# Liste des technologies et formulaire de création sur la même vue
@login_required(login_url='authentication:login')
def technologie_list_create(request):
    if request.method == 'POST':
        try:
            # Récupération des valeurs du formulaire
            type_technologie = request.POST.get('type_technologie')
            Technologie.objects.create(type_technologie=type_technologie)
            
            # Message de succès et redirection
            handle_message(request, "Technologie créée avec succès.", level='success')  # ici level est utilisé correctement
            return redirect('home:technologie_list_create')
        except Exception as e:
            # Message d'erreur en cas de problème
            handle_message(request, f"Erreur lors de la création de la technologie : {e}", level='error')  # ici level est utilisé correctement
            return redirect('home:technologie_list_create')

    # Rendu du formulaire de création
    return render(request, 'home/technologie_list_create.html')

# Mise à jour d'une technologie existante
@login_required(login_url='authentication:login')
def technologie_update(request, pk):
    technologie = get_object_or_404(Technologie, pk=pk)
    if request.method == 'POST':
        try:
            type_technologie = request.POST.get('type_technologie')
            technologie.type_technologie = type_technologie
            technologie.save()

            # Message de succès et redirection
            handle_message(request, "Technologie mise à jour avec succès.")
            return redirect('home:technologie_list_create')
        except Exception as e:
            handle_message(request, f"Erreur lors de la mise à jour de la technologie : {e}", tag='error')
            return redirect('home:technologie_update', pk=pk)

    context = {'technologie': technologie}
    return render(request, 'home/technologie_update.html', context)

# Suppression d'une technologie
@login_required(login_url='authentication:login')
def technologie_delete(request, pk):
    technologie = get_object_or_404(Technologie, pk=pk)
    if request.method == 'POST':
        try:
            technologie.delete()
            handle_message(request, "Technologie supprimée avec succès.")
            return redirect('home:technologie_list_create')
        except Exception as e:
            handle_message(request, f"Erreur lors de la suppression de la technologie : {e}", level='error')
            return redirect('home:technologie_delete', pk=pk)

    context = {'technologie': technologie}
    return render(request, 'home/technologie_confirm_delete.html', context)

# Vues CRUD pour les  conformité et les rapports d'analyse 
# Vues pour ajouter les  conformités et les rapports d'analyse 
@login_required(login_url='authentication:login')
def add_conformite(request, site_id):
    current_site = get_object_or_404(Site, id=site_id)

    if request.method == 'POST':
        try:
            # Récupérer les données pour la Conformité
            rapport = request.FILES.get('rapport')
            date_inspection_str = request.POST.get('date_inspection')
            statut = request.POST.get('statut') == 'conforme'

            # Récupérer les données pour le Site
            ref_courrier = request.POST.get('ref_courrier')
            observation = request.POST.get('observation')
            avis_arcep = request.POST.get('avis_arcep')
            date_autorisation_str = request.POST.get('date_autorisation')

            # Validation des dates
            try:
                date_inspection = datetime.strptime(date_inspection_str, '%Y-%m-%d').date()
                date_autorisation = datetime.strptime(date_autorisation_str, '%Y-%m-%d').date() if date_autorisation_str else None
            except ValueError:
                context = {
                    'current_site': current_site,
                    'error': 'Le format de la date est incorrect. Le format attendu est AAAA-MM-JJ.'
                }
                return render(request, 'home/conformite_form.html', context)

            # Mise à jour des informations du site
            current_site.ref_courrier = ref_courrier
            current_site.observation = observation
            current_site.avis_arcep = avis_arcep
            current_site.date_autorisation = date_autorisation
            current_site.save()

            # Création de la conformité
            Conformite.objects.create(
                site=current_site,
                rapport=rapport,
                date_inspection=date_inspection,
                statut=statut,
            )

            # Rediriger vers 'site_detail' en utilisant 'pk'
            return redirect('home:site_detail', pk=current_site.id)

        except Exception as e:
            context={
                'current_site': current_site,
                'error': f"Erreur lors de l'enregistrement : {e}"
            }
            return render(request, 'home/conformite_form.html', context)
    context={
        'current_site': current_site,
    }
    # Cas d'affichage initial du formulaire
    return render(request, 'home/conformite_form.html', context)

#Vue pour mettre a jour les rapports de conformité et les rapports d'analyse
@login_required(login_url='authentication:login')
def update_conformite(request, site_id):
    current_site = get_object_or_404(Site, id=site_id)
    
    try:
        conformite = Conformite.objects.get(site=current_site)
    except Conformite.DoesNotExist:
        return redirect('home:add_conformite', site_id=current_site.id)

    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            rapport = request.FILES.get('rapport', conformite.rapport)
            date_inspection_str = request.POST.get('date_inspection')

            # Convertir le statut en booléen
            statut = request.POST.get('statut') == 'True'

            # Mettre à jour les champs du site
            current_site.ref_courrier = request.POST.get('ref_courrier')
            current_site.observation = request.POST.get('observation')
            current_site.avis_arcep = request.POST.get('avis_arcep')
            date_autorisation_str = request.POST.get('date_autorisation')

            # Gestion des dates
            date_inspection = datetime.strptime(date_inspection_str, '%Y-%m-%d').date()
            date_autorisation = datetime.strptime(date_autorisation_str, '%Y-%m-%d').date() if date_autorisation_str else None

            # Mise à jour du site et de la conformité
            current_site.date_autorisation = date_autorisation
            current_site.save()

            conformite.rapport = rapport
            conformite.date_inspection = date_inspection
            conformite.statut = statut
            conformite.save()

            # Rediriger vers le détail du site après mise à jour
            return redirect('home:site_detail', pk=current_site.id)

        except Exception as e:
            # Loguer l'exception pour plus de détails
            print(f"Erreur lors de la mise à jour : {e}")
            context = {
                'current_site': current_site,
                'conformite': conformite,
                'step': 1,
                'error': f"Erreur lors de la mise à jour : {e}"
            }
            return render(request, 'home/conformite_update_form.html', context)

    context = {
        'current_site': current_site,
        'conformite': conformite,
        'step': 1  
    }
    return render(request, 'home/conformite_update_form.html', context)

# Vue pour supprimer les conformité  et les rapports d'analyse
@login_required(login_url='authentication:login')
def delete_conformite(request, site_id):
    # Récupérer le site associé à l'ID
    current_site = get_object_or_404(Site, id=site_id)
    
    try:
        # Récupérer la conformité liée au site
        conformite = Conformite.objects.get(site=current_site)

        # Si la méthode est POST, supprimer la conformité et réinitialiser les champs
        if request.method == 'POST':
            # Suppression de la conformité
            conformite.delete()

            # Réinitialiser les champs dans la table Site
            current_site.ref_courrier = None  # ou '' si c'est un champ CharField qui n'accepte pas NULL
            current_site.observation = None  # ou ''
            current_site.avis_arcep = None  # ou ''
            current_site.date_autorisation = None  # Pour un champ DateField

            # Sauvegarder les changements sur le site
            current_site.save()

            # Message de confirmation
            handle_message(request, "Conformité supprimée et champs du site réinitialisés avec succès.")
            return redirect('home:site_detail', pk=current_site.id)

    except Conformite.DoesNotExist:
        # Si la conformité n'existe pas, rediriger
        return redirect('home:site_detail', pk=current_site.id)

    context = {
        'current_site': current_site,
    }
    return render(request, 'home/conformite_delete.html', context)

@login_required(login_url='authentication:login')
def file_upload_view(request):
    if request.method != 'POST':
        return render(request, 'home/file_upload.html')

    uploaded_file = request.FILES.get('file')

    if not uploaded_file:
        handle_message(request, "Aucun fichier sélectionné.")
        return redirect('home:file_upload')

    try:
        # Sauvegarde du fichier téléversé
        instance = UploadedFile(file=uploaded_file)
        instance.save()

        # Processus de traitement basé sur le type de fichier sélectionné
        errors = process_excel_file(uploaded_file)

        if errors:
            for error in errors:
                handle_message(request, error)
            handle_message(request, "Certaines lignes n'ont pas pu être importées. Consultez les messages d'erreur.")
        else:
            handle_message(request, "Fichier téléversé et traité avec succès.") 
            return redirect('home:home')
    except ValidationError as ve:
        handle_message(request, f"Erreur lors du traitement du fichier : {ve}")
        logger.error(f"Erreur lors du traitement du fichier {uploaded_file.name}: {ve}")
    except Exception as e:
        handle_message(request, f"Une erreur inattendue s'est produite : {e}")
        logger.exception(f"Erreur imprévue lors du téléversement ou du traitement du fichier {uploaded_file.name}: {e}")

    return redirect('home:file_upload')

