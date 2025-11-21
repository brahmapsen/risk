"""
Integration tests for the FastAPI endpoints.
"""

import pytest
import httpx
import os
import subprocess
import time
import signal


@pytest.fixture(scope="module")
def api_server():
    """Start API server for testing or use existing server."""
    # Check if model exists, if not skip
    if not os.path.exists("readmission_model.json"):
        pytest.skip("Model file does not exist. Run training first.")

    if not os.path.exists("data/training_snapshot.csv"):
        pytest.skip("Training snapshot does not exist. Run training first.")

    base_url = "http://127.0.0.1:8000"
    process = None

    # Check if server is already running (e.g., in CI)
    try:
        response = httpx.get(f"{base_url}/health", timeout=2.0)
        if response.status_code == 200:
            # Server already running, use it
            yield base_url
            return
    except (httpx.ConnectError, httpx.TimeoutException):
        # Server not running, start our own
        pass

    # Start server
    process = subprocess.Popen(
        ["uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to be ready (with retries)
    max_retries = 10
    for i in range(max_retries):
        try:
            response = httpx.get(f"{base_url}/health", timeout=2.0)
            if response.status_code == 200:
                break
        except (httpx.ConnectError, httpx.TimeoutException):
            if i == max_retries - 1:
                # Server failed to start
                if process:
                    process.terminate()
                    process.wait()
                pytest.fail("API server failed to start")
            time.sleep(1)

    yield base_url

    # Cleanup (only if we started the server)
    if process:
        process.terminate()
        process.wait()


def test_predict_endpoint(api_server):
    """Test the /predict endpoint with valid data."""
    client = httpx.Client(base_url=api_server, timeout=10.0)

    response = client.post(
        "/predict",
        json={
            "age": 72,
            "gender": 1,
            "num_encounters": 2,
            "avg_los": 4.5,
            "creatinine": 1.8,
            "heart_rate": 110,
            "systolic_bp": 145,
        },
    )

    if response.status_code != 200:
        # Print error details for debugging
        print(f"API Error: {response.status_code}")
        print(f"Response: {response.text}")

    assert (
        response.status_code == 200
    ), f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()

    assert "probability" in data
    assert "risk_level" in data
    assert 0 <= data["probability"] <= 1
    assert data["risk_level"] in ["High", "Low"]


def test_predict_endpoint_invalid_data(api_server):
    """Test the /predict endpoint with invalid data."""
    client = httpx.Client(base_url=api_server, timeout=10.0)

    # Missing required field
    response = client.post(
        "/predict",
        json={
            "age": 72,
            "gender": 1,
            # Missing other required fields
        },
    )

    assert response.status_code == 422  # Validation error


def test_predict_endpoint_edge_cases(api_server):
    """Test edge cases for predictions."""
    client = httpx.Client(base_url=api_server, timeout=10.0)

    # Test with very high risk factors
    response = client.post(
        "/predict",
        json={
            "age": 85,
            "gender": 1,
            "num_encounters": 10,
            "avg_los": 20.0,
            "creatinine": 3.5,
            "heart_rate": 150,
            "systolic_bp": 200,
        },
    )

    if response.status_code != 200:
        print(f"API Error: {response.status_code}")
        print(f"Response: {response.text}")

    assert (
        response.status_code == 200
    ), f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert "probability" in data

    # Test with very low risk factors
    response = client.post(
        "/predict",
        json={
            "age": 30,
            "gender": 0,
            "num_encounters": 1,
            "avg_los": 2.0,
            "creatinine": 0.8,
            "heart_rate": 70,
            "systolic_bp": 120,
        },
    )

    if response.status_code != 200:
        print(f"API Error: {response.status_code}")
        print(f"Response: {response.text}")

    assert (
        response.status_code == 200
    ), f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert "probability" in data
