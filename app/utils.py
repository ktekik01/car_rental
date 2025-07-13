from flask import request, url_for

def paginate_query(query, endpoint, serializer=lambda x: x.to_dict(), **kwargs):
    page     = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    pag      = query.paginate(page=page, per_page=per_page, error_out=False)

    return {
        'items':     [serializer(item) for item in pag.items],
        'total':     pag.total,
        'pages':     pag.pages,
        'page':      pag.page,
        'per_page':  pag.per_page,
        'next_url':  url_for(endpoint, page=pag.page+1, per_page=pag.per_page, _external=True, **kwargs) if pag.has_next else None,
        'prev_url':  url_for(endpoint, page=pag.page-1, per_page=pag.per_page, _external=True, **kwargs) if pag.has_prev else None
    }
