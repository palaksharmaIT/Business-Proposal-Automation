from django.db import models
from proposals.models import Proposal


class ProposalDelivery(models.Model):
    DELIVERY_STATUS = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]

    APPROVAL_STATUS = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='deliveries')

    sent_to_email = models.EmailField()
    delivery_status = models.CharField(max_length=20, choices=DELIVERY_STATUS, default='pending')
    delivery_error = models.TextField(blank=True, null=True)  # store error message if email fails

    approval_status = models.CharField(max_length=20, choices=APPROVAL_STATUS, default='pending')
    approval_notes = models.TextField(blank=True, null=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)

    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Delivery for {self.proposal} → {self.sent_to_email} ({self.approval_status})"