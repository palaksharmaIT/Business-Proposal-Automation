from django.shortcuts import get_object_or_404, HttpResponse
from django.utils import timezone

from .models import ProposalDelivery


def approve_proposal(request, token):
    delivery = get_object_or_404(
        ProposalDelivery,
        approval_token=token
    )

    # Already reviewed
    if delivery.approval_status != "pending":
        return HttpResponse(
            f"Proposal has already been {delivery.approval_status}."
        )

    # Mark delivery as approved
    delivery.approval_status = "approved"
    delivery.reviewed_at = timezone.now()
    delivery.save(
        update_fields=[
            "approval_status",
            "reviewed_at"
        ]
    )

    # Mark proposal as approved
    proposal = delivery.proposal
    proposal.status = "approved"
    proposal.save(
        update_fields=["status"]
    )

    return HttpResponse(
        "<h1>Proposal Approved</h1>"
        "<p>Thank you. The proposal has been approved successfully.</p>"
    )


def reject_proposal(request, token):
    delivery = get_object_or_404(
        ProposalDelivery,
        approval_token=token
    )

    # Already reviewed
    if delivery.approval_status != "pending":
        return HttpResponse(
            f"Proposal has already been {delivery.approval_status}."
        )

    # For now, simply reject when the button is clicked
    delivery.approval_status = "rejected"
    delivery.reviewed_at = timezone.now()
    delivery.save(
        update_fields=[
            "approval_status",
            "reviewed_at"
        ]
    )

    # Mark proposal as rejected
    proposal = delivery.proposal
    proposal.status = "rejected"
    proposal.save(
        update_fields=["status"]
    )

    return HttpResponse(
        "<h1>Proposal Rejected</h1>"
        "<p>The proposal has been rejected successfully.</p>"
    )