# outreach/models.py
from django.db import models

class Lead(models.Model):
    company_name = models.CharField(max_length=255)
    website = models.URLField()
    employee_count = models.IntegerField()
    scraped_insights = models.TextField()
    personalized_message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.company_name

