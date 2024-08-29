from .config import Config

'''
Sample:
{
    "Loading...":{"zh": "加载中...", "ja": "読み込み中..."},
    "Files":{"zh": "文件", "ja": "ファイル"},
    "Terminal":{"zh": "终端", "ja": "端末"},
    "Get Apps":{"zh": "应用商店", "ja": "アプリストア"},
    "Reload Apps":{"zh": "重新加载应用", "ja": "アプリ再読"},
    "UI Sound":{"zh": "界面声音", "ja": "UIサウンド"},
    "Settings":{"zh": "设置", "ja": "設定"},
    "On":{"zh": "开", "ja": "オン"},
    "Off":{"zh": "关", "ja": "オフ"}
}
'''

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
        cur_lang = self.lang if to_lang == None else to_lang
        if not text in cur_trans or not cur_lang in cur_trans[text]:
            return text
        else:
            return cur_trans[text][cur_lang]
            
    