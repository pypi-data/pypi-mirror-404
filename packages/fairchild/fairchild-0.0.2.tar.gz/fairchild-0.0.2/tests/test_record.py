"""Tests for Record class."""
from fairchild import Record


def test_record_creation():
    """Test creating a Record with a value."""
    record = Record({"key": "value"})
    
    assert record.value == {"key": "value"}


def test_record_with_dict():
    """Test Record with dictionary value."""
    data = {"name": "test", "count": 42}
    record = Record(data)
    
    assert record.value == data
    assert record.value["name"] == "test"
    assert record.value["count"] == 42


def test_record_with_list():
    """Test Record with list value."""
    data = [1, 2, 3, 4, 5]
    record = Record(data)
    
    assert record.value == data
    assert len(record.value) == 5


def test_record_with_primitive():
    """Test Record with primitive value."""
    record_int = Record(42)
    assert record_int.value == 42
    
    record_str = Record("hello")
    assert record_str.value == "hello"
    
    record_bool = Record(True)
    assert record_bool.value is True
