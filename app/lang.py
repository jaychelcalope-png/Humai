from flask import Blueprint, redirect, url_for, request, session

lang_bp = Blueprint('lang', __name__)

@lang_bp.route('/change_lang/<language>')
def change_lang(language):
    session['lang'] = language
    return redirect(request.referrer or url_for('main.dashboard'))

