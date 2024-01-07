from datetime import datetime

from flask import url_for, abort
from pymongo import DESCENDING, ReturnDocument

from model.log import LogNoValidation, Log

from app import logs


def create_page_links(o_id, page, per_page, count):
    """
    Create links for pagination
    :param o_id: link operationId, format: `'{file_name}_{function_name}'`, example: `'log_get_all'`
    :param page: current page
    :param per_page: records per page
    :param count: total count of records
    :return: a link dict with current link, last page link, prev link and next link if applicable
    """
    links = {
        "self": {"href": url_for("/api/v1.{}".format(o_id), page=page, per_page=per_page, _external=True)},
        "last": {
            "href": url_for(
                "/api/v1.{}".format(o_id), page=(count // per_page) + 1, per_page=per_page, _external=True
            )
        },
    }
    # Add a 'prev' link if it's not on the first page:
    if page > 1:
        links["prev"] = {
            "href": url_for("/api/v1.{}".format(o_id), page=page, per_page=per_page - 1, _external=True)
        }
    # Add a 'next' link if it's not on the last page:
    if page - 1 < count // per_page:
        links["next"] = {
            "href": url_for("/api/v1.{}".format(o_id), page=page, per_page=per_page + 1, _external=True)
        }

    return links


def create(log):
    now_dt = datetime.utcnow()

    new_log = Log(**{**log, 'create_dt': now_dt, 'update_dt': now_dt})

    insert_result = logs.insert_one(new_log.to_bson())

    return LogNoValidation(**{**new_log.to_json(), '_id': str(insert_result.inserted_id)}).to_json()


def get_all(page=1, per_page=100, user_ids=None, tool_ids=None, is_online: bool = None):
    """
    GET a list of log.

    The results are paginated using the `page` parameter.
    """
    mongodb_filter = {'is_delete': False}
    if isinstance(user_ids, list):
        mongodb_filter['user_id'] = {'$in': user_ids}
    if isinstance(tool_ids, list):
        mongodb_filter['tool_id'] = {'$in': tool_ids}
    if is_online:
        mongodb_filter['end_dt'] = None
    cursor = (logs
              .find(mongodb_filter)
              .sort([("start_dt", DESCENDING), ("end_dt", DESCENDING)])
              .skip(per_page * (page - 1))
              .limit(per_page))

    count = logs.count_documents(mongodb_filter)

    return {
        "logs": [LogNoValidation(**doc).to_json() for doc in cursor],
        "_links": create_page_links('log_get_all', page, per_page, count),
        "count": count
    }


def get_one(log_id):
    log = logs.find_one({"log_id": log_id})
    if log is None:
        abort(404)
    return LogNoValidation(**log).to_json()


def update(log_id, log):
    log['log_id'] = log_id
    log['update_dt'] = datetime.utcnow()
    if 'is_delete' in log and not log['is_delete']:
        log['delete_dt'] = None
    if 'end_dt' in log and type(log['end_dt']) is str:
        log['end_dt'] = datetime.fromisoformat(log['end_dt'])

    updated_log = logs.find_one_and_update(
        {'log_id': log_id},
        {
            '$set': {
                **log
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    if updated_log:
        return LogNoValidation(**updated_log).to_json()
    else:
        abort(404, 'Log {} not found'.format(log_id))


def delete(log_id, is_hard=False):
    if is_hard:
        deleted_log = logs.find_one_and_delete({'log_id': log_id})
        if deleted_log:
            return LogNoValidation(**deleted_log).to_json()
        else:
            abort(404, 'Log {} not found'.format(log_id))
    else:
        soft_deleted_log = logs.find_one_and_update(
            {'log_id': log_id},
            {
                '$set': {
                    'is_delete': True,
                    'delete_dt': datetime.utcnow()
                }
            },
            return_document=ReturnDocument.AFTER,
        )
        if soft_deleted_log:
            return LogNoValidation(**soft_deleted_log).to_json()
        else:
            abort(404, 'Log {} not found'.format(log_id))
