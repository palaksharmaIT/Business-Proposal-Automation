from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Proposal
from .serializers import ProposalSerializer
from .services.proposal_generator import generate_proposal_content
from .services.estimator import estimate_cost_and_timeline
from rfp.models import RFP
from knowledge_base.models import HistoricalProject
from exporter.models import ProposalDelivery
from exporter.services.pdf_generator import generate_proposal_pdf
from exporter.services.email_service import send_proposal_for_review


class ProposalViewSet(viewsets.ModelViewSet):
    queryset = Proposal.objects.all().order_by('-created_at')
    serializer_class = ProposalSerializer


@api_view(['POST'])
def generate_proposal(request):
    """
    POST /api/proposals/generate/
    Body: { "rfp_id": <id> }
    Generates a Proposal linked to the given analyzed RFP.
    """
    rfp_id = request.data.get('rfp_id')
    if not rfp_id:
        return Response({"error": "Missing 'rfp_id'."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        rfp_instance = RFP.objects.get(id=rfp_id)
    except RFP.DoesNotExist:
        return Response({"error": "RFP not found."}, status=status.HTTP_404_NOT_FOUND)

    if not rfp_instance.extracted_requirements:
        return Response(
            {"error": "This RFP has not been analyzed yet. Call /analyze/ first."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        content = generate_proposal_content(rfp_instance.extracted_requirements)
    except Exception as e:
        return Response({"error": f"Proposal generation failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    referenced_ids = content.pop('referenced_project_ids', [])

    proposal = Proposal.objects.create(
        rfp=rfp_instance,
        title=f"Proposal for {rfp_instance.extracted_requirements.get('project_type', rfp_instance.title)}",
        executive_summary=content.get('executive_summary'),
        scope_of_work=content.get('scope_of_work'),
        technology_stack=content.get('technology_stack'),
        deliverables=content.get('deliverables'),
        terms_and_conditions=content.get('terms_and_conditions'),
        status='generated',
    )

    if referenced_ids:
        historical_projects = HistoricalProject.objects.filter(id__in=referenced_ids)
        proposal.referenced_projects.set(historical_projects)

    return Response(
        {
            "message": "Proposal generated successfully.",
            "proposal": ProposalSerializer(proposal).data,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(['POST'])
def estimate_proposal(request, pk):
    """
    POST /api/proposals/proposals/{id}/estimate/
    Computes cost & timeline for an existing proposal using its linked RFP's requirements.
    """
    try:
        proposal = Proposal.objects.get(id=pk)
    except Proposal.DoesNotExist:
        return Response({"error": "Proposal not found."}, status=status.HTTP_404_NOT_FOUND)

    rfp_requirements = proposal.rfp.extracted_requirements
    if not rfp_requirements:
        return Response({"error": "Linked RFP has no extracted requirements."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        estimation = estimate_cost_and_timeline(rfp_requirements)
    except Exception as e:
        return Response({"error": f"Estimation failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    proposal.estimated_cost = estimation["estimated_cost"]
    proposal.cost_breakdown = estimation["cost_breakdown"]
    proposal.estimated_timeline_weeks = estimation["estimated_timeline_weeks"]
    proposal.timeline_breakdown = estimation["timeline_breakdown"]
    proposal.save()

    return Response(
        {
            "message": "Cost and timeline estimated successfully.",
            "proposal": ProposalSerializer(proposal).data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(['POST'])
def export_proposal_pdf(request, pk):
    """
    POST /api/proposals/proposals/{id}/export-pdf/
    Generates a PDF for the proposal and saves it.
    """
    try:
        proposal = Proposal.objects.get(id=pk)
    except Proposal.DoesNotExist:
        return Response({"error": "Proposal not found."}, status=status.HTTP_404_NOT_FOUND)

    try:
        generate_proposal_pdf(proposal)
    except Exception as e:
        return Response({"error": f"PDF generation failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(
        {
            "message": "PDF generated successfully.",
            "pdf_url": proposal.generated_pdf.url,
            "proposal": ProposalSerializer(proposal).data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(['POST'])
def send_proposal_for_review_view(request, pk):
    """
    POST /api/proposals/proposals/{id}/send-for-review/
    Emails the proposal PDF to the internal sales manager for review
    and logs a ProposalDelivery record.
    """
    try:
        proposal = Proposal.objects.get(id=pk)
    except Proposal.DoesNotExist:
        return Response({"error": "Proposal not found."}, status=status.HTTP_404_NOT_FOUND)

    if not proposal.generated_pdf:
        return Response({"error": "No PDF generated yet. Export the PDF first."}, status=status.HTTP_400_BAD_REQUEST)

    recipient_email = request.data.get('recipient_email')  # optional override

    delivery = ProposalDelivery.objects.create(
        proposal=proposal,
        sent_to_email=recipient_email or "",
        delivery_status='pending',
    )

    try:
        actual_recipient = send_proposal_for_review(proposal, recipient_email)
        delivery.sent_to_email = actual_recipient
        delivery.delivery_status = 'sent'
        delivery.save()

        proposal.status = 'sent_for_review'
        proposal.save()

    except Exception as e:
        delivery.delivery_status = 'failed'
        delivery.delivery_error = str(e)
        delivery.save()
        return Response({"error": f"Email sending failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(
        {
            "message": f"Proposal sent for review to {actual_recipient}.",
            "delivery_id": delivery.id,
            "proposal_status": proposal.status,
        },
        status=status.HTTP_200_OK,
    )


@api_view(['POST'])
def send_proposal_to_client_view(request, pk):
    """
    POST /api/proposals/proposals/{id}/send-to-client/
    Body: { "client_email": "client@example.com" }
    Emails the proposal PDF directly to the client's email address.
    This is separate from the internal "send for review" step.
    """
    try:
        proposal = Proposal.objects.get(id=pk)
    except Proposal.DoesNotExist:
        return Response({"error": "Proposal not found."}, status=status.HTTP_404_NOT_FOUND)

    if not proposal.generated_pdf:
        return Response({"error": "No PDF generated yet. Export the PDF first."}, status=status.HTTP_400_BAD_REQUEST)

    client_email = request.data.get('client_email')
    if not client_email:
        return Response({"error": "client_email is required."}, status=status.HTTP_400_BAD_REQUEST)

    delivery = ProposalDelivery.objects.create(
        proposal=proposal,
        sent_to_email=client_email,
        delivery_status='pending',
    )

    try:
        send_proposal_for_review(proposal, client_email)
        delivery.delivery_status = 'sent'
        delivery.save()
    except Exception as e:
        delivery.delivery_status = 'failed'
        delivery.delivery_error = str(e)
        delivery.save()
        return Response({"error": f"Email sending failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(
        {
            "message": f"Proposal sent to client at {client_email}.",
            "delivery_id": delivery.id,
        },
        status=status.HTTP_200_OK,
    )