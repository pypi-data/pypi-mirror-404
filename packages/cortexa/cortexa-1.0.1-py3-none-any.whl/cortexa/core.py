from .memory import Memory
from .llm import LLM
from .prompts import SYSTEM_PROMPT
import sys
import textwrap

class Cortexa:
    def __init__(self, model="llama3", max_history=4, width=80):
        self.memory = Memory()
        self.llm = LLM(model=model)
        self.max_history = max_history
        self.width = width

        self.memory.add(
            SYSTEM_PROMPT["role"],
            SYSTEM_PROMPT["content"]
        )

    def _get_context(self):
        system = self.memory.get()[:1]
        recent = self.memory.get()[-self.max_history:]
        return system + recent

    def _print_wrapped(self, text):
        wrapped = textwrap.fill(text, width=self.width)
        print(wrapped, end="", flush=True)

    def chat(self, message):
        self.memory.add("user", message)

        full_response = ""

        for chunk in self.llm.stream_generate(self._get_context()):
            full_response += chunk

            # Print wrapped output incrementally
            self._print_wrapped(chunk)

        print("\n")  # clean spacing after response

        self.memory.add("assistant", full_response)
        return full_response

    def reset(self):
        self.memory.clear()
        self.memory.add(
            SYSTEM_PROMPT["role"],
            SYSTEM_PROMPT["content"]
        )
