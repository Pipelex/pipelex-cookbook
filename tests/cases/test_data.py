from pydantic import BaseModel


class Person(BaseModel):
    name: str
    age: int


class LLMTestConstants:
    USER_TEXT_SHORT = "In one sentence, who is Bill Gates?"
