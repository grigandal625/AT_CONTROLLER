from enum import Enum, EnumMeta

class STATES_META(EnumMeta):
    
    @property
    def states(self):
        return [state.name for state in self]
    
    @property
    def translations(self):
        return [state.value for state in self]


class STATES(Enum, metaclass=STATES_META):
    UNAUTHORIZED = 'Начальное состояние\n(Экран авторизации обучаемого)'
    AUTHORIZED_INITIAL = 'Авторизован обучаемый\nбез прогресса'
    AUTHORIZED_SELECTING = 'Авторизован обучаемый\nс прогрессом'
    WORK1 = 'Приветственный экран\nработы 1'
    CREATE_EMPTY_KB = 'Экран редактора темпоральной БЗ\nсоздание нового фрагмента БЗ'
    LOAD_KB = 'Экран редактора темпоральной БЗ\nзагрузка готового фрагмента БЗ'
    BUILD_TYPES = 'Экран редактора темпоральной БЗ\nПостроение типов'
    BUILD_BASIC_OBJECTS = 'Экран редактора темпоральной БЗ\nпостроение базовых объектов'
    BUILD_INTERVALS = 'Экран редактора темпоральной БЗ\nпостроение интервалов'
    BUILD_EVENTS = 'Экран редактора темпоральной БЗ\nпостроение событий'
    BUILD_RULES = 'Экран редактора темпоральной БЗ\nпостроение правил (базовых и темпоральных)'
    WORK1_COMPLETED_KNOWN_KB = 'Экран подтверждения\nиспользования данного файла БЗ'
    WORK1_COMPLETED_UNKNOWN_KB = 'Экран выбора файла БЗ'
    FINISH_WORK1 = 'Работа 1 завершена,\nотображение результатов'
    WORK2 = 'Приветственный экрана\nработы 2'
    CREATE_EMPTY_SM = 'Экран модуля синтеза ИМ\nСоздание файла ИМ'
    LOAD_SM = 'Экран модуля синтеза ИМ\nЗагрузка готового файла ИМ'
    DEFINE_RESOURCE_TYPES = 'Экран модуля синтеза ИМ\nОпределение типов ресурсов и их параметров'
    BUILD_RESOURCES = 'Экран модуля синтеза ИМ\nПостроение ресурсов'
    DEFINE_EVENTS_AND_LAWS = 'Экран модуля синтеза ИМ\nОпределение событий и законов функционирования ИМ (образцы операций)'
    BUILD_OPERATIONS = 'Экран модуля синтеза ИМ\nПостроение операций'
    BUILD_FUNCTIONS = 'Экран модуля синтеза ИМ\nПостроение функций'
    BUILD_COMPLETED_KNOWN_SM = 'Экран подтверждения\nиспользования данного файла ИМ'
    BUILD_COMPLETED_UNKNOWN_SM = 'Экран выбора файла ИМ'
    FINISH_BUILD_SM = 'Построение ИМ на языке РДО-АТ завершено,\nподготовка к трансляции'
    TRANSLATION = 'Экран транслятора ИМ\nОписание ИМ на языке РДО-АТ загружено'
    SUCCESS_TRANSLATION = 'Экран транслятора ИМ\nВсе этапы трансляции пройдены успешно'
    LEX_ERROR = 'Экран транслятора ИМ\nОбнаружены ошибки при лексическом анализе'
    SYNTAX_ERROR = 'Экран транслятора ИМ\nОбнаружены ошибки при синтаксическом анализе'
    SEMANTIC_ERROR = 'Экран транслятора ИМ\nОбнаружены ошибки при семантическом анализе'
    COMPILATION_ERROR = 'Экран транслятора ИМ\nОбнаружены ошибки при компиляции ИМ'
    SIMULATION_EXPERIMENT = 'Экран компонента\nподдержкри рассчета состояний ИМ\nНастройка конфигурации ИМ'
    SIMULATION_COMPLETED = 'Экран компонента\nподдержкри рассчета состояний ИМ\nРезультаты прогона ИМ'
    FINISH_WORK2 = 'Работа 2 завершена,\nотображение результатов'
    WORK3 = 'Приветственный экран\nработы 3'
    CONFIGURE_PROTOTYPE = 'Экран конфигуратора прототипа\nНастройка минимальной конфигурации\nбазовых компонентов'
    LAUNCH_FUNCTIONING = 'Экран компонента отладки совместного функционирования\nЗапуск совместного функционирования\nс показом деталей'
    FINISHED = 'Работа 3 завершена,\nотображение результатов'


class TRANSITIONS_META(EnumMeta):
    
    @property
    def transitions(self):
        return [{'trigger': transition.name, 'source': transition.value[0][0].name, 'dest': transition.value[0][1].name} for transition in self]

    @property
    def translations(self):
        return [{'trigger': transition.value[1], 'source': transition.value[0][0].value, 'dest': transition.value[0][1].value} for transition in self]
    

class TRANSITIONS(Enum, metaclass=TRANSITIONS_META):
    AUTHORIZE_INIT = (STATES.UNAUTHORIZED, STATES.AUTHORIZED_INITIAL), 'Обучаемый аворизуется, прогресса выполнения не обнаружено'
    AUTHORIZE_SELECT = (STATES.UNAUTHORIZED, STATES.AUTHORIZED_SELECTING), 'Обучаемый аворизуется, прогресс выполнения обнаружен'
    START_WORK1 = (STATES.AUTHORIZED_INITIAL, STATES.WORK1), 'Обучаемый начинает работу'
    START_SELECTED_WORK1 = (STATES.AUTHORIZED_SELECTING, STATES.WORK1), 'Обучаемый выбирает начало работы 1'
    START_SELECTED_WORK1_CREATE_EMPTY_KB = (STATES.AUTHORIZED_SELECTING, STATES.CREATE_EMPTY_KB), 'Обучаемый выбирает создание нового фрагмента БЗ'
    START_SELECTED_WORK1_LOAD_KB = (STATES.AUTHORIZED_SELECTING, STATES.LOAD_KB), 'Обучаемый выбирает загрузку имеющегося фрагмента БЗ'
    START_SELECTED_WORK2 = (STATES.AUTHORIZED_SELECTING, STATES.WORK2), 'Обучаемый выбирает начало работы 2'
    START_SELECTED_WORK2_CREATE_EMPTY_SM = (STATES.AUTHORIZED_SELECTING, STATES.CREATE_EMPTY_SM), 'Обучаемый выбирает создание нового файла ИМ'
    START_SELECTED_WORK2_LOAD_SM = (STATES.AUTHORIZED_SELECTING, STATES.LOAD_SM), 'Обучаемый выбирает загрузку имеющегося файла ИМ'
    START_SELECTING_WORK3 = (STATES.AUTHORIZED_SELECTING, STATES.WORK3), 'Обучаемый выбирает начало работы 3'
    START_SELECTING_WORK3_CONFIGURE_PROTOTYPE = (STATES.AUTHORIZED_SELECTING, STATES.CONFIGURE_PROTOTYPE), 'Обучаемый выбирает редактирование конфигурации прототипа'
    START_SELECTING_WORK3_LAUNCH_FUNCTIONING = (STATES.AUTHORIZED_SELECTING, STATES.LAUNCH_FUNCTIONING), 'Обучаемый выбирает запуск совместного функционирования'
    CREATE_KB = (STATES.WORK1, STATES.CREATE_EMPTY_KB), 'Обучаемый переходит к созданию нового фрагмента БЗ'
    LOAD_READY_KB = (STATES.WORK1, STATES.LOAD_KB), 'Обучаемый переходит к загрузке имеющегося фрагмента БЗ'
    BUILD_TYPES = (STATES.CREATE_EMPTY_KB, STATES.BUILD_TYPES), 'Обучаемый переходит к построениею типов'
    BUILD_BASIC_OBJECTS = (STATES.BUILD_TYPES, STATES.BUILD_BASIC_OBJECTS), 'Обучаемый переходит к построению базовых объектов'
    BUILD_INTERVALS = (STATES.BUILD_BASIC_OBJECTS, STATES.BUILD_INTERVALS), 'Обучаемый переходит к построению интервалов'
    BUILD_EVENTS = (STATES.BUILD_BASIC_OBJECTS, STATES.BUILD_EVENTS), 'Обучаемый переходит к построению событий'
    BUILD_RULES = (STATES.BUILD_INTERVALS, STATES.BUILD_RULES), 'Обучаемый переходит к построению правил'
    BUILD_RULES_2 = (STATES.BUILD_EVENTS, STATES.BUILD_RULES), 'Обучаемый переходит к построению правил (2)'
    FROM_INTERVALS_TO_EVENTS = (STATES.BUILD_INTERVALS, STATES.BUILD_EVENTS), 'Обучаемый переходит к построению событий (2)'
    FROM_EVENTS_TO_INTERVALS = (STATES.BUILD_EVENTS, STATES.BUILD_INTERVALS), 'Обучаемый переходит к построению интервалов (2)'
    LOAD_KB_BUILD_TYPES = (STATES.LOAD_KB, STATES.BUILD_TYPES), 'Обучаемый переходит к редактированию типов'
    LOAD_KB_BUILD_BASIC_OBJECTS = (STATES.LOAD_KB, STATES.BUILD_BASIC_OBJECTS), 'Обучаемый переходит к редактированию объектов'
    LOAD_KB_BUILD_INTERVALS = (STATES.LOAD_KB, STATES.BUILD_INTERVALS), 'Обучаемый переходит к редактированию интервалов'
    LOAD_KB_BUILD_EVENTS = (STATES.LOAD_KB, STATES.BUILD_EVENTS), 'Обучаемый переходит к редактированию событий'
    LOAD_KB_BUILD_RULES = (STATES.LOAD_KB, STATES.BUILD_RULES), 'Обучаемый переходит к редактированию правил'
    FROM_BASIC_OBJECTS_TO_TYPES = (STATES.BUILD_BASIC_OBJECTS, STATES.BUILD_TYPES), 'Обучаемый возвращается к редактированию типов'
    FROM_INTERVALS_TO_BASIC_OBJECTS = (STATES.BUILD_INTERVALS, STATES.BUILD_BASIC_OBJECTS), 'Обучаемый возвращается к редактированию базовых объектов'
    FROM_EVENTS_TO_BASIC_OBJECTS = (STATES.BUILD_EVENTS, STATES.BUILD_BASIC_OBJECTS), 'Обучаемый возвращается к редактированию базовых объектов (2)'
    FROM_RULES_TO_INTERVALS = (STATES.BUILD_RULES, STATES.BUILD_INTERVALS), 'Обучаемый возвращается к редактированию интервалов'
    FROM_RULES_TO_EVENTS = (STATES.BUILD_RULES, STATES.BUILD_EVENTS), 'Обучаемый возвращается к редактированию событий'
    COMPLETE_WORK1_WITH_KNOWN_KB = (STATES.BUILD_RULES, STATES.WORK1_COMPLETED_KNOWN_KB), 'Обучаемый завершает построение фрагмента БЗ, файл удалось зафиксировать'
    COMPLETE_WORK1_WITH_UNKNOWN_KB = (STATES.BUILD_RULES, STATES.WORK1_COMPLETED_UNKNOWN_KB), 'Обучаемый завершает построение фрагмента БЗ, закрыв окно редактирования, из-за чего файл не удалось зафиксировать'
    ERROR_FOUND_KNOWN_KB = (STATES.WORK1_COMPLETED_KNOWN_KB, STATES.WORK1_COMPLETED_UNKNOWN_KB), 'Обучаемый принял решение использовать фрагмент, отличающийся от зафиксированного'
    FINISH_WORK2_FROM_KNOWN_KB = (STATES.WORK1_COMPLETED_KNOWN_KB, STATES.FINISH_WORK1), 'Обучаемый подтверждает использование зафиксированного фрагмента БЗ, завершает работу 1'
    FINISH_WORK2_FROM_UNKNOWN_KB = (STATES.WORK1_COMPLETED_UNKNOWN_KB, STATES.FINISH_WORK1), 'Обучаемый выбирает фрагмент БЗ для дальнейшего использования, завершает работу 1'
    START_WORK2 = (STATES.FINISH_WORK1, STATES.WORK2), 'Обучаемый начинает работу 2'
    CREATE_SM = (STATES.WORK2, STATES.CREATE_EMPTY_SM), 'Обучаемый переходит к созданию нового описания ИМ'
    LOAD_READY_SM = (STATES.WORK2, STATES.LOAD_SM), 'Обучаемый переходит к загрузке имеющегося описания ИМ'
    DEFINE_RESOURCE_TYPES = (STATES.CREATE_EMPTY_SM, STATES.DEFINE_RESOURCE_TYPES), 'Обучаемый переходит к построению типов ресурсов'
    BUILD_RESOURCES = (STATES.DEFINE_RESOURCE_TYPES, STATES.BUILD_RESOURCES), 'Обучаемый переходит к построению ресурсов'
    BUILD_FUNCTIONS = (STATES.BUILD_RESOURCES, STATES.BUILD_FUNCTIONS), 'Обучаемый переходит к построению функций'
    DEFINE_EVENTS_AND_LAWS = (STATES.BUILD_RESOURCES, STATES.DEFINE_EVENTS_AND_LAWS), 'Обучаемый переходит к построению образцов операций'
    DEFINE_EVENTS_AND_LAWS_2 = (STATES.BUILD_FUNCTIONS, STATES.DEFINE_EVENTS_AND_LAWS), 'Обучаемый переходит к построению образцов операций (2)'
    BUILD_OPERATIONS = (STATES.DEFINE_EVENTS_AND_LAWS, STATES.BUILD_OPERATIONS), 'Обучаемый переходит к построению операций'
    LOAD_SM_DEFINE_RESOURCE_TYPES = (STATES.LOAD_SM, STATES.DEFINE_RESOURCE_TYPES), 'Обучаемый переходит к редактированию типов ресурсов'
    LOAD_SM_BUILD_RESOURCES = (STATES.LOAD_SM, STATES.BUILD_RESOURCES), 'Обучаемый переходит к редактированию ресурсов'
    LOAD_SM_DEFINE_EVENTS_AND_LAWS = (STATES.LOAD_SM, STATES.DEFINE_EVENTS_AND_LAWS), 'Обучаемый переходит к редактированию образцов операций'
    LOAD_SM_BUILD_OPERATIONS = (STATES.LOAD_SM, STATES.BUILD_OPERATIONS), 'Обучаемый переходит к редактированию операций'
    LOAD_SM_BUILD_FUNCTIONS = (STATES.LOAD_SM, STATES.BUILD_FUNCTIONS), 'Обучаемый переходит к редактированию функций'
    FROM_RESOURCES_TO_DEFINE_RESOURCE_TYPES = (STATES.BUILD_RESOURCES, STATES.DEFINE_RESOURCE_TYPES), 'Обучаемый возвращается к редактированию типов ресурсов'
    FROM_FUNCTIONS_TO_BUILD_RESOURCES = (STATES.BUILD_FUNCTIONS, STATES.BUILD_RESOURCES), 'Обучаемый возвращается к редактированию ресурсов'
    FROM_FUNCTIONS_TO_DEFINE_RESOURCE_TYPES = (STATES.BUILD_FUNCTIONS, STATES.DEFINE_RESOURCE_TYPES), 'Обучаемый возвращается к редактированию типов ресурсов (2)'
    FROM_EVENTS_AND_LAWS_TO_BUILD_FUNCTIONS = (STATES.DEFINE_EVENTS_AND_LAWS, STATES.BUILD_FUNCTIONS), 'Обучаемый возвращается к редактированию функций'
    FROM_EVENTS_AND_LAWS_TO_DEFINE_RESOURCE_TYPES = (STATES.DEFINE_EVENTS_AND_LAWS, STATES.DEFINE_RESOURCE_TYPES), 'Обучаемый возвращается к редактированию типов ресурсов (3)'
    FROM_OPERATIONS_TO_DEFINE_EVENTS_AND_LAWS = (STATES.BUILD_OPERATIONS, STATES.DEFINE_EVENTS_AND_LAWS), 'Обучаемый возвращается к редактированию образцов операций'
    FROM_OPERATIONS_TO_BUILD_RESOURCES = (STATES.BUILD_OPERATIONS, STATES.BUILD_RESOURCES), 'Обучаемый возвращается к редактированию ресурсов (2)'
    COMPLETE_BUILD_WITH_KNOWN_SM = (STATES.BUILD_OPERATIONS, STATES.BUILD_COMPLETED_KNOWN_SM), 'Обучаемый завершает построение описания ИМ, файл удалось зафиксировать'
    COMPLETE_BUILD_WITH_UNKNOWN_SM = (STATES.BUILD_OPERATIONS, STATES.BUILD_COMPLETED_UNKNOWN_SM), 'Обучаемый завершает построение описания ИМ, закрыв окно редактирования, из-за чего файл не удалось зафиксировать'
    ERROR_FOUND_KNOWN_SM = (STATES.BUILD_COMPLETED_KNOWN_SM, STATES.BUILD_COMPLETED_UNKNOWN_SM), 'Обучаемый принял решение использовать файл ИМ, отличающийся от зафиксированного'
    FINISH_BUILD_FROM_KNOWN_SM = (STATES.BUILD_COMPLETED_KNOWN_SM, STATES.FINISH_BUILD_SM), 'Обучаемый подтверждает использование зафиксированного файла описания ИМ'
    FINISH_BUILD_FROM_UNKNOWN_SM = (STATES.BUILD_COMPLETED_UNKNOWN_SM, STATES.FINISH_BUILD_SM), 'Обучаемый выбирает файл описания ИМ для дальнейшего использования'
    START_TRANSLATION = (STATES.FINISH_BUILD_SM, STATES.TRANSLATION), 'Обучаемый переходит к трансляции'
    SUCCESSFUL_TRANSLATION = (STATES.TRANSLATION, STATES.SUCCESS_TRANSLATION), 'Обучаемый запустил трансляцию, все этапы выполнились без ошибок'
    LEXICAL_ERROR = (STATES.TRANSLATION, STATES.LEX_ERROR), 'Обучаемый запустил трансляцию, ошибки на этапе лексического анализа'
    SYNTAX_ERROR = (STATES.TRANSLATION, STATES.SYNTAX_ERROR), 'Обучаемый запустил трансляцию, ошибки на этапе синтаксического анализа'
    SEMANTIC_ERROR = (STATES.TRANSLATION, STATES.SEMANTIC_ERROR), 'Обучаемый запустил трансляцию, ошибки на этапе семантического анализа'
    COMPILATION_ERROR = (STATES.TRANSLATION, STATES.COMPILATION_ERROR), 'Обучаемый запустил трансляцию, ошибки на этапе компиляции'
    FIX_LEX = (STATES.LEX_ERROR, STATES.LOAD_SM), 'Обучаемый возвращается корректировать описание ИМ'
    FIX_SYNTAX = (STATES.SYNTAX_ERROR, STATES.LOAD_SM), 'Обучаемый возвращается корректировать описание ИМ (2)'
    FIX_SEMANTIC = (STATES.SEMANTIC_ERROR, STATES.LOAD_SM), 'Обучаемый возвращается корректировать описание ИМ (3)'
    FIX_COMPILATION = (STATES.COMPILATION_ERROR, STATES.LOAD_SM), 'Обучаемый возвращается корректировать описание ИМ (4)'
    START_EXPERIMENT = (STATES.SUCCESS_TRANSLATION, STATES.SIMULATION_EXPERIMENT), 'Обучаемый переходит к конфигурации параметров и расчету состояний ИМ'
    START_SIMULATION = (STATES.SIMULATION_EXPERIMENT, STATES.SIMULATION_COMPLETED), 'Обучаемый запустил прогон модели'
    REPEAT_SIMULATION = (STATES.SIMULATION_COMPLETED, STATES.SIMULATION_EXPERIMENT), 'Обучаемый возвращается к конфигурации параметров'
    FIX_MODEL = (STATES.SIMULATION_COMPLETED, STATES.LOAD_SM), 'Обучаемый возвращается модифицировать описание ИМ'
    COMPLETE_WORK2 = (STATES.SIMULATION_COMPLETED, STATES.FINISH_WORK2), 'Обучаемый завершает работу 2'
    START_WORK3 = (STATES.FINISH_WORK2, STATES.WORK3), 'Обучаемый начинает работу 3'
    CONFIGURE_PROTOTYPE = (STATES.WORK3, STATES.CONFIGURE_PROTOTYPE), 'Обучаемый переходит к конфигурированию базовых компонентов прототипа'
    LAUNCH_FUNCTIONING = (STATES.CONFIGURE_PROTOTYPE, STATES.LAUNCH_FUNCTIONING), 'Обучаемый запускает совместное функционирование'
    COMPLETE_WORK3 = (STATES.LAUNCH_FUNCTIONING, STATES.FINISHED), 'Обучаемый завершает работу 3'
    
    
def get_all_state_transitions(state):
    if isinstance(state, str):
        state = STATES[state]
        
    return [transition for transition in TRANSITIONS if state in transition.value[0]]


def get_triggering_transitions(state):
    if isinstance(state, str):
        state = STATES[state]
        
    return [transition for transition in TRANSITIONS if state == transition.value[0][0]]