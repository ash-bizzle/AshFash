from datetime import datetime
from flask import current_app


class RateLimitExceeded(Exception):
    pass


def rate_tracker_has_budget(cursor):
    month = datetime.utcnow().strftime('%Y-%m')
    limit = current_app.config['API_MONTHLY_LIMIT']
    cursor.execute(
        'SELECT calls_used, calls_limit FROM api_rate_tracker WHERE month_year = %s',
        (month,)
    )
    row = cursor.fetchone()
    if not row:
        cursor.execute(
            'INSERT INTO api_rate_tracker (month_year, calls_used, calls_limit) VALUES (%s, 0, %s)',
            (month, limit)
        )
        return True
    return row['calls_used'] < row['calls_limit']


def rate_tracker_increment(cursor):
    month = datetime.utcnow().strftime('%Y-%m')
    cursor.execute(
        'UPDATE api_rate_tracker SET calls_used = calls_used + 1 WHERE month_year = %s',
        (month,)
    )


def rate_tracker_status(cursor):
    month = datetime.utcnow().strftime('%Y-%m')
    cursor.execute(
        'SELECT * FROM api_rate_tracker WHERE month_year = %s',
        (month,)
    )
    row = cursor.fetchone()
    if not row:
        return {'month_year': month, 'calls_used': 0, 'calls_limit': current_app.config['API_MONTHLY_LIMIT'], 'remaining': current_app.config['API_MONTHLY_LIMIT']}
    return {
        'month_year': row['month_year'],
        'calls_used': row['calls_used'],
        'calls_limit': row['calls_limit'],
        'remaining': row['calls_limit'] - row['calls_used'],
    }


def sync_log_start(cursor, sync_type, target_identifier=None):
    cursor.execute(
        'INSERT INTO sync_logs (sync_type, target_identifier, status, started_at) VALUES (%s, %s, %s, NOW())',
        (sync_type, target_identifier, 'running')
    )
    return cursor.lastrowid


def sync_log_complete(cursor, log_id, inserted=0, updated=0, fetched=0, api_calls=0):
    cursor.execute(
        '''UPDATE sync_logs
           SET status = %s, records_inserted = %s, records_updated = %s,
               records_fetched = %s, api_calls_used = %s, completed_at = NOW()
           WHERE id = %s''',
        ('success', inserted, updated, fetched, api_calls, log_id)
    )


def sync_log_fail(cursor, log_id, error):
    cursor.execute(
        'UPDATE sync_logs SET status = %s, error_message = %s, completed_at = NOW() WHERE id = %s',
        ('failed', str(error), log_id)
    )


def sync_log_to_dict(row):
    return {
        'id': row['id'],
        'sync_type': row['sync_type'],
        'target_identifier': row['target_identifier'],
        'status': row['status'],
        'records_fetched': row['records_fetched'],
        'records_inserted': row['records_inserted'],
        'records_updated': row['records_updated'],
        'api_calls_used': row['api_calls_used'],
        'error_message': row['error_message'],
        'started_at': row['started_at'].isoformat() if row['started_at'] else None,
        'completed_at': row['completed_at'].isoformat() if row['completed_at'] else None,
    }
