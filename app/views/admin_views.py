import datetime
import os
from flask import render_template, flash, redirect, url_for, request
from flask.ext.login import login_required, current_user
from sqlalchemy import desc, func, distinct
from app import app, db
from ..models import Image, Popularity
from ..forms.admin_forms import AdminForm


@app.route('/admin/<page>/<count>/', methods=['GET', 'POST'])
@app.route('/admin/<page>/', methods=['GET', 'POST'])
@app.route('/admin/', methods=['GET', 'POST'])
@login_required
def admin(page=0, count=None):
    form = AdminForm()
    page = int(page)
    count = int(count) if count is not None else count
    
    # Form submission and redirection with query string
    if form.validate_on_submit():
        user = None if form.user.data == "" else form.user.data
        subject = None if form.subject.data == "" else form.subject.data
        hierarchy = None if form.hierarchy.data == "" else form.hierarchy.data
        dateBefore = None if form.dateBefore.data == "" else form.dateBefore.data
        dateAfter = None if form.dateAfter.data == "" else form.dateAfter.data
        
        return redirect(url_for('admin', page=page, count=count, user=user,
                                subject=subject, hierarchy=hierarchy,
                                dataBefore=dateBefore, dateAfter=dateAfter, generate=1))
    
    table_headers = []
    row_header = None
    rows = []
    limit = 30
    offset = 0 if (page == 0 or page == 1) else (page-1)*limit
    has_next = False if count is None else (offset + limit < count)
    has_prev = (offset - limit > 0)
    pages = 0 if count is None else math.ciel(count/limit)
    
    generate = request.args.get("generate", None)
    user = request.args.get("user", None)
    subject = request.args.get("subject", None)
    hierarchy = request.args.get("hierarchy", None)
    dateBefore = request.args.get("dateBefore", None)
    dateAfter = request.args.get("dateAfter", None)

    # Set up column headers
    if hierarchy == "Weekly":
        table_headers = ["Week "+str(i) for i in range(1, 53)]
    elif hierarchy == "Monthly":
        table_headers = ["Jan", "Feb", "Mar", "Apr", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    elif hierarchy == "Yearly":
        table_headers = []
    elif generate:
        table_headers = ["All Time"]
        
    if user is not None:
        row_header = "Subject"
    elif subject is not None:
        row_header = "User"
    elif generate:
        row_header = "Subject" # + [all user names]
    
    # Construct query for User and All Time
    if user is not None and hierarchy is None:
        if count is None:
            countquery = db.session.query(func.count(distinct(Image.subject)))
            count = subjectByAllTimeQuery(countquery, user, subject, dateAfter, dateBefore).first()[0]

        query = db.session.query(Image.subject, func.count(Image.photo_id).label('total'))
        query = subjectByAllTimeQuery(query, user, subject, dateAfter, dateBefore)
        query = query.group_by(Image.subject).order_by('total DESC')
        rows = query.limit(limit).offset(offset).all()
    
    # Construct query for All Users and All Subjects (hierarchy must be none)
    if user is None and subject is None:
        if count is None:
            count = db.session.query(func.count(distinct(Image.subject))).first()[0]
            
    return render_template('logged_in/admin.html', title='Admin', current_user=current_user,
                           form=form, headers=table_headers, row_header=row_header, rows=rows,
                           page=1 if page == 0 else page, count=count)

def subjectByAllTimeQuery(query, user, subject, dateAfter, dateBefore):
    query = addUserFilter(query, user)
    query = addSubjectFilter(query, subject)
    query = addDateRangeFilters(query, dateAfter, dateBefore)
    return query


def addSubjectFilter(query, subject):
    if subject is not None:
        query = query.filter(Image.subject == subject)
    return query

def addUserFilter(query, user):
    if user is not None:
        query = query.filter(Image.owner_name == user)
    return query

def addDateRangeFilters(query, after, before):
    if before is not None and after is not None:
        date1 = datetime.datetime.strptime(after, "%Y-%m-%d").date()
        date2 = datetime.datetime.strptime(before, "%Y-%m-%d").date()
        query = query.filter(Image.timing > date1, Image.timing < date2)
    elif before is not None:
        date = datetime.datetime.strptime(before, "%Y-%m-%d").date()
        query = query.filter(Image.timing < date)
    elif after is not None:
        date = datetime.datetime.strptime(after, "%Y-%m-%d").date()
        query = query.filter(Image.timing > date)
    
    return query

