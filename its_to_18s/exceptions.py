class UserError(ValueError):
    def __init__(self, message, *args, **kwargs):
        self.message = message
        super(ValueError, self).__init__(message, *args, **kwargs)

    def format_for_user(self):
        return "Unable to continue: "+self.message

