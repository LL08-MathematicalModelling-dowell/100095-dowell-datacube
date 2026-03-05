from rest_framework import serializers


class DashboardQuerySerializer(serializers.Serializer):
    db_id = serializers.CharField(required=True)
    days = serializers.IntegerField(required=False, default=7, min_value=1, max_value=90)


class StorageQuerySerializer(serializers.Serializer):
    db_id = serializers.CharField(required=True)


class ExportQuerySerializer(serializers.Serializer):
    db_id = serializers.CharField(required=True)
    days = serializers.IntegerField(required=False, default=30, min_value=1, max_value=365)
    format = serializers.ChoiceField(choices=['pdf'], default='pdf', required=False)