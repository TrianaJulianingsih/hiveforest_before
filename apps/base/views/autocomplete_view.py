from dal import autocomplete
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
# ╔════════════════════════════════════════════════════════════╗
# ║  Name: Autocomplete                                        ║
# ║  Type: Class Base View                                     ║
# ║  Purpose: To be used by django autocomplete light (dal)    ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\base\views\autocomplete_view.py                ║
# ║  Created: May/26-2025 by Setiadji                          ║
# ║  Updated: Jul/2-2025 by Setiadji                           ║
# ╚════════════════════════════════════════════════════════════╝
class GenericAutocompleteView(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    model = None
    _search_fields = ['name']  # fallback default

    def get_search_fields(self):
        return self._search_fields

    def get_queryset(self):
        if not self.request.user.is_authenticated or self.model is None:
            return self.model.objects.none()

        qs = self.model.objects.filter(deleted=False, status=1)

        if self.q:
            q_obj = Q()
            for field in self.get_search_fields():
                q_obj |= Q(**{f"{field}__icontains": self.q})
            qs = qs.filter(q_obj)

        return qs.order_by('name')

    def get_result_label(self, result):
        return str(result)


def autocomplete_view(model_class, search_fields=None, order_by='name'):
    class _Autocomplete(GenericAutocompleteView):
        model = model_class
        _search_fields = search_fields or ['name']

        def get_queryset(self):
            qs = super().get_queryset()
            return qs.order_by(order_by)

    return _Autocomplete


