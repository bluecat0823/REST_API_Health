from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields, ValidationError
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///workouts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 모델 정의
class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    sets = db.Column(db.Integer, nullable=False)
    reps = db.Column(db.Integer, nullable=False)
    date = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD 형식

class Diet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    calories = db.Column(db.Integer, nullable=False)
    date = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD 형식
    protein = db.Column(db.Float, nullable=True)
    carbs = db.Column(db.Float, nullable=True)
    fats = db.Column(db.Float, nullable=True)

# 스키마 정의
class WorkoutSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    sets = fields.Int(required=True)
    reps = fields.Int(required=True)
    date = fields.Str(required=True)

class DietSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    calories = fields.Int(required=True)
    date = fields.Str(required=True)
    protein = fields.Float()
    carbs = fields.Float()
    fats = fields.Float()

# 스키마 인스턴스 생성
workout_schema = WorkoutSchema()
workouts_schema = WorkoutSchema(many=True)
diet_schema = DietSchema()
diets_schema = DietSchema(many=True)

# 라우트 정의
@app.route("/")
def home():
    return jsonify({"message": "운동 및 식단 관리 API"}), 200

# 운동 기록 추가
@app.route("/workouts", methods=["POST"])
def add_workout():
    try:
        data = workout_schema.load(request.json)  # 요청 데이터를 검증 및 로드
        workout = Workout(**data)  # Workout 객체 생성
        db.session.add(workout)
        db.session.commit()
        return jsonify(workout_schema.dump(workout)), 201  # JSON 응답
    except ValidationError as err:
        return jsonify(err.messages), 400  # 유효성 검사 오류 처리

# 운동 기록 조회
@app.route("/workouts", methods=["GET"])
def get_workouts():
    date = request.args.get('date')
    if date:
        workouts = Workout.query.filter_by(date=date).all()
    else:
        workouts = Workout.query.all()
    return jsonify(workouts_schema.dump(workouts)), 200

# 운동 주간 요약
@app.route("/workouts/summary/weekly", methods=["GET"])
def weekly_summary():
    start_date = request.args.get('start_date')
    if not start_date:
        return jsonify({"error": "start_date is required"}), 400
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = start + timedelta(days=6)
        workouts = Workout.query.filter(Workout.date.between(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))).all()
        total_sets = sum(w.sets for w in workouts)
        total_reps = sum(w.reps for w in workouts)
        unique_exercises = len(set(w.name for w in workouts))
        return jsonify({
            "total_sets": total_sets,
            "total_reps": total_reps,
            "unique_exercises": unique_exercises,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end.strftime("%Y-%m-%d")
        }), 200
    except ValueError:
        return jsonify({"error": "Invalid start_date format"}), 400

# 운동 월간 요약
@app.route("/workouts/summary/monthly", methods=["GET"])
def monthly_summary():
    month = request.args.get('month')
    if not month:
        return jsonify({"error": "month is required"}), 400
    try:
        workouts = Workout.query.filter(Workout.date.like(f"{month}-%")).all()
        total_sets = sum(w.sets for w in workouts)
        total_reps = sum(w.reps for w in workouts)
        unique_exercises = len(set(w.name for w in workouts))
        return jsonify({
            "total_sets": total_sets,
            "total_reps": total_reps,
            "unique_exercises": unique_exercises,
            "month": month
        }), 200
    except ValueError:
        return jsonify({"error": "Invalid month format"}), 400

# 식단 추가
@app.route("/diets", methods=["POST"])
def add_diet():
    try:
        data = diet_schema.load(request.json)
        diet = Diet(**data)
        db.session.add(diet)
        db.session.commit()
        return jsonify(diet_schema.dump(diet)), 201
    except ValidationError as err:
        return jsonify(err.messages), 400

# 식단 조회
@app.route("/diets", methods=["GET"])
def get_diets():
    date = request.args.get('date')
    if date:
        diets = Diet.query.filter_by(date=date).all()
    else:
        diets = Diet.query.all()
    return jsonify(diets_schema.dump(diets)), 200

# 식단 수정
@app.route("/diets/<int:id>", methods=["PUT"])
def update_diet(id):
    diet = Diet.query.get_or_404(id)
    try:
        data = diet_schema.load(request.json)
        diet.name = data['name']
        diet.calories = data['calories']
        diet.date = data['date']
        diet.protein = data.get('protein')
        diet.carbs = data.get('carbs')
        diet.fats = data.get('fats')
        db.session.commit()
        return jsonify(diet_schema.dump(diet)), 200
    except ValidationError as err:
        return jsonify(err.messages), 400

# 식단 삭제
@app.route("/diets/<int:id>", methods=["DELETE"])
def delete_diet(id):
    diet = Diet.query.get_or_404(id)
    db.session.delete(diet)
    db.session.commit()
    return jsonify({"message": f"Diet {id} deleted"}), 200

# 애플리케이션 실행
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
