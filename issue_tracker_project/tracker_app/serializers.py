# serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser,Project,Issue,TaskAssignment,Resolution

# Serializer for User Registration
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    employee_code = serializers.CharField(required=True)  # Ensure employee_code is required
    employee_name = serializers.CharField(required=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'username', 'password', 'first_name', 'last_name', 'employee_code','employee_name','department','designation']

    def validate_employee_code(self, value):
        # Check if employee_code is unique
        if CustomUser.objects.filter(employee_code=value).exists():
            raise serializers.ValidationError("Employee code must be unique.")
        return value

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            employee_code=validated_data['employee_code'],  # Ensure it's passed correctly
            employee_name=validated_data['employee_name'],
            department=validated_data['department'],
            designation=validated_data['designation']
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Invalid email or password.")
    
class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'employee_code', 'first_name', 'last_name','employee_name','designation']


# Project serializer
class ProjectSerializer(serializers.ModelSerializer):
    project_manager = CustomUserSerializer(read_only=True)
    development_team = CustomUserSerializer(many=True, read_only=True)
    testing_team = CustomUserSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = ['id','project_code', 'project_name', 'project_manager', 'development_team', 'testing_team'  , "created_at", "project_version"]


class IssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issue
        fields = '__all__'



class TaskAssignmentSerializer(serializers.ModelSerializer):
    issue_code = serializers.CharField(source='issue.issue_code', read_only=True)
    issue_title = serializers.CharField(source='issue.issue_title', read_only=True)
    employee_code = serializers.CharField(source='CustomUser.employee_code', read_only=True)
    employee_name = serializers.CharField(source='CustomUser.employee_name', read_only=True)

    class Meta:
        model = TaskAssignment
        fields = ['id', 'issue_code', 'issue_title', 'employee_code', 'employee_name', 'assigned_at']



class ResolutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resolution
        fields = ['id', 'issue', 'description', 'created_at']