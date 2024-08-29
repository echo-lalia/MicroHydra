'''
This module implements a lightweight internationalization class, 
which can be used to implement translations in MicroHydra.
'''

from .config import Config
import json


class I18n:
    """
    Internationalization class.

    args:
    - translations:
        A json string defining a list of dicts,
        where each dict is formatted like {'lang':'translation', }.
        Example:
        '''[
        {"en": "Loading...", "zh": "加载中...", "ja": "読み込み中..."},
        {"en": "Files", "zh": "文件", "ja": "ファイル"}
        ]'''

    """
    def __init__(self, translations, key='en'):
        '''
        This function initializes the I18n class.
        '''
        # extract lang from config
        config = Config.instance if hasattr(Config, 'instance') else Config()
        self.lang = config['language']

        # extract and prune target translations into one dict
        self.translations = {item[key]:item[self.lang] for item in json.loads(translations)}

    def __getitem__(self, text):
        """
        Get the translation for the given text,
        defaulting to the given text.
        """
        return self.translations.get(text, text)
