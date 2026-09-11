from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse
from django.http import Http404

class GenericFormView(TemplateView):
    template_name = "base/generic_form.html"
    model = None
    form_class = None
    mode = 'detail'  # 'add', 'edit', or 'detail'
    success_url = None
    pk_url_kwarg = 'pk'

    def get_object(self):
        if self.mode == 'add':
            return None
        pk = self.kwargs.get(self.pk_url_kwarg)
        if not pk:
            raise Http404("Object not found")
        return get_object_or_404(self.model, pk=pk)

    def get_form(self):
        if self.request.method == 'POST':
            return self.form_class(self.request.POST, instance=self.get_object())
        return self.form_class(instance=self.get_object())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()

        context.update({
            'mode': self.mode,
            'form': self.get_form() if self.mode != 'detail' else self.form_class(instance=obj, disabled=True),
            'object': obj,
            'page_title': self.page_title,
            'card_title': self.card_title,
            'fieldsets': self.fieldsets,
        })
        return context

    def post(self, request, *args, **kwargs):
        if self.mode == 'detail':
            raise Http404("Detail view does not accept POST")

        form = self.get_form()
        if form.is_valid():
            instance = form.save()
            messages.success(request, "Saved successfully.")
            return redirect(self.success_url or reverse('home'))
        else:
            return self.render_to_response(self.get_context_data(form=form))
