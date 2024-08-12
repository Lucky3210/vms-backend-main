from .serializers import *
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, status
from .models import *
from django.views.generic import View
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import login, logout, authenticate
from django.utils.timezone import now
from django.contrib.auth.models import AnonymousUser
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

def get_current_time():
        return now().time()


def register_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']
        is_staff = request.POST.get('is_staff', 'off') == 'on'

        user = User.objects.create_user(
            username=username, password=password, email=email)
        user.is_staff = is_staff
        user.save()

        return HttpResponse(f'User {username} registered successfully')

    return render(request, 'register.html')

@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):

    def post(self, request):
        user_id = request.data.get('user_id')
        password = request.data.get('password')
        # print(user_id,password)
        user = authenticate(request, username=user_id, password=password)

        if user is not None:
            token, created = Token.objects.get_or_create(user=user)

            login(request, user)
            # [1500, qwerty]staff
            return Response({
                'status': 'success',
                'message': 'Login Successful',
                'token': token.key,
                'is_staff': user.is_staff,
                'user_id': user_id
            }, status=status.HTTP_200_OK)

        else:
            return Response({"error": "Invalid User ID or Password"}, status=status.HTTP_400_BAD_REQUEST)


# Register/Schedule Visitor
class RegisterVisitorView(generics.CreateAPIView):
    serializer_class = VisitorSerializer
    # only authenticated user(attendant/staff) can register a visitor
    # permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):

        # create new visitor instance
        visitor = serializer.save()

        # Retrieve the department data from the request
        department_name = self.request.data.get('department')

        # Fetch or create the department
        if department_name:
            department = Department.objects.get(departmentName=department_name.upper())
            visitor.department = department
            visitor.save()
        
        # save visitor instance in the VLog db
        # attendant = get_object_or_404(Attendant, user=self.request.user.id) # we use this when the attendant is authenticated
        # attendant = self.request.user
        attendant = self.request.user if not isinstance(self.request.user, AnonymousUser) else None
        # print(attendant)

        # create a new instance of the newly registered visitor and store in the visitorlog db
        VisitorLog.objects.create(
                visitor=visitor,
                staff=visitor.whomToSee,
                attendant=attendant,
                checkInTime=timezone.now(),
            )

        # send visitor's details to the expected staff
        
        firstName, lastName = self.request.data.get('whomToSeeInput').split(maxsplit=1)
        # print(firstName, lastName) 
        # print(visitor.whomToSee)
        try:
            staffMember = Staff.objects.get(firstName=firstName.lower(), lastName=lastName.lower())
            print(staffMember)
        except Staff.DoesNotExist:
            return Response({'error': f'Staff with name "{firstName}, {lastName}" does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        
        VisitRequest.objects.create(
            visitor=visitor,
            staff=staffMember,
            # attendant=attendant,
            status=VisitRequest.PENDING,
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)
                # Send email notification to the staff member
                # subject = 'New Visitor Request'
                # message = f'Hello {staff.name},\n\nYou have a new visitor request.\nVisitor Details:\nName: {visitor.firstName} {visitor.lastName}\nEmail: {visitor.email}\nPhone: {visitor.phoneNumber}\n\nPlease login to your account to approve or decline the request.\n\nBest regards,\nIGCOMSAT'

                # send_mail(subject, message, settings.EMAIL_HOST_USER, [staff.email])


# Render all visitors
class ListVisitorView(generics.ListAPIView):
    serializer_class = VisitorSerializer
    # permission_classes = [IsAuthenticated]

    # queryset to return all the visitors
    # queryset = Visitor.objects.all()
    # def get_queryset(self):
    #     return Visitor.objects.all().select_related('whomToSee', 'department')

    def get_queryset(self):
        # Retrieve the status and staff_id from query parameters
        isApproved = self.request.query_params.get('isApproved')
        checkOut = self.request.query_params.get('checkOut')

        # Filter queryset based on isApproved and checkOut
        queryset = Visitor.objects.all().select_related('whomToSee', 'department')

        if isApproved:
            queryset = queryset.filter(isApproved=isApproved)

        if checkOut:
            queryset = queryset.filter(checkOut=checkOut)
        else:
            queryset = queryset  # Return empty queryset if status is invalid

        return queryset

# APPROVED VISITORS LIST - localhost:8000/api/visitorList?isApproved=True&checkOut=False
# WAITING LIST - localhost:8000/api/visitorList?isApproved=False&checkOut=False
# VISITORS REQUEST - localhost:8000/api/visitRequestList/
# VISITORS REQUEST ON STAFF DASHBOARD - localhost:8000/api/visitRequestList/?staff_id=1600&status=Pending
# ALL VISITORS - localhost:8000/api/visitorLogList (because visitorLog contains visitor timeout)


# Render all staff
class ListStaffView(generics.ListAPIView):
    serializer_class = StaffSerializer
    queryset = Staff.objects.all()
    def get_queryset(self):
        return Staff.objects.all().select_related('department')

# Render all visitors that have been approved and checkout
class ListVisitorLogView(generics.ListAPIView):
    serializer_class = VisitorLogSerializer
    # permission_classes = [IsAuthenticated]

    # queryset to return all the visitors
    queryset = VisitorLog.objects.all().select_related('visitor', 'staff')  # visitorlog instead of visitor


# Accept Visitors Request
class AcceptVisitRequest(APIView):
    # permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        visitRequest = VisitRequest.objects.get(visitor__id=pk)

        # if visitRequest.staff != request.user:
        #     return Response({'error': 'You do not have permission to make this decision.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            visitRequest.status = VisitRequest.APPROVED
            visitRequest.save()

            # feedback = request.data.get('feedback')
            # if feedback:
            #     visitRequest.feedback = feedback
            #     visitRequest.save()

            # update Approval field for visitor
            visitor = visitRequest.visitor
            visitor.isApproved = True
            visitor.save()

            return Response({"message": "Request Approved"}, status=status.HTTP_200_OK)

        except VisitRequest.DoesNotExist:
            return Response({"error": "Request Not found"}, status=status.HTTP_404_NOT_FOUND)
     

# Decline Visitors Request
class DeclineVisitRequest(APIView):
    # permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        visitRequest = VisitRequest.objects.get(visitor__id=pk)

        # if visitRequest.staff != request.user:
        #     return Response({'error': 'You do not have permission to make this decision.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            visitRequest.status = VisitRequest.DECLINED
            visitRequest.save()

            # Update Approval field for visitor
            visitor = visitRequest.visitor
            visitor.isApproved = False
            visitor.save()

            return Response({"message": "Request Declined"}, status=status.HTTP_200_OK)

        except VisitRequest.DoesNotExist:
            return Response({"error": "Request Not found"}, status=status.HTTP_404_NOT_FOUND)


# Check out visitor view from the approval list
class CheckoutVisitorView(APIView):
    def post(self, request, pk):
        visitorLog = get_object_or_404(VisitorLog, visitor__id=pk)
        visitorLog.checkOutTime = timezone.now()
        visitorLog.save()

        # access visitor instance and approve visitor
        visitor = visitorLog.visitor
        visitor.isApproved = False
        visitor.checkOut = True
        visitor.save()

        # Update the status in the VisitRequest to Approved
        try:
            visitRequest = VisitRequest.objects.get(visitor=visitor)
            visitRequest.status = VisitRequest.DISMISSED
            visitRequest.save()
        except VisitRequest.DoesNotExist:
            return Response({'message': 'VisitRequest not found for this visitor'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'message': 'Check out successful'}, status=status.HTTP_200_OK)


# Check in a vistor from the waiting list(automatically approves them and set their status to approved)
class CheckInVisitorView(APIView):
    def post(self, request, pk):
        visitorLog = get_object_or_404(VisitorLog, visitor__id=pk)
        visitorLog.checkInTime = timezone.now()
        visitorLog.save()

        # access visitor instance and approve visitor
        visitor = visitorLog.visitor
        visitor.isApproved = True
        visitor.checkOut = False
        visitor.save()

        # Update the status in the VisitRequest to Approved
        try:
            visitRequest = VisitRequest.objects.get(visitor=visitor)
            visitRequest.status = VisitRequest.APPROVED
            visitRequest.save()
        except VisitRequest.DoesNotExist:
            return Response({'message': 'VisitRequest not found for this visitor'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'message': 'Check in successful'}, status=status.HTTP_200_OK)


# List all visitors pending request for each staff(awaiting approval) - localhost:8000/api/visitRequestList/?staff_id={insertstaffid}&status=Pending
# List all approved visitors for each staff(appointments) - localhost:8000/api/visitRequestList/?staff_id={insertstaffid}&status=Approved&view_type=appointments
# List all staff history - localhost:8000/api/visitRequestList/?staff_id={insertstaffid}&status=Approved&view_type=history
# List all visitors that have been approved and then dismissed(staff visitors history) - localhost:8000/api/visitRequestList/?staff_id={insertstaffid}&status=Dismissed
# Approve a visitor request - http://localhost:8000/api/visitRequest/{insertvisitorid}/accept
# Decline a visitor request - http://localhost:8000/api/visitRequest/{insertvisitorid}/decline
# Dismiss a visitor after appointment - http://localhost:8000/api/dismissVisitor/{insertvisitorid}
# Staff scheduling a visit(staff must be authenticated) - http://127.0.0.1:8000/api/staffVisitRegister


# View for Staff Scheduling a Visit
class StaffVisitRegisterView(generics.CreateAPIView):
    serializer_class = VisitorSerializer
    # only authenticated user(attendant/staff) can register a visitor
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # create new visitor instance
        visitor = serializer.save()

        department_name = self.request.data.get('department')
        # Fetch the department
        if department_name:
            department = Department.objects.get(departmentName=department_name.upper())
            visitor.department = department
            visitor.save()

        # set isApproved to true
        visitor.isApproved = True
        visitor.save()

        # save visitor instance in the VLog db
        staff = self.request.user # uncomment in production

        # create a new instance of the newly registered visitor and store in the visitorlog db
        VisitorLog.objects.create(
            visitor=visitor,
            staff=staff,
            checkInTime=timezone.now(),
        )


# List all Staff Schedules
class StaffScheduleListView(generics.ListAPIView):
    queryset = VisitorLog.objects.all()
    serializer_class = VisitorLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filter visitor logs by staff member
        return self.queryset.filter(staff=self.request.user)


# render request for a specific staff(pending, approved, declined)
class VisitRequestStatusView(generics.ListAPIView):
    serializer_class = VisitRequestSerializer

    def get_queryset(self):
        # Retrieve the status and staff_id from query parameters
        status = self.request.query_params.get('status', 'pending') # pending because it's the default
        staff_id = self.request.query_params.get('staff_id')
        view_type = self.request.query_params.get('view_type', '').lower()

        # Filter queryset based on status and staff_id
        queryset = VisitRequest.objects.all()

        if staff_id:
            queryset = queryset.filter(staff__staffId=staff_id)

        if status.lower() in ['pending', 'approved', 'declined', 'dismissed']:
            queryset = queryset.filter(status=status.capitalize())
        else:
            queryset = queryset.none()  # Return empty queryset if status is invalid

        # Handle the view type for appointments and history
        today = timezone.now().date()
        if view_type == 'appointments':
            queryset = queryset.filter(visitor__visitDate__gte=today)
        elif view_type == 'history':
            queryset = queryset.filter(visitor__visitDate__lt=today)
        return queryset


# render all visit request, both approved and pending
class AllVisitRequest(generics.ListAPIView):
    serializer_class = VisitRequestSerializer
    queryset = VisitRequest.objects.all()


# view for staff to dismiss a visitor when they're done with appointment(render them in history)
class DismissVisitorView(APIView):
    def post(self, request, pk):
        visitRequest = VisitRequest.objects.get(visitor__id=pk)

        try:
            visitRequest.status = VisitRequest.DISMISSED
            visitRequest.save()

            return Response({"message": "Visitor Dismissed"}, status=status.HTTP_200_OK)

        except VisitRequest.DoesNotExist:
            return Response({"error": "Request Not found"}, status=status.HTTP_404_NOT_FOUND)
   


# # render visit request of a particular staff(All pending request)
# class ListVisitRequestView(generics.ListAPIView):
#     # permission_classes = [IsAuthenticated]
#     serializer_class = VisitRequestSerializer

#     def get_queryset(self):
#         # Retrieve the staff ID from the URL query parameters or request data
#         staff_id = self.request.query_params.get('staff_id')
#         if staff_id is not None:
#             queryset = VisitRequest.objects.filter(staff__staffId=staff_id, status="Pending").select_related('visitor', 'staff')

#         else:
#             queryset = VisitRequest.objects.all()

#         return queryset

# # render staff-scheduled visit/appointment (Visitors that have been approved)
# class StaffApprovedVisitorView(generics.ListAPIView):
#     # permission_classes = [IsAuthenticated]
#     serializer_class = VisitRequestSerializer

#     def get_queryset(self):
#         # Retrieve the staff ID from the URL query parameters or request data
#         staff_id = self.request.query_params.get('staff_id')
#         if staff_id is not None:
#             queryset = VisitRequest.objects.filter(staff__staffId=staff_id, status="Approved").select_related('visitor', 'staff')

#         else:
#             queryset = VisitRequest.objects.all()

#         return queryset
    

# Staff Reschedule Visit
class StaffRescheduleVisit(generics.UpdateAPIView):
    pass


class LogoutView(APIView):
    # Ensure only authenticated users can access this view
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Logout the user
        logout(request)

        # Return a successful response
        return Response({'success': True, 'message': 'Logged out successfully'}, status=200)

# class LoginView(APIView):
#     def post(self, request):
#         serializer = UserSerializer(data=request.data)

#         if serializer.is_valid():
#             # Authenticate the user
#             user_id = serializer.validated_data.get('user_id')
#             password = serializer.validated_data.get('password')

#             user = authenticate(request, user_id=user_id, password=password)

#             if user:
#                 # Handle successful authentication (e.g., return a success response)
#                 return Response({'status': 'success', 'message': 'Login successful'}, status=status.HTTP_200_OK)
#             else:
#                 # Handle invalid credentials
#                 return Response({'status': 'error', 'message': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

#         # Handle invalid request data
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
