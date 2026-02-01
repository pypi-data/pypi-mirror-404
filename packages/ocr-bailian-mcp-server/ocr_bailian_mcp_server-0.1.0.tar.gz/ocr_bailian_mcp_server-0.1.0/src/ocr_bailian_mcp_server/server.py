# -*- coding: utf-8 -*-
from mcp.server.fastmcp import FastMCP
from pydantic import Field
import os
import logging
import dashscope
import textwrap
from typing import Optional

logger = logging.getLogger('mcp')
settings = {'log_level': 'DEBUG'}

# 初始化 MCP 服务
mcp = FastMCP('bailian-ocr-mcp-server', log_level='ERROR')

# 从环境变量读取配置
BAI_LIAN_API_KEY = os.environ.get("BAI_LIAN_API_KEY")
# 注意：DashScope 目前没有 qwen3-vl-plus，请使用官方支持的模型
MODEL_NAME = os.environ.get("BAI_LIAN_MODEL_NAME", "qwen3-vl-plus")


@mcp.tool(name='身份证信息提取器', description='从身份证图片中提取结构化信息，支持 URL 或 Base64 编码')
async def extract_text_from_image(
        image_url: Optional[str] = Field(default=None, description='图片的 URL 地址'),
        image_base64: Optional[str] = Field(default=None,
                                            description='图片的 Base64 编码（纯 base64 字符串，不含 data: 前缀）')
) -> str:
    """
    使用百炼 VL 模型从身份证图片中提取结构化信息。
    优先使用 image_url，若为空则使用 image_base64。
    返回严格格式化的 JSON 字符串。
    """
    logger.info(f'收到请求，image_url: {image_url is not None}, image_base64: {image_base64 is not None}')

    api_key = BAI_LIAN_API_KEY
    model_name = MODEL_NAME

    if not api_key:
        return "错误：服务未配置 BAI_LIAN_API_KEY 环境变量。"
    if not model_name:
        return "错误：服务未配置 BAI_LIAN_MODEL_NAME 环境变量。"
    if not image_url and not image_base64:
        return "错误：必须提供 image_url 或 image_base64 参数之一。"

    # === 构造结构化提示词 ===
    prompt = textwrap.dedent('''\
        你是一位专业的身份证信息识别专家。请从提供的身份证图片中**精确提取所有可见文字信息**，并严格按照以下 JSON 格式输出，不要包含任何额外说明、解释或 Markdown：

        {
          "姓名": "XXX",
          "性别": "XXX",
          "民族": "XXX",
          "出生日期": "YYYY年MM月DD日",
          "住址": "XXX",
          "公民身份号码": "XXX",
          "签发机关": "XXX",
          "有效期限": "YYYY.MM.DD-YYYY.MM.DD 或 长期"
        }

        ## 格式要求：
        1. 所有字段必须存在，若图片中未显示某字段，则固定填写 "未知"。
        2. 日期格式必须严格按示例（如 "1990年05月20日"、"2020.01.01-2030.01.01"）。
        3. "住址" 字段需保留完整地址，包括省市区和详细门牌号。
        4. 不要添加任何注释、换行、Markdown 或额外字段。
        5. 仅输出纯 JSON，不要用 ```json 包裹。
    ''').strip()

    # === 构造 content 列表 ===
    content = [{'text': prompt}]

    if image_url:
        content.append({'image': image_url})
    else:

        content.append({'image': image_base64})

    # === 调用百炼 VL 模型 ===
    try:
        response = dashscope.MultiModalConversation.call(
            model=model_name,
            messages=[{'role': 'user', 'content': content}],
            api_key=api_key
        )

        if response.status_code == 200:
            text_result = response.output.choices[0].message.content[0]['text']
            return text_result.strip()
        else:
            error_msg = getattr(response, 'message', '未知错误')
            logger.error(f'百炼 API 调用失败: {error_msg}')
            return f"API 调用失败: {error_msg}"

    except Exception as e:
        logger.exception(f'处理请求时发生异常: {e}')
        return f"处理过程中发生错误: {str(e)}"


def main():
    log_level = os.getenv("LOG_LEVEL", "INFO")
    logging.basicConfig(level=getattr(logging, log_level.upper()))

    if not BAI_LIAN_API_KEY:
        logger.error("缺少环境变量 BAI_LIAN_API_KEY，服务启动失败。")
        return
    if not MODEL_NAME:
        logger.error("缺少环境变量 BAI_LIAN_MODEL_NAME，服务启动失败。")
        return

    logger.info(f"服务启动，使用模型: {MODEL_NAME}")
    mcp.run(transport='stdio')


def run():
    mcp.run(transport='stdio')


if __name__ == '__main__':
    run()
