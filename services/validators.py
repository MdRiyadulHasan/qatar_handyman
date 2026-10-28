from django.core.exceptions import ValidationError


def validate_image_size(value):
    if value.size > 10 * 1024 * 1024:
        raise ValidationError("Images must be 10 MB or smaller.")


def validate_seo_faqs(value):
    if not isinstance(value, list):
        raise ValidationError('Enter a JSON list of question/answer objects.')
    for item in value:
        if not isinstance(item, dict) or set(item) != {'question', 'answer'}:
            raise ValidationError('Each FAQ must have exactly question and answer keys.')
        for key, limit in (('question', 500), ('answer', 5000)):
            text = item[key]
            if not isinstance(text, str) or not text.strip() or len(text) > limit:
                raise ValidationError(f'FAQ {key} must be non-empty text up to {limit} characters.')
