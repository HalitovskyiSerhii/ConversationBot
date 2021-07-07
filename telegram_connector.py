import logging

from rasa.core.channels.telegram import TelegramOutput, TelegramInput
from sanic import Blueprint, response
from sanic.request import Request
from sanic.response import HTTPResponse
from telebot.apihelper import ApiTelegramException
from telebot.types import Update, Message
from typing import Text, Any, Callable, Awaitable, Optional, Dict

from rasa.core.channels.channel import UserMessage
from rasa.shared.constants import INTENT_MESSAGE_PREFIX
from rasa.shared.core.constants import USER_INTENT_RESTART
from rasa.shared.exceptions import RasaException

logger = logging.getLogger(__name__)


class CustomTelegramOutput(TelegramOutput):

    @classmethod
    def name(cls) -> Text:
        return "custom"


class CustomTelegramInput(TelegramInput):

    @classmethod
    def name(cls) -> Text:
        return "custom"
    
    def blueprint(
            self, on_new_message: Callable[[UserMessage], Awaitable[Any]]
    ) -> Blueprint:
        telegram_webhook = Blueprint("telegram_webhook", __name__)
        out_channel = self.get_output_channel()

        @telegram_webhook.route("/", methods=["GET"])
        async def health(_: Request) -> HTTPResponse:
            return response.json({"status": "ok"})

        @telegram_webhook.route("/set_webhook", methods=["GET", "POST"])
        async def set_webhook(_: Request) -> HTTPResponse:
            s = out_channel.set_webhook(url=self.webhook_url)
            if s:
                logger.info("Webhook Setup Successful")
                return response.text("Webhook setup successful")
            else:
                logger.warning("Webhook Setup Failed")
                return response.text("Invalid webhook")

        @telegram_webhook.route("/webhook", methods=["GET", "POST"])
        async def message(request: Request) -> Any:
            if request.method == "POST":
                file_urls = []
                request_dict = request.json
                update = Update.de_json(request_dict)
                if not out_channel.get_me().username == self.verify:
                    logger.debug("Invalid access token, check it matches Telegram")
                    return response.text("failed")

                if self._is_button(update):
                    msg = update.callback_query.message
                    text = update.callback_query.data
                elif self._is_edited_message(update):
                    msg = update.edited_message
                    text = update.edited_message.text
                else:
                    msg: Message = update.message
                    if self._is_user_message(msg):
                        text = msg.text.replace("/bot", "")
                    elif self._is_location(msg):
                        text = '{{"lng":{0}, "lat":{1}}}'.format(
                            msg.location.longitude, msg.location.latitude
                        )
                    elif self._has_content(msg):
                        file_ids = []
                        text = msg.caption
                        if msg.photo:
                            file_ids += [ph.file_id for ph in msg.photo]
                        if msg.document:
                            file_ids.append(msg.document.file_id)
                        file_urls = list(map(out_channel.get_file_url, file_ids))
                    else:
                        return response.text("success")
                sender_id = msg.chat.id
                metadata = self.get_metadata(request)

                # Filling files info
                if file_urls:
                    metadata.update({"file_urls": file_urls})

                try:
                    if text == (INTENT_MESSAGE_PREFIX + USER_INTENT_RESTART):
                        await on_new_message(
                            UserMessage(
                                text,
                                out_channel,
                                sender_id,
                                input_channel=self.name(),
                                metadata=metadata,
                            )
                        )
                        await on_new_message(
                            UserMessage(
                                "/start",
                                out_channel,
                                sender_id,
                                input_channel=self.name(),
                                metadata=metadata,
                            )
                        )
                    else:
                        await on_new_message(
                            UserMessage(
                                text,
                                out_channel,
                                sender_id,
                                input_channel=self.name(),
                                metadata=metadata,
                            )
                        )
                except Exception as e:
                    logger.error(f"Exception when trying to handle message.{e}")
                    logger.debug(e, exc_info=True)
                    if self.debug_mode:
                        raise
                    pass

                return response.text("success")

        return telegram_webhook

    @staticmethod
    def _has_content(message: Message) -> bool:
        return message.content_type in ['document', 'photo']
    
    def get_metadata(self, request: Request) -> Optional[Dict[Text, Any]]:
        return {}
    
    def get_output_channel(self) -> TelegramOutput:
        """Loads the telegram channel."""
        channel = CustomTelegramOutput(self.access_token)

        try:
            channel.set_webhook(url=self.webhook_url)
        except ApiTelegramException as error:
            raise RasaException(
                "Failed to set channel webhook: " + str(error)
            ) from error

        return channel
