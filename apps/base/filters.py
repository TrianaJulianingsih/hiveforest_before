from django.contrib.admin import SimpleListFilter

class CustomerMap(SimpleListFilter):
    title = 'Customer Map Status'
    parameter_name = 'customer'

    def lookups(self, request, model_admin):
        return (
            ('no', 'Not Mapped'),
            ('yes', 'Mapped'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(customer__isnull=False)
        elif self.value() == 'no':
            return queryset.filter(customer__isnull=True)
        return queryset
    
class DeletedListFilter(SimpleListFilter):
    title = 'Deleted Status'
    parameter_name = 'deleted'

    def lookups(self, request, model_admin):
        return (
            ('no', 'Existing'),
            ('yes', 'Deleted'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(deleted=True)
        elif self.value() == 'no':
            return queryset.filter(deleted=False)
        return queryset
    
class StatusListFilter(SimpleListFilter):
    title = 'Active Status'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return (
            ('1', 'Active'),
            ('0', 'Inactive'),
        )

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.filter(status=True)
        elif self.value() == '0':
            return queryset.filter(status=False)
        return queryset
    
class EffectiveYearFilter(SimpleListFilter):
    title = 'Effective Year'
    parameter_name = 'effective_year'
    template = 'admin/dropdown_filter.html'

    def lookups(self, request, model_admin):
        # For DateField use .dates(), not .datetimes()
        years = model_admin.get_queryset(request).dates('effective', 'year', order='DESC')
        return [(dt.year, dt.year) for dt in years]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(effective__year=self.value())
        return queryset