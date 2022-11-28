import pyessv


def get_authority_node(authority_name: str) -> pyessv.Authority:
    for a in pyessv.get_cached(pyessv.Authority):
        if a.name == authority_name:
            return a
    return None


def get_scope_node(authority_name: str, scope_name: str) -> pyessv.Scope:
    for a in pyessv.get_cached(pyessv.Authority):
        if a.name == authority_name:
            for s in a:
                if s.name == scope_name:
                    return s
    return None


def get_collection_node(authority_name: str, scope_name: str, collection_name: str) -> pyessv.Collection:
    for a in pyessv.get_cached(pyessv.Authority):
        if a.name == authority_name or authority_name in a.alternative_names:
            for s in a:
                if s.name == scope_name or scope_name in s.alternative_names:
                    for c in s:
                        if c.name == collection_name or collection_name in c.alternative_names:
                            return c
    return None
