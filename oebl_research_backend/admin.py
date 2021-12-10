from django.contrib import admin

from .models import List, ListEntry, IRSPerson

admin.site.register(List)
admin.site.register(ListEntry)
admin.site.register(IRSPerson)