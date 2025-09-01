import discord
import asyncio

async def send_notification(token, channel_id, message):
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f'{client.user} がDiscordに接続しました。')
        channel = client.get_channel(channel_id)
        if channel:
            await channel.send(message)
            print("メッセージを送信しました。")
        else:
            print(f"チャンネルID {channel_id} が見つかりません。")
        await client.close()

    try:
        # 非同期処理としてクライアントを実行
        await client.start(token)
    except discord.errors.LoginFailure:
        print("不適切なトークンが渡されました。")
    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == '__main__':
    # このファイルは通常、直接実行しません。
    # send_notification関数をインポートして呼び出すことを想定しています。
    print("このスクリプトは直接実行しないでください。")
