import os
from typing import List
from unittest import TestCase

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google-cloud.json"

from firestore_ci import FirestoreDocument
from firestore_ci.firestore_ci import FirestoreCIError


class User(FirestoreDocument):

    def __init__(self):
        super().__init__()
        self.name: str = ""
        self.email: str = ""
        self.clients: List[Client] = list()


User.init("users")


class Client(FirestoreDocument):

    def __init__(self):
        super().__init__()
        self.name: str = ""
        self.address: str = ""
        self.account_type: str = ""
        self.amount_pending: int = 0
        self.contacts: List[str] = list()
        self.address_map: dict = {
            "city": str(),
            "country": str(),
        }


Client.init("clients")


class FirestoreTest(TestCase):
    def setUp(self) -> None:
        self.nayan_dict = {
            "name": "Nayan",
            "email": "nayan@crazyideas.co.in",
            "clients": [
                {
                    "name": "Nayan",
                    "address": "Mumbai",
                    "account_type": "Individual",
                    "amount_pending": 5000,
                    "contacts": ["+91 91234 50001", "+91 91234 50002"],
                    "address_map": {"city": "Mumbai", "country": "India"},
                },
            ]
        }
        self.avani_dict = {
            "name": "Avani",
            "email": "avani@crazyideas.co.in",
            "clients": [
                {
                    "name": "Avani",
                    "address": "Netherlands",
                    "account_type": "Individual",
                    "amount_pending": 1100,
                    "contacts": ["+31 612 345 001"],
                    "address_map": {"city": "Maastricht", "country": "Netherlands"},
                },
                {
                    "name": "Hiten",
                    "address": "Netherlands",
                    "account_type": "Individual",
                    "amount_pending": 0,
                    "contacts": [],
                    "address_map": {"city": "Maastricht", "country": "Netherlands"},
                },
                {
                    "name": "Crazy Ideas",
                    "address": "Mumbai",
                    "account_type": "Partnership Firm",
                    "amount_pending": 0,
                    "contacts": ["+91 91234 50011", "+91 91234 50012", "+91 91234 50013"],
                    "address_map": {"city": "Mumbai", "country": "India"},
                },
            ]
        }
        users: List[User] = User.create_from_list_of_dict([self.nayan_dict, self.avani_dict])
        self.nayan = next(user for user in users if user.name == "Nayan")
        self.avani = next(user for user in users if user.name == "Avani")

    def test_create(self):
        # Nayan - Client #1
        self.assertEqual(f"/users/{self.nayan.id}", str(self.nayan))
        self.assertEqual("nayan@crazyideas.co.in", self.nayan.email)
        self.assertEqual(f"/clients/{self.nayan.clients[0].id}", str(self.nayan.clients[0]))
        self.assertEqual("Nayan", self.nayan.clients[0].name)
        self.assertEqual("Mumbai", self.nayan.clients[0].address)
        # Avani - Client #1
        self.assertEqual(f"/users/{self.avani.id}", str(self.avani))
        self.assertEqual("avani@crazyideas.co.in", self.avani.email)
        self.assertEqual(f"/clients/{self.avani.clients[0].id}", str(self.avani.clients[0]))
        self.assertEqual("Avani", self.avani.clients[0].name)
        self.assertEqual("Netherlands", self.avani.clients[0].address)
        # Avani - Client #2
        self.assertEqual(f"/clients/{self.avani.clients[1].id}", str(self.avani.clients[1]))
        self.assertEqual("Hiten", self.avani.clients[1].name)
        self.assertEqual("Netherlands", self.avani.clients[1].address)
        self.assertEqual("Individual", self.avani.clients[1].account_type)
        # Avani - Client #3
        self.assertEqual(f"/clients/{self.avani.clients[2].id}", str(self.avani.clients[2]))
        self.assertEqual("Crazy Ideas", self.avani.clients[2].name)
        self.assertEqual("Mumbai", self.avani.clients[2].address)
        self.assertEqual("Partnership Firm", self.avani.clients[2].account_type)

    def test_read(self):
        # Set ID in dict and test cascade_to_dict
        self.nayan_dict["id"] = self.nayan.id
        self.nayan_dict["clients"][0]["id"] = self.nayan.clients[0].id
        self.avani_dict["id"] = self.avani.id
        self.avani_dict["clients"][0]["id"] = self.avani.clients[0].id
        self.avani_dict["clients"][1]["id"] = self.avani.clients[1].id
        self.avani_dict["clients"][2]["id"] = self.avani.clients[2].id
        self.assertEqual(self.avani_dict, User.objects.cascade.filter_by(name="Avani").first().cascade_to_dict())
        self.assertEqual(self.nayan_dict, User.objects.cascade.filter_by(name="Nayan").first().cascade_to_dict())
        # Test filter_by and first
        nayan: User = User.objects.filter_by(name="Nayan").first()
        self.assertEqual(f"/users/{nayan.id}", str(nayan))
        self.assertEqual("Nayan", nayan.name)
        nayan_client: Client = Client.objects.filter_by(name="Nayan").first()
        self.assertListEqual([nayan_client.id], nayan.clients)
        # Test filter, cascade and get and ARRAY_CONTAINS and IN
        avani: List[User] = User.objects.cascade.filter("email", "==", "avani@crazyideas.co.in").get()
        avani: User = next(iter(avani))  # or avani: User = avani[0]
        self.assertEqual(f"/users/{avani.id}", str(avani))
        self.assertEqual("Avani", avani.name)
        self.assertListEqual(["Avani", "Hiten", "Crazy Ideas"], [client.name for client in avani.clients])
        nayan = Client.objects.filter("contacts", Client.objects.ARRAY_CONTAINS, "+91 91234 50002").first()
        self.assertEqual("Nayan", nayan.name)
        clients = Client.objects.filter("name", Client.objects.IN, ["Avani", "Hiten"]).get()
        self.assertEqual(2, len(clients))
        # Test order_by and limit
        clients: List[Client] = Client.objects.order_by("name", Client.objects.ORDER_DESCENDING).limit(100).get()
        self.assertListEqual(["Nayan", "Hiten", "Crazy Ideas", "Avani"], [client.name for client in clients])
        clients: List[Client] = Client.objects.order_by("name").limit(3).get()
        self.assertListEqual(["Avani", "Crazy Ideas", "Hiten"], [client.name for client in clients])
        client: Client = Client.objects.order_by("name").first()
        self.assertEqual("Avani", client.name)
        client: Client = Client.objects.limit(0).first()  # limit does not work with first; first overrides the limit
        self.assertIsNotNone(client.name)
        clients: List[Client] = Client.objects.limit(0).get()  # limit of 0 or negative returns an empty list with get
        self.assertListEqual(list(), clients)
        clients: List[Client] = Client.objects.limit(-3).get()
        self.assertListEqual(list(), clients)
        self.assertIsNone(User.get_by_id("invalid id"))
        # Test exceptions
        self.assertRaises(FirestoreCIError, User.objects.filter, "invalid", "==", "some data")
        self.assertRaises(FirestoreCIError, User.objects.filter, "email", "!=", "some data")
        self.assertRaises(FirestoreCIError, User.objects.filter_by, invalid="some data")
        self.assertRaises(FirestoreCIError, User.objects.order_by, "invalid")
        self.assertRaises(FirestoreCIError, User.objects.order_by, "email", "desc")

    def test_update(self):
        # Test on objects returned by create
        self.nayan.name = "NHZ"
        self.assertEqual(True, self.nayan.save())  # Will save on the parent object
        self.assertEqual("NHZ", User.get_by_id(self.nayan.id).name)
        self.nayan.clients[0].name = "NHZ"
        self.assertEqual(True, self.nayan.save(cascade=True))  # Will save on the child object
        self.assertIsNotNone(Client.objects.filter_by(name="NHZ").first())
        new_client = Client.create_from_dict({"name": "Nayan HUF", "address": "India", "account_type": "HUF"})
        self.assertEqual("India", new_client.address)
        new_client.address = "Mumbai"
        self.assertEqual(True, new_client.save())  # Will save
        self.assertEqual("Mumbai", Client.objects.filter_by(name="Nayan HUF").first().address)
        # Save after retrieving the objects
        nayan: User = User.objects.cascade.filter_by(name="NHZ").first()
        nayan.name = "Nayan Zaveri"
        self.assertEqual(True, nayan.save())  # Will save on the parent object
        self.assertEqual("Nayan Zaveri", User.get_by_id(nayan.id).name)
        nayan.name = "Nayan"
        nayan.clients[0].address = "Dallas/Fort Worth"
        self.assertEqual(True, nayan.save(cascade=True))  # Will now save on the child object also
        self.assertEqual("Dallas/Fort Worth", Client.objects.filter_by(name="NHZ").first().address)
        self.assertEqual("Nayan", User.get_by_id(nayan.id).name)
        # Link a child object manually without using cascade
        nayan: User = User.objects.filter_by(name="Nayan").first()  # Don"t use cascade here
        nayan.clients.append(new_client.id)
        self.assertEqual(True, nayan.save())  # cascade=True not required here since nayan does not contain Client
        nayan: User = User.objects.cascade.filter_by(name="Nayan").first()  # Use cascade to test nested clients
        self.assertEqual(2, len(nayan.clients))
        self.assertEqual("Nayan HUF", nayan.clients[1].name)

    def test_delete(self) -> None:
        # Test direct delete of object with no child
        deleted_id = Client.objects.filter_by(name="Nayan").delete()
        self.assertNotEqual(str(), deleted_id)  # Will delete
        self.assertIsNone(Client.objects.filter_by(name="Nayan").first())
        # But it leaves a dangling reference in the database
        nayan = User.objects.filter_by(name="Nayan").first()  # Not use cascade so ids are retrieved
        self.assertEqual(1, len(nayan.clients))
        self.assertEqual(deleted_id, nayan.clients[0])
        nayan_whole = User.objects.cascade.filter_by(name="Nayan").first()
        self.assertEqual(0, len(nayan_whole.clients))
        self.assertListEqual(list(), nayan_whole.clients)
        # Fix it by removing the dangling reference
        nayan.clients.remove(deleted_id)
        nayan.save()
        self.assertEqual(0, len(nayan.clients))
        nayan_whole = User.objects.cascade.filter_by(name="Nayan").first()
        self.assertEqual(0, len(nayan_whole.clients))
        # Deleting a child object without using id (Not applicable for many-to-many relationship)
        # 1 Read the parent object with cascade (Needs to be done before Step #2)
        # 2 Delete the child document
        # 3 Remove the child object from the parent object.
        # 4 Save the parent object
        avani = User.objects.cascade.filter_by(name="Avani").first()
        Client.objects.filter_by(name="Crazy Ideas").delete()
        avani.clients.remove(next(client for client in avani.clients if client.name == "Crazy Ideas"))
        avani.save()
        self.assertEqual(2, len(User.objects.filter_by(name="Avani").first().clients))
        # Delete a child object using id
        # 1 Read the parent object without cascade
        # 2 Delete the child document and get its id
        # 3 Remove the deleted id from the parent object
        # 4 Save the parent object
        avani = User.objects.filter_by(name="Avani").first()  # Read without cascade
        deleted_id = Client.objects.filter_by(name="Hiten").delete()
        avani.clients.remove(deleted_id)
        avani.save()
        self.assertEqual(1, len(User.objects.filter_by(name="Avani").first().clients))

    def test_bulk_update(self):
        clients = Client.objects.get()
        for client in clients:
            client.amount_pending += 100
        results = Client.save_all(clients)
        self.assertTrue(all(results))
        self.assertEqual(clients, Client.objects.get())

    def test_filter_map(self):
        clients = Client.objects.filter("address_map.city", "==", "Mumbai").get()
        self.assertEqual(2, len(clients))
        self.assertSetEqual({"Nayan", "Crazy Ideas"}, {client.name for client in clients})

    def test_truncate(self):
        query = Client.objects.filter_by(address="Netherlands")
        query1 = query.filter_by(amount_pending=0)
        query2 = query.filter_by(name="Avani")
        self.assertEqual("Hiten", query1.first().name)
        self.assertEqual("Avani", query2.first().name)
        # With Truncate
        client = Client.objects.truncate.create({
            "name": "Purvi",
            "address": "Mumbai",
            "account_type": "Individual"
        })
        self.assertEqual("Purvi", client.name)
        clients = Client.objects.filter_by(amount_pending=0).get()
        self.assertEqual(2, len(clients))
        Client.objects.filter_by(name="Purvi").delete()
        # Without Truncate
        client = Client.objects.create({
            "name": "Purvi",
            "address": "Mumbai",
            "account_type": "Individual"
        })
        self.assertEqual("Purvi", client.name)
        clients = Client.objects.filter_by(amount_pending=0).get()
        self.assertEqual(3, len(clients))
        Client.objects.filter_by(name="Purvi").delete()
        # Create list of dicts with Truncate
        companies = [
            {"name": "company 1", "account_type": "Company"},
            {"name": "company 2", "account_type": "Company"},
            {"name": "company 3", "account_type": "Company"},
        ]
        clients = Client.objects.truncate.create_all(companies)
        self.assertListEqual(["company 1", "company 2", "company 3"], [client.name for client in clients])
        clients = Client.objects.filter_by(amount_pending=0).get()
        self.assertEqual(2, len(clients))
        Client.objects.filter_by(account_type="Company").delete()
        # Create list of dicts without Truncate
        clients = Client.objects.create_all(companies)
        self.assertListEqual(["company 1", "company 2", "company 3"], [client.name for client in clients])
        clients = Client.objects.filter_by(amount_pending=0).get()
        self.assertEqual(5, len(clients))

    def test_no_orm(self):
        clients = Client.objects.no_orm.filter_by(address="Netherlands").get()
        self.assertSetEqual({"Avani", "Hiten"}, {client["name"] for client in clients})
        self.assertIn("id", clients[0])
        self.assertIn("id", clients[1])
        self.assertEqual(7, len(clients[0]))
        client = Client.objects.no_orm.order_by("amount_pending", Client.objects.ORDER_DESCENDING).first()
        self.assertEqual("Nayan", client["name"])
        self.assertEqual(7, len(client))
        self.assertIn("id", client)
        client = Client.objects.no_orm.create({"name": "Purvi"})
        self.assertEqual("Purvi", client["name"])
        self.assertEqual(0, client["amount_pending"])
        self.assertEqual(7, len(client))
        self.assertIn("id", client)
        Client.objects.filter_by(name="Purvi").delete()
        companies = [
            {"name": "company 1", "account_type": "Company"},
            {"name": "company 2", "account_type": "Company"},
            {"name": "company 3", "account_type": "Company"},
        ]
        clients = Client.objects.no_orm.truncate.create_all(companies)
        self.assertListEqual(["company 1", "company 2", "company 3"], [client["name"] for client in clients])
        self.assertEqual(3, len(clients))
        self.assertIn("id", clients[0])
        self.assertNotIn("amount_pending", clients[1])
        self.assertEqual(3, len(clients[2]))

    def test_save_all(self):
        clients = Client.objects.get()
        clients.sort(key=lambda item: (item.amount_pending, item.name))
        for client in clients:
            client.amount_pending += 100
        clients: List[Client] = Client.objects.save_all(clients)  # Document to Document
        self.assertListEqual([100, 100, 1200, 5100], [client.amount_pending for client in clients])
        # Test save
        clients[0].address = "Bangalore"
        client = Client.objects.no_orm.save(clients[0])  # Document to Dict
        self.assertEqual("Bangalore", client["address"])
        # If one of the ID is corrupted then nothing is changed
        clients[2].set_id("")
        for client in clients:
            client.amount_pending += 100
        clients = Client.objects.save_all(clients)
        self.assertListEqual(list(), clients)
        # Test with no_orm and truncate
        clients: List[dict] = Client.objects.no_orm.get()
        clients.sort(key=lambda item: (item["amount_pending"], item["name"]))
        self.assertEqual([100, 100, 1200, 5100], [client["amount_pending"] for client in clients])
        self.assertIn("id", clients[2])
        # Test with no_orm and truncate
        for client in clients:
            client["amount_pending"] -= 100
        clients: List[dict] = Client.objects.truncate.no_orm.save_all(clients)  # Dict to Dict
        self.assertNotIn("amount_pending", clients[0])
        self.assertNotIn("amount_pending", clients[1])
        self.assertIn("amount_pending", clients[2])
        self.assertIn("amount_pending", clients[3])
        self.assertEqual(4, sum(1 if "id" in client else 0 for client in clients))
        self.assertListEqual([6, 5, 7, 7], [len(client) for client in clients])
        # Test you cannot add a new field in save
        clients[0]["new_field"] = "new data"
        client = Client.objects.no_orm.save(clients[0])
        self.assertNotIn("new_field", client)
        # Test save
        clients[1]["address"] = "Delhi"
        client = Client.objects.save(clients[1])  # Dict to Document
        self.assertEqual("Delhi", client.address)

    def tearDown(self) -> None:
        User.objects.delete()
        Client.objects.delete()
