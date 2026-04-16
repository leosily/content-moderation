import requests
from config import settings

def text_audit(content: str) -> dict:
    """
    调用百度智能云文本审核API，实现自媒体文本违规检测
    返回格式：{"status": "PASS/VIOLATE/failed", "violate_type": str, "violate_detail": str}
    """
    try:
        # 百度AI文本审核接口参数
        ai_config = settings.AI_CONFIG or {}
        url = settings.AI_CONFIG["audit_url"]
        #access_token = str(ai_config.get("access_token") or "").strip()
        authorization = str(ai_config.get("authorization") or "").strip()
        strategy_id = ai_config.get("strategy_id")

        query_params = {}
        """if access_token:
            query_params["access_token"] = access_token"""

        payload = {
            "text": content,
            "confidence": 90  # 置信度阈值，高于90判定为违规
        }
        if strategy_id not in (None, ""):
            payload["strategyId"] = str(strategy_id)

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        if authorization:
            headers["Authorization"] = authorization
        
        # 发送POST请求调用API
        response = requests.post(url, params=query_params, headers=headers, data=payload, timeout=10)
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
