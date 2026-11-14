from flask import Flask, jsonify, request
from flask_cors import CORS
from PIL import Image, UnidentifiedImageError, ExifTags
from io import BytesIO
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Maximum upload size: 15 MB
app.config["MAX_CONTENT_LENGTH"] = 15 * 1024 * 1024


@app.route("/")
def home():
    return jsonify({
        "message": "Welcome to Verify Lens Backend!",
        "status": "Running"
    })


@app.route("/health")
def health():
    return jsonify({
        "project": "Verify Lens",
        "backend": "Active",
        "status": "Success"
    })


# IMAGE ANALYSIS API
@app.route("/api/analyze-image", methods=["POST"])
def analyze_image():

    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    try:
        image_data = file.read()

        image = Image.open(BytesIO(image_data))
        image.verify()

        image = Image.open(BytesIO(image_data))

        width, height = image.size
        image_format = image.format

        # Extract EXIF metadata
        exif_data = image.getexif()

        metadata = {}

        for tag_id, value in exif_data.items():
            tag_name = ExifTags.TAGS.get(tag_id, tag_id)

            if tag_name in [
                "Make",
                "Model",
                "DateTime",
                "Software",
                "Orientation"
            ]:
                metadata[tag_name] = str(value)

        # Check metadata
        metadata_available = bool(metadata)

        # Identify editing software
        editing_software = metadata.get("Software", "Not available")

        # Basic risk assessment
        risk_score = 20
        risk_level = "Low"

        indicators = []

        if not metadata_available:
            risk_score += 15
            indicators.append(
                "EXIF metadata is missing"
            )

        if metadata_available:
            indicators.append(
                "Image contains some metadata"
            )

        if editing_software != "Not available":
            risk_score += 10
            indicators.append(
                f"Editing software information found: {editing_software}"
            )

        if risk_score >= 60:
            risk_level = "High"
        elif risk_score >= 35:
            risk_level = "Medium"

        return jsonify({

            "status": "Success",

            "filename": file.filename,

            "format": image_format,

            "width": width,

            "height": height,

            "file_size_kb": round(
                len(image_data) / 1024, 2
            ),

            "exif_metadata_available": metadata_available,

            "metadata": metadata,

            "editing_software": editing_software,

            "risk_score": risk_score,

            "risk_level": risk_level,

            "indicators": indicators,

            "message": "Image metadata analysis completed successfully",

            "disclaimer": (
                "This is a preliminary metadata-based assessment, "
                "not a forensic determination of image authenticity."
            )

        })

    except (UnidentifiedImageError, OSError):
        return jsonify({
            "error": "Invalid or unsupported image file"
        }), 400


# Start Flask server
if __name__ == "__main__":
    import os
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )