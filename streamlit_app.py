import streamlit as st
from openai import OpenAI

# タイトルと説明
st.title("📚 文書対応チャットボット")
st.write(
    "文書をアップロードして、その内容について質問できるチャットボットです。"
#     "OpenAI APIキーが必要です。[こちら](https://platform.openai.com/account/api-keys)から取得できます。"
)

# OpenAI APIキーの入力
openai_api_key = st.secrets.get("OPENAI_API_KEY")
# openai_api_key = st.text_input("OpenAI API Key", type="password")
# if not openai_api_key:
#     st.info("OpenAI APIキーを入力してください。", icon="🗝️")
# else:
# OpenAIクライアントの作成
client = OpenAI(api_key=openai_api_key)

# セッション状態の初期化
if "messages" not in st.session_state:
    st.session_state.messages = []
if "document_content" not in st.session_state:
    st.session_state.document_content = ""

# ファイルアップロード
uploaded_file = st.file_uploader(
    "文書をアップロード (.txt または .md)", type=("txt", "md")
)

# ファイルがアップロードされた場合、内容を読み込む
if uploaded_file:
    document = uploaded_file.read().decode()
    # 新しい文書の場合、セッション状態を更新
    if st.session_state.document_content != document:
        st.session_state.document_content = document
        st.session_state.messages = []  # チャット履歴をクリア
        st.success(f"✅ {uploaded_file.name} を読み込みました！（{len(document):,} 文字）")

# チャット履歴を表示
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# チャット入力
if prompt := st.chat_input("文書について質問してください", disabled=not uploaded_file):
    # ユーザーメッセージを保存・表示
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # アシスタントの応答を生成
    with st.chat_message("assistant"):
        # 文書内容と質問を組み合わせたメッセージを作成
        messages = [
            {
                "role": "user",
                "content": f"以下は文書の内容です: {st.session_state.document_content} \n\n---\n\n {prompt}",
            }
        ]

        # OpenAI APIで応答を生成（ストリーミング）
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            stream=True,
        )

        # ストリーミングで応答を表示
        response = st.write_stream(stream)

    # アシスタントの応答を保存
    st.session_state.messages.append({"role": "assistant", "content": response})
