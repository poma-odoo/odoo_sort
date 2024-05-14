from osort._main import main

main()
exit()
from osort._osort import osort

s = osort(
    """
import os

print (os)

from odoo import fields, api
import sys

class A:
    def _search_f(self):
        pass
    def test(self):
        pass
    def _compute_f(self):
        pass
    def _default_g(self):
        pass
    def _compute_g(self):
        pass
    
    def _compute_j(self):
        pass
    
    def _inverse_f(self):
        pass
        
    g = fields.Char()
    
    @api.depends('g')
    def _comp_h(self):
        pass
        
    def _compute_i(self):
        pass

    f =fields.Date()
    
    _name = "A"
"""
)
print(s)
print(osort(s, sort_fields=True))

exit(0)
main()
