"""
View for the admin page and helper functions
for generation reports
"""
import datetime
from flask import render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from sqlalchemy import func, select, outerjoin, extract
from app import app, db
from ..models import Image, User
from ..forms.admin_forms import AdminForm


@app.route('/admin/<submitted>', methods=['GET', 'POST'])
@app.route('/admin/', methods=['GET', 'POST'])
@login_required
def admin(submitted=False):
    """ Handles Posts/Gets and if the form is valid calls generateReport """
    
    if current_user.user_name != "admin":
        redirect(url_for("home"))
        
    form = AdminForm()
    
    # Form submission and redirection with query string
    if form.validate_on_submit():
        user = None if form.user.data == "No Users" else form.user.data
        subject = None if form.subject.data == "No Subjects" else form.subject.data
        hierarchy = None if form.hierarchy.data == "" else form.hierarchy.data
        before = None if form.dateBefore.data == "" else form.dateBefore.data
        after = None if form.dateAfter.data == "" else form.dateAfter.data
        
        return redirect(url_for('admin', user=user,
                                subject=subject, hierarchy=hierarchy,
                                dateBefore=before, dateAfter=after, submitted=True))
    elif request.method == "POST" or submitted == False:
        return render_template('logged_in/admin.html', title='Admin', current_user=current_user,
                       form=form, headers=[], rows=[])

    return generateReport(form)

def generateReport(form):
    """
    Handles the job of trafficing from fields to one of the
    SQL generator functions
    """

    # Preserve Search parameters
    user = form.user.data  = request.args.get("user", None)
    subject = request.args.get("subject", None)
    hierarchy = request.args.get("hierarchy", None)
    before = request.args.get("dateBefore", None)
    after = request.args.get("dateAfter", None)
    query = None
    headers = []
    rows = []

    # Keep form data filled in
    form.user.data = request.args.get("user", None)
    form.subject.data = request.args.get("subject", None)
    form.hierarchy.data = request.args.get("hierarchy", None)
    form.dateBefore.data = request.args.get("dateBefore", None)
    form.dateAfter.data = request.args.get("dateAfter", None)

    # Construct based on hierarcy/no hierarchy because hierarchies require subqueries
    if hierarchy == "All Time":
        if subject is None and user is None:
            headers += ["Total Images"]
            query = db.session.query(func.count(Image.photo_id))
        elif singleSubject(subject) or subject is None:
            query = allTimeUsersLeft(headers, after, before, user, subject)
        elif subject == "All Subjects":
            query = allTimeSubjectsLeft(headers, after, before, user, subject)

    # Hiearchy uses different SQL queries
    elif hierarchy in ["Yearly", "Monthly", "Weekly"]:
        if subject is None and user is None:
            query = byHierarchySubjectRight(headers, after, before, user, subject, hierarchy)
        elif singleSubject(subject) or subject is None:
            query = byHierarchyUserLeft(headers, after, before, user, subject, hierarchy)
        elif subject == "All Subjects":
            query = byHierarchySubjectRight(headers, after, before, user, subject, hierarchy)

    # Grab the Rows to output on the page
    if query:
        rows = query.all()

    flash(query)

    return render_template('logged_in/admin.html', title='Admin', current_user=current_user,
                           form=form, headers=headers, rows=rows)


def allTimeSubjectsLeft(headers, after, before, user, subject):
    """
        SQL generated for reports where Subjects are in the first column.
        Used when Time Hierarchy = "All Time"
    """

    if user == "All Users":
        user_names = [user.user_name for user in User.query.all()]
    elif user is not None:
        user_names = [user]
    else:
        user_names = []

    columns = ["images.subject"]

    # Build list of columns to select by
    for name in user_names:
        columns += ["SUM( CASE images.owner_name WHEN '{0}' THEN 1 ELSE 0 END ) AS '{0}'".format(name)]
    columns += ["COUNT( images.subject ) AS 'Total'"]

    # Build select statement
    statement = select(columns, from_obj=Image) \
        .where(getSubjectFilter(subject)) \
        .where(getDateRangeFilter(after, before)) \
        .group_by("images.subject WITH ROLLUP")

    # Get headers for the table
    new_headers = user_names
    select_columns = user_names
    if user == "All Users" or user is None:
        new_headers = new_headers + ["Total"]
        select_columns = select_columns + ["Total"]
    if subject is not None:
        new_headers = ["Subject"] + new_headers
        select_columns = [Image.subject] + select_columns

    # Save as sqlalchemy query type
    query = db.session.query(*select_columns).from_statement(statement)
    headers += new_headers
    return query


def allTimeUsersLeft(headers, after, before, user, subject):
    """
        SQL generated for reports where Users are in the first column.
        Used when Time Hierarchy = "All Time"
    """

    if subject == "All Subjects":
        subjects = [image.subject for image in Image.query.all()]
    elif subject is not None:
        subjects = [subject]
    else:
        subjects = []

    columns = ["users.user_name"]

    # Build list of columns to select by
    for name in subjects:
        columns += ["SUM( CASE images.subject WHEN '{0}' THEN 1 ELSE 0 END ) AS '{0}'".format(name)]

    if not singleSubject(subject):
        columns += ["COUNT( images.photo_id ) AS 'Total'"]

    # Build select statement
    j = outerjoin(User, Image)
    statement = select(columns, from_obj=User) \
        .where(getUserFilter(user)) \
        .where(getDateRangeFilter(after, before)) \
        .select_from(j)

    if user is not None:
        statement = statement.group_by("users.user_name WITH ROLLUP")

    # Generate headers for report table
    new_headers = subjects
    select_columns = subjects

    if not singleSubject(subject):
        new_headers = new_headers + ["Total"]
        select_columns = select_columns + ["Total"]
    if user is not None:
        new_headers = ["User"] + new_headers
        select_columns = [User.user_name] + select_columns

    # Save as sqlalchemy query object
    query = db.session.query(*select_columns).from_statement(statement)
    headers += new_headers
    return query

def byHierarchyUserLeft(headers, after, before, user, subject, hierarchy):
    """
        SQL generated for reports where Users are in the first column.
        Used when a time hierarchy is selected.
    """

    # Grab data neccessary for hiearchy type
    if hierarchy == "Yearly":
        cols = getYears(after, before)
        table_headers = cols
        sqlType = "YEAR"
    elif hierarchy == "Monthly":
        cols = getMonths()
        table_headers = getMonthHeaders()
        sqlType = "MONTH"
    else:
        cols = getWeeks()
        table_headers = getWeekHeaders()
        sqlType = "WEEK"

    # Build list of columns to select by
    columns = ["users.user_name as Name"]
    if singleSubject(subject):
        columns += ["SUM( CASE images.subject WHEN '{0}' THEN 1 ELSE 0 END ) AS Total".format(subject)]
    else:
        columns += ["COUNT( images.photo_id ) AS Total"]

    columns += [sqlType + "(images.timing) As Col"]

    # Build select statement
    j = outerjoin(User, Image)
    statement = select(columns, from_obj=User) \
        .where(getUserFilter(user)) \
        .where(getDateRangeFilter(after, before)) \
        .select_from(j) \
        .group_by("Name, Col")

    # Save as sqlalchemy subquery
    subquery = db.session.query("Username", "Total", "Col").from_statement(statement).subquery()

    # Build list of columns to select by for outer select
    columns2 = ["Name As Name"]
    columns2 += ["SUM( CASE Col WHEN {0} THEN Total ELSE 0 END ) AS '{0}'".format(col) for col in cols]
    columns2 += ["SUM(Total) AS Total"]

    # Build outer select
    statement2 = select(columns2).group_by("Name WITH ROLLUP").select_from(subquery)

    select_columns = ["Name"] + cols + ["Total"]
    headers += ["User"] + table_headers + ["Total"]

    # Save outer select as sql alchemy query
    query = db.session.query(*select_columns).from_statement(statement2)
    return query

def byHierarchySubjectRight(headers, after, before, user, subject, hierarchy):
    """
        SQL generated for reports where Subjects are in the first column.
        Used when a time hierarchy is selected.
    """

    # Grab data neccessary for hiearchy type
    if hierarchy == "Yearly":
        cols = getYears(after, before)
        table_headers = cols
        sqlType = "YEAR"
    elif hierarchy == "Monthly":
        cols = getMonths()
        table_headers = getMonthHeaders()
        sqlType = "MONTH"
    else:
        cols = getWeeks()
        table_headers = getWeekHeaders()
        sqlType = "WEEK"

    # Build list of columns to select by
    columns = ["images.subject as Name"]
    if singleUser(user):
        columns += ["SUM( CASE images.owner_name WHEN '{0}' THEN 1 ELSE 0 END ) AS TOTAL".format(user)]
    else:
        columns += ["COUNT( images.subject ) AS 'Total'"]

    columns += [sqlType + "(images.timing) As Col"]

    # Build statements
    statement = select(columns, from_obj=Image) \
        .where(getSubjectFilter(subject)) \
        .where(getDateRangeFilter(after, before)) \
        .group_by("Name, Col")

    # Save as sqlalchemy subquery
    subquery = db.session.query("Name", "Total", "Col").from_statement(statement).subquery()

    # Build outer select statement
    if subject is not None:
        columns2 = ["Name As Name"]
        columns2 += ["SUM( CASE Col WHEN {0} THEN Total ELSE 0 END ) AS '{0}'".format(col) for col in cols]
        columns2 += ["SUM(Total) AS Total"]
        statement2 = select(columns2).group_by("Name WITH ROLLUP").select_from(subquery)
        select_columns = ["Name"] + cols + ["Total"]
    else:
        # Special case when we're selecting by Any User/Any Subject, we don't need the subject name
        columns2 = ['"All Subjects" as Label' ]
        columns2 += ["SUM( CASE Col WHEN {0} THEN Total ELSE 0 END ) AS '{0}'".format(col) for col in cols]
        columns2 += ["SUM(Total) AS Total"]
        statement2 = select(columns2).group_by("Label").select_from(subquery)
        select_columns = ["Label"] + cols + ["Total"]
        
    headers += ["Subject"] + table_headers + ["Total"]

    # Save as sql alchemy query
    query = db.session.query(*select_columns).from_statement(statement2)
    return query

def getDateRangeFilter(after, before):
    """ Generates sql for date filter """
    filter = ""
    if before is not None and after is not None:
        filter = "((images.timing BETWEEN '{}' AND '{}') OR images.timing is Null)".format(after, before)
    elif before is not None:
        filter = "(images.timing <= '{}' OR images.timing is Null)".format(before)
    elif after is not None:
        filter = "(images.timing >= '{}' OR images.timing is Null)".format(after)
    return filter

def getMonths():
    """ Gets a list of months in number format """
    return [str(month) for month in list(range(1, 13))]

def getMonthHeaders():
    """ List of strings we want when displaying data by month """
    return ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

def getWeekHeaders():
    """ List of strings we want when displaying data by year """
    return ["Week "+str(i) for i in range(1, 53)]

def getWeeks():
    """ Gets a list of weeks in number format """
    return [str(week) for week in range(1, 53)]

def getYears(after, before):
    """ Gets years in number format. """

    if before is None:
        before_year = datetime.date.today().year
    else:
        before_year = datetime.datetime.strptime(before, "%Y-%m-%d").date().year

    if after is None:
        after_year = db.session.query(func.min(extract('year', Image.timing))).all()
        if not after_year or after_year[0][0] is None:
            after_year = before_year
        else:
            after_year = after_year[0][0]
            if after_year > before_year:
                after_year = before_year
    else:
        after_year = datetime.datetime.strptime(after, "%Y-%m-%d").date().year
        
    years = [str(year) for year in list(range(int(after_year), int(before_year)+1))]
    return years

def getSubjectFilter(subject):
    """ Generates sql for filtering by image subject """
    if singleSubject(subject):
        return 'images.subject = "{}"'.format(subject)
    return ""

def getUserFilter(user):
    """ Generates sql for filtering by user name """
    if singleUser(user):
        return 'users.user_name = "{}"'.format(user)
    return ""

def singleUser(user):
    return user is not None and user != "All Users"

def singleSubject(subject):
    return subject is not None and subject != "All Subjects"
