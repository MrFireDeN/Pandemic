from __future__ import annotations

import json
from typing import TYPE_CHECKING

from sympy.codegen.ast import continue_

from data.enums import ColorType

if TYPE_CHECKING:
    from data.cities import CityGame, CityGraph
    from data.decks import CardGame, DeckCards, DeckDiseases
    from data.players import PlayerGame

class Board:
    def __init__(self, game):
        """
        Board — состояние игровой партии.
        """
        self.game = game
        self.code = game.code

        self.turn_order: int = 0
        
        self.outbreak_indicator: int = 0
        self.infection_indicator: int = 0
        
        self.cubes_per_color = {color: 24 for color in ColorType}
        self.vaccines_state = {color: 0 for color in ColorType}

        self.is_game_over = False

    def add_outbreak(self):
        """Увеличивает счётчик вспышек."""
        self.outbreak_indicator += 1
        
        self.game.notify_outbreak()
        
        if self.outbreak_indicator >= 8:
            self.trigger_game_over()

    def trigger_epidemic(self):
        """
        Обрабатывает событие эпидемии согласно правилам Pandemic.
    
        Метод реализует полный цикл эпидемии и выполняет следующие этапы:
    
        1. Увеличивает индикатор заражения.
    
        2. Фаза инфицирования:
        
           - извлекает нижнюю карту из колоды инфекций;
           - если игра уже завершена или карта отсутствует, выполнение прекращается;
           - находит соответствующий город и добавляет в него
             три куба инфекции соответствующего цвета;
           - отправляет карту инфекции в сброс.
    
        3. Фаза обострения:
        
           - возвращает все карты из сброса колоды инфекций
             наверх колоды (с последующим перемешиванием,
             если это предусмотрено реализацией).
    
        Метод не возвращает значения и может досрочно завершаться,
        если в процессе эпидемии игра переходит в состояние завершения.
    
        :return: None
        """
        # 1) Распространение
        self.infection_indicator += 1
        
        # 2) Инфицирование 
        diseases_card = self.game.deck_diseases.draw_last()
        if self.is_game_over or diseases_card is None:
            return 
            
        city = self.game.cities.get_city_by_name(diseases_card.name)
        
        color = city.color
        if self.vaccines_state[color] != 2:
            city.add_infection(color, 3)
        
        self.game.deck_diseases.distract(diseases_card)
        
        if self.is_game_over:
            return
        
        # 3) Обострение
        self.game.deck_diseases.return_discard_on_top()
        
        self.game.notify_epidemic()

    def use_cube(self, color: ColorType, count: int = 1):
        """
        Использует кубики для болезни определенного цвета.
        
        :param color: Цвет болезни.
        :param count: Количество кубиков для использования.
        """
        if self.cubes_per_color[color] >= count:
            self.cubes_per_color[color] -= count
            print(f"Использовано {count} кубиков цвета {color.name}. Осталось: {self.cubes_per_color[color]}")
        else:
            self.trigger_game_over()

    def return_cube(self, color: ColorType, count: int = 1):
        """
        Возвращает кубики обратно в запасы.
        
        :param color: Цвет болезни.
        :param count: Количество кубиков для возврата.
        """
        self.cubes_per_color[color] += count
        print(f"Возвращено {count} кубиков цвета {color.name}. Осталось: {self.cubes_per_color[color]}")
        
        if self.cubes_per_color[color] >= 24 and self.vaccines_state[color] == 1:
            self.cure_upgraded(color)

    def cure_discovered(self, color: ColorType):
        """
        Открытие лекарства от болезни определенного цвета.
        
        :param color: Цвет болезни.
        """
        self.vaccines_state[color] = 1
        print(f"Лекарство для {color.name} создано!")

    def cure_upgraded(self, color: ColorType):
        """
        Лекарство от болезни определенного цвета уничтожает болезнь.
        
        :param color: Цвет болезни.
        """
        self.vaccines_state[color] = 2
        print(f"Лекарство для {color.name} улучшено и болезнь уничтожена!")

    def trigger_game_over(self, is_victory=False):
        """
        Завершается игра и уведомляется об этом всех участников.
        
        :param is_victory: Если True, игра завершена победой, если False — поражением.
        """
        self.is_game_over = True
    
        result = "Победа" if is_victory else "Поражение"
        print(f"Игра завершена: {result}")
    
        self.game.notify_game_over(is_victory)

    def diseases_count_by_infection_indicator(self) -> int:
        """
        Возвращает количество карт инфекции,
        которое необходимо взять в текущий ход.
        
        :return: Количество карт инфекции.
        """
        if self.outbreak_indicator < 3:
            return 2
        elif self.outbreak_indicator < 5:
            return 3
        return 4
