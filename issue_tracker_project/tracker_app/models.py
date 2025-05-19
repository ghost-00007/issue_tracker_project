# models.py
from django.contrib.auth.models import AbstractUser,BaseUserManager
from django.db import models


# Create your models here.


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        valid_fields = {field.name for field in CustomUser._meta.fields}
        filtered_fields = {key: value for key, value in extra_fields.items() if key in valid_fields}
        
        user = self.model(email=email, **filtered_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        # Ensure the superuser has these fields set
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)




class CustomUser(AbstractUser):
    email = models.EmailField(unique=True, blank=False, max_length=50, verbose_name="email address")
    employee_code = models.CharField(max_length=50, blank=True, unique=True, verbose_name="Employee ID")
    employee_name = models.CharField(max_length=100,verbose_name="Employee Name")
    salutation = models.CharField(max_length=50, blank=True, verbose_name="Salutation")
    department = models.CharField(max_length=25, blank=True, verbose_name="Department")
    designation = models.CharField(max_length=50, blank=True, verbose_name="Designation")
    contact_number = models.CharField(max_length=15, blank=True, null=True, verbose_name="Contact Number")
    emergency_contact = models.CharField(max_length=15, blank=True, null=True, verbose_name="Emergency Contact")
    date_of_birth = models.DateField(blank=True, null=True, verbose_name="Date of Birth")
    grade = models.CharField(max_length=25, blank=True, null=True, verbose_name="Grade")
    gender = models.CharField(max_length=25, blank=True, null=True, verbose_name="Gender")
    employee_type = models.CharField(max_length=100, blank=True, verbose_name="Employee Type")
    login = models.CharField(max_length=100, blank=True, verbose_name="Login Time")
    logout = models.CharField(max_length=100, blank=True, verbose_name="Logout Time")
    attendance_id = models.CharField(max_length=15, blank=True, verbose_name="Attendance ID")
    teamleader = models.CharField(max_length=50, blank=True, verbose_name="Team Leader")
    last_update = models.DateTimeField(auto_now=True, verbose_name="Last Update")
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    # Permissions fields
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=('groups'),
        blank=True,
        related_name='customuser_set',
        related_query_name='customuser',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=('user permissions'),
        blank=True,
        related_name='customuser_set',
        related_query_name='customuser',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.username} ({self.email})"
    




class Project(models.Model):
    project_code = models.CharField(max_length=20, unique=True)
    project_name = models.CharField(max_length=100)
    project_manager = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='managed_projects')
    development_team = models.ManyToManyField(CustomUser, related_name='development_team', blank=True)
    testing_team = models.ManyToManyField(CustomUser, related_name='testing_team', blank=True)
    project_version = models.CharField(max_length=100 , null=True , blank= True)
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.project_name
    
    class Meta :
        db_table = 'project'
        ordering = ['-created_at']
    
# class TestingTeam(models.Model):
#     project_id = models.ForeignKey(Project, on_delete=models.CASCADE)
#     customuser_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE)   

class Issue(models.Model):
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
        ('Closed', 'Closed'),
    ]
    # project_code = models.CharField(max_length=20)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    project_name = models.CharField(max_length=100)
    issue_code = models.CharField(max_length=20, unique=True, blank=True)  # Make issue_code optional
    issue_title = models.CharField(max_length=100)
    issue_priority = models.CharField(max_length=50)
    testcase_code = models.CharField(max_length=50, blank=True, null=True)
    attachment = models.FileField(upload_to='attachments/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    employee_name = models.CharField(max_length=100, default= "Not Allocated")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')  # New status field

    def __str__(self):
        return self.issue_title

    def save(self, *args, **kwargs):
        # Generate issue_code only if it's not already set
        self.project_name = self.project.project_name
        if not self.issue_code:
            last_issue = Issue.objects.order_by('-id').first()  # Get the last created issue
            if last_issue:
                last_issue_number = int(last_issue.issue_code.split('ISS')[1])
                self.issue_code = f'ISS{str(last_issue_number + 1).zfill(3)}'  # Increment the number and pad with zeros
            else:
                self.issue_code = 'ISS001'  # Start from ISS001 if no issues exist
        super().save(*args, **kwargs)



class TaskAssignment(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='assignments')
    employee = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.issue.issue_code} assigned to {self.employee.employee_name}"
    



class Resolution(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='resolutions')
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return f"Resolution for {self.issue.issue_code}"
    

    