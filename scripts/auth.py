"""
Step 1: OAuth 2.0 認証

実行方法:
  python scripts/auth.py

動作:
  初回はブラウザが開き、Googleアカウントでログインを求められます。
  成功すると token.json が生成され、以降は自動的に再利用されます。

次のステップ:
  → python scripts/step2_test.py
"""

import os
import sys

# scriptsディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from config import CLIENT_SECRET_FILE, TOKEN_FILE, SCOPES


def get_credentials():
    """認証済みのcredentialsを返す。未認証なら認証フローを開始。"""
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("トークンを更新中...")
            creds.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRET_FILE):
                print(f"❌ エラー: {CLIENT_SECRET_FILE} が見つかりません。")
                print(f"   scripts/step0_setup.md に従って client_secret.json を配置してください。")
                return None

            print("ブラウザで認証を行います...")
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_FILE, SCOPES
            )
            creds = flow.run_local_server(
                port=0,
                prompt="select_account",
                login_hint="famous.adhd@gmail.com",
            )

        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
        print(f"✅ 認証成功。トークンを保存しました。")

    return creds


if __name__ == "__main__":
    print("=" * 50)
    print("Step 1: OAuth認証")
    print("=" * 50)
    creds = get_credentials()
    if creds:
        print("\n✅ 認証完了。token.json が生成されました。")
        print("次のステップ → python scripts/step2_test.py")
    else:
        print("\n❌ 認証に失敗しました。step0_setup.md を確認してください。")
