"""
Automated Pytest Suite for Performance Profiling and Agronomic Benchmarks.
"""

from fastapi.testclient import TestClient
from app.main import app
from app.benchmarks import (
    benchmark_recommendation_engine,
    benchmark_zero_cost_tools,
    run_full_diagnostic_benchmark
)

client = TestClient(app)


def test_recommendation_engine_benchmark():
    res = benchmark_recommendation_engine(iterations=5)
    assert res["iterations_evaluated"] == 5
    assert res["database_crops_evaluated"] >= 100
    assert res["mean_latency_ms"] > 0.0
    assert res["throughput_ops_per_sec"] > 0.0
    assert "PASS" in res["status"]


def test_zero_cost_tools_benchmark():
    res = benchmark_zero_cost_tools(iterations=10)
    assert res["iterations_per_tool"] == 10
    assert res["tools_profiled"] == 5
    for tool_name, metrics in res["results"].items():
        assert metrics["mean_latency_ms"] >= 0.0
        assert metrics["throughput_ops_per_sec"] > 0.0


def test_full_diagnostic_benchmark_function():
    res = run_full_diagnostic_benchmark()
    assert res["service"] == "AgriAssist Agronomic Decision Core"
    assert res["system_health"] == "OPTIMAL"
    assert "timestamp_iso" in res
    assert "recommender_engine" in res
    assert "zero_cost_tools" in res


def test_benchmarks_api_endpoint():
    response = client.get("/api/benchmarks")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "AgriAssist Agronomic Decision Core"
    assert data["system_health"] == "OPTIMAL"
    assert data["recommender_engine"]["database_crops_evaluated"] >= 100
    assert data["zero_cost_tools"]["tools_profiled"] == 5
