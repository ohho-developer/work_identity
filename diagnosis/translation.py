from modeltranslation.translator import TranslationOptions, register
from .models import Axis, Question

@register(Axis)
class AxisTranslationOptions(TranslationOptions):
    fields = ('name', 'description', 'work_style', 'work_condition', 'work_develop', 'work_communication')

@register(Question)
class QuestionTranslationOptions(TranslationOptions):
    fields = ('text', 'option_a', 'option_b') 