from .config import Config


class I18n:
    """
    Internationalization class.
    """
    def __init__(self, translations = None):
        '''
        This function initializes the I18n class.
        '''
        self.config = Config()
        self.lang = self.config['language']
        self.translations = translations
        '''Sample Translation:
        [{"en":"Hello","zh":"你好","ja":"こんにちは"},
        {"en":"OK","zh":"好","ja":"はい"}]
        '''
        
    def set_translations(self, translations):
        '''
        This function sets the translations for the I18n class.
        '''
        self.translations = translations
        return self.translations
    
    def set_language(self, lang):
        '''
        This function sets the language for the I18n class.
        '''
        self.lang = lang
        return self.lang
    
    def trans(self, text, custom_trans = None, to_lang = None):
        '''
        This function translates the text to the language specified in the config.
        '''
        if custom_trans == None and self.translations == None:
            return text
        
        cur_trans = custom_trans if custom_trans != None else self.translations
        for i in cur_trans:
            if text in i.values():
                return i[self.lang if to_lang == None else to_lang]
            
        return text
            
    