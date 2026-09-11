from import_export import resources, fields
from apps.base.models.locations import Island, Province, RegencyType, Regency, District, Village
from import_export.widgets import ForeignKeyWidget
from django_currentuser.middleware import get_current_authenticated_user
from apps.base.models.utils import prepare_import, set_cby_uby
from django.utils import timezone

class VillageImportRsc(resources.ModelResource):

    district = fields.Field(
        column_name='district',
        attribute='district',
        widget=ForeignKeyWidget(District, 'code')
    )

    def before_import_row(self, row, **kwargs):
        prepare_import(row, Village)
    
    def before_save_instance(self, instance, row, **kwargs):
        is_new = not instance.pk
        user = kwargs.get('user', None)
        set_cby_uby(instance, is_new, user)

    class Meta:
        model = Village
        import_id_fields = ['code']
        exclude = ('id')
        fields = (
            'code',
            'name',
            'district',
            'latitude',
            'longitude',
            'postcode',
            'status',
        )

class DistrictImportRsc(resources.ModelResource):

    regency = fields.Field(
        column_name='regency',
        attribute='regency',
        widget=ForeignKeyWidget(Regency, 'code')
    )

    def before_import_row(self, row, **kwargs):
        prepare_import(row, District)
    
    def before_save_instance(self, instance, row, **kwargs):
        is_new = not instance.pk
        user = kwargs.get('user', None)
        set_cby_uby(instance, is_new, user)

    class Meta:
        model = District
        import_id_fields = ['code']
        fields = (
            'code',
            'name',
            'regency',
            'latitude',
            'longitude',
            'status',
        )

class RegencyImportRsc(resources.ModelResource):

    type = fields.Field(
        column_name='type',
        attribute='type',
        widget=ForeignKeyWidget(RegencyType, 'code')
    )
    province = fields.Field(
        column_name='province',
        attribute='province',
        widget=ForeignKeyWidget(Province, 'name')
    )

    def before_import_row(self, row, **kwargs):
        prepare_import(row, Regency)
    
    def before_save_instance(self, instance, row, **kwargs):
        is_new = not instance.pk
        user = kwargs.get('user', None)
        set_cby_uby(instance, is_new, user)

    class Meta:
        model = Regency
        import_id_fields = ['code']
        fields = (
            'code',
            'iso',
            'name',
            'type',
            'province',
            'capital',
            'remark',
            'latitude',
            'longitude',
            'status'
        )

class ProvinceImportRsc(resources.ModelResource):

    island = fields.Field(
        column_name='island',
        attribute='island',
        widget=ForeignKeyWidget(Island, 'name')
    )
 
    def before_import_row(self, row, **kwargs):
        prepare_import(row, Province)

    def before_save_instance(self, instance, row, **kwargs):
        user = kwargs.get('user', get_current_authenticated_user())
        if not instance.pk:  # On create
            if user:
                instance.cby = user  # Set 'created by'
            instance.uat = None  # 'Updated at' should not be set on creation
            instance.uby = None  # 'Updated by' should not be set on creation
        else:  # On update
            if user:
                instance.uby = user  # Set 'updated by'
            instance.uat = timezone.now()  # Always update the 'updated at' timestamp

        if instance.status == 'Active':
            instance.status = 1
        elif instance.status == 'Inactive':
            instance.status = 0

    class Meta:
        model = Province
        import_id_fields = ['code']
        fields = (
            'code',
            'name',
            'description',
            'shortname',
            'initial',
            'capital',
            'remark',
            'iso',
            'longitude',
            'latitude',
            'status',
            'island'
        )

class IslandImportRsc(resources.ModelResource):

    def before_import_row(self, row, **kwargs):
        prepare_import(row, Island)

    class Meta:
        model = Island
        import_id_fields = ['code']
        fields = (
            'code',
            'name',
            'initial',
            'iso',
            'description',
            'remark',
            'status'
        )