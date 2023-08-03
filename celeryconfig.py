import os

broker_url = os.getenv('BROKER_URL')
task_serializer = 'json'
accept_content = ['json']
result_serializer = 'json'
timezone = 'Europe/Oslo'
enable_utc = True
worker_enable_remote_control = False
