#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Class to handle dataset directory for DRS management.

"""

# #class File():
#
# #class DRS(self):
#
# class Facets(self):
#     def __init__(self, **facets):
#         if "activity" not in facets: CANNOT
#         SET
#         self._allowed_facets = self._get_allowed_facets()
#
#         self.items = {}
#
#         # Check for valid facets
#         bad_facets = []
#         for (key, value) in facets.items():
#             if key not in self._allowed_facets:
#                 bad_facets.append(key)
#
#         if bad_facets:
#             bad_facets.sort()
#             raise Exception(
#                 "The following facet name(s) are not allowed for : %s" % str(
#                     bad_facets))
#
#
#     def __getitem__(self, key):
#         return self.items[key]
#
#
#     def _is_allowed(self):
