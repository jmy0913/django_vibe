from dotenv import load_dotenv

from transformers import BertTokenizer

from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.chains.query_constructor.schema import AttributeInfo

# LangChain Community
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings


from langchain.embeddings import OpenAIEmbeddings  # OpenAIEmbeddings 임포트 추가
from langchain_openai import ChatOpenAI

from rank_bm25 import BM25Okapi
from nltk.tokenize import word_tokenize
import string
import os

# Load environment variables
load_dotenv()

current_dir = os.path.dirname(os.path.abspath(__file__))
faiss_path1 = os.path.join(current_dir, "faiss_index3")
faiss_path2 = os.path.join(current_dir, "faiss_index_bge_m3")
print(faiss_path1, faiss_path2)

def faiss_retriever_loading():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    faiss_path1 = os.path.join(current_dir, "faiss_index3")
    faiss_path2 = os.path.join(current_dir, "faiss_index_bge_m3")
    embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")

    vector_db1 = FAISS.load_local(
        faiss_path1,
        embeddings,
        allow_dangerous_deserialization=True
    )

    accounting_retriever = vector_db1.as_retriever(
        search_type='similarity',
        search_kwargs={
            'k': 6
        })

    # 사업보고서 벡터 db
    vector_db2 = FAISS.load_local(
        faiss_path2,
        embeddings,
        allow_dangerous_deserialization=True
    )


    business_retriever = vector_db2.as_retriever(
        search_type='similarity',
        search_kwargs={
            'k': 6,
        })



    # metadata_field_info = [
    #     AttributeInfo(
    #         name='year',
    #         type='list[string]',
    #         description='사업보고서 연도(예시:2024)'),
    #     AttributeInfo(
    #         name='page_content',
    #         type='string',
    #         description='문서 본문 내용')]


    # 사업보고서 벡터 db - SelfQueryRetriever 객체생성
    # fiass는 지원하지 않아서 제외..

    # self_query_retriever = SelfQueryRetriever.from_llm(
    #     llm=ChatOpenAI(model='gpt-4o-mini', temperature=0),
    #     vectorstore=vector_db2,
    #     document_contents='page_content',  # 문서 내용을 가리키는 메타데이터 필드명
    #     metadata_field_info=metadata_field_info,
    #     search_kwargs={"k": 6}
    # )

    return accounting_retriever, business_retriever