import os
import re
import discord


# =========================
# 配置
# =========================

SOURCE_DOMAIN = os.getenv(
    "SOURCE_DOMAIN",
    "nitter.meowing.monster"
)

TARGET_DOMAIN = os.getenv(
    "TARGET_DOMAIN",
    "fixupx.com"
)

# true  = 删除原消息，再发送转换后的消息
# false = 保留原消息，再发送转换后的消息
DELETE_ORIGINAL = os.getenv(
    "DELETE_ORIGINAL",
    "true"
).lower() == "true"


# =========================
# Discord 设置
# =========================

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


# =========================
# URL 匹配
# =========================

url_pattern = re.compile(
    rf"https?://{re.escape(SOURCE_DOMAIN)}(?P<rest>/[^\s<>\"]*)",
    re.IGNORECASE
)


def replace_urls(text: str) -> str:
    """只替换指定的 Nitter 域名，后面的路径保持不变。"""
    return url_pattern.sub(
        lambda match: (
            "https://"
            + TARGET_DOMAIN
            + match.group("rest")
        ),
        text
    )


# =========================
# Bot 启动
# =========================

@client.event
async def on_ready():
    print(f"Bot 已登录：{client.user}")
    print(f"转换：{SOURCE_DOMAIN} -> {TARGET_DOMAIN}")
    print(f"删除原消息：{DELETE_ORIGINAL}")


# =========================
# 监听消息
# =========================

@client.event
async def on_message(message: discord.Message):

    # 只忽略 Bot 自己发送的消息。
    # 不能写 message.author.bot，
    # 因为 MonitoRSS 本身也是 Bot / Webhook。
    if client.user and message.author.id == client.user.id:
        return

    # 没有文字内容就不处理
    if not message.content:
        return

    # 替换 Nitter 域名
    converted = replace_urls(message.content)

    # 没有匹配到目标域名
    if converted == message.content:
        return

    try:
        # 发送转换后的链接
        await message.channel.send(converted)

        # 删除原消息
        if DELETE_ORIGINAL:
            await message.delete()

    except discord.Forbidden:
        print(
            "权限不足，请确认 Bot 在该频道拥有："
            "View Channel / Send Messages / Embed Links / Manage Messages"
        )

    except discord.HTTPException as e:
        print(f"Discord API 错误：{e}")


# =========================
# 启动
# =========================

token = os.getenv("DISCORD_TOKEN")

if not token:
    raise RuntimeError(
        "没有找到 DISCORD_TOKEN 环境变量。"
    )

client.run(token)
