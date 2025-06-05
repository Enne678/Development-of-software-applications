from flask import Flask, request, jsonify
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)


@app.route('/square', methods=['POST'])
def calculate_square():
    """
    Возводит переданное значение в квадрат
    Ожидает JSON: {"value": число}
    Возвращает: {"result": число^2}
    """
    try:
        data = request.get_json()
        if not data or 'value' not in data:
            return jsonify({"error": "Требуется параметр 'value'"}), 400

        value = data['value']

        # Проверяем что значение является числом
        if not isinstance(value, (int, float)):
            return jsonify({"error": "Значение должно быть числом"}), 400

        # Ограничиваем максимальное значение для безопасности
        if abs(value) > 100000:
            return jsonify({"error": "Слишком большое число (максимум ±100000)"}), 400

        result = value ** 2

        app.logger.info(f"Вычислено: {value}^2 = {result}")

        return jsonify({
            "result": result,
            "operation": f"{value}^2"
        })

    except Exception as e:
        app.logger.error(f"Ошибка при вычислении: {str(e)}")
        return jsonify({"error": "Внутренняя ошибка сервера"}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Проверка работоспособности сервиса"""
    return jsonify({"status": "healthy", "service": "microservice-b"})


if __name__ == '__main__':
    print("Запускается Микросервис B (возведение в квадрат)")
    print("Эндпоинт: POST /square")
    print("Формат запроса: {\"value\": число}")
    app.run(host='0.0.0.0', port=5002, debug=True)