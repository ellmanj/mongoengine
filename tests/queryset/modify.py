import sys
sys.path[0:0] = [""]

import unittest

from mongoengine import connect, Document, IntField

__all__ = ("FindAndModifyTest",)


class Doc(Document):
    id = IntField(primary_key=True)
    value = IntField()


class DocTwo(Document):
    id = IntField(primary_key=True)
    value1 = IntField(default=-1)
    value2 = IntField(default=-1)


class FindAndModifyTest(unittest.TestCase):

    def setUp(self):
        connect(db="mongoenginetest")
        Doc.drop_collection()

    def assertDbEqual(self, docs):
        self.assertEqual(list(Doc._collection.find().sort("id")), docs)

    def assertDbTwoEqual(self, docs):
        self.assertEqual(list(DocTwo._collection.find().sort("id")), docs)

    def test_modify(self):
        Doc(id=0, value=0).save()
        doc = Doc(id=1, value=1).save()

        old_doc = Doc.objects(id=1).modify(set__value=-1)
        self.assertEqual(old_doc.to_json(), doc.to_json())
        self.assertDbEqual([{"_id": 0, "value": 0}, {"_id": 1, "value": -1}])

    def test_modify_with_new(self):
        Doc(id=0, value=0).save()
        doc = Doc(id=1, value=1).save()

        new_doc = Doc.objects(id=1).modify(set__value=-1, new=True)
        doc.value = -1
        self.assertEqual(new_doc.to_json(), doc.to_json())
        self.assertDbEqual([{"_id": 0, "value": 0}, {"_id": 1, "value": -1}])

    def test_modify_not_existing(self):
        Doc(id=0, value=0).save()
        self.assertEqual(Doc.objects(id=1).modify(set__value=-1), None)
        self.assertDbEqual([{"_id": 0, "value": 0}])

    def test_modify_with_upsert(self):
        Doc(id=0, value=0).save()
        old_doc = Doc.objects(id=1).modify(set__value=1, upsert=True)
        self.assertEqual(old_doc, None)
        self.assertDbEqual([{"_id": 0, "value": 0}, {"_id": 1, "value": 1}])

    def test_modify_with_upsert_existing(self):
        Doc(id=0, value=0).save()
        doc = Doc(id=1, value=1).save()

        old_doc = Doc.objects(id=1).modify(set__value=-1, upsert=True)
        self.assertEqual(old_doc.to_json(), doc.to_json())
        self.assertDbEqual([{"_id": 0, "value": 0}, {"_id": 1, "value": -1}])

    def test_modify_with_upsert_with_new(self):
        Doc(id=0, value=0).save()
        new_doc = Doc.objects(id=1).modify(upsert=True, new=True, set__value=1)
        self.assertEqual(new_doc.to_mongo(), {"_id": 1, "value": 1})
        self.assertDbEqual([{"_id": 0, "value": 0}, {"_id": 1, "value": 1}])

    def test_modify_with_remove(self):
        Doc(id=0, value=0).save()
        doc = Doc(id=1, value=1).save()

        old_doc = Doc.objects(id=1).modify(remove=True)
        self.assertEqual(old_doc.to_json(), doc.to_json())
        self.assertDbEqual([{"_id": 0, "value": 0}])

    def test_find_and_modify_with_remove_not_existing(self):
        Doc(id=0, value=0).save()
        self.assertEqual(Doc.objects(id=1).modify(remove=True), None)
        self.assertDbEqual([{"_id": 0, "value": 0}])

    def test_modify_with_order_by(self):
        Doc(id=0, value=3).save()
        Doc(id=1, value=2).save()
        Doc(id=2, value=1).save()
        doc = Doc(id=3, value=0).save()

        old_doc = Doc.objects().order_by("-id").modify(set__value=-1)
        self.assertEqual(old_doc.to_json(), doc.to_json())
        self.assertDbEqual([
            {"_id": 0, "value": 3}, {"_id": 1, "value": 2},
            {"_id": 2, "value": 1}, {"_id": 3, "value": -1}])

    def test_modify_with_fields(self):
        Doc(id=0, value=0).save()
        Doc(id=1, value=1).save()

        old_doc = Doc.objects(id=1).only("id").modify(set__value=-1)
        self.assertEqual(old_doc.to_mongo(), {"_id": 1})
        self.assertDbEqual([{"_id": 0, "value": 0}, {"_id": 1, "value": -1}])

    def test_modify_with_exclude_then_save(self):
        DocTwo(id=0, value1=1, value2=1).save()

        doc = DocTwo.objects(id=0).exclude("value1").modify(set__value2=2)

        # value1 is -1 (the default) on the object, but still 1 in the database
        self.assertEqual(doc.value1, -1)
        self.assertDbTwoEqual([{"_id": 0, "value1": 1, "value2": 2}])

        # calling save() on the object incorrectly writes the default value of value1 to the database
        doc.save()
        self.assertDbTwoEqual([{"_id": 0, "value1": 1, "value2": 2}])

    def test_first_with_exclude_then_save(self):
        DocTwo(id=0, value1=1, value2=1).save()

        doc = DocTwo.objects(id=0).exclude("value1").first()

        # value1 is -1 (the default) on the object, but still 1 in the database
        self.assertEqual(doc.value1, -1)
        self.assertDbTwoEqual([{"_id": 0, "value1": 1, "value2": 1}])

        # calling save() on the object incorrectly writes the default value of value1 to the database
        doc.save()
        self.assertDbTwoEqual([{"_id": 0, "value1": 1, "value2": 1}])


if __name__ == '__main__':
    unittest.main()