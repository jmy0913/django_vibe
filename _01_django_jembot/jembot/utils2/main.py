from .graph_setting import graph_setting

compiled_graph = graph_setting()

# 초급 전체 분기 실행 함수
def run_langraph(user_input, config_id, level='basic', chat_history=None):
    config = {"configurable": {"thread_id": config_id}}
    
    # chat_history가 None이면 빈 리스트로 초기화
    if chat_history is None:
        chat_history = []
    
    result = compiled_graph.invoke({
        "question": user_input,
        "level": level,
        "chat_history": chat_history,
    }, config=config)

    return result