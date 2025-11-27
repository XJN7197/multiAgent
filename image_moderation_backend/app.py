import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from zai import ZhipuAiClient
from sensitive_data import sensitive_keywords

app = Flask(__name__)
CORS(app)

ZHIPU_AI_API_KEY = os.getenv("ZHIPU_AI_API_KEY")

if not ZHIPU_AI_API_KEY:
    raise ValueError("ZHIPU_AI_API_KEY environment variable not set.")

client = ZhipuAiClient(api_key=ZHIPU_AI_API_KEY)

def extract_text_from_image(image_data_base64):
    prompt_text = "请输出这张图片中的所有文字，直接输出提取的文字内容，不要包含任何其他解释或markdown标记。如果图片中没有文字，请输出空字符串。"
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt_text},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data_base64}"}}
            ]
        }
    ]
    
    try:
        response = client.chat.completions.create(
            model="GLM-4.1V-Thinking-Flash", # Using a vision model for OCR
            messages=messages,
            stream=False,
            temperature=0.1,
            max_tokens=4096
        )
        text = response.choices[0].message.content
        # Clean up potential markdown formatting if the model adds it despite instructions
        text = text.replace("```text", "").replace("```", "").strip()
        return text
    except Exception as e:
        print(f"Error during LLM OCR: {e}")
        return ""

import json

@app.route('/moderate_image', methods=['POST'])
def moderate_image():
    if 'image' not in request.json:
        return jsonify({"error": "No image data provided"}), 400

    image_data_base64 = request.json['image']

    extracted_text = extract_text_from_image(image_data_base64)
    print(f"Extracted text from image: {extracted_text}")

    # 1. Preliminary Check (Sensitive Keywords)
    preliminary_check = {
        "has_risk": False,
        "matched_keywords": []
    }
    for keyword in sensitive_keywords:
        if keyword in extracted_text.lower():
            preliminary_check["has_risk"] = True
            preliminary_check["matched_keywords"].append(keyword)
    
    # 2. LLM Check
    llm_result = {}
    if preliminary_check["has_risk"]:
        print("Sensitive keywords found. Skipping LLM check.")
        final_decision = "reject"
    else:
        prompt_text = f"请客观分析该 meme 中是否包含不安全或者敏感内容。图片中提取的文字：{extracted_text}。请以纯 JSON 格式回答，不要包含 markdown 格式标记（如 ```json ... ```），JSON 需包含以下字段：risk_level (string, 选项: 'high', 'medium', 'low', 'safe'), reasoning (string, 详细依据), suggestion (string, 操作建议, 如: 'block', 'review', 'pass')。"

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data_base64}"}}
                ]
            }
        ]

        try:
            response = client.chat.completions.create(
                model="GLM-4.1V-Thinking-Flash",
                messages=messages,
                # thinking={
                #     "type": "enabled",
                # }, # Thinking mode might interfere with strict JSON output if not handled carefully, disabling for structured output stability or keeping if needed but parsing carefully. Let's keep it simple first.
                stream=False,
                max_tokens=4096,
                temperature=0.1 # Lower temperature for more deterministic JSON
            )
            print(f"ZhipuAI API Response: {response}")
            
            content = response.choices[0].message.content
            # Try to parse JSON. It might be wrapped in markdown code blocks despite instructions.
            cleaned_content = content.replace("```json", "").replace("```", "").strip()
            try:
                llm_result = json.loads(cleaned_content)
            except json.JSONDecodeError:
                print("Failed to parse JSON from LLM response. Fallback to raw text.")
                llm_result = {
                    "risk_level": "unknown",
                    "reasoning": content,
                    "suggestion": "review"
                }

        except Exception as e:
            print(f"Error calling ZhipuAI API: {e}")
            llm_result = {
                "error": str(e),
                "risk_level": "unknown",
                "reasoning": "Error calling AI service",
                "suggestion": "review"
            }

        # 3. Final Decision Logic (Simple aggregation)
        final_decision = "pass"
        if llm_result.get("risk_level") in ["high", "medium"] or llm_result.get("suggestion") == "block":
            final_decision = "reject"
        elif llm_result.get("suggestion") == "review" or llm_result.get("risk_level") == "unknown":
            final_decision = "manual_review"

    response_data = {
        "ocr_text": extracted_text,
        "preliminary_check": preliminary_check,
        "llm_check": llm_result if llm_result else None,
        "final_decision": final_decision
    }

    return jsonify(response_data), 200

@app.route('/')
def hello_world():
    return 'Hello, this is the Image Moderation Backend!'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)