from flask import Flask, render_template, request, jsonify
from pathlib import Path
import json
import joblib
import pandas as pd
from feature_engineering import fe_transform

# ============================================================
# FLASK SETUP
# ============================================================
BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__, template_folder=str(BASE_DIR / "templates"))

# ============================================================
# MODEL VE SAMPLE DATA YÜKLEME
# ============================================================
try:
    model = joblib.load(BASE_DIR / "hydrate_model_pipeline.pkl")
except Exception as e:
    print("\nModel dosyası yüklenirken hata oluştu!\n")
    print(str(e))
    input("\nHata mesajını okuduktan sonra Enter tuşuna basarak çıkabilirsiniz...")
    raise SystemExit

try:
    with open(BASE_DIR / "data_sample.json", "r", encoding="utf-8") as f:
        sample_input = json.load(f)
except Exception as e:
    print("\nÖrnek veri dosyası (data_sample.json) okunurken hata oluştu!\n")
    print(str(e))
    input("\nHata mesajını okuduktan sonra Enter tuşuna basarak çıkabilirsiniz...")
    raise SystemExit

# Feature isimleri (sadece ham kolonlar - 16 adet)
feature_names = list(sample_input.keys())
defaults = sample_input

# ============================================================
# WEB FORM ENDPOINT
# ============================================================
@app.route("/", methods=["GET", "POST"])
def index():
    prediction = None
    user_values = defaults.copy()

    if request.method == "POST":
        try:
            user_inputs = {}

            for f in feature_names:
                if f == "H2O":
                    user_values[f] = 0.07
                    user_inputs[f] = 0.07
                    continue

                val = request.form.get(f, "")

                if val == "":
                    user_values[f] = float(defaults[f])
                    user_inputs[f] = float(defaults[f])
                else:
                    user_values[f] = float(val)
                    user_inputs[f] = float(val)

            # DataFrame oluştur (sadece ham kolonlarla - 16 adet)
            input_df = pd.DataFrame([user_inputs])
            
            # Pipeline otomatik FE yapıp tahmin eder
            y_pred = model.predict(input_df)[0]
            prediction = float(y_pred)

        except Exception as e:
            prediction = f"Hata: {e}"

    return render_template(
        "index.html",
        feature_names=feature_names,
        defaults=defaults,
        prediction=prediction,
        user_values=user_values
    )

# ============================================================
# API: FEATURE SCHEMA
# ============================================================
@app.route("/api/feature-schema", methods=["GET"])
def feature_schema():
    return jsonify(
        {
            "feature_names": feature_names,
            "defaults": defaults,
            "note": "POST /api/predict endpoint'ine bu alanlari gonderin. "
                    "Eksik alanlar varsayilanlarla doldurulur.",
        }
    )

# ============================================================
# API: PREDICT
# ============================================================
@app.route("/api/predict", methods=["POST"])
def api_predict():
    try:
        payload = request.get_json(force=True, silent=False)
        if payload is None:
            return jsonify({"error": "JSON bekleniyor."}), 400
            
        # Hem {"features": {...}} hem de düz dict destekle
        if isinstance(payload, dict) and "features" in payload and isinstance(payload["features"], dict):
            feats = payload["features"]
        elif isinstance(payload, dict):
            feats = payload
        else:
            return jsonify({"error": "Gecersiz JSON formati."}), 400
            
        used = {}
        missing = []
        bad_values = {}
        
        for name in feature_names:
            raw = feats.get(name, None)
            if raw is None or raw == "":
                used[name] = float(defaults[name])
                missing.append(name)
            else:
                try:
                    used[name] = float(raw)
                except Exception:
                    used[name] = float(defaults[name])
                    bad_values[name] = raw
        
        # DataFrame oluştur
        input_df = pd.DataFrame([used])
        
        # Pipeline tahmin yapar (FE otomatik)
        y_pred = model.predict(input_df)[0]
        pred = float(y_pred)
        
        resp = {
            "prediction": pred,
            "units": "C",
            "used_features": used,
        }
        if missing:
            resp["filled_with_defaults"] = missing
        if bad_values:
            resp["coerced_to_defaults_due_to_parse_error"] = bad_values
            
        return jsonify(resp)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================
# CORS (OPSIYONEL)
# ============================================================
try:
    from flask_cors import CORS
    CORS(app)
except Exception:
    # flask-cors yoksa sorun değil
    pass

# ============================================================
# SUNUCU BAŞLATMA
# ============================================================
if __name__ == "__main__":
    try:
        from waitress import serve
        # PRODUCTION için:
        # serve(app, host="0.0.0.0", port=5000)
        
        # DEVELOPMENT için:
        app.run(debug=True, use_reloader=False)
    except Exception as e:
        print("\nUygulama başlatılırken bir hata oluştu!\n")
        print(str(e))
        input("\nHata mesajını okuduktan sonra Enter tuşuna basarak çıkabilirsiniz...")