from typing import TypedDict, Literal, List, Optional
from langgraph.graph import StateGraph, START, END
from typing import Literal, TypedDict, List, Optional

# 체인 및 기타 함수들
from .chain_setting import create_chain
from .normalize_code_search import parse_extracted_text
from .normalize_code_search import find_corporation_code, parse_extracted_text
from .retreiver_setting import faiss_retriever_loading
from .api_get import get_financial_state

accounting_retriever, business_retriever = faiss_retriever_loading()

simple_chain, classification_chain, extract_chain,hybrid_chain1, hybrid_chain2, hybrid_chain3,account_chain1, account_chain2, account_chain3,business_chain1, business_chain2, business_chain3, financial_chain1, financial_chain2, financial_chain3 = create_chain()


# State 타입 정의
class ChatTurn(TypedDict):
    role: Literal["user", "assistant"]  # 타입 명시(필수는 아님)
    content: str

class ChatState(TypedDict, total=False):
    question: str                 # 질문
    company: Optional[str]        # 회사명 (선택사항)
    year: Optional[List[str]]     # 연도 리스트 (선택사항)
    route: Optional[str]          # 작업 유형 (accounting, finance, etc.)
    level: Optional[str]          # 난이도 레벨 (basic, intermediate, advanced)
    answer: Optional[str]         # 답변
    chat_history: List[ChatTurn]   # 대화 히스토리 (user, assistant 대화 내용)


# 분류 토드
def classify(state: ChatState) -> dict:
    question = state["question"]
    chat_history = state.get("chat_history", [])

    # 최근 대화 몇 개만 context로 붙임
    context = "\n".join([f"{turn['role']}: {turn['content']}" for turn in chat_history[-4:]])

    result = classification_chain.invoke({
        "question": question,
        "context": context
    }).strip()

    return {
    **state,
    "route": result
}


def route_from_classify(state):
    route = state.get("route", "").strip()
    # classification_chain이 실제로 뭘 반환하는지에 따라 매핑
    if route in ["accounting", "finance", "business", "hybrid"]:
        return route
    return "simple"



def extract_entities(state: ChatState) -> dict:
    question = state["question"]
    prev_company = state.get("company")
    prev_years = state.get("year")

    result = extract_chain.invoke({"question": question})
    # result는 문자열이므로 바로 사용
    parsed = parse_extracted_text(result)

    company = parsed.get("company") or prev_company
    years = parsed.get("year_list") or prev_years or ["2024"]

    return {
        **state,
        "company": company,
        "year": years,
    }

def route_from_extract(state: ChatState) -> str:
    mapping = {
        "accounting": "accounting",
        "finance": "financial",
        "business": "business",
        "hybrid": "hybrid",
    }
    return mapping.get(state.get("route", "").strip(), "simple")

def route_from_extract_with_level(state: ChatState) -> str:
    route = state.get("route")
    level = state.get("level", "basic")  # 기본 레벨은 "basic"

    # route와 level을 조합하여 반환
    return f"{route}_{level}"

def handle_accounting1(state: ChatState) -> dict:
    question = state["question"]
    docs = accounting_retriever.invoke(question)
    context = "\n\n".join(doc.page_content for doc in docs)
    answer = account_chain1.invoke({"context": context, "question": question})
    updated_history = state.get("chat_history", []).copy()
    updated_history.append({"role": "user", "content": question})
    updated_history.append({"role": "assistant", "content": answer})

    return {
        **state,
        "answer": answer,
        "chat_history": updated_history
    }

def handle_accounting2(state: ChatState) -> dict:
    question = state["question"]
    docs = accounting_retriever.invoke(question)
    context = "\n\n".join(doc.page_content for doc in docs)
    answer = account_chain2.invoke({"context": context, "question": question})
    updated_history = state.get("chat_history", []).copy()
    updated_history.append({"role": "user", "content": question})
    updated_history.append({"role": "assistant", "content": answer})

    return {
        **state,
        "answer": answer,
        "chat_history": updated_history
    }

def handle_accounting3(state: ChatState) -> dict:
    question = state["question"]
    docs = accounting_retriever.invoke(question)
    context = "\n\n".join(doc.page_content for doc in docs)
    answer = account_chain3.invoke({"context": context, "question": question})
    updated_history = state.get("chat_history", []).copy()
    updated_history.append({"role": "user", "content": question})
    updated_history.append({"role": "assistant", "content": answer})

    return {
        **state,
        "answer": answer,
        "chat_history": updated_history
    }

def handle_financial1(state: ChatState) -> dict:
    question = state["question"]
    company = state["company"]
    years = state.get("year", ["2024"])

    corp_code = find_corporation_code(company)
    if corp_code.startswith("[ERROR]"):
        return {**state, "answer": corp_code}

    fin_blocks = []
    for y in years:
        rows = get_financial_state(corp_code, y, "11011", "CFS")
        if rows:
            fin_blocks.append(f"📅 {y}년 재무제표:\n" + "\n".join(rows))

    structured_financial = "\n\n".join(fin_blocks)
    answer = financial_chain1.invoke({
        "financial_data": structured_financial,
        "question": question,
        "resolved_corp_name": company,
    })

    updated_history = state.get("chat_history", []).copy()
    updated_history.append({"role": "user", "content": question})
    updated_history.append({"role": "assistant", "content": answer})

    return {
        **state,
        "answer": answer,
        "chat_history": updated_history
    }

def handle_financial2(state: ChatState) -> dict:
    question = state["question"]
    company = state["company"]
    years = state.get("year", ["2024"])

    corp_code = find_corporation_code(company)
    if corp_code.startswith("[ERROR]"):
        return {**state, "answer": corp_code}

    fin_blocks = []
    for y in years:
        rows = get_financial_state(corp_code, y, "11011", "CFS")
        if rows:
            fin_blocks.append(f"📅 {y}년 재무제표:\n" + "\n".join(rows))

    structured_financial = "\n\n".join(fin_blocks)
    answer = financial_chain2.invoke({
        "financial_data": structured_financial,
        "question": question,
        "resolved_corp_name": company,
    })

    updated_history = state.get("chat_history", []).copy()
    updated_history.append({"role": "user", "content": question})
    updated_history.append({"role": "assistant", "content": answer})

    return {
        **state,
        "answer": answer,
        "chat_history": updated_history
    }

def handle_financial3(state: ChatState) -> dict:
    question = state["question"]
    company = state["company"]
    years = state.get("year", ["2024"])

    corp_code = find_corporation_code(company)
    if corp_code.startswith("[ERROR]"):
        return {**state, "answer": corp_code}

    fin_blocks = []
    for y in years:
        rows = get_financial_state(corp_code, y, "11011", "CFS")
        if rows:
            fin_blocks.append(f"📅 {y}년 재무제표:\n" + "\n".join(rows))

    structured_financial = "\n\n".join(fin_blocks)
    answer = financial_chain3.invoke({
        "financial_data": structured_financial,
        "question": question,
        "resolved_corp_name": company,
    })

    updated_history = state.get("chat_history", []).copy()
    updated_history.append({"role": "user", "content": question})
    updated_history.append({"role": "assistant", "content": answer})

    return {
        **state,
        "answer": answer,
        "chat_history": updated_history
    }




def handle_business1(state: ChatState) -> dict:
    question = state["question"]
    docs = business_retriever.get_relevant_documents(question)
    context = "\n\n".join(doc.page_content for doc in docs)
    answer = business_chain1.invoke({"context": context, "question": question})
    updated_history = state.get("chat_history", []).copy()
    updated_history.append({"role": "user", "content": question})
    updated_history.append({"role": "assistant", "content": answer})

    return {
        **state,
        "answer": answer,
        "chat_history": updated_history
    }

def handle_business2(state: ChatState) -> dict:
    question = state["question"]
    docs = business_retriever.get_relevant_documents(question)
    context = "\n\n".join(doc.page_content for doc in docs)
    answer = business_chain2.invoke({"context": context, "question": question})
    updated_history = state.get("chat_history", []).copy()
    updated_history.append({"role": "user", "content": question})
    updated_history.append({"role": "assistant", "content": answer})

    return {
        **state,
        "answer": answer,
        "chat_history": updated_history
    }


def handle_business3(state: ChatState) -> dict:
    question = state["question"]
    docs = business_retriever.get_relevant_documents(question)
    context = "\n\n".join(doc.page_content for doc in docs)
    answer = business_chain3.invoke({"context": context, "question": question})
    updated_history = state.get("chat_history", []).copy()
    updated_history.append({"role": "user", "content": question})
    updated_history.append({"role": "assistant", "content": answer})

    return {
        **state,
        "answer": answer,
        "chat_history": updated_history
    }

def handle_hybrid1(state: ChatState) -> dict:
    question = state["question"]
    company = state["company"]
    years = state.get("year", ["2024"])

    corp_code = find_corporation_code(company)
    if corp_code.startswith("[ERROR]"):
        return {**state, "answer": corp_code}

    def try_get_financial_strict(corp_code: str, year: str) -> str:
        rows = get_financial_state(corp_code, year, "11011", "CFS")
        if rows and "[API 오류]" not in rows[0]:
            return f"📅 {year}년 (CFS):\n" + "\n".join(rows)
        return f"📅 {year}년 재무제표: 유효한 데이터를 찾을 수 없습니다."

    fin = "\n\n".join([try_get_financial_strict(corp_code, y) for y in years])
    acct_docs = accounting_retriever.invoke(question)
    biz_docs = business_retriever.invoke(question)

    acct = "\n\n".join(doc.page_content for doc in acct_docs)
    biz = "\n\n".join(doc.page_content for doc in biz_docs)

    answer = hybrid_chain1.invoke({
        "question": question,
        "acct": acct,
        "biz": biz,
        "fin": fin
    })

    updated_history = state.get("chat_history", []).copy()
    updated_history.append({"role": "user", "content": question})
    updated_history.append({"role": "assistant", "content": answer})

    return {
        **state,
        "answer": answer,
        "chat_history": updated_history
    }

def handle_hybrid2(state: ChatState) -> dict:
    question = state["question"]
    company = state["company"]
    years = state.get("year", ["2024"])

    corp_code = find_corporation_code(company)
    if corp_code.startswith("[ERROR]"):
        return {**state, "answer": corp_code}

    def try_get_financial_strict(corp_code: str, year: str) -> str:
        rows = get_financial_state(corp_code, year, "11011", "CFS")
        if rows and "[API 오류]" not in rows[0]:
            return f"📅 {year}년 (CFS):\n" + "\n".join(rows)
        return f"📅 {year}년 재무제표: 유효한 데이터를 찾을 수 없습니다."

    fin = "\n\n".join([try_get_financial_strict(corp_code, y) for y in years])
    acct_docs = accounting_retriever.invoke(question)
    biz_docs = business_retriever.invoke(question)

    acct = "\n\n".join(doc.page_content for doc in acct_docs)
    biz = "\n\n".join(doc.page_content for doc in biz_docs)

    answer = hybrid_chain2.invoke({
        "question": question,
        "acct": acct,
        "biz": biz,
        "fin": fin
    })

    updated_history = state.get("chat_history", []).copy()
    updated_history.append({"role": "user", "content": question})
    updated_history.append({"role": "assistant", "content": answer})

    return {
        **state,
        "answer": answer,
        "chat_history": updated_history
    }

def handle_hybrid3(state: ChatState) -> dict:
    question = state["question"]
    company = state["company"]
    years = state.get("year", ["2024"])

    corp_code = find_corporation_code(company)
    if corp_code.startswith("[ERROR]"):
        return {**state, "answer": corp_code}

    def try_get_financial_strict(corp_code: str, year: str) -> str:
        rows = get_financial_state(corp_code, year, "11011", "CFS")
        if rows and "[API 오류]" not in rows[0]:
            return f"📅 {year}년 (CFS):\n" + "\n".join(rows)
        return f"📅 {year}년 재무제표: 유효한 데이터를 찾을 수 없습니다."

    fin = "\n\n".join([try_get_financial_strict(corp_code, y) for y in years])
    acct_docs = accounting_retriever.invoke(question)
    biz_docs = business_retriever.invoke(question)

    acct = "\n\n".join(doc.page_content for doc in acct_docs)
    biz = "\n\n".join(doc.page_content for doc in biz_docs)

    answer = hybrid_chain3.invoke({
        "question": question,
        "acct": acct,
        "biz": biz,
        "fin": fin
    })

    updated_history = state.get("chat_history", []).copy()
    updated_history.append({"role": "user", "content": question})
    updated_history.append({"role": "assistant", "content": answer})

    return {
        **state,
        "answer": answer,
        "chat_history": updated_history
    }

def elief(state: ChatState) -> dict:
    question = state["question"]
    chat_history = state.get("chat_history", [])

    # chat_history를 포맷하여 함께 전달
    response = simple_chain.invoke({
        "question": question,
        "chat_history": chat_history
    })

    # chat_history에 assistant 응답도 추가
    updated_history = state.get("chat_history", []).copy()
    updated_history.append({"role": "user", "content": question})
    updated_history.append({"role": "assistant", "content": response})

    return {
        **state,
        "answer": response,
        "chat_history": updated_history
    }