from __future__ import annotations

from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessageParam,
    completion_create_params,
)
from typing_extensions import Dict, Iterable, List, Optional, Union

from fixmate.common.client.llm.protocol import NOT_GIVEN, LlmClient, NotGiven
from fixmate.logger import logger


class AioLlmClient(LlmClient):
    def __init__(self, *clients: LlmClient):
        self.__original_clients = clients
        self.__clients = []
        self.__supported_models = set()
        print("clientsclientsclients", clients)
        for client in clients:
            try:
                print("clientclidfdsfentclient", client)
                # self.__supported_models.update(client.get_models())
                self.__supported_models.update('gpt-3.5-turbo')
                self.__clients.append(client)
            except Exception as error:
                print("Exceptiondfsdfsd", error)
                pass
        print("89jndjdsnkjnksdjnf", self.__clients)

    def get_models(self) -> set[str]:
        return self.__supported_models

    def is_model_supported(self, model: str) -> bool:
        return any(client.is_model_supported(model) for client in self.__clients)

    def chat_completion(
        self,
        messages: Iterable[ChatCompletionMessageParam],
        model: str,
        frequency_penalty: Optional[float] | NotGiven = NOT_GIVEN,
        logit_bias: Optional[Dict[str, int]] | NotGiven = NOT_GIVEN,
        logprobs: Optional[bool] | NotGiven = NOT_GIVEN,
        max_tokens: Optional[int] | NotGiven = NOT_GIVEN,
        n: Optional[int] | NotGiven = NOT_GIVEN,
        presence_penalty: Optional[float] | NotGiven = NOT_GIVEN,
        response_format: completion_create_params.ResponseFormat | NotGiven = NOT_GIVEN,
        stop: Union[Optional[str], List[str]] | NotGiven = NOT_GIVEN,
        temperature: Optional[float] | NotGiven = NOT_GIVEN,
        top_logprobs: Optional[int] | NotGiven = NOT_GIVEN,
        top_p: Optional[float] | NotGiven = NOT_GIVEN,
    ) -> ChatCompletion:
        print("kndskjfndskfjs", self.__clients)
        for client in self.__clients:
            print("clientclientclient", client)
            from g4f.client import Client
            openai_client = Client()
            if True:
            # if client.is_model_supported(model):
                logger.debug(f"Using {client.__class__.__name__} for model {model}")

                return openai_client.chat.completions.create(
                # return client.chat.completion.create(
                    messages,
                    model,
                    # frequency_penalty,
                    # logit_bias,
                    # logprobs,
                    # max_tokens,
                    # n,
                    # presence_penalty,
                    # response_format,
                    # stop,
                    # temperature,
                    # top_logprobs,
                    # top_p,
                )
        client_names = [client.__class__.__name__ for client in self.__original_clients]
        raise ValueError(
            f"Model {model} is not supported by {client_names} clients. "
            f"Please ensure that the respective API keys are correct."
        )
