from django.contrib import admin
from .models import (
    Operateur,
    Emplacement,
    Departement,
    Commune,
    Localite,
    Technologie,
    Site,
    Conformite,
    SiteTechnologie,
    UploadedFile,
)

@admin.register(Operateur)
class OperateurAdmin(admin.ModelAdmin):
    list_display = ('nom', 'couleur')
    search_fields = ('nom',)
    list_filter = ('couleur',)
    ordering = ('nom',)

@admin.register(Emplacement)
class EmplacementAdmin(admin.ModelAdmin):
    list_display = ('type_emplacement',)
    search_fields = ('type_emplacement',)

@admin.register(Departement)
class DepartementAdmin(admin.ModelAdmin):
    list_display = ('nom',)
    search_fields = ('nom',)

@admin.register(Commune)
class CommuneAdmin(admin.ModelAdmin):
    list_display = ('nom', 'departement')
    search_fields = ('nom',)
    list_filter = ('departement',)

@admin.register(Localite)
class LocaliteAdmin(admin.ModelAdmin):
    list_display = ('localite', 'commune')
    search_fields = ('localite',)
    list_filter = ('commune__departement',)

@admin.register(Technologie)
class TechnologieAdmin(admin.ModelAdmin):
    list_display = ('nom',)
    search_fields = ('nom',)

@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ('nom', 'operateur', 'localite', 'date_mise_en_service')
    search_fields = ('nom', 'operateur__nom', 'localite__localite')
    list_filter = ('operateur', 'localite', 'date_mise_en_service')
    ordering = ('nom',)
    date_hierarchy = 'date_mise_en_service'
    list_select_related = ('operateur', 'localite')

@admin.register(Conformite)
class ConformiteAdmin(admin.ModelAdmin):
    list_display = ('site', 'date_inspection', 'statut')
    list_filter = ('statut',)
    search_fields = ('site__nom',)
    ordering = ('-date_inspection',)

    def mark_as_compliant(self, request, queryset):
        queryset.update(statut=True)
        self.message_user(request, "Sélectionné(s) marqué(s) comme conforme(s).")

    def mark_as_non_compliant(self, request, queryset):
        queryset.update(statut=False)
        self.message_user(request, "Sélectionné(s) marqué(s) comme non conforme(s).")

    mark_as_compliant.short_description = "Marquer comme conforme"
    mark_as_non_compliant.short_description = "Marquer comme non conforme"

    actions = [mark_as_compliant, mark_as_non_compliant]

@admin.register(SiteTechnologie)
class SiteTechnologieAdmin(admin.ModelAdmin):
    list_display = ('site', 'technologie', 'date_ajout')
    list_filter = ('site', 'technologie')
    search_fields = ('site__nom', 'technologie__nom')
    ordering = ('-date_ajout',)

@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ('file', 'uploaded_at')
    search_fields = ('file',)
    ordering = ('-uploaded_at',)
