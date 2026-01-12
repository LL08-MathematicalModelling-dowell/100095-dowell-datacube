# analytics/serializers.py
from rest_framework import serializers
from datetime import datetime


class DatabaseSummarySerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    size_mb = serializers.FloatField()
    doc_count = serializers.IntegerField()
    avg_doc_size = serializers.IntegerField()
    index_size_mb = serializers.FloatField()

class CollectionSummarySerializer(serializers.Serializer):
    name = serializers.CharField()
    size_mb = serializers.FloatField()
    doc_count = serializers.IntegerField()
    avg_doc_size = serializers.IntegerField()
    index_size_mb = serializers.FloatField()

class SummarySerializer(serializers.Serializer):
    databases = DatabaseSummarySerializer(many=True)
    collections = CollectionSummarySerializer(many=True, required=False)

class TimeSeriesPointSerializer(serializers.Serializer):
    timestamp = serializers.DateTimeField()
    value = serializers.FloatField()

class TimeSeriesSerializer(serializers.Serializer):
    metric = serializers.CharField()
    series = TimeSeriesPointSerializer(many=True)

class UsageStatSerializer(serializers.Serializer):
    period = serializers.CharField()
    total_requests = serializers.IntegerField()
    active_users = serializers.IntegerField()
    peak_time = serializers.DateTimeField(required=False)

class IOStatSerializer(serializers.Serializer):
    reads = serializers.IntegerField()
    writes = serializers.IntegerField()
    avg_latency_ms = serializers.FloatField()
    error_rate = serializers.FloatField()

class SlowQuerySerializer(serializers.Serializer):
    query = serializers.DictField()
    duration_ms = serializers.FloatField()
    timestamp = serializers.DateTimeField()

class ExportSerializer(serializers.Serializer):
    format = serializers.ChoiceField(choices=['csv', 'pdf'])
    data_type = serializers.ChoiceField(choices=['summary', 'time-series', 'usage', 'io-stats'])