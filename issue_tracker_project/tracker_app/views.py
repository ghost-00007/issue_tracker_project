# views.py
from rest_framework import status,generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from .models import CustomUser,Project,Issue,TaskAssignment,Resolution
from .serializers import UserRegistrationSerializer, UserLoginSerializer,ProjectSerializer,CustomUserSerializer,IssueSerializer,TaskAssignmentSerializer,ResolutionSerializer
from django.shortcuts import render
from django.db import IntegrityError
from rest_framework.permissions import AllowAny
from django.contrib.auth import login
from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import IsAuthenticated  # Optional: Use for authentication
from rest_framework.exceptions import NotFound
from django.http import HttpResponse
from openpyxl import Workbook
from io import BytesIO
import os
from django.conf import settings
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
User = get_user_model()
from django.core.mail import EmailMessage


import logging
from django.conf import settings

# Create your views here.
logger = logging.getLogger(__name__)  # Initialize logger




# API for User Signup
class UserRegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            login(request, user)

            # Generate or retrieve token
            token, created = Token.objects.get_or_create(user=user)

            # Assuming the user has designation, employee_name, and employee_code fields or related data
            # Modify the access to match your actual model structure
            designation = getattr(user, 'designation', None)
            employee_name = getattr(user, 'employee_name', None)
            employee_code = getattr(user, 'employee_code', None)

            response_data = {
                "message": "Login successful",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "designation": designation,
                    "employee_name": employee_name,
                    "employee_code": employee_code,
                },
                "token": token.key  # Include the token in the response
            }
            # print("----response_data----",response_data)
            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Create project view
class ProjectCreateView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    def create(self, request, *args, **kwargs):
        project_data = request.data
        # Create the project
        project = Project.objects.create(
            project_code=project_data['project_code'],
            project_name=project_data['project_name'],
            project_manager=CustomUser.objects.get(id=project_data['project_manager'])
        )
        # Add development team members
        dev_team_ids = project_data.get('development_team', [])
        for user_id in dev_team_ids:
            try:
                user = CustomUser.objects.get(id=int(user_id))  # Convert to int if needed
                project.development_team.add(user)
            except CustomUser.DoesNotExist:
                return Response(
                    {"error": f"Developer with ID {user_id} does not exist."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Add testing team members
        test_team_ids = project_data.get('testing_team', [])
        for user_id in test_team_ids:
            try:
                user = CustomUser.objects.get(id=int(user_id))  # Convert to int if needed
                project.testing_team.add(user)
            except CustomUser.DoesNotExist:
                return Response(
                    {"error": f"Tester with ID {user_id} does not exist."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        project.save()
        return Response(ProjectSerializer(project).data, status=status.HTTP_201_CREATED)


# Get employee list
class EmployeeListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer


class ProjectListView(APIView):
    permission_classes = [AllowAny]  # Modify as necessary

    # def get(self, request, user_id, format=None):
        # Fetch projects based on userId
        # projects = Project.objects.filter(project_manager_id=user_id)
        # # Use the serializer to convert queryset to JSON
        # serializer = ProjectSerializer(projects, many=True)
        # return Response(serializer.data, status=status.HTTP_200_OK)
    def get(self, request, user_id, format=None):

        try:
            user = CustomUser.objects.get(id=user_id)

            designation = user.designation  # Assuming 'designation' is a field in the User model
            if designation == 'Testing':
                projects = Project.objects.filter(testing_team=user).order_by('-id')
                if projects.exists():
                    # Serialize the projects
                    serializer = ProjectSerializer(projects, many=True)
                    return Response(serializer.data, status=status.HTTP_200_OK)
                else:
                    return Response({"error": "No projects found for this user in the testing team"}, status=status.HTTP_404_NOT_FOUND)
                # print("---user_id----",user_id)
                # projects = Project.objects.all()
                # print("---projects----",projects)
                # # Use the serializer to convert queryset to JSON
                # serializer = ProjectSerializer(projects, many=True)
                # return Response(serializer.data, status=status.HTTP_200_OK)
                # testing_team_projects = Project.objects.filter(testing_team=user)
                # print("------testing_team_projects-------",testing_team_projects)
                # # Get only user ids in the testing team of the project
                # testing_team_user_ids = testing_team_projects.values_list('testing_team__id', flat=True)
                # print("-testing_team_user_ids=--",testing_team_user_ids)
                # You will have a list of user IDs that belong to the testing team
                # return Response({'testing_team_user_ids': list(testing_team_user_ids)}, status=status.HTTP_200_OK)
                # return Response(status=status.HTTP_200_OK)
                # Filter projects where the user is part of the testing team
                # testing_team_projects = TestingTeam.objects.filter(customuser_id=user_id).values_list('project_id', flat=True)
                # print("----testing_team_projects----",testing_team_projects)
                # # Fetch the project details
                # projects = Project.objects.filter(id__in=testing_team_projects)
                # print("---projects----",projects)
                # # Serialize the projects
                # serializer = ProjectSerializer(projects, many=True)
                # return Response(serializer.data, status=status.HTTP_200_OK)
                 # Fetch the project by project_id
                # project = Project.objects.get(id=project_id)

                # # Get all members in the testing_team ManyToMany field
                # testing_team = project.testing_team.all()

                # # Serialize the testing_team members
                # serializer = CustomUserSerializer(testing_team, many=True)

                # return Response(serializer.data, status=status.HTTP_200_OK)
            
            elif designation == 'Project Manager':
                    projects = Project.objects.filter(project_manager_id=user_id).order_by('-id')
                    # Use the serializer to convert queryset to JSON
                    serializer = ProjectSerializer(projects, many=True)
                    return Response(serializer.data, status=status.HTTP_200_OK)
            # # Check if the user is a Project Manager
            # manager_projects = Project.objects.filter(project_manager_id=user_id)

            # # Check if the user is part of the Testing Team
            # testing_team_projects_ids = TestingTeam.objects.filter(customuser_id=user_id).values_list('project_id', flat=True)

            # # Get projects managed by the user or in the testing team
            # all_projects = Project.objects.filter(
            #     Q(id__in=testing_team_projects_ids) | Q(project_manager_id=user_id)
            # ).distinct()

            # # Use the serializer to convert queryset to JSON
            # serializer = ProjectSerializer(all_projects, many=True)
            # return Response(serializer.data, status=status.HTTP_200_OK)

        except Project.DoesNotExist:
            return Response({"error": "No projects found for this user"}, status=status.HTTP_404_NOT_FOUND)
    

    def delete(self, request, project_id, format=None):
        try:
            # Fetch the project by project_id
            project = Project.objects.get(id=project_id)
            # Delete the project
            project.delete()
            return Response({"message": "Project deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Project.DoesNotExist:
            return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
# @permission_classes([AllowAny])  
def add_issue(request):
    permission_classes = [AllowAny]
    serializer = IssueSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def delete_issue(request, pk):
    try:
        print("---pk",pk)
        issue = Issue.objects.get(pk=pk)
    except Issue.DoesNotExist:
        return Response({"error": "Issue not found"}, status=status.HTTP_404_NOT_FOUND)
    issue.delete()
    return Response({"message": "Issue deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


# class IssueListView(APIView):
#     def get(self, request):
#         issues = Issue.objects.all()  # Fetch all issues
#         serializer = IssueSerializer(issues, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)
    
# class IssueListView(APIView):
#     permission_classes = [IsAuthenticated]  # Ensure the user is authenticated
    
#     def get(self, request):
#         # Fetch issues assigned only to the logged-in user
#         user = request.user  # Get the authenticated user
#         print("--user--",user)
#         task_assignments = TaskAssignment.objects.filter(employee=user)  # Filter issues based on the assigned employee (user)
#         print("--task_assignments--",task_assignments)
#         serializer = TaskAssignmentSerializer(task_assignments, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)

class IssueListView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure the user is authenticated
    # permission_classes = [AllowAny]  # Ensure the user is authenticated

    def get(self, request, userId):
        try:
            # Get the user object and its designation (e.g., "Project Manager" or "Developer")
            user = CustomUser.objects.get(id=userId)
            designation = user.designation  # Assuming 'designation' is a field in the User model

            if designation == 'Project Manager':
                  
                  projects = Project.objects.filter(project_manager_id=user.id).order_by('-id')

        
                  if not projects.exists():
                        return Response({"error": "No projects found for this manager"}, status=status.HTTP_404_NOT_FOUND)

                     # Get the project IDs where the current user is the project manager
                  project_ids = projects.values_list('id', flat=True)

                    # Find all issues where the project_id is in the list of projects
                  issues = Issue.objects.filter(project_id__in=project_ids).order_by('-id')
                    
                    # Serialize the issues
                  issue_serializer = IssueSerializer(issues, many=True)
                    
                    # Return the serialized issues
                  return Response(issue_serializer.data, status=status.HTTP_200_OK)     

            elif designation == 'Developer':
                # If the user is a Developer, return only their assigned issues
                task_assignments = TaskAssignment.objects.filter(employee_id=userId)
                issue_ids = task_assignments.values_list('issue_id', flat=True)
                issues = Issue.objects.filter(id__in=issue_ids).exclude(status="Developed").distinct().order_by('-id')
                issue_serializer = IssueSerializer(issues, many=True)
                return Response(issue_serializer.data, status=status.HTTP_200_OK)
            
            elif designation == 'Testing':
                 # Get projects where the user is part of the testing team
                projects = Project.objects.filter(testing_team=user)

                if projects.exists():
              
                    project_ids = projects.values_list('id', flat=True)
                    # Filter issues by the project IDs
                    # issues = Issue.objects.filter(project_id__in=project_ids)
                    issues = Issue.objects.filter(
                    project_id__in=project_ids,
                    # status__in=["Open", "Developed"]  # Filter by status
                        )
                    print("-----project_ids------",project_ids)
                    print("-----issues------",issues)
                    # print("-----issues------",issues)
                    # Get resolution data for those issues
                    resolutions = Resolution.objects.filter(issue__in=issues)
                    print("-----resolutions------",resolutions)
                    # Serialize issues and resolutions
                    issue_serializer = IssueSerializer(issues, many=True)
                    resolution_serializer = ResolutionSerializer(resolutions, many=True)

                    # Combine the serialized data into one response
                    response_data = {
                        "issues": issue_serializer.data,
                        "resolutions": resolution_serializer.data
                    }
                    
                    return Response(response_data, status=status.HTTP_200_OK)
                else:
                    return Response({"error": "No projects found for this user in the testing team"}, status=status.HTTP_404_NOT_FOUND)

            else:
                return Response({"error": "User role not recognized"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(f"Error: {e}")
            return Response({"error": "Something went wrong"}, status=status.HTTP_400_BAD_REQUEST)


class TaskAssignView(APIView):
    # permission_classes = [AllowAny]
    def post(self, request):
        # Retrieve data from the request body
        issue_code = request.data.get('issue_code')
        issue_title = request.data.get('issue_title')
        employee_code = request.data.get('employee_code')
        employee_name = request.data.get('employee_name')
        print("----------", issue_code, issue_title, employee_code, employee_name)

        try:
            # Fetch the issue object based on issue_code and issue_title
            issue = Issue.objects.get(issue_code=issue_code, issue_title=issue_title)
            
            # Fetch the employee object based on employee_code and employee_name
            employee = CustomUser.objects.get(employee_code=employee_code, employee_name=employee_name)
            
            # Create a TaskAssignment instance with the retrieved issue and employee
            task_assignment = TaskAssignment.objects.create(issue=issue, employee=employee)
            
            # Update the status of the issue to 'Assigned'
            issue.status = 'Assigned'  # Change 'Assigned' to the appropriate status you want
            
            # Set the employee_name field in the Issue model
            issue.employee_name = employee.employee_name  # Update employee_name field with the employee's name
            
            # Save the updated issue with the assigned employee's name
            issue.save()

            # Serialize the TaskAssignment instance to display issue_code, employee_code, and assigned_at
            serializer = TaskAssignmentSerializer(task_assignment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Issue.DoesNotExist:
            return Response({'error': 'Issue with the given code and title not found'}, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            return Response({'error': 'Employee with the given code and name not found'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        # Fetch all task assignments
        task_assignments = TaskAssignment.objects.all().order_by('-id')
        serializer = TaskAssignmentSerializer(task_assignments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    

class ResolutionView(APIView):
    def post(self, request):
        # Fetch issue_code and description from the request body
        issue_code = request.data.get('issue_code')
        description = request.data.get('description')

        try:
            # Fetch the Issue object by its issue_code
            issue = Issue.objects.get(issue_code=issue_code)

            # Create the Resolution instance
            resolution = Resolution.objects.create(issue=issue, description=description)

            # Update the status of the issue to 'Developed'
            issue.status = 'Developed'  # Set the status to the desired value, e.g., 'Developed'
            issue.save()  # Save the updated status of the issue

            # Serialize the Resolution instance
            serializer = ResolutionSerializer(resolution)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Issue.DoesNotExist:
            return Response({'error': 'Issue not found'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

@api_view(['GET'])
def get_project_status_report(request, userId):
    try:
        # Get the user (assuming project manager ID matches the logged-in user)
        user = CustomUser.objects.get(id=userId)
        
        # Retrieve all projects managed by the user
        projects = Project.objects.filter(project_manager_id=user).order_by('-id')
        
        if not projects.exists():
            return Response({"message": "No projects found for this user."}, status=404)
        
        # Prepare the project status report data
        report_data = []
        
        for project in projects:
            # Get issues related to this project
            issues = Issue.objects.filter(project_name=project.project_name)  # or project_id
            
            # Calculate the status counts
            open_issues = issues.filter(status="Open").count()
            assigned_issues = issues.filter(status="Assigned").count()
            developed_issues = issues.filter(status="Developed").count()
            # closed_issues = issues.filter(status="Closed").count() 
            retested_issues = issues.filter(status="Re-Tested").count()
            completed_issues = issues.filter(status="Completed").count()
            
            # Append the data to the report
            report_data.append({
                "project_name": project.project_name,
                "open": open_issues,
                "assigned": assigned_issues,
                "developed": developed_issues,
                "retested": retested_issues,
                # "closed": closed_issues,
                "completed": completed_issues,
                "total": issues.count()
            })
        return Response(report_data, status=200)
    
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['POST'])
def update_issue_status(request, issue_id):
    try:
        # Get the issue by its ID
        issue = Issue.objects.get(id=issue_id)
        
        # Get the new status from the request data
        new_status = request.data.get('status')
        
        # Validate if the status is either "Completed" or "Re-Tested"
        if new_status not in ["Completed", "Re-Tested"]:
            return Response({"error": "Invalid status provided."}, status=status.HTTP_400_BAD_REQUEST)

        # Update the issue status
        issue.status = new_status
        issue.save()

        return Response({"message": "Issue status updated successfully."}, status=status.HTTP_200_OK)
    except Issue.DoesNotExist:
        return Response({"error": "Issue not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

############## update contents ####################



class FliterIssueDetailsView(APIView):
    # permission_classes = [AllowAny]
    def get(self, request, project_id):
        try:
            issues = Issue.objects.filter(project_id=project_id)
            if not issues.exists():
                raise NotFound(detail="No issues found for the given project.")
            serializer = IssueSerializer(issues, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        


class IssueExportView(APIView):
    # permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        try:
            if not os.path.exists(settings.MEDIA_ROOT):
                os.makedirs(settings.MEDIA_ROOT)

            # Create a workbook and worksheet
            wb = Workbook()
            ws = wb.active
            ws.title = "Issues"

            
            headers = ['Issue Code', 'Issue Title', 'Priority', 'Testcase Code', 'Employee Name', 'Status', 'Description', 'Project']
            ws.append(headers)

            issues = Issue.objects.all()
            for issue in issues:
                row = [
                    issue.issue_code,
                    issue.issue_title,
                    issue.issue_priority,
                    issue.testcase_code,
                    issue.employee_name,
                    issue.status,
                    issue.description,
                    issue.project_name,
                ]
                ws.append(row)

            file_path = os.path.join(settings.MEDIA_ROOT, "issues.xlsx")

            
            wb.save(file_path)

            
            file_url = request.build_absolute_uri(settings.MEDIA_URL + "issues.xlsx")
            return Response({
                "status": "success",
                "message": "Excel file generated successfully",
                "data": {
                    "file_url": file_url
                }
            })
        except Exception as e:
            return Response({
                "status": "error",
                "message": f"An error occurred: {str(e)}",
                "data": {}
            })



class v1_ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        print(f"Received password reset request for email: {email}")
        logger.info(f"Received password reset request for email: {email}")

        if not email:
            msg = "Email is required."
            print(msg)
            logger.warning(msg)
            return Response({"error": msg}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(email=email)
            print(f"User found: {user}")
            logger.info(f"User found: {user}")
        except CustomUser.DoesNotExist:
            msg = "User with this email does not exist."
            print(msg)
            logger.error(msg)
            return Response({"error": msg}, status=status.HTTP_404_NOT_FOUND)

        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_link = f"https://issuetracker.keelis.in/reset/{uid}/{token}/"

        print(f"Generated reset link: {reset_link}")
        logger.info(f"Generated reset link for user {user.email}")

        subject = "Password Reset Request"
        html_message = render_to_string(
            "IssueEmail_HTML/reset_password.html",
            {
                "user": user,
                "reset_link": reset_link,
                "click_link": "Click here to reset your password"
            },
        )

        try:
            email_message = EmailMessage(
                subject=subject,
                body=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email],
            )
            email_message.content_subtype = "html"
            email_message.send()
            print(f"Reset email sent to {email}")
            logger.info(f"Reset email sent to {email}")
        except Exception as e:
            error_msg = "Failed to send email. Please try again later."
            print(f"{error_msg} Exception: {str(e)}")
            logger.error(f"{error_msg} Exception: {str(e)}")
            return Response({"error": error_msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        success_msg = "Password reset link sent to your email."
        print(success_msg)
        logger.info(success_msg)
        return Response({"message": success_msg}, status=status.HTTP_200_OK)
class PasswordResetConfirmView(APIView):
    def post(self, request, *args, **kwargs):
        uid = kwargs.get("uid")
        token = kwargs.get("token")

        try:
            user_id = urlsafe_base64_decode(uid).decode()
            user = User.objects.get(pk=user_id)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return Response(
                {"error": "Invalid user ID."}, status=status.HTTP_400_BAD_REQUEST
            )

        token_generator = PasswordResetTokenGenerator()
        if not token_generator.check_token(user, token):
            return Response(
                {"error": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_password = request.data.get("new_password")
        if not new_password:
            return Response(
                {"error": "New password is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)  # This will hash the password automatically
        user.save()

        return Response(
            {"message": "Password has been reset successfully."},
            status=status.HTTP_200_OK,
        )


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")

        if not email:
            return Response(
                {"error": "Email is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = CustomUser.objects.get(email=email) 
        except CustomUser.DoesNotExist:
            return Response(
                {"error": "User with this email does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_link = f''' http://94.136.187.221:2007/reset/{uid}/{token}/'''

        subject = "Password Reset Request"
        html_message = render_to_string(
            "IssueEmail_HTML/reset_password.html",
            {
                "user": user,
                "reset_link": reset_link,
                "click_link": "Click here to reset your password"
            },
        )
        plain_message = strip_tags(html_message)

        try:
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                html_message=html_message,
                fail_silently=False,
            )
        except Exception as e:
            return Response(
                {"error": "Failed to send email. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"message": "Password reset link sent to your email."},
            status=status.HTTP_200_OK,
        )
class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        uid = kwargs.get("uid")
        token = kwargs.get("token")

        try:
            user_id = urlsafe_base64_decode(uid).decode()
            user = User.objects.get(pk=user_id)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return Response(
                {"error": "Invalid user ID."}, status=status.HTTP_400_BAD_REQUEST
            )

        token_generator = PasswordResetTokenGenerator()
        if not token_generator.check_token(user, token):
            return Response(
                {"error": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_password = request.data.get("new_password")
        if not new_password:
            return Response(
                {"error": "New password is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)  # This will hash the password automatically
        user.save()

        return Response(
            {"message": "Password has been reset successfully."},
            status=status.HTTP_200_OK,
        )


class ProjectStatusReportView(APIView):
    # permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        try:
            # Retrieve all projects
            projects = Project.objects.all().order_by('-id')
            
            if not projects.exists():
                return Response({"message": "No projects found."}, status=status.HTTP_404_NOT_FOUND)
            
            # Initialize report data
            report_data = []

            # Iterate through all projects and calculate issue status counts
            for project in projects:
                # Get all issues associated with the current project
                issues = Issue.objects.filter(project_name=project.project_name)

                # Calculate counts for each status
                open_issues = issues.filter(status="Open").count()
                assigned_issues = issues.filter(status="Assigned").count()
                developed_issues = issues.filter(status="Developed").count()
                retested_issues = issues.filter(status="Re-Tested").count()
                completed_issues = issues.filter(status="Completed").count()
                total_issues = issues.count()

                # Append project data to the report
                report_data.append({
                    "project_name": project.project_name,
                    "open": open_issues,
                    "assigned": assigned_issues,
                    "developed": developed_issues,
                    "retested": retested_issues,
                    "completed": completed_issues,
                    "total": total_issues,
                })

            # Return the aggregated report data
            return Response(report_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class ProjectList(APIView):
    # permission_classes = [AllowAny]

    def get(self, request):
        try:
            projects = Project.objects.all().order_by('-id')
            serializer = ProjectSerializer(projects, many=True)
            return Response(
                 serializer.data,status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {
                    "status": False,
                    "message": "An error occurred while fetching the project list",
                    "data": None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class SearchProjectAPIView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        query = request.query_params.get('q', None)
        
        if query:
            results = Project.objects.filter(project_name__icontains=query)
            if results.exists():
                serializer = ProjectSerializer(results, many=True)
                return Response({
                    "message": "Data found",
                    "projects": serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "message": "No data found"
                }, status=status.HTTP_404_NOT_FOUND)
        results = Project.objects.all()
        if results.exists():
            serializer = ProjectSerializer(results, many=True)
            return Response({
                "message": "Data found",
                "projects": serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "message": "No data found"
            }, status=status.HTTP_404_NOT_FOUND)
        





# filter
class ProjectFilterView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset(request)
            serializer = ProjectSerializer(queryset, many=True)
            return Response({
                "status": True,
                "message": "Project list fetched successfully.",
                "error": False,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "status": False,
                "message": "Failed to fetch project list.",
                "error": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_queryset(self, request):
        queryset = Project.objects.all()

        # Query parameters
        project_name = request.GET.get('project_name')
        project_version = request.GET.get('project_version')
        date_filter = request.GET.get('date_filter')  # 'current' or 'recent'

        # Filter by project name
        if project_name:
            queryset = queryset.filter(project_name__icontains=project_name)

        # Filter by project version
        if project_version:
            queryset = queryset.filter(project_version__iexact=project_version)

        # Optional ordering
        if date_filter == 'current':
            queryset = queryset.order_by('created_at')  # Ascending
        else:
            queryset = queryset.order_by('-created_at')  # Default: Descending

        return queryset
    


class ProjectUpdateDeleteView(APIView):

    def put(self, request, pk, *args, **kwargs):
        try:
            project = Project.objects.get(pk=pk)
            data = request.data

            project.project_code = data.get('project_code', project.project_code)
            project.project_name = data.get('project_name', project.project_name)
            
            # Update project manager
            if 'project_manager' in data:
                try:
                    manager = CustomUser.objects.get(id=data['project_manager'])
                    project.project_manager = manager
                except CustomUser.DoesNotExist:
                    return Response(
                        {"status": False, "message": f"Manager with ID {data['project_manager']} not found.", "error": True, "data": {}},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Update development team
            if 'development_team' in data:
                project.development_team.clear()
                for user_id in data['development_team']:
                    try:
                        user = CustomUser.objects.get(id=int(user_id))
                        project.development_team.add(user)
                    except CustomUser.DoesNotExist:
                        return Response(
                            {"status": False, "message": f"Developer with ID {user_id} not found.", "error": True, "data": {}},
                            status=status.HTTP_400_BAD_REQUEST
                        )

            # Update testing team
            if 'testing_team' in data:
                project.testing_team.clear()
                for user_id in data['testing_team']:
                    try:
                        user = CustomUser.objects.get(id=int(user_id))
                        project.testing_team.add(user)
                    except CustomUser.DoesNotExist:
                        return Response(
                            {"status": False, "message": f"Tester with ID {user_id} not found.", "error": True, "data": {}},
                            status=status.HTTP_400_BAD_REQUEST
                        )

            project.project_version = data.get('project_version', project.project_version)
            project.save()

            return Response({
                "status": True,
                "message": "Project updated successfully.",
                "error": False,
                "data": ProjectSerializer(project).data
            }, status=status.HTTP_200_OK)

        except Project.DoesNotExist:
            return Response({
                "status": False,
                "message": "Project not found.",
                "error": True,
                "data": {}
            }, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk, *args, **kwargs):
        try:
            project = Project.objects.get(pk=pk)
            project.delete()
            return Response({
                "status": True,
                "message": "Project deleted successfully.",
                "error": False,
                "data": {}
            }, status=status.HTTP_200_OK)
        except Project.DoesNotExist:
            return Response({
                "status": False,
                "message": "Project not found.",
                "error": True,
                "data": {}
            }, status=status.HTTP_404_NOT_FOUND)