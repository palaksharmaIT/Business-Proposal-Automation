from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Proposal
from .serializers import ProposalSerializer
from .services.proposal_generator import generate_proposal_content
from rfp.models import RFP
from knowledge_base.models import HistoricalProject


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