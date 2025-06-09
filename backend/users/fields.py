import base64
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
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
        if not value:
            return None

        try:
            url = value.url
        except Exception:
            return None

        return url
