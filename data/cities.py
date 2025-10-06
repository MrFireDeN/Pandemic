class City:
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color
        self.connections: list["City"] = []
        self.has_research_station = False
        self.infection_cubes = {"blue": 0, "yellow": 0, "black": 0, "red": 0}

    def connect(self, other: "City"):
        if other not in self.connections:
            self.connections.append(other)
            other.connections.append(self)


class CityGraph:
    def __init__(self):
        self.cities: dict[str, City] = {}

    def add_city(self, name: str, color: str):
        self.cities[name] = City(name, color)

    def connect(self, a: str, b: str):
        self.cities[a].connect(self.cities[b])

    def get_city(self, name: str) -> City:
        return self.cities[name]

def build_city_graph() -> CityGraph:
    graph = CityGraph()

    # === Синие города ===
    graph.add_city("Сан-Франциско", "синий")
    graph.add_city("Чикаго", "синий")
    graph.add_city("Монреаль", "синий")
    graph.add_city("Нью-Йорк", "синий")
    graph.add_city("Лондон", "синий")
    graph.add_city("Эссен", "синий")
    graph.add_city("Санкт-Петербург", "синий")
    graph.add_city("Милан", "синий")
    graph.add_city("Париж", "синий")
    graph.add_city("Мадрид", "синий")
    graph.add_city("Вашингтон", "синий")
    graph.add_city("Атланта", "синий")

    # === Жёлтые города ===
    graph.add_city("Лос-Анджелес", "жёлтый")
    graph.add_city("Мехико", "жёлтый")
    graph.add_city("Майами", "жёлтый")
    graph.add_city("Богота", "жёлтый")
    graph.add_city("Лима", "жёлтый")
    graph.add_city("Сантьяго", "жёлтый")
    graph.add_city("Буэнос-Айрес", "жёлтый")
    graph.add_city("Сан-Паулу", "жёлтый")
    graph.add_city("Лагос", "жёлтый")
    graph.add_city("Киншаса", "жёлтый")
    graph.add_city("Йоханнесбург", "жёлтый")
    graph.add_city("Хартум", "жёлтый")

    # === Чёрные города ===
    graph.add_city("Алжир", "чёрный")
    graph.add_city("Стамбул", "чёрный")
    graph.add_city("Москва", "чёрный")
    graph.add_city("Каир", "чёрный")
    graph.add_city("Багдад", "чёрный")
    graph.add_city("Тегеран", "чёрный")
    graph.add_city("Эр-Рияд", "чёрный")
    graph.add_city("Карачи", "чёрный")
    graph.add_city("Дели", "чёрный")
    graph.add_city("Мумбаи", "чёрный")
    graph.add_city("Ченнаи", "чёрный")
    graph.add_city("Калькутта", "чёрный")

    # === Красные города ===
    graph.add_city("Бангкок", "красный")
    graph.add_city("Джакарта", "красный")
    graph.add_city("Хошимин", "красный")
    graph.add_city("Гонконг", "красный")
    graph.add_city("Шанхай", "красный")
    graph.add_city("Пекин", "красный")
    graph.add_city("Сеул", "красный")
    graph.add_city("Токио", "красный")
    graph.add_city("Осака", "красный")
    graph.add_city("Тайбэй", "красный")
    graph.add_city("Манила", "красный")
    graph.add_city("Сидней", "красный")

    # === Связи между городами ===
    # Синий континент
    graph.connect("Сан-Франциско", "Токио")
    graph.connect("Сан-Франциско", "Манила")
    graph.connect("Сан-Франциско", "Лос-Анджелес")
    graph.connect("Сан-Франциско", "Чикаго")

    graph.connect("Чикаго", "Сан-Франциско")
    graph.connect("Чикаго", "Лос-Анджелес")
    graph.connect("Чикаго", "Мехико")
    graph.connect("Чикаго", "Атланта")
    graph.connect("Чикаго", "Монреаль")

    graph.connect("Монреаль", "Чикаго")
    graph.connect("Монреаль", "Нью-Йорк")
    graph.connect("Монреаль", "Вашингтон")
    graph.connect("Монреаль", "Атланта")

    graph.connect("Нью-Йорк", "Монреаль")
    graph.connect("Нью-Йорк", "Вашингтон")
    graph.connect("Нью-Йорк", "Лондон")
    graph.connect("Нью-Йорк", "Мадрид")

    graph.connect("Лондон", "Нью-Йорк")
    graph.connect("Лондон", "Мадрид")
    graph.connect("Лондон", "Париж")
    graph.connect("Лондон", "Эссен")

    graph.connect("Эссен", "Лондон")
    graph.connect("Эссен", "Париж")
    graph.connect("Эссен", "Милан")
    graph.connect("Эссен", "Санкт-Петербург")

    graph.connect("Санкт-Петербург", "Эссен")
    graph.connect("Санкт-Петербург", "Москва")
    graph.connect("Санкт-Петербург", "Стамбул")

    graph.connect("Милан", "Эссен")
    graph.connect("Милан", "Париж")
    graph.connect("Милан", "Стамбул")

    graph.connect("Париж", "Лондон")
    graph.connect("Париж", "Эссен")
    graph.connect("Париж", "Милан")
    graph.connect("Париж", "Алжир")
    graph.connect("Париж", "Мадрид")

    graph.connect("Мадрид", "Париж")
    graph.connect("Мадрид", "Лондон")
    graph.connect("Мадрид", "Нью-Йорк")
    graph.connect("Мадрид", "Алжир")
    graph.connect("Мадрид", "Сан-Паулу")

    graph.connect("Вашингтон", "Нью-Йорк")
    graph.connect("Вашингтон", "Монреаль")
    graph.connect("Вашингтон", "Атланта")
    graph.connect("Вашингтон", "Майами")

    graph.connect("Атланта", "Вашингтон")
    graph.connect("Атланта", "Майами")
    graph.connect("Атланта", "Чикаго")

    # Жёлтые города
    graph.connect("Лос-Анджелес", "Сан-Франциско")
    graph.connect("Лос-Анджелес", "Чикаго")
    graph.connect("Лос-Анджелес", "Мехико")
    graph.connect("Лос-Анджелес", "Сидней")

    graph.connect("Мехико", "Лос-Анджелес")
    graph.connect("Мехико", "Чикаго")
    graph.connect("Мехико", "Майами")
    graph.connect("Мехико", "Богота")
    graph.connect("Мехико", "Лима")

    graph.connect("Майами", "Вашингтон")
    graph.connect("Майами", "Атланта")
    graph.connect("Майами", "Мехико")
    graph.connect("Майами", "Богота")

    graph.connect("Богота", "Майами")
    graph.connect("Богота", "Мехико")
    graph.connect("Богота", "Лима")
    graph.connect("Богота", "Буэнос-Айрес")
    graph.connect("Богота", "Сан-Паулу")

    graph.connect("Лима", "Мехико")
    graph.connect("Лима", "Богота")
    graph.connect("Лима", "Сантьяго")

    graph.connect("Сантьяго", "Лима")

    graph.connect("Буэнос-Айрес", "Богота")
    graph.connect("Буэнос-Айрес", "Сан-Паулу")

    graph.connect("Сан-Паулу", "Буэнос-Айрес")
    graph.connect("Сан-Паулу", "Богота")
    graph.connect("Сан-Паулу", "Мадрид")
    graph.connect("Сан-Паулу", "Лагос")

    graph.connect("Лагос", "Сан-Паулу")
    graph.connect("Лагос", "Киншаса")
    graph.connect("Лагос", "Хартум")

    graph.connect("Киншаса", "Лагос")
    graph.connect("Киншаса", "Йоханнесбург")
    graph.connect("Киншаса", "Хартум")

    graph.connect("Йоханнесбург", "Киншаса")
    graph.connect("Йоханнесбург", "Хартум")

    graph.connect("Хартум", "Лагос")
    graph.connect("Хартум", "Киншаса")
    graph.connect("Хартум", "Йоханнесбург")
    graph.connect("Хартум", "Каир")

    # Чёрные города
    graph.connect("Алжир", "Париж")
    graph.connect("Алжир", "Мадрид")
    graph.connect("Алжир", "Каир")
    graph.connect("Алжир", "Стамбул")

    graph.connect("Стамбул", "Алжир")
    graph.connect("Стамбул", "Милан")
    graph.connect("Стамбул", "Москва")
    graph.connect("Стамбул", "Санкт-Петербург")
    graph.connect("Стамбул", "Багдад")
    graph.connect("Стамбул", "Каир")

    graph.connect("Москва", "Санкт-Петербург")
    graph.connect("Москва", "Стамбул")
    graph.connect("Москва", "Тегеран")

    graph.connect("Каир", "Алжир")
    graph.connect("Каир", "Стамбул")
    graph.connect("Каир", "Хартум")
    graph.connect("Каир", "Эр-Рияд")
    graph.connect("Каир", "Багдад")

    graph.connect("Багдад", "Стамбул")
    graph.connect("Багдад", "Каир")
    graph.connect("Багдад", "Тегеран")
    graph.connect("Багдад", "Карачи")
    graph.connect("Багдад", "Эр-Рияд")

    graph.connect("Тегеран", "Москва")
    graph.connect("Тегеран", "Багдад")
    graph.connect("Тегеран", "Карачи")
    graph.connect("Тегеран", "Дели")

    graph.connect("Эр-Рияд", "Каир")
    graph.connect("Эр-Рияд", "Багдад")
    graph.connect("Эр-Рияд", "Карачи")

    graph.connect("Карачи", "Эр-Рияд")
    graph.connect("Карачи", "Багдад")
    graph.connect("Карачи", "Тегеран")
    graph.connect("Карачи", "Дели")
    graph.connect("Карачи", "Мумбаи")

    graph.connect("Дели", "Тегеран")
    graph.connect("Дели", "Карачи")
    graph.connect("Дели", "Мумбаи")
    graph.connect("Дели", "Ченнаи")
    graph.connect("Дели", "Калькутта")

    graph.connect("Мумбаи", "Карачи")
    graph.connect("Мумбаи", "Дели")
    graph.connect("Мумбаи", "Ченнаи")

    graph.connect("Ченнаи", "Мумбаи")
    graph.connect("Ченнаи", "Дели")
    graph.connect("Ченнаи", "Калькутта")
    graph.connect("Ченнаи", "Джакарта")
    graph.connect("Ченнаи", "Бангкок")

    graph.connect("Калькутта", "Дели")
    graph.connect("Калькутта", "Ченнаи")
    graph.connect("Калькутта", "Бангкок")
    graph.connect("Калькутта", "Гонконг")

    # Красные города
    graph.connect("Бангкок", "Ченнаи")
    graph.connect("Бангкок", "Калькутта")
    graph.connect("Бангкок", "Гонконг")
    graph.connect("Бангкок", "Хошимин")
    graph.connect("Бангкок", "Джакарта")

    graph.connect("Джакарта", "Ченнаи")
    graph.connect("Джакарта", "Бангкок")
    graph.connect("Джакарта", "Хошимин")
    graph.connect("Джакарта", "Сидней")

    graph.connect("Хошимин", "Бангкок")
    graph.connect("Хошимин", "Джакарта")
    graph.connect("Хошимин", "Гонконг")
    graph.connect("Хошимин", "Манила")

    graph.connect("Гонконг", "Калькутта")
    graph.connect("Гонконг", "Бангкок")
    graph.connect("Гонконг", "Хошимин")
    graph.connect("Гонконг", "Манила")
    graph.connect("Гонконг", "Тайбэй")
    graph.connect("Гонконг", "Шанхай")

    graph.connect("Шанхай", "Пекин")
    graph.connect("Шанхай", "Сеул")
    graph.connect("Шанхай", "Тайбэй")
    graph.connect("Шанхай", "Гонконг")

    graph.connect("Пекин", "Шанхай")
    graph.connect("Пекин", "Сеул")

    graph.connect("Сеул", "Пекин")
    graph.connect("Сеул", "Шанхай")
    graph.connect("Сеул", "Токио")

    graph.connect("Токио", "Сеул")
    graph.connect("Токио", "Осака")
    graph.connect("Токио", "Тайбэй")
    graph.connect("Токио", "Сан-Франциско")

    graph.connect("Осака", "Токио")
    graph.connect("Осака", "Тайбэй")

    graph.connect("Тайбэй", "Осака")
    graph.connect("Тайбэй", "Токио")
    graph.connect("Тайбэй", "Шанхай")
    graph.connect("Тайбэй", "Гонконг")
    graph.connect("Тайбэй", "Манила")

    graph.connect("Манила", "Тайбэй")
    graph.connect("Манила", "Гонконг")
    graph.connect("Манила", "Хошимин")
    graph.connect("Манила", "Сидней")
    graph.connect("Манила", "Сан-Франциско")

    graph.connect("Сидней", "Манила")
    graph.connect("Сидней", "Джакарта")
    graph.connect("Сидней", "Лос-Анджелес")

    return graph