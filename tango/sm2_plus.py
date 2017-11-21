# Determines which words should be studied in the current session using
# the SM2+ algorithm described here: http://www.blueraja.com/blog/477/a-better-spaced-repetition-learning-algorithm-sm2
from . import model
from .utils import get_datetime_from_string, get_current_datetime

correct_threshold = 0.5

DAY_TO_SECONDS = 24 * 60 * 60


def get_default_variables(tango):
    return {"difficulty": 0.3, "dateLastReviewed": tango['created'], 'daysBetweenReviews': .25}


def update_sm2p(tango, performance_rating):
    db_model = model.get_model()
    sm2p_vars = dict(db_model.get_sm2p_vars(tango) or {}) or get_default_variables(tango)
    correct = performance_rating >= correct_threshold
    date_now = get_current_datetime()
    if correct:
        delta = date_now - get_datetime_from_string(sm2p_vars['dateLastReviewed'])
        delta_days = float(delta.total_seconds()) / DAY_TO_SECONDS
        percent_overdue = min(2, delta_days / sm2p_vars['daysBetweenReviews'])
    else:
        percent_overdue = 1
    sm2p_vars['difficulty'] += percent_overdue * 1 / 17 * (8 - 9 * performance_rating)
    difficulty_weight = _get_difficulty_weight(sm2p_vars['difficulty'])
    if correct:
        sm2p_vars['daysBetweenReviews'] *= 1 + (difficulty_weight - 1) * percent_overdue
    else:
        sm2p_vars['daysBetweenReviews'] *= 1 / difficulty_weight ** 2

    sm2p_vars['dateLastReviewed'] = date_now
    db_model.update_sm2p_vars(tango, sm2p_vars)


def _get_difficulty_weight(difficulty):
    return 3 - 1.7 * difficulty
