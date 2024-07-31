from rest_framework import serializers
from vms.models import Visitor, VisitorLog, VisitRequest, Staff, Department
# from phonenumber_field.serializerfields import PhoneNumberField

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['departmentName']


class StaffSerializer(serializers.ModelSerializer):
    # phoneNumber = PhoneNumberField()
    department = DepartmentSerializer(read_only=True)
    class Meta:
        model = Staff
        fields = ['staffId', 'firstName', 'lastName', 'email', 'department', 'phoneNumber']


class VisitorSerializer(serializers.ModelSerializer):
    # phoneNumber = PhoneNumberField()
    whomToSee = StaffSerializer(read_only=True)
    whomToSeeInput = serializers.CharField(write_only=True)
    department = DepartmentSerializer(read_only=True)

    class Meta:
        model = Visitor
        fields = ['id', 'firstName', 'lastName', 'email', 'phoneNumber', 'organization', 'department', 'isApproved',  'checkOut', 'whomToSee', 'whomToSeeInput', 'numberOfGuest', 'reason', 'visitDate', 'visitTime', 'registrationTime', 'registrationDate']


    def validate(self, data):
        if 'whomToSeeInput' in data:
            staff = data['whomToSeeInput']
            # print(staff)
            if staff.firstName:
                staff.firstName = staff.firstName.lower()
                
            if staff.lastName:
                staff.lastName = staff.lastName.lower()
            
            staff.save()
        return data

    # def get_whomToSee(self, obj):
    #     # obj is an instance of Visitor
    #     staff = obj.whomToSeeInput
    #     print(staff)
    #     return StaffSerializer(staff).data

    def validate_whomToSeeInput(self, value):
        try:
            firstName, lastName = value.split(' ')
            
        except ValueError:
            raise serializers.ValidationError("whomToSeeInput field should contain both first name and last name separated by a space.")
        
        try:
            staff = Staff.objects.get(firstName__iexact=firstName, lastName__iexact=lastName)
           
        except Staff.DoesNotExist:
            raise serializers.ValidationError("Staff member with the provided first name and last name does not exist.")
        
        return staff
       

    def create(self, validated_data):
        # Remove the input field after validation and set the whomToSee field
        
        validated_data['whomToSee'] = validated_data.pop('whomToSeeInput')
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'whomToSeeInput' in validated_data:
            instance.whomToSee = validated_data.pop('whomToSeeInput')
        return super().update(instance, validated_data)


class VisitorLogSerializer(serializers.ModelSerializer):
    visitor = VisitorSerializer(read_only=True)
    staff = StaffSerializer(read_only=True)
    class Meta:
        model = VisitorLog
        fields = ['id', 'visitor', 'staff', 'checkInTime', 'checkOutTime']

class VisitRequestSerializer(serializers.ModelSerializer):
    visitor = VisitorSerializer(read_only=True)
    staff = StaffSerializer(read_only=True)
    class Meta:
        model = VisitRequest
        fields = ['visitor', 'staff', 'request_time', 'status']


