def paginate(query, page: int = 1, per_page: int = 10, additional_data: dict = None):
    total = query.count()
    last_page = (total + per_page - 1) // per_page
    
    # if page is greater than last page, set page to last page
    if page > last_page:
        page = last_page

    offset = (page - 1) * per_page
    paginated_query = query.offset(offset).limit(per_page).all()

    data = paginated_query

    next_page = page + 1 if page < last_page else None
    prev_page = page - 1 if page > 1 else None

    output = {
        "data": data,
        "pagination": {
            "total": total,
            "current_page": page,
            "next_page": next_page,
            "prev_page": prev_page,
            "per_page": per_page,
            "last_page": last_page,
            "from_item": offset + 1 if data else None,
            "to_item": offset + len(data) if data else None
        }
    }

    if additional_data:
        if callable(additional_data):
            output['additional_data'] = additional_data(data)
        else:
            output['additional_data'] = additional_data

    return output
    