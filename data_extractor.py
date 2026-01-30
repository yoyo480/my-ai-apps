import streamlit as st
import json
import pandas as pd
from openai import OpenAI
import io  # <--- 新增这一行！这是用来做虚拟文件的

# 设置页面标题
st.title("AI 招聘信息结构化助手")

# 输入框：用户粘贴招聘职位描述
jd_text = st.text_area("请粘贴招聘职位描述 (JD):", height=200)

# 提取按钮
if st.button("提取并生成 Excel"):
    if not jd_text:
        st.warning("请输入招聘职位描述！")
    else:
        # 构造Prompt
        prompt = f"""
        你是一个数据提取 API。必须且只能返回纯净的 JSON 格式数据。不要包含 markdown 标记（如 ```json），不要说任何废话。
        从以下文本中提取以下字段：
        - Position (职位名称)
        - Salary (薪资范围，如果没写就填'面议')
        - Skills (技能要求，用逗号分隔)
        - Education (学历要求)

        文本：{jd_text}
        """

        # 调用DeepSeek API
        client = OpenAI(api_key=st.secrets["DEEPSEEK_API_KEY"], base_url="https://api.siliconflow.cn/v1")
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3",
            messages=[
                {"role": "system", "content": "你是一个数据提取 API。必须且只能返回纯净的 JSON 格式数据。不要包含 markdown 标记（如 ```json），不要说任何废话。"},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        # 解析返回的JSON
        try:
            extracted_data = json.loads(response.choices[0].message.content)
            df = pd.DataFrame([extracted_data])

            # 展示提取的表格
            st.dataframe(df, hide_index=True)

            # 提供下载按钮
            # 1. 创建一个在内存里的虚拟文件（就像一个空盘子）
            output = io.BytesIO()
            # 2. 让 Pandas 把表格写入这个虚拟文件
            # engine='openpyxl' 是必须的，用来处理 xlsx 格式
    
            df.to_excel(output, index=False, engine='openpyxl')
            # 3. 关键动作：把指针拨回文件开头
            # (写完文件后指针在最后，不拨回去的话读出来是空的)
            output.seek(0)

            # 4. 生成下载按钮
            st.download_button(
                label="📥 下载 Excel 表格",
                data=output,             # 把这个虚拟文件塞给按钮
                file_name="招聘信息.xlsx", # 用户下载下来看到的文件名
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" # 告诉浏览器这是个 Excel
            )
        except json.JSONDecodeError:
            st.error("AI 返回的数据格式无效，请重试！")
