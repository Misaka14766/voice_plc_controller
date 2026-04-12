from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage

from .base import BaseLLM, LLMResponse
from backend.config import settings

_plc_instance = None

def set_plc_instance(plc):
    global _plc_instance
    _plc_instance = plc

@tool
def plc_read(variable: str, data_type: str = "INT") -> str:
    """读取 PLC 变量值。variable 为变量完整路径（如 MAIN.TestInt），data_type 可选 BOOL/INT/REAL/STRING"""
    if _plc_instance is None:
        return "PLC 未连接"
    try:
        val = _plc_instance.read(variable, data_type)
        return f"{variable} 当前值为 {val}"
    except Exception as e:
        return f"读取失败：{e}"

@tool
def plc_write(variable: str, value: str, data_type: str = "INT") -> str:
    """写入 PLC 变量。variable 为变量完整路径，value 为要写入的值，data_type 可选 BOOL/INT/REAL/STRING"""
    if _plc_instance is None:
        return "PLC 未连接"
    success = _plc_instance.write(variable, value, data_type)
    if success:
        return f"成功将 {variable} 设置为 {value}"
    else:
        return f"写入 {variable} 失败，请检查变量名或类型"

@tool
def plc_list_variables() -> str:
    """列出 PLC 中所有可访问的变量（真实从 PLC 获取），同时包含配置的物理名称映射"""
    if _plc_instance is None:
        return "PLC 未连接"
    try:
        symbols = _plc_instance.get_all_symbols()
        if not symbols:
            return "未找到任何 PLC 变量，请检查连接或程序配置"

        lines = ["PLC 中可访问的变量列表："]
        # 获取物理映射，用于补充显示
        mappings = settings.mappings
        reverse_map = {info['variable']: name for name, info in mappings.items()}

        for sym in symbols:
            name = sym.get('name', '')
            var_type = sym.get('type', 'UNKNOWN')
            comment = sym.get('comment', '')
            physical_hint = reverse_map.get(name, '')
            if physical_hint:
                physical_hint = f" (物理名: {physical_hint})"
            lines.append(f"- {name} : {var_type}{physical_hint} {comment}")

        return "\n".join(lines)
    except Exception as e:
        return f"获取变量列表失败：{e}"


class OpenAICompatibleLLM(BaseLLM):
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
        )
        self.tools = [plc_read, plc_write, plc_list_variables]
        self.system_prompt = self._build_system_prompt()
        self._agent = None

    def _build_system_prompt(self) -> str:
        """构建包含物理映射信息的系统提示词"""
        base_prompt = "你是工业语音助手，可控制PLC。回答要简短，适合语音播报。"
        mappings = settings.mappings
        if mappings:
            mapping_text = "\n当前配置的物理名称映射：\n"
            for physical_name, info in mappings.items():
                mapping_text += (
                    f"- 物理名称: {physical_name} -> 变量路径: {info['variable']}, "
                    f"类型: {info.get('type', 'REAL')}, "
                    f"描述: {info.get('description', '')}\n"
                )
            mapping_text += "\n当用户使用物理名称时，优先使用对应的变量路径。"
            return base_prompt + mapping_text
        return base_prompt

    def _get_agent(self):
        if self._agent is None:
            self._agent = create_agent(
                model=self.llm,
                tools=self.tools,
                system_prompt=self.system_prompt,
            )
        return self._agent

    async def generate(self, messages, tools=None):
        if not messages:
            return LLMResponse(content="")

        langchain_messages = []
        for msg in messages:
            if msg["role"] == "user":
                langchain_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                langchain_messages.append(AIMessage(content=msg["content"]))

        agent = self._get_agent()
        result = await agent.ainvoke({"messages": langchain_messages})

        response_content = ""
        if "messages" in result and result["messages"]:
            last_message = result["messages"][-1]
            response_content = last_message.content

        return LLMResponse(content=response_content)