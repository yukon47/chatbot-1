import streamlit as st
from openai import OpenAI

# タイトルと説明
st.title("📚 文書対応チャットボット")
st.write(
    "文書をアップロードして、その内容について質問できるチャットボットです。"
#     "OpenAI APIキーが必要です。[こちら](https://platform.openai.com/account/api-keys)から取得できます。"
)
st.write("【工夫した点】")
st.write(" ・APIキーを秘匿化してプログラムに埋め込み")
st.write(" ・ファイル未アップロード時はチャット入力が無効化")
st.write(" ・ファイル読み込み時に文字数を表示")
st.write(" ・ストリーミング応答で回答をリアルタイム表示")
st.write(" ・チャット形式で一連の対話をしながら質問ができる")

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
if "quiz_generated" not in st.session_state:
    st.session_state.quiz_generated = False

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
        st.session_state.quiz_generated = False  # クイズ生成フラグをリセット
        st.success(f"✅ {uploaded_file.name} を読み込みました！（{len(document):,} 文字）")

# 文書がアップロードされている場合
if uploaded_file and st.session_state.document_content:
    
    # クイズ生成ボタン
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("📝 クイズ出題", disabled=st.session_state.quiz_generated):
            # クイズを生成
            with st.chat_message("assistant"):
                st.markdown("📝 文書の内容に関するクイズを出題します...")
                
                # クイズ生成用のメッセージ
                quiz_messages = [
                    {
                        "role": "system",
                        "content": f"あなたは教育者です。以下の文書の内容に基づいて、理解度を確認するクイズを1問出題してください。\n\n文書内容:\n{st.session_state.document_content}"
                    },
                    {
                        "role": "user",
                        "content": "この文書の内容について、理解度を確認するクイズを1問出題してください。選択肢形式または記述式で、適切な難易度の問題をお願いします。"
                    }
                ]
                
                # クイズを生成
                stream = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=quiz_messages,
                    stream=True,
                )
                
                quiz_response = st.write_stream(stream)
                
            # クイズをチャット履歴に追加
            st.session_state.messages.append({"role": "assistant", "content": quiz_response})
            st.session_state.quiz_generated = True
            st.rerun()
    
    with col2:
        if st.button("🔄 会話をリセット"):
            st.session_state.messages = []
            st.session_state.quiz_generated = False
            st.rerun()

    # チャット履歴を表示
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # チャット入力
    if prompt := st.chat_input("文書について質問してください、またはクイズに回答してください"):
        # ユーザーメッセージを保存・表示
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # アシスタントの応答を生成
        with st.chat_message("assistant"):
            # API用のメッセージリストを作成
            # 最初のメッセージには文書内容を含める
            if len(st.session_state.messages) == 1:
                # 初回の質問
                messages = [
                    {
                        "role": "user",
                        "content": f"以下は文書の内容です: {st.session_state.document_content} \n\n---\n\n {prompt}",
                    }
                ]
            else:
                # 2回目以降は、文書内容をシステムメッセージとして設定し、会話履歴を追加
                messages = [
                    {
                        "role": "system",
                        "content": f"あなたは以下の文書に基づいて質問に答えるアシスタントです。ユーザーとの会話履歴を考慮して、文脈に沿った回答をしてください。クイズの回答に対しては、正誤を判定し、解説を加えてください。\n\n文書内容:\n{st.session_state.document_content}",
                    }
                ]
                # 会話履歴を追加
                for msg in st.session_state.messages[:-1]:  # 最後のメッセージ（今追加したもの）以外
                    messages.append({"role": msg["role"], "content": msg["content"]})
                # 現在の質問を追加
                messages.append({"role": "user", "content": prompt})

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