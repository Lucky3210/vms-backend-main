from .models import Staff
from django.utils.crypto import get_random_string

staffs = Staff.objects.all()
for staff in staffs:
    if not staff.staffId:
        staff.staffId = get_random_string(length=8)  # Generate a unique ID
        staff.save()
