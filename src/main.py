import gradio as gr

from dotenv import load_dotenv
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.prompts import HumanMessagePromptTemplate
from langchain.prompts.chat import ChatPromptTemplate
from langchain.prompts.prompt import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI


VECTORSTORE_DIRECTORY = "vectordb"


def main(file_paths: list[str], query: str, can_extract_images: bool) -> str:
    load_dotenv("config/.env")
    # api_key = os.getenv("OPENAI_API_KEY")
    # os.environ["OPENAI_API_KEY"] = api_key


    # Step 1. Load
    '''
    載入文件(僅支援PDF)
    '''
    # file_path = "assets/"+file_name
    print("file_path: ", file_paths)
    assert len(file_paths) == 1, "Only one file can be uploaded at a time."
    loader = PyPDFLoader(file_paths[0], extract_images=can_extract_images)
    data = loader.load()


    # Step 2. Split
    '''
    選擇splitter，將文件拆分成多個chunk
    '''

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=0)
    all_splits = text_splitter.split_documents(data)


    # Step 3. Store
    '''
    將embedding和splits儲存至vectorstore
    '''

    vectordb = Chroma.from_documents(
        documents=all_splits,
        embedding=OpenAIEmbeddings(),
        persist_directory=VECTORSTORE_DIRECTORY,
    )
    vectordb.persist()


    # Step 4. Retrieval QA
    ## query

    ## prompt

    input_variables = ['question', 'context']
    messages = [
        HumanMessagePromptTemplate(
            prompt=PromptTemplate(
                input_variables=input_variables,
                template="You are a very powerful assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Respond in the language of the question.\nQuestion: {question} \nContext: {context} \nAnswer:"
            )
        )
    ]
    prompt = ChatPromptTemplate(input_variables=input_variables, messages=messages)

    ##LLM

    llm = ChatOpenAI(model_name="gpt-3.5-turbo",
                    temperature=0)


    # Step 5. Generate
    # ## RAG prompt template
    # from langchain import hub
    # prompt = hub.pull("rlm/rag-prompt")


    ## QA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm,
        retriever=vectordb.as_retriever(),
        chain_type_kwargs={"prompt": prompt}
    )
    result = qa_chain({"query": query})

    # Output
    return result["result"]


title = "My chatPDF"
# 設定Gradio UI介面，指定兩個文字輸入框
file_name = gr.FileExplorer(label="Upload PDF file")
question = gr.Textbox(placeholder="Enter the message", type="text")
extract_images = gr.Checkbox(label="Extract images from PDF", default=False)


# Gradio UI 介面
ui=gr.Interface(
    fn=main,
    # inputs=gr.Textbox(placeholder="Enter the message..."),
    inputs=[file_name, question, extract_images],
    # outputs=gr.HighlightedText(color_map={"0":"yellow"}),
    outputs="text",
    title=title
)



# 啟動 Gradio 介面
ui.launch(
    debug=True,
    server_name="127.0.0.1",
    server_port=8080
)