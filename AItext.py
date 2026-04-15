import time
import streamlit as st
import datetime as date
from openai import OpenAI

with st.sidebar:
    if st.button("➕ 新建对话", use_container_width=True):
        # 重置消息历史，仅保留 system prompt
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.rerun()

st.title("欢迎使用食堂智选侠")
st.subheader("--基于口味与营养推荐餐品")
with st.container():
    st.info("💡 小贴士：选择你今天的口味偏好，系统将智能推荐最佳餐品")

SYSTEM_PROMPT = """
你是食堂智选侠，一个专业的食堂推荐助手。你的任务是：
1. 根据用户的口味偏好（如辣、清淡、酸甜）推荐食堂菜品。
2. 兼顾营养均衡，提供高蛋白、低脂、素食等选项。
3. 回答简洁友好，每次推荐2-3个菜品并附带简单理由。
请注意：直接输出最终推荐内容，不要包含任何思考过程或推理步骤。

"""

#初始化对话
if "messages" not in st.session_state:
    # 第一条必须是 system 消息
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

# 显示历史对话（跳过 system 消息不显示）
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

ZHIPU_API_KEY1 = "65220d78711242b0b2e5ecb1d2464caf.xHafJGt7Yqo02shP"
client = OpenAI(
    api_key=ZHIPU_API_KEY1,# 从 bigmodel.cn 获取
    base_url="https://open.bigmodel.cn/api/paas/v4",
)


if prompt := st.chat_input("描述你的口味，例如：今天想吃辣的，要高蛋白..."):
    # 1. 显示并保存用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. 调用 AI 生成回答（使用完整对话历史）
    with st.chat_message("assistant"):
        with st.spinner("🤔 AI正在为你搭配美食..."):
            try:
                response = client.chat.completions.create(
                    model="glm-4.7-flash",
                    messages=st.session_state.messages,
                    temperature=0.7,
                    max_tokens=1000,
                    timeout=30.0,
                    extra_body={"thinking": {"type": "disabled"}}
                )
                # ---------- 调试代码：查看完整响应 ----------
                #已删除
                answer = response.choices[0].message.content

                if answer:
                    st.markdown(answer)

                else:
                    st.error("AI 返回了空内容，请重试。")
                    # 输出 finish_reason 帮助判断
                    finish_reason = response.choices[0].finish_reason
                    st.warning(f"完成原因: {finish_reason}")

            except Exception as e:
                st.error(f"请求失败: {e}")
                st.exception(e)
        time.sleep(0.01)
    

