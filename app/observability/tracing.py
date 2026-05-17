"""OpenTelemetry 全链路追踪配置"""
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from fastapi import FastAPI

from app.config import settings


def setup_tracing(app: FastAPI, service_name: str = "library-ai-agent"):
    """配置 OpenTelemetry 全链路追踪"""
    provider = TracerProvider()
    otlp_exporter = OTLPSpanExporter(endpoint=f"{settings.OTLP_ENDPOINT}/v1/traces")
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)

    return trace.get_tracer(service_name)
