from .common import *
class index:
    def index():
        response.title="模板标题"
        response.content="模板内容"
        return response.tpl()
    def home():
        return response.tpl()
    def api():
        return response.json()