def min_value(record):
    min_confidence = 1.5
    for key, value in record._values.items():
        field_confidence = None
        if hasattr(value, "total_confidence"):
            field_confidence = value.total_confidence(min_value)
        else:
            field_confidence = record.get_confidence(key)
        if field_confidence is not None and field_confidence < min_confidence:
            min_confidence = field_confidence
    if min_confidence <= 1.0:
        return min_confidence
    return None
