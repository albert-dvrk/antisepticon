from flask import Flask, jsonify, request, render_template_string
import requests
import xml.etree.ElementTree as ET

app = Flask(__name__)

CBR_URL = "https://www.cbr.ru/scripts/XML_daily.asp"


def get_all_courses():
    """Возвращает список всех валют с ЦБ"""
    response = requests.get(CBR_URL)
    root = ET.fromstring(response.content)
    result = []
    for valute in root.findall('Valute'):
        vunit_rate = valute.find('VunitRate').text.replace(',', '.')
        result.append({
            "id": valute.get('ID'),
            "char_code": valute.find('CharCode').text,
            "name": valute.find('Name').text,
            "rate": float(vunit_rate)
        })
    return result


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Курс валют ЦБ РФ</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial; max-width: 600px; margin: 50px auto; text-align: center; }
        .input-container { position: relative; width: 300px; margin: 0 auto; }
        input { 
            padding: 10px; 
            width: 100%; 
            font-size: 16px; 
            box-sizing: border-box;
            border: 2px solid #ccc;
            border-radius: 4px;
        }
        input:focus {
            border-color: #4CAF50;
            outline: none;
        }
        .suggestions {
            position: absolute;
            top: 100%;
            left: 0;
            width: 100%;
            max-height: 200px;
            overflow-y: auto;
            border: 1px solid #ccc;
            border-top: none;
            background: white;
            border-radius: 0 0 4px 4px;
            z-index: 1000;
            display: none;
        }
        .suggestions.show {
            display: block;
        }
        .suggestion-item {
            padding: 10px;
            cursor: pointer;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        .suggestion-item:hover {
            background: #f0f0f0;
        }
        .suggestion-item strong {
            color: #4CAF50;
        }
        .suggestion-item small {
            color: #888;
            font-size: 12px;
        }
        button { 
            padding: 10px 20px; 
            font-size: 16px; 
            cursor: pointer; 
            margin-top: 10px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
        }
        button:hover {
            background: #45a049;
        }
        #result { margin-top: 20px; font-size: 20px; font-weight: bold; }
        .error { color: red; }
        .rate { color: #2e7d32; font-size: 32px; }
        .hint { color: #666; font-size: 14px; margin-top: 5px; }
    </style>
</head>
<body>
    <h1>💰 Курс валют ЦБ РФ</h1>
    <p>Начните вводить название валюты:</p>

    <form method="POST" id="currencyForm">
        <div class="input-container">
            <input type="text" 
                   id="currencyInput" 
                   name="currency_name" 
                   placeholder="Например: Доллар, Евро, Сомони..." 
                   value="{{ selected_name or '' }}"
                   autocomplete="off">
            <div id="suggestions" class="suggestions">
                {% for currency in currencies %}
                    <div class="suggestion-item" data-code="{{ currency.char_code }}" data-name="{{ currency.name }}">
                        <strong>{{ currency.name }}</strong>
                        <small>({{ currency.char_code }})</small>
                    </div>
                {% endfor %}
            </div>
        </div>
        <button type="submit">Узнать курс</button>
    </form>

    <div id="result">
        {% if result %}
            <p>Курс <b>{{ result.name }}</b> ({{ result.char_code }}):</p>
            <p class="rate">{{ result.rate }} руб.</p>
        {% elif error %}
            <p class="error">{{ error }}</p>
        {% endif %}
    </div>
    <p><small>Данные с сайта ЦБ РФ</small></p>

    <script>
        const input = document.getElementById('currencyInput');
        const suggestions = document.getElementById('suggestions');
        const items = suggestions.querySelectorAll('.suggestion-item');

        function filterSuggestions(query) {
            const lowerQuery = query.toLowerCase();
            let hasMatch = false;

            items.forEach(item => {
                const name = item.dataset.name.toLowerCase();
                // Поиск по названию (содержит подстроку)
                if (name.includes(lowerQuery) && query.length > 0) {
                    item.style.display = 'block';
                    hasMatch = true;
                } else {
                    item.style.display = 'none';
                }
            });

            suggestions.classList.toggle('show', hasMatch);
        }

        input.addEventListener('input', function() {
            filterSuggestions(this.value);
        });

        items.forEach(item => {
            item.addEventListener('click', function() {
                input.value = this.dataset.name;
                suggestions.classList.remove('show');
            });
        });

        document.addEventListener('click', function(e) {
            if (!document.querySelector('.input-container').contains(e.target)) {
                suggestions.classList.remove('show');
            }
        });

        input.addEventListener('focus', function() {
            if (this.value.length > 0) {
                filterSuggestions(this.value);
            }
        });
    </script>
</body>
</html>
"""


@app.route('/', methods=['GET', 'POST'])
def home():
    currencies = get_all_courses()
    selected_name = None
    result = None
    error = None

    if request.method == 'POST':
        currency_name = request.form.get('currency_name', '').strip()
        if not currency_name:
            error = "Введите название валюты"
        else:
            # Ищем валюту по названию (точное совпадение)
            found = None
            for course in currencies:
                if course['name'].lower() == currency_name.lower():
                    found = course
                    selected_name = course['name']
                    break

            if found:
                result = found
            else:
                error = f"Валюта '{currency_name}' не найдена. Попробуйте выбрать из подсказок."

    return render_template_string(HTML_TEMPLATE,
                                  currencies=currencies,
                                  selected_name=selected_name,
                                  result=result,
                                  error=error)


@app.route('/api/rate/<char_code>')
def api_rate(char_code):
    char_code = char_code.upper()
    courses = get_all_courses()
    for course in courses:
        if course['char_code'] == char_code:
            return jsonify(course)
    return jsonify({"error": f"Валюта {char_code} не найдена"}), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)