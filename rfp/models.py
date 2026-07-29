from django.db import models


class RFP(models.Model):
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('extracted', 'Text Extracted'),
        ('analyzed', 'AI Analyzed'),
        ('failed', 'Failed'),
    ]

    title = models.CharField(max_length=255, blank=True)
    file = models.FileField(upload_to='rfp_uploads/')

    extracted_text = models.TextField(blank=True, null=True)

    # AI-extracted structured data: project type, features, budget, timeline, client requirements
    extracted_requirements = models.JSONField(blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')

    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title or f"RFP #{self.pk}"
    