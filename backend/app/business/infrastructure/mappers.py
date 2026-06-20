# app/business/infrastructure/mappers.py
from app.business.domain.entities import Business, WeeklyOffRule
from app.business.domain.value_objects import (
    normalize_business_name_for_lookup,
    normalize_whitespace,
)
from app.business.infrastructure.orm import BusinessModel, BusinessWeeklyOffRuleModel


def business_model_to_domain(model: BusinessModel) -> Business:
    return Business(
        owner_id=model.owner_id,
        name=model.name,
        default_wage_type=model.default_wage_type,
        default_working_hours_per_day=model.default_working_hours_per_day,
        default_overtime_multiplier=model.default_overtime_multiplier,
        payroll_start_day=model.payroll_start_day,
        weekly_off_rules=[
            WeeklyOffRule(
                id=rule.id,
                weekday=rule.weekday,
                week_of_month=rule.week_of_month,
            )
            for rule in model.weekly_off_rules
        ],
        id=model.id,
    )


def business_domain_to_model(domain: Business) -> BusinessModel:
    # normalize for DB
    normalized_display_name = normalize_whitespace(domain.name)
    normalized_lookup_name = normalize_business_name_for_lookup(domain.name)

    model = BusinessModel(
        id=domain.id,
        owner_id=domain.owner_id,
        name=normalized_display_name,
        normalized_name=normalized_lookup_name,
        default_wage_type=domain.default_wage_type,
        default_working_hours_per_day=domain.default_working_hours_per_day,
        default_overtime_multiplier=domain.default_overtime_multiplier,
        payroll_start_day=domain.payroll_start_day,
    )

    model.weekly_off_rules = [
        BusinessWeeklyOffRuleModel(
            id=rule.id,
            weekday=rule.weekday,
            week_of_month=rule.week_of_month,
        )
        for rule in domain.weekly_off_rules
    ]

    return model


def sync_business_identity_from_model(domain: Business, model: BusinessModel) -> None:
    # In case DB generated the id
    domain.id = model.id
