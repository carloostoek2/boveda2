# backend/routes/prompts.py
import json
from flask import Blueprint, request, jsonify, url_for
from database import db
from models.prompt import Prompt
from models.tag import Tag
from services.ai import analyze_prompt_sync as analyze_prompt
import os
from werkzeug.utils import secure_filename
import uuid

bp = Blueprint("prompts", __name__, url_prefix="/api/prompts")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route("", methods=["GET"])
def list_prompts():
    query = Prompt.query

    # Filters
    category = request.args.get("category")
    if category:
        query = query.filter(Prompt.category == category)

    search = request.args.get("search")
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                Prompt.title.ilike(search_term),
                Prompt.description.ilike(search_term),
                Prompt.content.like(search_term)
            )
        )

    favorites_only = request.args.get("favorites")
    if favorites_only == "true":
        query = query.filter(Prompt.is_favorite == True)

    prompts = query.order_by(Prompt.created_at.desc()).all()
    return jsonify([p.to_dict() for p in prompts])


@bp.route("", methods=["POST"])
def create_prompt():
    content = request.form.get("content")
    if not content:
        return jsonify({"error": "content is required"}), 400

    analyze = request.form.get("analyze", "false").lower() == "true"

    # Handle image upload
    image_url = None
    if "image" in request.files:
        file = request.files["image"]
        if file and allowed_file(file.filename):
            filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
            filepath = os.path.join("uploads", filename)
            file.save(filepath)
            image_url = f"/uploads/{filename}"

    # Create prompt
    prompt = Prompt(
        content=content,
        image_url=image_url,
        analysis_status="PENDING" if analyze else "MANUAL"
    )
    db.session.add(prompt)

    if analyze:
        try:
            result = analyze_prompt(content)
            prompt.title = result.get("title")
            prompt.description = result.get("description")
            prompt.category = result.get("category", "TEXTO")
            prompt.subcategory = result.get("subcategory")
            prompt.meta = json.dumps(result.get("metadata", {}))
            prompt.analysis_result = json.dumps(result)
            prompt.analysis_status = "COMPLETED"

            # Create tags
            for tag_name in result.get("tags", []):
                tag = Tag.get_or_create(tag_name)
                prompt.tags.append(tag)
        except Exception as e:
            prompt.analysis_status = "FAILED"
            prompt.analysis_result = json.dumps({"error": str(e)})

    db.session.commit()
    return jsonify(prompt.to_dict()), 201


@bp.route("/<prompt_id>", methods=["GET"])
def get_prompt(prompt_id):
    prompt = Prompt.query.get_or_404(prompt_id)
    return jsonify(prompt.to_dict())


@bp.route("/<prompt_id>", methods=["PUT"])
def update_prompt(prompt_id):
    prompt = Prompt.query.get_or_404(prompt_id)

    content = request.form.get("content")
    if content:
        prompt.content = content

    title = request.form.get("title")
    if title is not None:
        prompt.title = title

    description = request.form.get("description")
    if description is not None:
        prompt.description = description

    reanalyze = request.form.get("reanalyze", "false").lower() == "true"

    if reanalyze:
        try:
            result = analyze_prompt(prompt.content)
            prompt.title = prompt.title or result.get("title")
            prompt.description = prompt.description or result.get("description")
            prompt.category = result.get("category", prompt.category)
            prompt.subcategory = result.get("subcategory")
            prompt.meta = json.dumps(result.get("metadata", {}))
            prompt.analysis_result = json.dumps(result)
            prompt.analysis_status = "COMPLETED"
            prompt.tags = []
            for tag_name in result.get("tags", []):
                tag = Tag.get_or_create(tag_name)
                prompt.tags.append(tag)
        except Exception as e:
            prompt.analysis_status = "FAILED"

    db.session.commit()
    return jsonify(prompt.to_dict())


@bp.route("/<prompt_id>", methods=["DELETE"])
def delete_prompt(prompt_id):
    prompt = Prompt.query.get_or_404(prompt_id)
    db.session.delete(prompt)
    db.session.commit()
    return jsonify({"message": "deleted"})


@bp.route("/<prompt_id>/favorite", methods=["POST"])
def toggle_favorite(prompt_id):
    prompt = Prompt.query.get_or_404(prompt_id)
    prompt.is_favorite = not prompt.is_favorite
    db.session.commit()
    return jsonify(prompt.to_dict())