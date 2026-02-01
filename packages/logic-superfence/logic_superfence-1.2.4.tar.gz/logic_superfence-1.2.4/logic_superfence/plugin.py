import os
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import File

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
BUNDLE_PATH = BASE_PATH + '/lib/'


class LogicBundlePlugin(BasePlugin):

    def __init__(self, **kwargs):
        super().__init__()

    def on_files(self, files, config):
        files.append(File('bundle.js', BUNDLE_PATH,
                          config['site_dir'] + '/javascripts/', False))
        files.append(File('bundle.js.map', BUNDLE_PATH,
                          config['site_dir'] + '/javascripts/', False))
        return files

    def on_post_page(self, out, page, config, **kwargs):
        out = out.replace("</title>",
                          f"</title>\n<script src=\"/javascripts/bundle.js\"></script>\n"
        )
        return out
