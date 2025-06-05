from flask import Flask, request, jsonify
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)


@app.route('/power', methods=['POST'])
def calculate_power():
    """
    Возводит 2 в степень переданного значения
    Ожидает JSON: {"value": число}
    Возвращает: {"result": 2^число}
    """
    try:
        data = request.get_json()
        if not data or 'value' not in data:
            return jsonify({"error": "Требуется параметр 'value'"}), 400

        value = data['value']

        # Проверяем что значение является числом
        if not isinstance(value, (int, float)):
            return jsonify({"error": "Значение должно быть числом"}), 400

        # Ограничиваем максимальную степень для безопасности
        if value > 1000:
            return jsonify({"error": "Слишком большая степень (максимум 1000)"}), 400

        result = 2 ** value

        app.logger.info(f"Вычислено: 2^{value} = {result}")

        return jsonify({
            "result": result,
            "operation": f"2^{value}"
        })

    except Exception as e:
        app.logger.error(f"Ошибка при вычислении: {str(e)}")
        return jsonify({"error": "Внутренняя ошибка сервера"}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Проверка работоспособности сервиса"""
    return jsonify({"status": "healthy", "service": "microservice-a"})


if __name__ == '__main__':
    print("Запускается Микросервис A (возведение 2 в степень)")
    print("Эндпоинт: POST /power")
    print("Формат запроса: {\"value\": число}")
    app.run(host='0.0.0.0', port=5001, debug=True)