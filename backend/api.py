from flask import Flask, request, jsonify
from google import genai

app = Flask(__name__)

client = genai.Client(api_key="AIzaSyDOp_W8MM3i_PKzsxLKcirvIoGrjAIgNus")

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    prompt = data.get("prompt")

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return jsonify({
            "response": response.text
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(debug=True)