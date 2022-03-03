# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo
#
##############################################################################
import base64
import json
import requests
import logging
import time
from datetime import datetime
from collections import OrderedDict
from odoo import api, fields, models,_
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval
_logger = logging.getLogger(__name__)



class membrete_company(models.Model):
    _inherit='res.company'
    header_img=fields.Binary("Imagen de encabezado")
    footer_img=fields.Binary("Imagen de pie")
    
