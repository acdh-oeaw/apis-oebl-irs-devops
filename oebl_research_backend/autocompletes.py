from dal import autocomplete
from .models import ProfessionGroup

class ProfessionGroupAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = ProfessionGroup.objects.all()
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs
