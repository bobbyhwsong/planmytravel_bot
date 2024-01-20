import openai
import os
import dotenv
import logging
from datetime import datetime as time

dotenv.load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
openai.organization = os.getenv("OPENAI_ORGANIZATION")

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


class MyTravelAgent:
    def __init__(
        self,
        user,
        prompt_file=None,
        model="gpt-4-1106-preview",
        style={"emoji": False, "polite": False, "verbose": False, "warm": False},
    ):
        self.prompt_file = prompt_file
        self.prompt = self.read_prompt(prompt_file) if prompt_file else ""
        self.style_prompt = ""
        self.user = user
        self.messages = []
        logger.info(f"{user} history initialized: {self.messages}")
        self.temperature = 0.9
        self.top_p = 1
        self.frequency_penalty = 0.0
        self.presence_penalty = 0.6
        self.max_tokens = 150
        self.style = style

        os.makedirs("chatlog", exist_ok=True)
        self.logfile = open(f"chatlog/{user}.log", "a")

    def read_prompt(self, prompt_file):
        try:
            with open(f"prompts/{prompt_file}.txt", "r") as f:
                prompt = f.read()
            return prompt
        except FileNotFoundError:
            logger.error(f"Prompt file '{prompt_file}' not found.")
            return ""
        except Exception as e:
            logger.error(f"Error reading prompt file '{prompt_file}': {e}")
            return ""

    def set_style(self):
        self.style_prompt = f"\n## 대답 스타일은 꼭 아래 사항을 명심하고 반영해서 대답해줘.\n"
        self.style_prompt += (
            "\n- 이모티콘을 상황에 맞게 적극적으로 사용해서 대답해 주세요."
            if self.style["emoji"]
            else "\n- 이모티콘은 절대 사용하지 마세요."
        )
        self.style_prompt += (
            "\n- 존댓말로 답해주세요." if self.style["polite"] else "\n- 반말로 대답해주세요."
        )
        self.style_prompt += (
            # "\n- 대답은 최대한 자세하고 길게 해주세요."
            "\n- User의 질문에 대한 대답과 이유를 짧게 30단어 이하로 말한다."
            if self.style["verbose"]
            # else "\n- 대답은 최대한 간결하게 요점만 정리 해주세요."
            else "\n- User의 질문에 대한 대답만 매우 짧게 10단어 이하로 말한다."
        )
        self.style_prompt += (
            "\n- 대답은 최대한 따뜻하고 공감하는 말투로 해주세요."
            if self.style["warm"]
            # else "\n- 대답은 최대한 냉정하게 해주세요.\n\n"
            else "\n- 대답은 최대한 차갑고 싸늘한 말투로 말해주세요.\n\n"
        )
        content = f"{self.prompt}\n\n{self.style_prompt}\n\n단, 토큰 수 {self.max_tokens}는 절대로 넘지 말아야해."
        self.messages.append({"role": "system", "content": content})
        logger.info(f"Style prompt: {self.style_prompt}")

    def response(self, message, model="gpt-4", last_n=15):
        if self.style_prompt == "":
            self.set_style()

        content = message

        self.messages.append({"role": "user", "content": content})

        logger.info(self.messages)
        with open(f"chatlog/{self.user}.log", "a") as f:
            f.write(f"{time.now()} - {'user':<9}: {content}\n")

        response = openai.chat.completions.create(
            model=model,
            messages=self.messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            top_p=self.top_p,
            frequency_penalty=self.frequency_penalty,
            presence_penalty=self.presence_penalty,
        )

        logger.info(response.choices)
        self.messages.append(
            {"role": "assistant", "content": response.choices[0].message.content}
        )

        with open(f"chatlog/{self.user}.log", "a") as f:
            f.write(
                f"{time.now()} - {'assistant':<9}: {response.choices[0].message.content}\n"
            )

        if len(self.messages) > 14:
            self.messages = []
            content = (
                self.prompt
                + "\n\n"
                + self.style_prompt
                # + "그러나 너는 무조건 틀린 답을 말해야한다. 누가 봐도 한 눈에 틀린거라고 알 수 있을만큼 생뚱맞은 답을 하여라."
                # + f"그러나 너는 틀리거나 말도 안되는 답을 말해야해. 짜증을 유발해도 좋고 도발해도 괜찮아. 대신 명확해야해. 토큰 수 {self.max_tokens}는 절대로 넘지 말아야해."
                + "그러나 너는 틀린 답을 말해야해. 여행지에 대한 아무 지식도 없는 유저가 봐도 틀렸다는 것을 알 수 있는 말을 해. 대신 명확한 답을 해야해."
            )
            self.messages.append({"role": "system", "content": content})
        return response.choices[0].message.content


if __name__ == "__main__":
    agent = MyTravelAgent("template_03")
    agent.response("제주도 여행을 가려고 하는데 어떻게 가면 좋을까?")