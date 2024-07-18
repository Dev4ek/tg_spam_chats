import re

class MessageEntity:
    def __init__(self, type, custom_emoji_id):
        self.type = type
        self.custom_emoji_id = custom_emoji_id

def replace_custom_emojis(text, entities):
    pattern = re.compile(r'\{prem\}(.+?)\{prem\}')
    matches = pattern.findall(text)

    for match, entity in zip(matches, entities):
        emoji_symbol = match
        emoji_id = entity.custom_emoji_id
        replacement = f"[{emoji_symbol}](emoji/{emoji_id})"
        text = text.replace(f"{{prem}}{emoji_symbol}{{prem}}", replacement, 1)
    return text

text = "тут текст {prem}😀{prem} дальше текст {prem}💩{prem}{prem}🙏{prem} как дела?"
entities = [
    MessageEntity(type='custom_emoji', custom_emoji_id='5377458526727712735'),
    MessageEntity(type='custom_emoji', custom_emoji_id='5429334864010681294'),
    MessageEntity(type='custom_emoji', custom_emoji_id='5231249426130935149')
]

converted_text = replace_custom_emojis(text, entities)
print(converted_text)
