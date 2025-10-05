"""All constants to be used are available here"""

from typing import List

ORIENTATION: List[str] = ['landscape', 'portrait', 'square']
"Desired photo orientation."

SIZE: List[str] = ['large', 'medium', 'small']
"Minimum photo size."

COLOR: List[str] = ['red', 'orange', 'yellow', 'green', 'turquoise', 'blue', 'violet', 'pink', 'brown', 'black', 'gray', 'white']
"Desired Photo color."

LOCALE_SUPPORTED: List[str] = [
    'en-US',
    'pt-BR',
    'es-ES',
    'ca-ES',
    'de-DE',
    'it-IT',
    'fr-FR',
    'sv-SE',
    'id-ID',
    'pl-PL', 
    'ja-JP',
    'zh-TW',
    'zh-CN',
    'ko-KR',
    'th-TH',
    'nl-NL',
    'hu-HU',
    'vi-VN',
    'cs-CZ',
    'da-DK',
    'fi-FI',
    'uk-UA',
    'el-GR',
    'ro-RO',
    'nb-NO',
    'sk-SK',
    'tr-TR',
    'ru-RU'
]
"The locale of the search you are performing."