from flask import Blueprint, render_template, redirect, url_for, flash, request

from app import db

default_bp = Blueprint("default_bp", __name__, url_prefix="/")


@default_bp.route("/")
def index():
    return render_template("index.html")
