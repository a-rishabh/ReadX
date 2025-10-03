import pytest
from readx.pipelines import Pipeline

@pytest.fixture
def sample_data():
    return [
        {"text": "Hello world!", "label": "greeting"},
        {"text": "Goodbye!", "label": "farewell"}
    ]

@pytest.fixture
def sample_pipeline():
    # Assuming Pipeline takes a list of steps/functions
    def step1(data):
        for item in data:
            item["text"] = item["text"].lower()
        return data

    def step2(data):
        for item in data:
            item["length"] = len(item["text"])
        return data

    return Pipeline(steps=[step1, step2])

def test_pipeline_processes_data(sample_pipeline, sample_data):
    processed = sample_pipeline.run(sample_data)
    assert all("length" in item for item in processed)
    assert processed[0]["text"] == "hello world!"
    assert processed[1]["length"] == len("goodbye!")

def test_pipeline_empty_input(sample_pipeline):
    processed = sample_pipeline.run([])
    assert processed == []

def test_pipeline_invalid_input(sample_pipeline):
    with pytest.raises(Exception):
        sample_pipeline.run(None)