class QAService:
    def __init__(self, chatbot):
        self.chatbot = chatbot

    def ask(self, question):
        return self.chatbot.query(question)