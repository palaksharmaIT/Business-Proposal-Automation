# import io
# from django.conf import settings
# from django.core.files.base import ContentFile
# from google import genai
# from google.genai import types


# def _build_image_prompt(rfp_requirements: dict) -> str:
#     """
#     Builds a clean, descriptive prompt for image generation based on
#     the RFP's extracted requirements — avoids text/logos/people, focuses
#     on an abstract/professional concept illustration.
#     """
#     project_type = rfp_requirements.get('project_type', 'software project')
#     summary = rfp_requirements.get('summary', '')

#     return (
#         f"A clean, modern, professional concept illustration representing a "
#         f"'{project_type}' software project. {summary} "
#         f"Style: minimalist corporate tech illustration, flat design, "
#         f"soft blue and white color palette, abstract icons representing "
#         f"technology and business growth. No text, no logos, no people's faces."
#     )


# def generate_proposal_image(rfp_requirements: dict) -> bytes:
#     """
#     Calls Google's Imagen model to generate a concept image based on
#     the RFP requirements. Returns raw image bytes (PNG).
#     """
#     client = genai.Client(api_key=settings.GOOGLE_API_KEY)

#     prompt = _build_image_prompt(rfp_requirements)

#     response = client.models.generate_images(
#         model='imagen-4.0-generate-001',
#         prompt=prompt,
#         config=types.GenerateImagesConfig(
#             number_of_images=1,
#             aspect_ratio="16:9",
#         ),

#     )

#     if not response.generated_images:
#         raise ValueError("No image was returned by the model.")

#     image_bytes = response.generated_images[0].image.image_bytes
#     return image_bytes

