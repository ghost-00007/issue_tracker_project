# urls.py
from django.urls import path
from .views import (UserRegistrationView,
                    UserLoginView,
                    ProjectCreateView,
                    EmployeeListView,
                    ProjectListView,
                    add_issue,
                    IssueListView,
                    TaskAssignView,
                    ResolutionView,
                    delete_issue,
                    get_project_status_report,
                    update_issue_status,
                    FliterIssueDetailsView,
                    IssueExportView, 
                    ForgotPasswordView, 
                    PasswordResetConfirmView, 
                    ProjectStatusReportView, 
                    ProjectList,
                    SearchProjectAPIView,
                    ProjectUpdateDeleteView,
                    ProjectFilterView,
                    v1_ForgotPasswordView
                    
                                             )
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [

    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('api/signup/', UserRegistrationView.as_view(), name='signup'),
    path('api/login/', UserLoginView.as_view(), name='login'),
    path('api/projects/', ProjectCreateView.as_view(), name='create-project'),
    path('api/employees/', EmployeeListView.as_view(), name='employee-list'),
    path('api/projects_list/<str:user_id>/',
         ProjectListView.as_view(), name='project-list'),
    path('api/projects_list/<int:project_id>/delete/', ProjectListView.as_view(),
         name='project-delete'),  # For deleting a project
    path('api/add_issue/', add_issue, name='add_issue'),
    path('api/view_issues/<str:userId>/',
         IssueListView.as_view(), name='issue-list'),
    path('api/view_issues/<int:pk>/delete/',
         delete_issue, name='delete_issue'),
    path('api/assign_task/', TaskAssignView.as_view(), name='assign-task'),
    path('api/resolutions/', ResolutionView.as_view(), name='resolutions'),
    path('api/get_project_status_report/<str:userId>/',
         get_project_status_report, name='resolutions'),
    path('api/update_issue_status/<int:issue_id>/',
         update_issue_status, name='update_issue_status'),

    # updated URLS
    path('api/fliterissuedetails/<int:project_id>/',
         FliterIssueDetailsView.as_view(), name='issue-filter'),
    path('api/issueexportview/', IssueExportView.as_view(), name='Issue-Export'),
    path('api/forgotpasswordview/',
         v1_ForgotPasswordView.as_view(), name='Forgot-Password'),
    path('api/passwordresetconfirm/<str:uid>/<str:token>/',
         PasswordResetConfirmView.as_view(), name='Password-Reset-Confirm'),
    path('api/overallproject/', ProjectStatusReportView.as_view(),
         name='OverALL-Project-StatusReport'),
    path('api/projectlist/', ProjectList.as_view(), name='Project-List'),
    path('api/search/', SearchProjectAPIView.as_view(), name='Search'),

     path('api/project/<int:pk>/', ProjectUpdateDeleteView.as_view(), name='project-update-delete'),
     path('api/project_filter/', ProjectFilterView.as_view(), name='project-filter'),

]
