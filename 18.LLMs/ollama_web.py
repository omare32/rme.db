from flask import Flask, render_template_string, request
import requests

app = Flask(__name__)

HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RME Chatbot Ver. 003</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f4f6fb; margin: 0; padding: 0; }
        .container { max-width: 600px; margin: 40px auto; background: #fff; border-radius: 10px; box-shadow: 0 2px 8px #0001; padding: 32px; }
        h1 { text-align: center; color: #333; }
        .model-info { text-align: center; background: #e0e7ff; color: #222; border-radius: 6px; padding: 8px 0; margin-bottom: 24px; font-weight: bold; }
        textarea { width: 100%; min-height: 80px; padding: 10px; border-radius: 6px; border: 1px solid #ccc; font-size: 1rem; }
        button { background: #4f8cff; color: #fff; border: none; padding: 12px 24px; border-radius: 6px; font-size: 1rem; cursor: pointer; margin-top: 12px; }
        button:hover { background: #2563eb; }
        .response { margin-top: 24px; background: #f0f4fa; padding: 16px; border-radius: 6px; white-space: pre-wrap; font-size: 1.05rem; }
        label { font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>RME Chatbot Rev003a</h1>
        <div class="model-info">Using Mistral v.{{ mistral_version }}</div>
        <form method="post">
            <label for="prompt">Enter your prompt:</label><br>
            <textarea id="prompt" name="prompt" required>{{ prompt or '' }}</textarea><br>
            <button type="submit">Send to Mistral</button>
        </form>
        {% if response %}
        <div class="response">
            <strong>Response:</strong><br>
            {{ response }}
        </div>
        {% endif %}
    </div>
</body>
</html>
'''

def get_mistral_version():
    try:
        r = requests.get('http://localhost:11434/api/tags', timeout=5)
        if r.status_code == 200:
            models = r.json().get('models', [])
            for model in models:
                if model['name'].startswith('mistral'):
                    # Try to extract version from model name or details
                    details = model.get('details', {})
                    param_size = details.get('parameter_size')
                    if param_size:
                        return param_size
                    # Fallback: try to parse from name
                    if '7b' in model['name'].lower():
                        return '7B'
            return '7B'  # Default if not found
        else:
            return '7B'
    except Exception:
        return '7B'

@app.route('/', methods=['GET', 'POST'])
def index():
    response = None
    prompt = None
    mistral_version = get_mistral_version()
    if request.method == 'POST':
        prompt = request.form['prompt']
        try:
            r = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': 'mistral:latest',
                    'prompt': prompt,
                    'stream': False
                },
                timeout=60
            )
            if r.status_code == 200:
                response = r.json().get('response', '(No response)')
            else:
                response = f"Ollama API error: {r.status_code}"
        except Exception as e:
            response = f"Error: {e}"
    return render_template_string(HTML, response=response, prompt=prompt, mistral_version=mistral_version)

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True) 