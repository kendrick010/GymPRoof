from dotenv import dotenv_values


class Config(object):
    _config = None

    def __init__(self):
        if not Config._config:
            Config._config = dotenv_values(".env")

        self.__config = Config._config

    def get_property(self, property_name: str, default=None):
        return self.__config.get(property_name, default)
    

class DiscordConfig(Config):
    def __init__(self):
        super().__init__()

    @property
    def server_id(self):
        return self.get_property('SERVER_ID')

    @property
    def bot_token(self):
        return self.get_property('BOT_TOKEN')
    
    @property
    def bot_channel_id(self):
        return self.get_property('BOT_CHANNEL_ID')

    @property
    def rules_channel_id(self):
        return self.get_property('RULES_CHANNEL_ID')

    @property
    def rules_message_id(self):
        return self.get_property('RULES_MESSAGE_ID')


class SupabaseConfig(Config):
    def __init__(self):
        super().__init__()

    @property
    def url(self):
        return self.get_property('SUPABASE_URL')

    @property
    def api_key(self):
        return self.get_property('SUPABASE_API_KEY')

