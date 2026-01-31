from __future__ import annotations

from enum import Enum


class Language(Enum):
    ENGLISH_US = ("en-US", "English")
    ARABIC_SAUDI_ARABIA = ("ar-SA", "Arabic (Saudi Arabia)")
    BULGARIAN = ("bg-BG", "Bulgarian")
    CATALAN = ("ca-ES", "Catalan")
    CHINESE = ("zh-CN", "Chinese")
    CHINESE_HONG_KONG = ("zh-HK", "Chinese (Hong Kong)")
    CHINESE_TAIWAN = ("zh-TW", "Chinese (Taiwan)")
    CROATIAN = ("hr-HR", "Croatian")
    CZECH = ("cs-CZ", "Czech")
    DANISH = ("da-DK", "Danish")
    DUTCH = ("nl-NL", "Dutch")
    ENGLISH_AUSTRALIA = ("en-AU", "English (Australia)")
    ENGLISH_CANADA = ("en-CA", "English (Canada)")
    ENGLISH_UK = ("en-GB", "English (UK)")
    ESTONIAN = ("et-EE", "Estonian")
    FINNISH = ("fi-FI", "Finnish")
    FRENCH = ("fr-FR", "French")
    FRENCH_CANADA = ("fr-CA", "French (Canada)")
    GERMAN = ("de-DE", "German")
    GREEK = ("el-GR", "Greek")
    HEBREW = ("he-IL", "Hebrew")
    HINDI = ("hi-IN", "Hindi")
    HUNGARIAN = ("hu-HU", "Hungarian")
    INDONESIAN = ("id-ID", "Indonesian")
    ITALIAN = ("it-IT", "Italian")
    JAPANESE = ("ja-JP", "Japanase")
    KOREAN = ("ko-KR", "Korean")
    LATVIAN = ("lv-LV", "Latvian")
    LITHUANIAN = ("lt-LT", "Lithuanian")
    NORWEGIAN_BOKMAL = ("nb-NO", "Norwegian Bokmål")
    PERSIAN = ("fa-IR", "Persian")
    POLISH = ("pl-PL", "Polish")
    PORTUGUESE = ("pt-BR", "Portuguese")
    PORTUGUESE_PORTUGAL = ("pt-PT", "Portuguese (Portugal)")
    ROMANIAN = ("ro-RO", "Romanian")
    RUSSIAN = ("ru-RU", "Russian")
    SLOVAK = ("sk-SK", "Slovak")
    SPANISH_SPAIN = ("es-ES", "Spanish")
    SPANISH_MEXICO = ("es-MX", "Spanish (Mexico)")
    SWEDISH = ("sv-SE", "Swedish")
    THAI = ("th-TH", "Thai")
    TURKISH = ("tr-TR", "Turkish")
    UKRAINIAN = ("uk-UA", "Ukranian")
    VIETNAMESE = ("vi-VN", "Vietnamese")

    @staticmethod
    # Forward Reference used here in type hint
    def get_all() -> list[Language]:
        return list(Language)

    @staticmethod
    def get_from_str(candidate: str) -> Language:
        languages = Language.get_all()

        for language in languages:
            if candidate.lower() == language.get_display_name().lower():
                return language

        for language in languages:
            if candidate.lower() == language.get_value().lower():
                return language

        description = f"Language not supported: {candidate}"
        raise ValueError(description)

    @staticmethod
    def get_default() -> Language:
        return Language.ENGLISH_US

    def get_display_name(self) -> str:
        return self.value[1]

    def get_value(self) -> str:
        return self.value[0]
