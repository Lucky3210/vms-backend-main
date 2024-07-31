from django.urls import path
from .views import *


urlpatterns = [
    path('api/login', LoginView.as_view(), name='login'),
    path('api/logout', LogoutView.as_view(), name='logout'),
    path('api/registerVisitor', RegisterVisitorView.as_view(),
         name='registerVisitor'),
    path('api/visitorList', ListVisitorView.as_view(), name='visitorList'),
    path('api/visitorLogList', ListVisitorLogView.as_view(), name='visitorLog'),
    path('api/visitRequest/<int:pk>/accept',
         AcceptVisitRequest.as_view(), name='acceptVisitorReq'),
    path('api/visitRequest/<int:pk>/decline',
         DeclineVisitRequest.as_view(), name='declineVisitorReq'),
     path('api/dismissVisitor/<int:pk>',
         DismissVisitorView.as_view(), name='dismissVisitor'),
    path('api/checkout/<int:pk>',
         CheckoutVisitorView.as_view(), name='visitorCheckout'),
    path('api/checkin/<int:pk>', CheckInVisitorView.as_view(), name='visitorCheckin'),
    path('api/staffVisitRegister', StaffVisitRegisterView.as_view(),
         name='staffVisitRegister'),
    path('api/staffVisit', StaffScheduleListView.as_view(), name='StaffVisitList'),
    path('api/staffList', ListStaffView.as_view(), name='StaffList'),
#     path('api/staffSchedules', StaffApprovedVisitorView.as_view(), name="staffScheduleList"),
    path('api/visitRequestList/', VisitRequestStatusView.as_view(), name="ListVisitRequest"),
    path('api/allrequest', AllVisitRequest.as_view(), name="AllVisitReq")
#     http://localhost:8000/api/visitRequestList/?staff_id=1600


]

"""
    {
        "firstName": "Havy",
        "lastName": "Lil",
        "email": "lilhavy@lili.com",
        "phoneNumber": "+2349096112330",
        "organization": "Lil Express",
        "department": "",
        "isApproved": false,
        "whomToSeeInput":"Ken Lam",
        "numberOfGuest": 1,
        "reason": "Official",
        "registrationTime": "12:31:48",
        "registrationDate": "2024-06-24"
    }
 """