from datetime import date

KYRGYZ_MONTHS = {
    1: 'Кулжа',
    2: 'Бугу',
    3: 'Жалган Куран',
    4: 'Чын Куран',
    5: 'Бугу',
    6: 'Кулжа',
    7: 'Теке',
    8: 'Баш Оона',
    9: 'Аяк Оона',
    10: 'Тогуздун айы',
    11: 'Жетинин айы',
    12: 'Бештин айы',
}


def get_kyrgyz_month_name(current_date: date | None = None) -> str:
    current_date = current_date or date.today()
    return KYRGYZ_MONTHS.get(current_date.month, 'Үркер')
