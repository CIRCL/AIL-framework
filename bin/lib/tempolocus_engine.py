#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Shared activity inference for chat messages and forum posts."""

import tempolocus
from tempolocus.core import DetectionError


def get_predictions_from_weekly(weekly_activity, top=5):
    if not weekly_activity:
        return {}
    try:
        return tempolocus.detect(weekly_activity, kind='weekly', top=top)
    except DetectionError:
        return {}

def get_holiday_predictions_from_yearly_activity(yearly_activity, top=5, holiday_profile='standard', activity_signal='lack'):
    yearly_results = []
    for year, daily_activity in sorted(yearly_activity.items()):
        if not daily_activity:
            continue
        try:
            result = tempolocus.detect({'nb': [[day, count] for day, count in sorted(daily_activity.items())]}, kind='yearly', top=top, holiday_profile=holiday_profile, activity_signal=activity_signal)
            result['year'] = year
            yearly_results.append(result)
        except DetectionError:
            continue
    if not yearly_results:
        return {}
    return {
        'input_type': 'yearly_daily_activity_by_year',
        'holiday_profile': holiday_profile,
        'activity_signal': activity_signal,
        'years': yearly_results,
    }
