from rest_framework.exceptions import ValidationError

MAX_DESCRIPTION_LENGTH = 200


def validate_description(data):
    """Return the cleaned description from a request body or raise a 400."""
    description = data.get('description') if isinstance(data, dict) else None
    if description is None:
        raise ValidationError({'description': 'This field is required.'})
    if not isinstance(description, str):
        raise ValidationError({'description': 'Must be a string.'})

    description = description.strip()
    if not description:
        raise ValidationError({'description': 'This field may not be blank.'})
    if len(description) > MAX_DESCRIPTION_LENGTH:
        raise ValidationError(
            {'description': f'Must be at most {MAX_DESCRIPTION_LENGTH} characters.'}
        )
    return description
