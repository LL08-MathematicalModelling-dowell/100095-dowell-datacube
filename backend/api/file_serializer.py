from rest_framework import serializers


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    # Optional: override filename or content-type (otherwise derived from the file)
    filename = serializers.CharField(required=False, allow_blank=True)
    content_type = serializers.CharField(required=False, allow_blank=True)

class FileListQuerySerializer(serializers.Serializer):
    page = serializers.IntegerField(default=1, min_value=1)
    page_size = serializers.IntegerField(default=50, min_value=1, max_value=100)
    search = serializers.CharField(required=False, allow_blank=True)

class FileDeleteSerializer(serializers.Serializer):
    # Not strictly needed if file_id is in URL, but can be used for body-based deletion
    file_id = serializers.CharField()

class FileRetrieveQuerySerializer(serializers.Serializer):
    # No query params needed for retrieve, but you can add fields if necessary
    pass