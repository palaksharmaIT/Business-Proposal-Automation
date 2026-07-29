from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from .models import HistoricalProject
from .serializers import HistoricalProjectSerializer
from .services.vector_store import build_or_update_index, search_similar_projects


class HistoricalProjectViewSet(viewsets.ModelViewSet):
    queryset = HistoricalProject.objects.all().order_by('-created_at')
    serializer_class = HistoricalProjectSerializer


@api_view(['POST'])
def rebuild_index(request):
    try:
        count = build_or_update_index()
        return Response({"message": f"Index rebuilt with {count} projects."}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def search_index(request):
    query = request.data.get('query')
    if not query:
        return Response({"error": "Missing 'query' field."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        results = search_similar_projects(query, top_k=3)
        return Response({"results": results}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)