import requests
from config import settings

def text_audit(content: str) -> dict:
    """
    调用百度智能云文本审核API，实现自媒体文本违规检测
    返回格式：{"status": "PASS/VIOLATE/failed", "violate_type": str, "violate_detail": str}
    """
    try:
        # 百度AI文本审核接口参数
        url = settings.AI_CONFIG["audit_url"]
        params = {
            "access_token": settings.AI_CONFIG["access_token"],
            "text": content,
            "confidence": 90  # 置信度阈值，高于90判定为违规
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        # 发送POST请求调用API
        response = requests.post(url, headers=headers, data=params, timeout=10)
        response.raise_for_status()  # 抛出HTTP请求异常
        result = response.json()
        
        # 解析API返回结果（百度API标准返回格式）
        if result.get("error_code"):
            return {
                "status": "failed",
                "msg": f"AI接口调用失败：{result.get('error_msg', '未知错误')}"
            }
        
        # conclusionType=1：通过；2：违规；3：疑似；4：审核失败
        conclusion_type = result.get("conclusionType")
        if conclusion_type == 1:
            return {
                "status": "PASS",
                "violate_type": None,
                "violate_detail": None
            }
        elif conclusion_type in [2, 3]:
            # 提取违规类型和详情（取第一个违规数据）
            data_list = result.get("data", [{}])
            first_data = data_list[0] if data_list else {}
            return {
                "status": "VIOLATE",
                "violate_type": first_data.get("subType", "未知违规"),
                "violate_detail": first_data.get("hitMsg", "无详细违规信息")
            }
        else:
            return {"status": "failed", "msg": "AI审核结果异常"}
    except Exception as e:
        return {"status": "failed", "msg": f"AI接口调用异常：{str(e)}"}
