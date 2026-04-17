import streamlit as st
import time
import datetime
from openai import OpenAI
import os
from dotenv import load_dotenv
#api工作区
load_dotenv("G:\PythonAI\AGENT\.venv\AI\KEY.env")
key = os.getenv("ZHIPU_API_KEY")

client = OpenAI(
    api_key=key,# 从 bigmodel.cn 获取
    base_url="https://open.bigmodel.cn/api/paas/v4",
    )

#人设注入
syetem_prompt ="""
你是食堂智选侠，一个专业的食堂推荐助手。你的任务是：
1. 根据用户的口味偏好（如辣、清淡、酸甜）推荐食堂菜品。
2. 兼顾营养均衡，提供高蛋白、低脂、素食等选项。
3. 回答简洁友好，每次推荐2-3个菜品并附带简单理由。
请注意：直接输出最终推荐内容，不要包含任何思考过程或推理步骤。
"""

#对话初始化
# ---------- 初始化 session_state ----------
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": syetem_prompt}]

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

# ---------- 辅助函数：保存当前对话到历史 ----------
def save_current_conversation():
    """如果当前对话非空（至少有一条用户消息），则保存到历史列表"""
    has_user_msg = any(msg["role"] != "system" for msg in st.session_state.messages)
    if has_user_msg:
        timestamp = datetime.datetime.now().strftime("%m-%d %H:%M")
        st.session_state.conversation_history.append({
            "time": timestamp,
            "messages": st.session_state.messages.copy()
        })

# ---------- 侧边栏 UI ----------
with st.sidebar:
    if st.button("➕ 新建对话", use_container_width=True):
        save_current_conversation()
        st.session_state.messages = [{"role": "system", "content": syetem_prompt}]
        st.rerun()

    st.divider()
    st.subheader("📚 历史对话")

    if st.session_state.conversation_history:
        # 倒序显示，最新的在上
        for idx, conv in enumerate(reversed(st.session_state.conversation_history)):
            first_user_msg = next(
                (m["content"] for m in conv["messages"] if m["role"] == "user"),
                "空对话"
            )
            preview = first_user_msg[:20] + "..." if len(first_user_msg) > 20 else first_user_msg
            label = f"{conv['time']} - {preview}"

            if st.button(label, key=f"hist_{idx}", use_container_width=True):
                st.session_state.messages = conv["messages"].copy()
                st.rerun()
    else:
        st.caption("暂无历史对话")


# ---------- 主界面 ----------
st.title("欢迎使用食堂智选侠")
st.subheader("--基于口味与营养推荐餐品")
with st.container():
    st.info("💡 小贴士：选择你今天的口味偏好，系统将智能推荐最佳餐品")

# ---------- 渲染当前对话历史 ----------
# 显示历史对话（跳过 system 消息不显示）
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

#AI主体调用
# ---------- 处理用户输入 ----------
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
                    model="GLM-4-Flash-250414",
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
                    st.error("返回了空内容，请重试。")
                    # 输出 finish_reason 帮助判断
                    finish_reason = response.choices[0].finish_reason
                    st.warning(f"完成原因: {finish_reason}")

            except Exception as e:
                st.error(f"请求失败: {e}")
                st.exception(e)
        time.sleep(1)
    st.rerun()