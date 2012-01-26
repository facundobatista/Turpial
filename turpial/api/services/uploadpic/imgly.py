# -*- coding: utf-8 -*-

"""Interfaz para img.ly en Turpial"""
#
# Author: Wil Alvarez (aka Satanas)
# Abr 19, 2010

import traceback

from turpial.api.interfaces.service import GenericService
from turpial.api.interfaces.service import ServiceResponse

class ImglyPicUploader(GenericService):
    def __init__(self):
        GenericService.__init__(self)
        self.server = "img.ly"
        self.base = "/api/2/upload.xml"
        self.provider = 'https://api.twitter.com/1/account/verify_credentials.json'
        
    def do_service(self, username, password, filepath, message, httpobj):
        try:
            _image = self._open_file(filepath)
        except:
            return self._error_opening_file(filepath)
        
        files = (
            ('media', self._get_pic_name(filepath), _image),
        )
        
        fields = (
            ('message', message),
        )
        
        try:
            resp = self._upload_pic(self.server, self.base, fields, files, httpobj)
            link = self._parse_xml('url', resp)
            return ServiceResponse(link)
        except Exception, error:
            self.log.debug("Error: %s\n%s" % (error, traceback.print_exc()))
            return ServiceResponse(err=True, err_msg=_('Problem uploading pic'))
        
