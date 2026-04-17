import streamlit as st
import time
import datetime
from openai import OpenAI
import os
from dotenv import load_dotenv
import pandas as pd

# ========== 菜品数据库 ==========(模拟数据)
dishes_df = pd.DataFrame([
    {"name": "清炒时蔬套餐", "calories": 200, "protein": 5, "fat": 8, "taste": "清淡", "health_goal": "减脂",
     "allergens": "无"},
    {"name": "鸡胸肉沙拉", "calories": 280, "protein": 30, "fat": 10, "taste": "清淡", "health_goal": "减脂",
     "allergens": "无"},
    {"name": "红烧肉套餐", "calories": 550, "protein": 20, "fat": 35, "taste": "浓郁", "health_goal": "常规",
     "allergens": "大豆"},
    {"name": "蒸鱼套餐", "calories": 350, "protein": 28, "fat": 12, "taste": "清淡", "health_goal": "增肌",
     "allergens": "鱼类"},
    {"name": "牛肉饭", "calories": 480, "protein": 25, "fat": 20, "taste": "浓郁", "health_goal": "增肌",
     "allergens": "无"},
    {"name": "麻婆豆腐饭", "calories": 420, "protein": 12, "fat": 18, "taste": "辣", "health_goal": "常规",
     "allergens": "大豆"},
    {"name": "酸辣土豆丝", "calories": 180, "protein": 3, "fat": 6, "taste": "酸辣", "health_goal": "减脂",
     "allergens": "无"},
])


# ========== 知识图谱推荐函数 ==========
def recommend_by_kg(health_goal=None, taste=None, allergens=None):
    """
    参数:
        health_goal: '减脂' / '增肌' / '常规' 或 None
        taste: '辣' / '清淡' / '酸辣' / '浓郁' 等
        allergens: 过敏原列表，如 ['大豆', '鱼类']
    返回: 推荐菜品列表（最多5个）
    """
    filtered = dishes_df.copy()

    # 过滤过敏原
    if allergens:
        for a in allergens:
            if a != "无":
                filtered = filtered[~filtered['allergens'].str.contains(a)]

    # 健康目标筛选
    if health_goal == '减脂':
        filtered = filtered[filtered['calories'] < 400]
        filtered = filtered[filtered['fat'] < 15]
        filtered = filtered.sort_values('calories')
    elif health_goal == '增肌':
        filtered = filtered[filtered['protein'] > 20]
        filtered = filtered.sort_values('protein', ascending=False)
    # 常规目标不过滤

    # 口味筛选（如果用户指定了口味）
    if taste and taste != "任意":
        # 模糊匹配：例如“辣”可以匹配“辣”、“酸辣”
        filtered = filtered[filtered['taste'].str.contains(taste) | (filtered['taste'] == taste)]

    # 如果结果太少，放宽条件：去掉口味限制再试一次
    if len(filtered) < 2 and taste:
        filtered = dishes_df.copy()
        if allergens:
            for a in allergens:
                if a != "无":
                    filtered = filtered[~filtered['allergens'].str.contains(a)]
        if health_goal == '减脂':
            filtered = filtered[filtered['calories'] < 400]
        elif health_goal == '增肌':
            filtered = filtered[filtered['protein'] > 20]
        # 不再限制口味

    return filtered.head(5).to_dict('records')

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
1. 根据用户的口味偏好（如辣、清淡、酸甜）、健康目标（减脂/增肌/常规）、过敏原，推荐合适的菜品。
2. 当你需要推荐菜品时，必须在回复中按以下格式输出推荐请求：
   [RECOMMEND: 健康目标, 口味, 过敏原列表]
   例如：
   - 用户说“我想减脂，不吃大豆” → 输出 [RECOMMEND: 减脂, 任意, 大豆]
   - 用户说“今天想吃辣的，高蛋白” → 输出 [RECOMMEND: 增肌, 辣, 无]
   然后等待系统自动填充推荐结果。不要自己编造菜品。
3. 如果用户只是闲聊或询问其他问题（如食堂位置、营业时间），请正常回答，不需要输出推荐请求。
4. 回答要简洁友好。
"""

#对话初始化
# ---------- 初始化 session_state ----------
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": syetem_prompt}]

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

# ---------- 辅助函数：保存当前对话到历史 ----------
def save_current_conversation():
    """保存当前对话到历史，如果与最新一条历史记录内容相同则跳过"""
    has_user_msg = any(msg["role"] != "system" for msg in st.session_state.messages)
    if not has_user_msg:
        return

    current_messages = st.session_state.messages.copy()

    if st.session_state.conversation_history:
        last_conv = st.session_state.conversation_history[-1]
        if last_conv["messages"] == current_messages:
            return  # 内容重复，不再保存

    timestamp = datetime.datetime.now().strftime("%m-%d %H:%M")
    st.session_state.conversation_history.append({
        "time": timestamp,
        "messages": current_messages
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
    # 1. 显示用户消息
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        with placeholder.container():
            with st.spinner("🤔 AI正在分析您的需求..."):
                try:
                    # 临时构造消息（包含当前用户输入）
                    current_messages = st.session_state.messages + [{"role": "user", "content": prompt}]
                    response = client.chat.completions.create(
                        model="GLM-4-Flash-250414",
                        messages=current_messages,
                        temperature=0.7,
                        max_tokens=500,
                        timeout=30.0,
                        extra_body={"thinking": {"type": "disabled"}}
                    )
                    raw_answer = response.choices[0].message.content

                    # ---------- 解析推荐标记 ----------
                    import re

                    recommend_pattern = r'\[RECOMMEND:\s*([^,]+),\s*([^,]+),\s*([^\]]+)\]'
                    match = re.search(recommend_pattern, raw_answer)

                    if match:
                        # 提取参数
                        health_goal = match.group(1).strip()
                        taste = match.group(2).strip()
                        allergens_str = match.group(3).strip()
                        # 处理过敏原：如果是"无"则为空列表，否则按逗号分割（注意可能有空格）
                        if allergens_str == "无" or allergens_str == "无过敏":
                            allergens = []
                        else:
                            allergens = [a.strip() for a in allergens_str.split(',')]

                        # 调用推荐函数
                        rec_list = recommend_by_kg(
                            health_goal=health_goal if health_goal != "任意" else None,
                            taste=taste if taste != "任意" else None,
                            allergens=allergens
                        )

                        # 将推荐结果格式化为可读文本
                        if rec_list:
                            rec_text = "🍽️ 根据您的需求，为您推荐：\n"
                            for idx, dish in enumerate(rec_list, 1):
                                rec_text += f"{idx}. **{dish['name']}** - {dish['calories']}千卡，蛋白质{dish['protein']}g，口味{dish['taste']}\n"
                                if dish['allergens'] != "无":
                                    rec_text += f"   ⚠️ 含过敏原：{dish['allergens']}\n"
                            # 替换掉原始回复中的 [RECOMMEND:...] 标记
                            final_answer = re.sub(recommend_pattern, rec_text, raw_answer)
                        else:
                            final_answer = raw_answer.replace(match.group(0),
                                                              "😢 抱歉，没有找到完全符合您条件的菜品，请调整一下需求试试？")
                    else:
                        final_answer = raw_answer

                except Exception as e:
                    final_answer = f"❌ 请求失败，请稍后重试。\n错误详情：{e}"

        placeholder.markdown(final_answer)

    # 保存对话
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "assistant", "content": final_answer})
    st.rerun()
    time.sleep(1)
