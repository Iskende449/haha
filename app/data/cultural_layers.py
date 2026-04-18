SOURCE_CUSTOM_URL = 'https://nomad.local/explorer'


def custom_source_url(slug: str) -> str:
    return f'{SOURCE_CUSTOM_URL}/{slug}'


CURATED_CULTURAL_LAYERS = [
    {
        'source_id': 9001,
        'name': 'Манжылы-Ата',
        'region': 'Иссык-Кульская область',
        'summary': 'Священные источники южного берега Иссык-Куля, куда едут за тишиной, водой и обрядами очищения.',
        'latitude': 42.13198,
        'longitude': 77.08257,
        'coordinate_quality': 'verified',
        'featured': True,
        'kind': 'sacred_site',
        'terrain': 'lake',
        'seasonality': 'all_season',
        'travel_tags': ['ritual', 'spring', 'family'],
        'source_url': custom_source_url('manjyly-ata'),
        'archaeological_description': 'Комплекс известен как сакральное место паломничества и сезонных обрядов у Иссык-Куля.',
        'ethnographic_description': 'Здесь совмещаются вода, поклонение предкам и практика тихого посещения без шумного туризма.',
    },
    {
        'source_id': 9002,
        'name': 'Сулайман-Тоо',
        'region': 'Ошская область',
        'summary': 'Сакральная гора Ошской долины с пещерами, тропами паломничества и сильной городской связью.',
        'latitude': 40.52836,
        'longitude': 72.80378,
        'coordinate_quality': 'verified',
        'featured': True,
        'kind': 'sacred_site',
        'terrain': 'city',
        'seasonality': 'all_season',
        'travel_tags': ['unesco', 'pilgrimage', 'urban'],
        'source_url': custom_source_url('sulayman-too'),
        'archaeological_description': 'Гора доминирует над историческим Ошем и служит узлом сакрального ландшафта.',
        'ethnographic_description': 'Маршруты посещения сочетают городскую доступность и традицию паломничества.',
    },
    {
        'source_id': 9101,
        'name': 'Чын Куран',
        'region': 'Нарынская область',
        'summary': 'Календарная точка начала нового жизненного цикла: кобылицы жеребятся, а кумыс открывает сезон.',
        'latitude': 42.16768,
        'longitude': 75.98613,
        'coordinate_quality': 'approximate',
        'featured': True,
        'kind': 'calendar_event',
        'terrain': 'steppe',
        'seasonality': 'warm_season',
        'travel_tags': ['calendar', 'kumys', 'jailoo'],
        'source_url': custom_source_url('chyn-kuran'),
        'archaeological_description': 'Это не археологический объект, а пространственный якорь традиционного календаря на пути к жайлоо.',
        'ethnographic_description': 'В этой фазе хозяйственного года важны первые жеребята, кумыс и открытие летнего цикла.',
    },
    {
        'source_id': 9102,
        'name': 'Саамал Мезгили',
        'region': 'Чуйская область',
        'summary': 'Календарная точка весеннего саамала, когда ранний кумыс и выезд к пастбищам становятся главным ритмом.',
        'latitude': 42.68082,
        'longitude': 74.34918,
        'coordinate_quality': 'approximate',
        'featured': False,
        'kind': 'calendar_event',
        'terrain': 'valley',
        'seasonality': 'warm_season',
        'travel_tags': ['calendar', 'spring', 'pasture'],
        'source_url': custom_source_url('saamal-mezgili'),
        'archaeological_description': 'Маркер весеннего цикла вынесен в долину как удобная точка маршрутизации.',
        'ethnographic_description': 'Сезон связывает первое молоко, пастбищный выход и обновление домашнего ритма.',
    },
]

CURATED_LAYER_BY_ID = {item['source_id']: item for item in CURATED_CULTURAL_LAYERS}
