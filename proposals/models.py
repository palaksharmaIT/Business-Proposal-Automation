from django.db import models
from rfp.models import RFP


class Proposal(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('generated', 'Generated'),
        ('sent_for_review', 'Sent for Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    rfp = models.ForeignKey(RFP, on_delete=models.CASCADE, related_name='proposals')

    title = models.CharField(max_length=255, blank=True)

    # Generated proposal sections
    executive_summary = models.TextField(blank=True, null=True)
    scope_of_work = models.TextField(blank=True, null=True)
    technology_stack = models.TextField(blank=True, null=True)
    deliverables = models.TextField(blank=True, null=True)
    terms_and_conditions = models.TextField(blank=True, null=True)

    # Cost & timeline (Phase 6)
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    cost_breakdown = models.JSONField(blank=True, null=True)  # e.g. {"design": 2000, "dev": 8000, ...}

    estimated_timeline_weeks = models.PositiveIntegerField(blank=True, null=True)
    timeline_breakdown = models.JSONField(blank=True, null=True)  # e.g. {"phase1": "2 weeks", ...}

    # References to similar past projects used for RAG context
    referenced_projects = models.ManyToManyField(
        'knowledge_base.HistoricalProject', blank=True, related_name='used_in_proposals'
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    generated_pdf = models.FileField(upload_to='generated_pdfs/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title or f"Proposal #{self.pk} for {self.rfp}"