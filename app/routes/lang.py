# in routes/lang.py
from flask import Blueprint, redirect, request, session

bp = Blueprint("lang", __name__)

@bp.route("/set_language/<lang_code>")
def set_language(lang_code):
    if lang_code in ["en", "fil", 'ceb']:
        session["lang"] = lang_code
    return redirect(request.referrer or "/")