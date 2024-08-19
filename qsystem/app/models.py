from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.db.models import Max

class Activity(models.Model):
    ACTIVE = 'active'
    INACTIVE = 'inactive'

    MODE_CHOICES = [
        (ACTIVE, 'Active'),
        (INACTIVE, 'Inactive'),
    ]

    name = models.CharField(max_length=100)
    code = models.PositiveIntegerField(unique=True)  # Manually assigned unique activity code
    mode = models.CharField(max_length=8, choices=MODE_CHOICES, default=ACTIVE)

    def __str__(self):
        return f"{self.name} ({self.code})"


class Counter(models.Model):
    name = models.CharField(max_length=100)
    STATUS_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
    ]
    status = models.CharField(max_length=7, choices=STATUS_CHOICES, default='offline')

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
class CounterActivityAssignment(models.Model):
    counter = models.ForeignKey(Counter, on_delete=models.CASCADE)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)

    class Meta:
        unique_together = ('counter', 'activity', 'date')

    def __str__(self):
        return f"{self.counter.name} assigned to {self.activity.name} on {self.date}"

class QueueNumber(models.Model):
    STATUS_CHOICES = [
        ('issued', 'Issued'),
        ('called', 'Called'),
        ('served', 'Served'),
        ('cancelled', 'Cancelled'),
    ]
    
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    counter = models.ForeignKey(Counter, on_delete=models.SET_NULL, null=True, blank=True)
    number = models.PositiveIntegerField()
    issued_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='issued')
    date = models.DateField(default=timezone.now) 
    called_at = models.DateTimeField(null=True, blank=True)
    is_recalled = models.BooleanField(default=False)

    class Meta:
        unique_together = ('activity', 'number', 'date')

    def __str__(self):
        return f"{self.activity.name} - {self.number} ({self.date})"

    def save(self, *args, **kwargs):
        if not self.pk:  # If this is a new QueueNumber
            # Ensure the timezone is set to Malaysia time
            malaysia_now = timezone.localtime(timezone.now(), timezone.get_current_timezone())
            current_date = malaysia_now.date()

            # Get the last number issued today, starting from the activity code
            last_number = QueueNumber.objects.filter(activity=self.activity, date=current_date).aggregate(Max('number'))['number__max'] or self.activity.code
            self.number = last_number + 1
            self.date = current_date  # Ensure the date is set to Malaysia time's date
        super().save(*args, **kwargs)


class CounterActivity(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    counter = models.ForeignKey(Counter, on_delete=models.CASCADE)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    class Meta:
        unique_together = ('counter', 'activity')

    def __str__(self):
        return f"{self.counter.name} - {self.activity.name} ({self.get_status_display()})"

class StaffProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    counter = models.ForeignKey(Counter, on_delete=models.SET_NULL, null=True, blank=True)
    current_activity = models.ForeignKey(Activity, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"
    


