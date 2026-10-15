
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse


def send_proposal_for_review(proposal, recipient_email=None, delivery=None):
    """
    Send a proposal PDF with Approve and Reject buttons.

    Uses an existing ProposalDelivery record.
    Does not create or update delivery records.
    Returns the recipient email on success.
    """

    if not proposal.generated_pdf:
        raise ValueError(
            "Proposal has no generated PDF. Export it first."
        )

    recipient = recipient_email or getattr(
        settings, "SALES_MANAGER_EMAIL", ""
    )

    if not recipient:
        raise ValueError(
            "No recipient email provided or configured."
        )

    if delivery is None:
        raise ValueError(
            "An existing ProposalDelivery record is required."
        )

    if not delivery.approval_token:
        raise ValueError(
            "The delivery record has no approval token."
        )

    site_url = getattr(settings, "SITE_URL", "").rstrip("/")

    if not site_url:
        raise ValueError(
            "SITE_URL is not configured in settings.py."
        )

    approve_url = (
        f"{site_url}"
        f"{reverse('proposal-approve', args=[delivery.approval_token])}"
    )

    reject_url = (
        f"{site_url}"
        f"{reverse('proposal-reject', args=[delivery.approval_token])}"
    )

    subject = f"Proposal for Review: {proposal.title}"

    body = f"""
Hello,

A new business proposal is ready for review.

Proposal: {proposal.title}
Estimated Cost: ${proposal.estimated_cost}
Estimated Timeline: {proposal.estimated_timeline_weeks} weeks

Approve Proposal:
{approve_url}

Reject Proposal:
{reject_url}

Please find the complete proposal attached as a PDF.

Regards,
AI Proposal System
"""

    html_body = f"""
<html>
<body>
    <h2>Proposal for Review</h2>

    <p>Hello,</p>

    <p>
        A new business proposal is ready for review.
    </p>

    <p>
        <strong>Proposal:</strong> {proposal.title}
    </p>

    <p>
        <strong>Estimated Cost:</strong> ${proposal.estimated_cost}
    </p>

    <p>
        <strong>Estimated Timeline:</strong>
        {proposal.estimated_timeline_weeks} weeks
    </p>

    <p>Please review the attached proposal and select an option:</p>

    <p>
        <a href="{approve_url}"
           style="background-color:#16a34a;
                  color:white;
                  padding:12px 22px;
                  text-decoration:none;
                  border-radius:6px;
                  font-weight:bold;
                  display:inline-block;">
            &#10003; Approve Proposal
        </a>

        &nbsp;&nbsp;

        <a href="{reject_url}"
           style="background-color:#dc2626;
                  color:white;
                  padding:12px 22px;
                  text-decoration:none;
                  border-radius:6px;
                  font-weight:bold;
                  display:inline-block;">
            Reject Proposal
        </a>
    </p>

    <p>The complete proposal is attached as a PDF.</p>

    <p>
        Regards,<br>
        AI Proposal System
    </p>
</body>
</html>
"""

    email = EmailMultiAlternatives(
        subject=subject,
        body=body,
        from_email=settings.EMAIL_HOST_USER,
        to=[recipient],
    )

    email.attach_alternative(html_body, "text/html")

    with proposal.generated_pdf.open("rb") as pdf_file:
        email.attach(
            f"{proposal.title or 'proposal'}.pdf",
            pdf_file.read(),
            "application/pdf",
        )

    email.send(fail_silently=False)

    return recipient
