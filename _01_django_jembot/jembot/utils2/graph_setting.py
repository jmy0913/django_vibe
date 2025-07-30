from typing import TypedDict, Literal, List, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from.graph_node import ChatState, ChatTurn, classify, extract_entities, handle_accounting1, handle_accounting2, handle_accounting3, handle_financial1, handle_financial2, handle_financial3, handle_hybrid1, handle_hybrid2, handle_hybrid3, handle_business1, handle_business2, handle_business3, route_from_extract, route_from_classify, elief, route_from_extract_with_level

def graph_setting():
    # LangGraph 정의
    graph = StateGraph(ChatState)


    # 노드 등록
    graph.add_node("classify", classify)  # 질문 분류
    graph.add_node("extract", extract_entities)  # 회사/년 추출
    graph.add_node("accounting_basic", handle_accounting1)
    graph.add_node("accounting_intermediate", handle_accounting2)
    graph.add_node("accounting_advanced", handle_accounting3)
    graph.add_node("finance_basic", handle_financial1)
    graph.add_node("finance_intermediate", handle_financial2)
    graph.add_node("finance_advanced", handle_financial3)
    graph.add_node("business_basic", handle_business1)
    graph.add_node("business_intermediate", handle_business2)
    graph.add_node("business_advanced", handle_business3)
    graph.add_node("hybrid_basic", handle_hybrid1)
    graph.add_node("hybrid_intermediate", handle_hybrid2)
    graph.add_node("hybrid_advanced", handle_hybrid3)
    graph.add_node("simple", elief)



    # 흐름 정의
    graph.set_entry_point("classify")

    # classify 후 route와 level에 따라 분기
    graph.add_conditional_edges(
        "classify",
        route_from_classify,  # classify 함수에서 route를 분류
        {
            "accounting": "extract",
            "finance": "extract",
            "business": "extract",
            "hybrid": "extract",
            "simple": "simple"
        }
    )

    # extract 후 level과 route에 따라 분기
    graph.add_conditional_edges(
        "extract",
        route_from_extract_with_level,  # route와 level을 함께 판단
        {
            "accounting_basic": "accounting_basic",
            "accounting_intermediate": "accounting_intermediate",
            "accounting_advanced": "accounting_advanced",
            "finance_basic": "finance_basic",
            "finance_intermediate": "finance_intermediate",
            "finance_advanced": "finance_advanced",
            "business_basic": "business_basic",
            "business_intermediate": "business_intermediate",
            "business_advanced": "business_advanced",
            "hybrid_basic": "hybrid_basic",
            "hybrid_intermediate": "hybrid_intermediate",
            "hybrid_advanced": "hybrid_advanced"
        }
    )

    # 종료 노드 지정
    for node in [
        "accounting_basic", "accounting_intermediate", "accounting_advanced",
        "finance_basic", "finance_intermediate", "finance_advanced",
        "business_basic", "business_intermediate", "business_advanced",
        "hybrid_basic", "hybrid_intermediate", "hybrid_advanced",
        "simple"
    ]:
        graph.add_edge(node, END)

    # 그래프 컴파일
    memory = MemorySaver()
    compiled_graph = graph.compile(checkpointer=memory)

    return compiled_graph