from telethon import TelegramClient, events, functions
from telethon.tl.types import InputPeerChat, InputDialogPeer
from telethon.extensions import markdown
from telethon.tl import types




# api_id = 28433327
# api_hash = '77970c9c064a94c4acadbe2ba7868a22'
# phone = '+79282519745'

api_id = 29515810
api_hash = 'edeecd40de7437a5fd76d706514ee94f'
phone = '+7 982 121 9051'



message_text = input('Введите текст сообщения: ')

chats_id = [5847945877]




client = TelegramClient(f'{28433327}', api_id, api_hash)

class CustomMarkdown:
    @staticmethod
    def parse(text):
        text, entities = markdown.parse(text)
        for i, e in enumerate(entities):
            if isinstance(e, types.MessageEntityTextUrl):
                if e.url == 'spoiler':
                    entities[i] = types.MessageEntitySpoiler(e.offset, e.length)
                elif e.url.startswith('emoji/'):
                    entities[i] = types.MessageEntityCustomEmoji(e.offset, e.length, int(e.url.split('/')[1]))
        return text, entities
    @staticmethod
    def unparse(text, entities):
        for i, e in enumerate(entities or []):
            if isinstance(e, types.MessageEntityCustomEmoji):
                entities[i] = types.MessageEntityTextUrl(e.offset, e.length, f'emoji/{e.document_id}')
            if isinstance(e, types.MessageEntitySpoiler):
                entities[i] = types.MessageEntityTextUrl(e.offset, e.length, 'spoiler')
        return markdown.unparse(text, entities)

async def main():
    # Получаем список всех диалогов
    # dialogs = await client.get_dialogs()

    # Please enter your phone (or bot token): 
    # Please enter the code you received: 

    # print(dialogs[2])


    client.parse_mode = CustomMarkdown()

    # # for chat_id in chats_id:
    entity = await client.get_entity(5847945877)
    # # print (entity)
    await client.send_message(entity, f'{message_text} [🤑](emoji/5406913184810409829)')

    # result = await client(functions.messages.GetEmojiKeywordsRequest(
    #     lang_code='en'
    # ))
    # print(result.stringify())



        # async def send_messages():
        #     client = client.start(phone)

        #     for chat_id in chat_ids:

        #         entity = await client.get_entity(chat_id)
        #         await client.send_message(entity, "Привет! Это тестовое сообщение.")
        #     await client.disconnect()  # Disconnect the client after sending messages


with client:
    client.loop.run_until_complete(main())




