import re
from datetime import datetime

from flask import (Flask, render_template, session, redirect,
                   url_for, flash, request)
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'
bootstrap = Bootstrap(app)
moment = Moment(app)


class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    email = StringField('What is your UofT Email address?',
                        validators=[DataRequired(), Email()])
    submit = SubmitField('Submit')


@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        old_name = session.get('name')
        if old_name is not None and old_name != form.name.data:
            flash('Looks like you have changed your name!')
        old_email = session.get('email')
        if old_email is not None and old_email != form.email.data:
            flash('Looks like you have changed your email!')
        session['name'] = form.name.data
        session['email'] = form.email.data
        session['uoft'] = 'utoronto' in form.email.data.lower()
        if session['uoft']:
            return redirect(url_for('chatbot'))
        return redirect(url_for('index'))
    return render_template('index.html', form=form,
                           name=session.get('name'),
                           email=session.get('email'),
                           uoft=session.get('uoft'),
                           current_time=datetime.utcnow())


@app.route('/chatbot')
def chatbot():
    if not session.get('uoft'):
        return redirect(url_for('index'))
    return render_template('chat.html', name=session['name'])


@app.route('/chat', methods=['POST'])
def chat():
    message = request.json['message']
    memory = session.get('memory', {})

    name_match = re.search(r"my name is\s+([A-Za-z][\w'-]*)", message, re.I)
    like_match = re.search(r"i like\s+(.+)", message, re.I)

    if name_match:
        memory['user_name'] = name_match.group(1).capitalize()
        reply = f"Nice to meet you, {memory['user_name']}!"
    elif re.search(r"what('s| is) my name", message, re.I):
        if 'user_name' in memory:
            reply = f"Your name is {memory['user_name']}."
        else:
            reply = "You haven't told me your name yet."
    elif like_match:
        memory['likes'] = like_match.group(1).strip(' .!?')
        reply = f"Got it, you like {memory['likes']}."
    elif re.search(r"what do i like", message, re.I):
        if 'likes' in memory:
            reply = f"You told me you like {memory['likes']}."
        else:
            reply = "You haven't told me what you like yet."
    elif "hello" in message.lower():
        reply = "Hello!"
    else:
        reply = "I don't understand."

    session['memory'] = memory
    return {"reply": reply}

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))    