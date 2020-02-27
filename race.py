import os
import threading

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-cloud.json'

from firestore_ci.firestore_ci import FirestoreDocument


class Bid(FirestoreDocument):

    def __init__(self):
        super().__init__()
        self.username: str = str()
        self.amount: int = 0
        self.player_name: str = str()
        self.status: str = str()
        self.bid_order: int = 0
        self.winner: bool = False


Bid.init()


def query(thread: int = 1):
    for index in range(11):
        Bid.objects.filter_by(player_name='nayan').get()
        Bid.objects.order_by('bid_order', Bid.objects.ORDER_DESCENDING).limit(1).get()
    print(f'Thread {thread}: Race done')


def race(number_of_threads: int = 2):
    for thread in range(number_of_threads):
        query_thread = threading.Thread(target=query, args=(thread,))
        query_thread.start()
    print('All races started')
