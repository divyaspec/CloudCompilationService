import os
from time import sleep

#
# The azure library provides access to services made available by the
# Microsoft Azure platform, such as storage and messaging. 
#
# See http://go.microsoft.com/fwlink/?linkid=254360 for documentation and
# example code.
#
from azure.servicebus import ServiceBusService, Message, Queue
from azure.storage import CloudStorageAccount
from azure.storage import BlobService, QueueService

#
# The CloudStorageAccount provides factory methods for the queue, table, and
# blob service
#
# See http://go.microsoft.com/fwlink/?linkid=246933 for Storage documentation.
#
STORAGE_ACCOUNT_NAME = 'linuxvmstorage'
STORAGE_ACCOUNT_KEY = 'gW6GwPYmuBL7Gs59eEa6br/G6N09+AxChQ4EBKNIF64JyEf9KDUxPdfJxov4EUf29tndVBHcTqgLAHfSe5A/5A=='

if os.environ.get('EMULATED', '').lower() == 'true':
    # Running in the emulator, so use the development storage account
    storage_account = CloudStorageAccount(None, None)
else:
    storage_account = CloudStorageAccount(STORAGE_ACCOUNT_NAME, STORAGE_ACCOUNT_KEY)

blob_service = storage_account.create_blob_service()
table_service = storage_account.create_table_service()
queue_service = storage_account.create_queue_service()

#
# Service Bus is a messaging solution for applications. It sits between
# components of your applications and enables them to exchange messages in a                                                                                                                                                                                                                                                                                                                                                              
# loosely coupled way for improved scale and resiliency.
#
# See http://go.microsoft.com/fwlink/?linkid=246934 for Service Bus documentation.

#bus_service = ServiceBusService(
#    service_namespace='servicebusqueue-json',
#    shared_access_key_name='queue-listener',
#    shared_access_key_value='V5raw40+X20pV0aAqymsfuwnU9S17EA6QvxYJ+nelvs=')
#bus_service.create_queue('jsonqueue')
#msg = Message('test123')
#bus_service.send_queue_message('jsonqueue', msg)
#msg = bus_service.receive_queue_message('jsonqueue', peek_lock=True)
#print(msg.body)

#bus_service = ServiceBusService(
#    service_namespace='servicebusqueue-json',
#    shared_access_key_name='queue-listener',
#    shared_access_key_value='V5raw40+X20pV0aAqymsfuwnU9S17EA6QvxYJ+nelvs=')
#bus_service.create_queue('jsonqueue')
#msg = Message('test123')
#bus_service.send_queue_message('jsonqueue', msg)
#msg = bus_service.receive_queue_message('jsonqueue', peek_lock=True)
#print(msg.body)
bus_service = ServiceBusService(
    service_namespace='servicebusqueue-json',
    shared_access_key_name='statusView',
    shared_access_key_value='16M2EsaGVVTVmsVPKXDR5Olnyxme+Ii8YEdtTSbwBUw=')

blob_service = BlobService(account_name='linuxvmstorage', account_key='gW6GwPYmuBL7Gs59eEa6br/G6N09+AxChQ4EBKNIF64JyEf9KDUxPdfJxov4EUf29tndVBHcTqgLAHfSe5A/5A==')

if __name__ == '__main__':
    while True:
        #
        # Write your worker process here.
        #
        # You will probably want to call a blocking function such as
        msg = bus_service.receive_subscription_message('updatestats','receivesubscription',timeout=10)
        print(msg.body)
        try:
          if (msg.body):
            guid = msg.body
            print guid   
            blob_metadata = blob_service.get_blob_properties('uploads', guid)
            print blob_metadata
        except:
           print "No Blob metadata Exists"
       # bus_service.receive_queue_message('jsonqueue', timeout=30)
        # to avoid consuming 100% CPU time while your worker has no work.
        #
       # msg = Message(b'Test Message')
        # bus_service.send_queue_message('jsonqueue', msg)
        try:
            msg.delete()
        except:
            print "no messages"
        sleep(0.0)

