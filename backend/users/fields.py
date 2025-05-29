import base64
from django.core.files.base import ContentFile
from rest_framework import serializers
import uuid


class Base64ImageField(serializers.ImageField):
    """Custom ImageField that accepts base64 encoded images"""

    def to_internal_value(self, data):
        """Convert base64 string to image file"""
        if isinstance(data, str) and data.startswith("data:image"):
            format, imgstr = data.split(";base64,")
            ext = format.split("/")[-1]

            try:
                decoded_file = base64.b64decode(imgstr)
            except TypeError:
                raise serializers.ValidationError("Invalid image format")

            file_name = f"{uuid.uuid4()}.{ext}"
            data = ContentFile(decoded_file, name=file_name)

        return super().to_internal_value(data)

    def to_representation(self, value):
        """Return URL of the image file"""
        if not value:
            return None

        try:
            url = value.url
        except Exception:
            return None

        return url
