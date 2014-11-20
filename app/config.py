SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://root@localhost/391database"
WTF_CSRF_ENABLED = True
SECRET_KEY = 'q(v(n&!j5=%m4vid#cfob44ze!iqj%rhi+il0!&el15_cg#yko'

# email server
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 465
MAIL_USE_SSL = True
MAIL_USERNAME = 'wildgamermail@gmail.com'
MAIL_PASSWORD = 'Iheartbats!'

# uploads
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif', 'bmp', 'PNG', 'JPG', 'JPEG', 'BMP', 'GIF'])
UPLOAD_FOLDER = '/home/html/static/images/'
SERVE_FOLDER = '/static/images/'
MAX_CONTENT_LENGTH = 50000000

# text indexing using whoosh
WHOOSH_BASE = '/home/tam/flask/app/full-text-index.db'

FROM = {
    '1' : 'home',
    '2' : 'pictures',
    '3' : 'search'
}