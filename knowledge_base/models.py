from django.db import models


class HistoricalProject(models.Model):
    """
    Stores past proposals/projects used as reference data for RAG.
    Each entry gets embedded and stored in FAISS for similarity search.
    """

    title = models.CharField(max_length=255)
    client_name = models.CharField(max_length=255, blank=True)

    project_type = models.CharField(max_length=100, blank=True)  # e.g. "E-commerce", "Mobile App"
    description = models.TextField()  # full project description / scope of work

    tech_stack = models.CharField(max_length=500, blank=True)  # e.g. "Django, React, PostgreSQL"

    actual_cost = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    actual_duration_weeks = models.PositiveIntegerField(blank=True, null=True)

    original_proposal_file = models.FileField(
        upload_to='historical_proposals/', blank=True, null=True
    )
    

    # Whether this project has been embedded and pushed into FAISS yet
    is_indexed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title