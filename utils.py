def allowed_file(filename):
  return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf', 'docx', 'xlsx', 'png', 'jpg', 'jpeg'}

