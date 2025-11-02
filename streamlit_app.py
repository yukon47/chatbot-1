import streamlit as st
from openai import OpenAI
import PyPDF2
import docx
import pandas as pd
from io import BytesIO

# ページ設定
st.set_page_config(page_title="文書対応チャットボット", page_icon="📚")

# タイトルと説明
st.title("📚 文書対応チャットボット")
st.write(
    "このチャットボットは、アップロードされた文書の内容を理解し、質問に答えます。"
    "以下の形式に対応しています：PDF, Word (DOCX), Excel, CSV, テキストファイル。"
)

# OpenAI APIキーの入力
# openai_api_key = st.text_input("OpenAI API Key", type="password")
# if not openai_api_key:
#     st.info("OpenAI APIキーを入力してください。", icon="🗝️")
#     st.stop()

# OpenAIクライアントの作成
client = OpenAI(api_key=openai_api_key)

# セッション状態の初期化
if "messages" not in st.session_state:
    st.session_state.messages = []
if "document_content" not in st.session_state:
    st.session_state.document_content = ""
if "document_name" not in st.session_state:
    st.session_state.document_name = ""


def extract_text_from_pdf(file):
    """PDFファイルからテキストを抽出"""
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text


def extract_text_from_docx(file):
    """Wordファイルからテキストを抽出"""
    doc = docx.Document(file)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text


def extract_text_from_excel(file):
    """Excelファイルからテキストを抽出"""
    df = pd.read_excel(file, sheet_name=None)
    text = ""
    for sheet_name, sheet_df in df.items():
        text += f"\n【シート名: {sheet_name}】\n"
        text += sheet_df.to_string(index=False) + "\n"
    return text


def extract_text_from_csv(file):
    """CSVファイルからテキストを抽出"""
    df = pd.read_csv(file)
    return df.to_string(index=False)


def extract_text_from_txt(file):
    """テキストファイルから内容を読み取る"""
    return file.read().decode('utf-8')


def process_uploaded_file(uploaded_file):
    """アップロードされたファイルを処理"""
    file_extension = uploaded_file.name.split('.')[-1].lower()
    
    try:
        if file_extension == 'pdf':
            return extract_text_from_pdf(uploaded_file)
        elif file_extension == 'docx':
            return extract_text_from_docx(uploaded_file)
        elif file_extension in ['xlsx', 'xls']:
            return extract_text_from_excel(uploaded_file)
        elif file_extension == 'csv':
            return extract_text_from_csv(uploaded_file)
        elif file_extension == 'txt':
            return extract_text_from_txt(uploaded_file)
        else:
            return None
    except Exception as e:
        st.error(f"ファイルの読み込み中にエラーが発生しました: {str(e)}")
        return None


# サイドバーにファイルアップロード機能を配置
with st.sidebar:
    st.header("📄 文書アップロード")
    uploaded_file = st.file_uploader(
        "文書をアップロード",
        type=['pdf', 'docx', 'xlsx', 'xls', 'csv', 'txt'],
        help="PDF, Word, Excel, CSV, テキストファイルをアップロードできます"
    )
    
    if uploaded_file is not None:
        if st.session_state.document_name != uploaded_file.name:
            with st.spinner('文書を読み込んでいます...'):
                content = process_uploaded_file(uploaded_file)
                if content:
                    st.session_state.document_content = content
                    st.session_state.document_name = uploaded_file.name
                    st.success(f"✅ {uploaded_file.name} を読み込みました！")
                    
                    # 文字数を表示
                    char_count = len(content)
                    st.info(f"文字数: {char_count:,} 文字")
                else:
                    st.error("このファイル形式はサポートされていません。")
    
    # 現在読み込まれている文書を表示
    if st.session_state.document_name:
        st.divider()
        st.write("**現在の文書:**")
        st.write(f"📄 {st.session_state.document_name}")
        
        if st.button("文書をクリア"):
            st.session_state.document_content = ""
            st.session_state.document_name = ""
            st.session_state.messages = []
            st.rerun()

# メインチャットエリア
if not st.session_state.document_content:
    st.info("👈 左側のサイドバーから文書をアップロードしてください。")
else:
    # チャット履歴の表示
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # チャット入力
    if prompt := st.chat_input("文書について質問してください"):
        # ユーザーメッセージを追加
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # システムプロンプトを作成（文書内容を含める）
        system_message = {
            "role": "system",
            "content": f"""あなたは親切なアシスタントです。以下の文書の内容に基づいて、ユーザーの質問に答えてください。
            文書に書かれていない内容については、「この文書には記載されていません」と答えてください。

【文書名: {st.session_state.document_name}】

【文書内容】
{st.session_state.document_content}
"""
        }
        
        # APIリクエスト用のメッセージリストを作成
        messages_for_api = [system_message] + [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ]
        
        # OpenAI APIで応答を生成
        with st.chat_message("assistant"):
            try:
                stream = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages_for_api,
                    stream=True,
                    temperature=0.7,
                )
                response = st.write_stream(stream)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"エラーが発生しました: {str(e)}")
                st.session_state.messages.pop()  # エラー時はユーザーメッセージを削除
