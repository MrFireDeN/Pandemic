from abc import ABC, abstractmethod


class Observer(ABC):
    @abstractmethod
    def update(self, message):
        pass

class Subject(ABC):
    @abstractmethod
    def add_observer(self, observer: Observer):
        pass

    @abstractmethod
    def remove_observer(self, observer: Observer):
        pass

    @abstractmethod
    def notify_observers(self, message):
        pass


from data.cities import CityGame, CityGraph
from data.players import PlayerGame
from data.decks import CardGame, DeckCards, DeckDiseases
from data.boards import Board
from data.enums import *


class PandemicGame(Subject):
    def __init__(self, code=None):
        from data.repo import GameRepository
        
        self.code = code
        self.phase = "waiting"
        self.difficult = Difficult.easy
        
        self.board = Board(self)
        self.players = []
        self.cities = GameRepository.initialize_cities(self)
        self.deck_cards, self.deck_diseases = GameRepository.initialize_decks(self)

        self._observers = []
        
    def add_player(self, player_id, name, role_id):
        pg = PlayerGame(
            game=self,
            player_id=player_id,
            name=name,
            role_id=role_id,
            pos=self.cities.get_start_city()
        )

        self.players.append(pg)

        return pg

    def start_game(self):
        """
        Запускает игровую сессию Pandemic.
    
        Метод выполняет полный начальный цикл подготовки игры и переводит её
        из состояния ожидания в активную фазу.
    
        Последовательность действий:
        
        1. Выполняет валидацию возможности старта игры:
        
           - количество игроков должно быть от 2 до 4;
           - игровое поле и колода карт должны быть инициализированы.
    
        2. Определяет количество карт, выдаваемых каждому игроку,
           согласно правилам Pandemic:
           
           - 2 игрока -> 4 карты
           - 3 игрока -> 3 карты
           - 4 игрока -> 2 карты
    
        3. Определяет стартовый город и строит в нём исследовательскую станцию.
    
        4. Размещает всех игроков в стартовом городе.
    
        5. Раздаёт стартовые карты игрокам:
        
           - карты извлекаются из колоды;
           - каждая карта хранит ссылку на своего владельца (PlayerGame);
           - игроки не хранят у себя списки карт напрямую.
    
        6. Определяет очередность хода:
        
           - первый ход получает игрок, у которого на руках карта города с наибольшим населением;
           - порядок вычисляется относительно списка self.players.
    
        7. Переводит игру в фазу "playing", уведомляет наблюдателей
           о начале игры и сохраняет состояние.
    
        :return: ``dict`` — словарь с HTTP-статусом и сообщением.
        """
        # 1) Валидация ДО сайд-эффектов
        players_count = len(self.players)
        
        if players_count < 2:
            return {"status": 401, "message": "Players not enough"}

        if players_count > 4:
            return {"status": 401, "message": "Too many players"}


        if not self.cities or not self.deck_cards:
            return {"status": 500, "message": "Game not initialized (cities/decks missing)"}

        # 2) Правило раздачи (Pandemic)
        cards_for_player_map = {2: 4, 3: 3, 4: 2}
        cards_for_player = cards_for_player_map[players_count]

        # 3) Стартовая инфраструктура
        start_city = self.cities.get_start_city()
        self.cities.build_research_station(start_city.name)

        # 4) Расставить игроков
        for player in self.players:
            player.pos = start_city

            # 5) Раздать карты: карты знают owner, игроки не знают карты
            for _ in range(cards_for_player):
                card = self.deck_cards.draw()
                card.player_owner = player

        # 6) Очередность хода: ходит тот у кого на руках карта города с наибольшим населением
        max_population = 0
        turn_order = 0
        
        for card in self.deck_cards.draw_pile:
            player = card.player_owner
            
            if player is None:
                continue
                
            if not card.is_city():
                continue
            
            city = self.cities.get_city_by_name(card.name)
            if city is None:
                continue
        
            population = city.population
            if population > max_population:
                max_population = population
                turn_order = self.players.index(card.player_owner)
                        
        self.board.turn_order = turn_order

        # 7) Фаза и нотификация — только после успешной подготовки
        self.phase = "active"
        self.notify_observers({"event": "game_started", "phase": self.phase})
        
        self.__save()
        return {"status": 200, "message": "Game started successfully"}

    def move_player(self, player_id: int, to_city: str, use_card: CardGame | None = None):
        player = self.__search_player(player_id)
        if player is None:
            return {"status": 401, "message": "Player not found"}

        city = self.cities.get_city_by_name(to_city)
        if city is None:
            return {"status": 402, "message": "City not found"}

        player.move_to(city, use_card)
        
        self.notify_observers({"event": "player_moved", "player_id": player_id, "new_city": to_city})
        self.__save()
        
        return {"status": 200, "message": "Player moved successfully"}

    def cure_city_player(self, player_id: int, city_name: str, color: ColorType):
        player = self.__search_player(player_id)
        if player is None:
            return {"status": 401, "message": "Player not found"}

        city = self.cities.get_city_by_name(city_name)
        if city is None:
            return {"status": 402, "message": "City not found"}

        player.cure_city(city, color)
        
        self.notify_observers({"event": "city_cured", "player_id": player_id, "city": city_name, "color": color})
        self.__save()
        
        return {"status": 200, "message": "City cured successfully"}

    def use_event_player(self, player_id: int, card: CardGame):
        player = self.__search_player(player_id)
        if player is None:
            return {"status": 401, "message": "Player not found"}

        player.use_card(card)
        
        self.notify_observers({"event": "event_used", "player_id": player_id, "card": card})
        self.__save()
        
        return {"status": 200, "message": "Event used successfully"}

    def build_research_station_player(self, player_id: int, city_name: str, card: CardGame):
        player = self.__search_player(player_id)
        if player is None:
            return {"status": 401, "message": "Player not found"}

        city = self.cities.get_city_by_name(city_name)
        if city is None:
            return {"status": 402, "message": "City not found"}

        player.build_research_station(city, card)
        
        self.notify_observers({"event": "research_station_built", "player_id": player_id, "city": city_name})
        self.__save()
        
        return {"status": 200, "message": "Research station built successfully"}

    def trade_card_player(self, from_player_id: int, to_player_id: int, card: CardGame):
        from_player = self.__search_player(from_player_id)
        to_player = self.__search_player(to_player_id)

        if from_player is None or to_player is None:
            return {"status": 401, "message": "Player not found"}

        from_player.trade_card(card, to_player)
        
        self.notify_observers({"event": "card_traded", "from_player_id": from_player_id, "to_player_id": to_player_id, "card": card})
        self.__save()
        
        return {"status": 200, "message": "Card traded successfully"}

    def discover_cure_player(self, player_id: int, color: ColorType, cards: list[CardGame]):
        player = self.__search_player(player_id)
        if player is None:
            return {"status": 401, "message": "Player not found"}

        player.discover_cure(color, cards)
        
        self.notify_observers({"event": "cure_discovered", "player_id": player_id, "color": color, "cards_used": cards})
        self.__save()
        
        return {"status": 200, "message": "Cure discovered successfully"}

    def notify_player_moved(self):
        self.notify_observers({"event": "player_moved"})

    def notify_turn_ended(self):
        """
        Завершает ход текущего игрока и выполняет полный цикл фаз конца хода.
    
        Метод реализует стандартную последовательность хода Pandemic:
    
        1. Фаза добора карт игроком:
        
           - текущий игрок берёт две карты из колоды игроков;
           - если вытянута карта эпидемии:
           
             - карта отправляется в сброс;
             - запускается обработка эпидемии;
           - обычные карты закрепляются за игроком как владельцем.
    
        2. Фаза заражения:
        
           - определяется количество карт инфекции в зависимости
             от индикатора заражения;
           - соответствующее количество карт берётся из колоды инфекций;
           - каждая карта инфекции:
           
             - отправляется в сброс колоды инфекций;
             - вызывает заражение соответствующего города.
    
        3. Проверка состояния завершения игры:
        
           - проверка выполняется после критических этапов хода
             (эпидемии, заражения).
    
        4. Передача хода следующему игроку:
        
           - порядок хода циклический относительно списка игроков.
    
        5. Уведомление наблюдателей о завершении хода
           и сохранение состояния игры.
    
        :return:
            dict — результат выполнения хода. HTTP-статус и сообщение.
        """
        current_player = self.players[self.board.turn_order]

        # 1) Добор карт игроком
        for _ in range(2):
            card = self.deck_cards.draw()
    
            if card.is_epidemic():
                card.player_owner = None
                self.deck_cards.discard(card)
    
                self.board.trigger_epidemic()
    
                if self.board.is_game_over:
                    self.__save()
                    return {"status": 200, "message": "Game over"}
            else:
                card.player_owner = current_player
    
        if self.board.is_game_over:
            self.__save()
            return {"status": 200, "message": "Game over"}
        
        self.notify_player_drew_cards()
    
        # 2) Фаза заражения
        diseases_count = self.board.diseases_count_by_infection_indicator()
    
        for _ in range(diseases_count):
            card = self.deck_diseases.draw()
    
            if not card.is_city():
                return {"status": 400, "message": "Infection card is not a city"}
    
            city = self.cities.get_city_by_name(card.name)
            if city is None:
                return {"status": 400, "message": f"City not found: {card.name}"}
    
            city.add_infection(city.color, 1)
    
            self.deck_diseases.discard(card)
    
            if self.board.is_game_over:
                self.__save()
                return {"status": 200, "message": "Game over"}
        
        self.notify_disease_spread()
    
        # 3) Следующий игрок
        player_count = len(self.players)
        self.board.turn_order = (self.board.turn_order + 1) % player_count
    
        if self.board.is_game_over:
            self.__save()
            return {"status": 200, "message": "Game over"}
    
        self.notify_observers({"event": "turn_ended", "turn_order": self.board.turn_order})
        self.__save()
    
        return {"status": 200, "message": "Turn ended successfully"}
        
    def notify_player_drew_cards(self):
        self.notify_observers({"event": "player_drew_cards"})

    def notify_disease_spread(self):
        self.notify_observers({"event": "disease_spread"})

    def notify_epidemic(self):
        self.notify_observers({"event": "epidemic"})

    def notify_outbreak(self):
        self.notify_observers({"event": "outbreak"})

    def notify_disease_cured(self):
        self.notify_observers({"event": "disease_cured"})

    def notify_game_over(self, is_victory=False):
        self.notify_observers({"event": "game_over", "victory": is_victory})

    def add_observer(self, observer: Observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer: Observer):
        if observer in self._observers:
            self._observers.remove(observer)

    def notify_observers(self, message):
        for observer in self._observers:
            observer.update(message)

    def __search_player(self, player_id: int) -> PlayerGame | None:
        for player in self.players:
            if player.id == player_id:
                return player
        return None

    def __save(self):
        from data.repo import GameRepository
        
        GameRepository.save_game(self)


class Sessions:
    _instance = None
    
    def __init__(self):
        self.sessions: list[PandemicGame] = []

    def add_session(self, session: PandemicGame):
        self.sessions.append(session)

    def create_session(self, code: str) -> PandemicGame:
        session = PandemicGame(code=code)
        self.add_session(session)
        return session

    def remove_session(self, session: PandemicGame):
        self.sessions.remove(session)

    def get_session(self, code) -> PandemicGame | None:
        for session in self.sessions:
            if session.code == code:
                return session
        return None

    @staticmethod
    def get_instance():
        if Sessions._instance is None:
            Sessions._instance = Sessions()
        return Sessions._instance


SESSIONS = Sessions()
