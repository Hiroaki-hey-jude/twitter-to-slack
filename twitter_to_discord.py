import tweepy
import requests
import os
import json
import logging
import config

# ロギングの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 環境変数から認証情報を取得
TWITTER_API_KEY = config.TWITTER_API_KEY
TWITTER_API_SECRET_KEY = config.TWITTER_API_SECRET_KEY
TWITTER_ACCESS_TOKEN = config.TWITTER_ACCESS_TOKEN
TWITTER_ACCESS_TOKEN_SECRET = config.TWITTER_ACCESS_TOKEN_SECRET
DISCORD_WEBHOOK_URL = config.DISCORD_WEBHOOK_URL

# 特定のドメインを設定（QiitaとZenn）
TARGET_DOMAINS = ['qiita.com', 'zenn.dev']

# 処理済み「いいね」を記録するファイル
PROCESSED_LIKES_FILE = 'processed_likes.json'

def load_processed_likes():
    if os.path.exists(PROCESSED_LIKES_FILE):
        with open(PROCESSED_LIKES_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_processed_likes(processed_likes):
    with open(PROCESSED_LIKES_FILE, 'w') as f:
        json.dump(list(processed_likes), f)

def authenticate_twitter():
    auth = tweepy.OAuth1UserHandler(
        TWITTER_API_KEY,
        TWITTER_API_SECRET_KEY,
        TWITTER_ACCESS_TOKEN,
        TWITTER_ACCESS_TOKEN_SECRET
    )
    api = tweepy.API(auth)
    try:
        api.verify_credentials()
        logging.info("Twitter Authentication OK")
    except Exception as e:
        logging.error("Error during Twitter authentication:", exc_info=True)
        raise e
    return api

def post_to_discord(message):
    payload = {'content': message}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code != 204:
            logging.error(f"Failed to send to Discord: {response.status_code}, {response.text}")
    except Exception as e:
        logging.error("Error sending to Discord:", exc_info=True)

def extract_urls(tweet):
    urls = tweet.entities.get('urls', [])
    expanded_urls = [url['expanded_url'] for url in urls]
    return expanded_urls

def is_target_url(url):
    for domain in TARGET_DOMAINS:
        if domain in url:
            return True
    return False

def main():
    api = authenticate_twitter()
    processed_likes = load_processed_likes()

    try:
        likes = api.favorites(count=5)  # 最新5件の「いいね」を取得
    except Exception as e:
        logging.error("Failed to fetch favorites:", exc_info=True)
        return

    new_processed = False

    for like in likes:
        if like.id not in processed_likes:
            urls = extract_urls(like)
            for url in urls:
                if is_target_url(url):
                    message = f'新しい「いいね」:\nURL: {url}\nユーザー: @{like.user.screen_name}'
                    post_to_discord(message)
            processed_likes.add(like.id)
            new_processed = True

    if new_processed:
        save_processed_likes(processed_likes)

if __name__ == "__main__":
    main()
