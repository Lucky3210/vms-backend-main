from django.contrib import admin
from .models import GenericUser, Staff, Visitor, VisitorLog, Attendant, VisitRequest, Department

# Register your models here.

admin.site.register(GenericUser)
admin.site.register(Department)
admin.site.register(Staff)
admin.site.register(Attendant)
admin.site.register(Visitor)
admin.site.register(VisitorLog)
admin.site.register(VisitRequest)