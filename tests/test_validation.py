from utils.validation import validate_location_query

def test_validate_location_query():
    assert validate_location_query("Mumbai") == True
    assert validate_location_query("New York") == True
    assert validate_location_query("") == False
    assert validate_location_query("A") == False
    assert validate_location_query(None) == False
