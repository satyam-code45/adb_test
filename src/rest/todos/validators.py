from rest_framework.exceptions import ValidationError

MAX_DESCRIPTION_LENGTH = 200


def _error(field, message):
    # Same {field: [messages]} shape DRF uses for its own validation errors
    return ValidationError({field: [message]})


def validate_description(data):
    """Return the cleaned description from a request body or raise a 400."""
    if not isinstance(data, dict):
        raise _error('non_field_errors', 'Request body must be a JSON object.')
    description = data.get('description')
    if description is None:
        raise _error('description', 'This field is required.')
    if not isinstance(description, str):
        raise _error('description', 'Must be a string.')

    description = description.strip()
    if not description:
        raise _error('description', 'This field may not be blank.')
    if len(description) > MAX_DESCRIPTION_LENGTH:
        raise _error('description', f'Must be at most {MAX_DESCRIPTION_LENGTH} characters.')
    return description
