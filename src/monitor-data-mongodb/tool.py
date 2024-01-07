from log import create_page_links

from app import logs


def get_online_users_by_tool(page=1, per_page=100):
    mongodb_filter = {'end_dt': None, 'is_delete': False}

    cursor = logs.aggregate(
        [
            {
                '$match': mongodb_filter,
            },
            {
                '$sort': {'tool_id': 1}
            },
            {
                '$skip': per_page * (page - 1)
            },
            {
                '$limit': per_page
            },
            {
                '$group': {
                    '_id': '$tool_id',
                    'user_ids': {
                        '$addToSet': '$user_id'
                    }
                }
            }
        ]
    )
    count = logs.count_documents(mongodb_filter)

    return {
        "detail": {doc['_id']: doc['user_ids'] for doc in cursor},
        "_links": create_page_links('tool_get_online_users_by_tool', page, per_page, count),
        "count": count
    }
