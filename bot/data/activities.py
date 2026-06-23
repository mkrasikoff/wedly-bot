from typing import List, Optional

ACTIVITIES: List[dict] = [
    {"id": 1, "title": "Устроить киновечер — выбрать фильм вместе и сделать попкорн", "category": "home", "tags": ["cozy", "together"]},
    {"id": 2, "title": "Приготовить что-то новое по рецепту, который ни разу не пробовали", "category": "home", "tags": ["creative", "together"]},
    {"id": 3, "title": "Поиграть в настольную игру или карты", "category": "home", "tags": ["fun", "together"]},
    {"id": 4, "title": "Устроить фотосессию дома — смешную или красивую, как получится", "category": "home", "tags": ["creative", "fun"]},
    {"id": 5, "title": "Посмотреть несколько эпизодов сериала и обсудить", "category": "home", "tags": ["cozy", "together"]},
    {"id": 6, "title": "Собрать пазл под музыку и чай", "category": "home", "tags": ["calm", "together"]},
    {"id": 7, "title": "Поиграть в видеоигру вдвоём — кооператив или соревнование", "category": "home", "tags": ["fun", "together"]},
    {"id": 8, "title": "Нарисовать что-нибудь вместе — хоть каракули, хоть шедевр", "category": "home", "tags": ["creative", "calm"]},
    {"id": 9, "title": "Организовать дома пикник: плед на полу, еда руками, никаких тарелок", "category": "home", "tags": ["cozy", "fun"]},
    {"id": 10, "title": "Прогуляться по новому маршруту и зайти в любое кафе, что понравится", "category": "outside", "tags": ["easy", "together"]},
    {"id": 11, "title": "Съездить в место, где ещё не были — хоть соседний район", "category": "outside", "tags": ["adventure", "together"]},
    {"id": 12, "title": "Сходить на рынок или фермерскую ярмарку и купить что-нибудь интересное", "category": "outside", "tags": ["fun", "together"]},
    {"id": 13, "title": "Поехать смотреть закат или рассвет в красивом месте", "category": "outside", "tags": ["romantic", "calm"]},
    {"id": 14, "title": "Сходить в музей или галерею — даже если редко ходите", "category": "outside", "tags": ["culture", "together"]},
    {"id": 15, "title": "Устроить пикник в парке с едой из дома", "category": "outside", "tags": ["cozy", "together"]},
    {"id": 16, "title": "Посетить мастер-класс или воркшоп вместе", "category": "outside", "tags": ["creative", "together"]},
    {"id": 17, "title": "Прогуляться ночью по городу — атмосфера совсем другая", "category": "outside", "tags": ["romantic", "adventure"]},
    {"id": 18, "title": "Сходить на концерт, стендап или спектакль", "category": "outside", "tags": ["culture", "fun"]},
    {"id": 19, "title": "Лечь и послушать плейлист, который нравится обоим", "category": "easy", "tags": ["calm", "cozy"]},
    {"id": 20, "title": "Полистать мемы или смешные видео вместе и потеряться на час", "category": "easy", "tags": ["fun", "lazy"]},
    {"id": 21, "title": "Заказать еду и поесть по-домашнему без телефонов", "category": "easy", "tags": ["cozy", "together"]},
    {"id": 22, "title": "Поиграть в вопросы — «36 вопросов» или придумать свои", "category": "easy", "tags": ["together", "romantic"]},
    {"id": 23, "title": "Посмотреть несколько коротких документалок на YouTube о чём-нибудь интересном", "category": "easy", "tags": ["calm", "together"]},
    {"id": 24, "title": "Сделать друг другу массаж — без обязательств насчёт качества", "category": "easy", "tags": ["cozy", "romantic"]},
    {"id": 25, "title": "Составить совместный плейлист на следующую поездку", "category": "easy", "tags": ["creative", "together"]},
    {"id": 26, "title": "Разобрать фотографии за последний год и вспомнить лучшие моменты", "category": "easy", "tags": ["together", "romantic"]},
    {"id": 27, "title": "Поиграть в слова или словесные ассоциации — никакой подготовки не нужно", "category": "easy", "tags": ["fun", "lazy"]},
    {"id": 28, "title": "Покататься на велосипедах или самокатах", "category": "active", "tags": ["outdoor", "fun"]},
    {"id": 29, "title": "Сходить в боулинг или на бильярд", "category": "active", "tags": ["fun", "together"]},
    {"id": 30, "title": "Поиграть в бадминтон или фрисби в парке", "category": "active", "tags": ["outdoor", "fun"]},
    {"id": 31, "title": "Устроить танцевальный вечер дома под случайный плейлист", "category": "active", "tags": ["fun", "home"]},
    {"id": 32, "title": "Сходить в скалодром или батутный центр", "category": "active", "tags": ["adventure", "fun"]},
    {"id": 33, "title": "Сделать совместную тренировку дома — YouTube-видео или своя программа", "category": "active", "tags": ["together", "health"]},
    {"id": 34, "title": "Устроить квест по городу — придумать маршрут с заданиями на ходу", "category": "active", "tags": ["adventure", "fun"]},
    {"id": 35, "title": "Поплавать в бассейне или сходить в баню/SPA", "category": "active", "tags": ["together", "relax"]},
    {"id": 36, "title": "Сходить на каток или в парк аттракционов", "category": "active", "tags": ["fun", "outdoor"]},
]

MOOD_TO_CATEGORIES: dict = {
    5: ["outside", "active"],
    4: ["active", "home"],
    3: ["outside", "home"],
    2: ["home", "easy"],
    1: ["easy"],
}


def get_activities_by_categories(categories: List[str]) -> List[dict]:
    """Возвращает все активности из указанных категорий."""
    return [a for a in ACTIVITIES if a["category"] in categories]


def get_activity_by_id(activity_id: int) -> Optional[dict]:
    """Возвращает активность по id или None."""
    return next((a for a in ACTIVITIES if a["id"] == activity_id), None)
