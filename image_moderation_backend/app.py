import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from zai import ZhipuAiClient
import base64
import pytesseract
from PIL import Image
import io

app = Flask(__name__)
CORS(app) 

ZHIPU_AI_API_KEY = os.getenv("ZHIPU_AI_API_KEY")

if not ZHIPU_AI_API_KEY:
    raise ValueError("ZHIPU_AI_API_KEY environment variable not set.")

client = ZhipuAiClient(api_key=ZHIPU_AI_API_KEY)

def extract_text_from_image(image_data_base64):
    try:
        image_bytes = base64.b64decode(image_data_base64)
        image = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(image, lang='chi_sim+eng') # Use simplified Chinese and English
        return text
    except Exception as e:
        print(f"Error during OCR: {e}")
        return ""

@app.route('/moderate_image', methods=['POST'])
def moderate_image():
    if 'image' not in request.json:
        return jsonify({"error": "No image data provided"}), 400

    image_data_base64 = request.json['image']
    
    extracted_text = extract_text_from_image(image_data_base64)
    print(f"Extracted text from image: {extracted_text}")

    # Local static matching rules
    sensitive_keywords = ["敏感词1", "敏感词2", "unsafe_word"]
    for keyword in sensitive_keywords:
        if keyword in extracted_text.lower():
            return jsonify({"result": f"是，图片包含敏感词: {keyword}"}), 200

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": f"请客观分析该 meme 中是否包含不安全或者敏感，请回答‘是’或‘否’，并说明详细的依据。图片中提取的文字：{extracted_text}"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data_base64}"}}
            ]
        }
    ]

    try:
        response = client.chat.completions.create(
            model="GLM-4.1V-Thinking-Flash",
            messages=messages,
            thinking={
                "type": "enabled",
            },
            stream=False, # For a single response, stream can be False
            max_tokens=4096,
            temperature=0.7
        )
        print(f"ZhipuAI API Response: {response}")
        print(f"ZhipuAI API Status Code: 200 (simulated for successful response)") # ZhipuAI client doesn't directly expose HTTP status code for successful calls
        
        moderation_result = response.choices[0].message.content
        return jsonify({"result": moderation_result}), 200

    except Exception as e:
        print(f"Error calling ZhipuAI API: {e}")
        print(f"ZhipuAI API Status Code: 500 (simulated for error response)")
        return jsonify({"error": str(e)}), 500

@app.route('/')
def hello_world():
    return 'Hello, this is the Image Moderation Backend!'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
