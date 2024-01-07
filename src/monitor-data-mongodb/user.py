from log import create_page_links

from app import logs


def get_user_info(user_id):
    cursor = logs.aggregate(
        [
            {
                # set end_dt': {'$exists': True} to ignore user online records
                '$match': {
                    'user_id': user_id,
                    'end_dt': {'$exists': True},
                    'is_delete': False
                },
            },
            {
                '$project': {
                    '_id': '$tool_id',
                    'time_used': {
                        '$subtract': ['$end_dt', '$start_dt']
                    }
                }
            }
        ]
    )

    usage_time = {}
    for doc in cursor:
        if doc['_id'] in usage_time:
            usage_time[doc['_id']]['total_time_used'] += doc['time_used']
            usage_time[doc['_id']]['number_of_time'] += 1
        else:
            usage_time[doc['_id']] = {
                'total_time_used': doc['time_used'],
                'number_of_time': 1
            }
    # may add other user info if going to put those detail into this mongodb another collection
    return {
        'usage_time': usage_time
    }


def get_online_user_with_tools(page=1, per_page=100):
    mongodb_filter = {'end_dt': None, 'is_delete': False}

    cursor = logs.aggregate(
        [
            {
                '$match': mongodb_filter,
            },
            {
                '$sort': {'user_id': 1}
            },
            {
                '$skip': per_page * (page - 1)
            },
            {
                '$limit': per_page
            },
            {
                '$group': {
                    '_id': '$user_id',
                    'tool_ids': {
                        '$addToSet': '$tool_id'
                    }
                }
            }
        ]
    )
    count = logs.count_documents(mongodb_filter)

    return {
        "detail": {doc['_id']: doc['tool_ids'] for doc in cursor},
        "_links": create_page_links('user_get_online_user_with_tools', page, per_page, count),
        "count": count
    }
