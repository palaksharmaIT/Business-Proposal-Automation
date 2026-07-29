from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import RFP
from .serializers import RFPSerializer
from .services.text_extractor import extract_text
from .services.requirement_extractor import extract_requirements_with_ai


class RFPViewSet(viewsets.ModelViewSet):
    queryset = RFP.objects.all().order_by('-uploaded_at')
    serializer_class = RFPSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rfp_instance = serializer.save()

        try:
            extracted = extract_text(rfp_instance.file.path)
            rfp_instance.extracted_text = extracted
            rfp_instance.status = 'extracted'
            rfp_instance.save()
        except Exception as e:
            rfp_instance.status = 'failed'
            rfp_instance.save()
            return Response(
                {
                    "message": "RFP uploaded but text extraction failed.",
                    "error": str(e),
                    "rfp": RFPSerializer(rfp_instance).data,
                },
                status=status.HTTP_207_MULTI_STATUS,
            )

        return Response(
            {
                "message": "RFP uploaded and text extracted successfully.",
                "rfp": RFPSerializer(rfp_instance).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'], url_path='analyze')
    def analyze(self, request, pk=None):
        """
        POST /api/rfp/rfps/{id}/analyze/
        Runs Gemini requirement extraction on this RFP's extracted_text.
        """
        rfp_instance = self.get_object()

        if not rfp_instance.extracted_text:
            return Response(
                {"error": "No extracted text available for this RFP. Upload/extract first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            requirements = extract_requirements_with_ai(rfp_instance.extracted_text)
            rfp_instance.extracted_requirements = requirements
            rfp_instance.status = 'analyzed'
            rfp_instance.save()
        except Exception as e:
            rfp_instance.status = 'failed'
            rfp_instance.save()
            return Response(
                {"error": f"AI analysis failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "message": "RFP analyzed successfully.",
                "rfp": RFPSerializer(rfp_instance).data,
            },
            status=status.HTTP_200_OK,
        )


    