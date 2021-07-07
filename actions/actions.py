import logging
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

from . import downloader, storage
from .exceptions import InvalidFileURL

logger = logging.getLogger(__name__)

def get_links(message):
    links = filter(lambda entity: entity['entity'] == 'url_link', message['entities'])
    return list(map(lambda x: x['value'], links))


class ActionDownloadImage(Action):

    def name(self) -> Text:
        return "action_download_image"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        links = get_links(tracker.latest_message)

        if not links:
            dispatcher.utter_message(text="Can't find any link in your message.")
        else:

            for link in links:
                try:
                    dispatcher.utter_message(image=link)
                except Exception as e:
                    logger.error(e)
                    dispatcher.utter_message(text=f"Something went wrong.\n"
                                                  f"Can't get {link}")
            else:
                dispatcher.utter_message(text="Here your images!")

        return []


class ActionSaveDock(Action):

    def name(self) -> Text:
        return "action_save_doc"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        links = tracker.latest_message['metadata']['file_urls']

        if not links:
            dispatcher.utter_message(text="Can't find any link in your message.")
        else:
            downloading = True
            while downloading:
                try:
                    for obj in downloader(urls=links):
                        url = storage.save_obj(obj, get_url=True)
                        dispatcher.utter_message(attachment=url)
                    downloading = False
                except InvalidFileURL as e:
                    dispatcher.utter_message(text=e.message)
                except Exception as e:
                    logger.error(e)
                    downloading = False
                    dispatcher.utter_message(text=f"Something went wrong.")
            else:
                dispatcher.utter_message(text=f"Your request were been processed")

        return []
