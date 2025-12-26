from agent_squad.classifiers import Classifier, ClassifierResult
from agent_squad.types import ConversationMessage


class MetaClassifier(Classifier):
    def __init__(self, meta_agent):
        super().__init__()
        self.meta_agent = meta_agent

    async def process_request(self, input_text: str, chat_history: list[ConversationMessage]) -> ClassifierResult:
        return ClassifierResult(selected_agent=self.meta_agent, confidence=1.0)
