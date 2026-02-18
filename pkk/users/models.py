from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.hashers import make_password, check_password

# Create your models here.

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = [
        ('user', 'Tourist/User'),
        ('company', 'Tour Company'),
    ]
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='user')
    full_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(
        max_length=15,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$')],
        blank=True
    )
    bio = models.TextField(max_length=500, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    location = models.CharField(max_length=100, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Social features
    followers = models.ManyToManyField('self', symmetrical=False, related_name='following', blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Only email is required

    def __str__(self):
        return self.full_name or self.username
    
    def get_followers_count(self):
        return self.followers.count()
    
    def get_following_count(self):
        return self.following.count()

class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    travel_preferences = models.TextField(blank=True)
    budget_range = models.CharField(max_length=50, blank=True)
    preferred_activities = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('booking', 'Booking Update'),
        ('review', 'New Review'),
        ('follow', 'New Follower'),
        ('message', 'New Message'),
        ('system', 'System Update'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"


class SecurityAnswer(models.Model):
    """Stores hashed answers to 3 security questions for password recovery."""
    QUESTION_1 = "What is your nickname?"
    QUESTION_2 = "What school did you attend?"
    QUESTION_3 = "What city or place are you from?"

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='security_answers')
    answer_1 = models.CharField(max_length=255)  # stored as hash
    answer_2 = models.CharField(max_length=255)
    answer_3 = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def set_answers(self, a1, a2, a3):
        self.answer_1 = make_password(a1.strip().lower())
        self.answer_2 = make_password(a2.strip().lower())
        self.answer_3 = make_password(a3.strip().lower())

    def check_answers(self, a1, a2, a3):
        return (
            check_password(a1.strip().lower(), self.answer_1) and
            check_password(a2.strip().lower(), self.answer_2) and
            check_password(a3.strip().lower(), self.answer_3)
        )

    def __str__(self):
        return f"SecurityAnswers for {self.user.username}"
