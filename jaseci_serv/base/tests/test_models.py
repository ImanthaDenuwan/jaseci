from jaseci.utils.utils import TestCaseHelper
from django.test import TestCase
from django.contrib.auth import get_user_model
from base import models
from obj_api.views import JaseciObjectSerializer
from jaseci import element


def sample_user(email='JSCITEST_user@jaseci.com', password='whatever'):
    """Create a sample user for testing"""
    if(get_user_model().objects.filter(email=email).exists()):
        return get_user_model().objects.get(email=email)
    return get_user_model().objects.create_user(email, password)


class model_tests(TestCaseHelper, TestCase):
    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test_users_based_on_email(self):
        """Tests that users are created based on valid emails"""

        email = 'JSCITEST_blah@BlaB.com'
        password = 'passW123'
        num_nodes = models.JaseciObject.objects.count()
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )
        # This tests that nodes are created/destroyed along side users
        self.assertEqual(num_nodes+1, models.JaseciObject.objects.count())

        self.assertEqual(user.email.split('@')[1], email.split('@')[1].lower())
        self.assertTrue(user.check_password(password))
        user.delete()
        self.assertFalse(get_user_model().objects.filter(id=user.id).exists())
        self.assertEqual(num_nodes, models.JaseciObject.objects.count())

    def test_create_super_user(self):
        """Tests that superuser is created and has the right permissions"""
        user = get_user_model().objects.create_superuser(
            email='JSCITEST_super@User.com',
            password='135jj'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_admin)
        user.delete()
        self.assertFalse(get_user_model().objects.filter(id=user.id).exists())

    def test_jaseci_obj_model_has_relevant_fields(self):
        """Test that Jaseci ORM models has all element class fields"""
        element_obj = element.element(element.mem_hook())
        orm_obj = models.JaseciObject()
        for a in vars(element_obj).keys():
            if not a.startswith('_') and not callable(getattr(element_obj, a)):
                self.assertIn(a, dir(orm_obj))

    def test_jaseci_json_has_relevant_fields(self):
        """Test that Jaseci ORM models has all element class fields"""
        element_obj = element.element(element.mem_hook())
        for a in vars(element_obj).keys():
            if not a.startswith('_') and not callable(getattr(element_obj, a)):
                self.assertIn(a, JaseciObjectSerializer.Meta.fields)

    def test_jaseci_obj_model_create_delete(self):
        """Test that we can create and delete jaseci object models"""
        orm_obj = models.JaseciObject.objects.create(name='test Obj',
                                                     user=sample_user())
        oid = orm_obj.jid
        newname = 'TESTING new Name'
        orm_obj.name = newname
        orm_obj.save()

        loaded = models.JaseciObject.objects.get(name=newname)
        self.assertEqual(loaded.jid, oid)
        self.assertEqual(loaded.name, newname)

        orm_obj.delete()
        self.assertFalse(
            models.JaseciObject.objects.filter(name=newname).exists()
        )

    def test_lookup_global_config(self):
        """Test look up config returns right value"""
        models.GlobalConfig.objects.create(name='testname', value="testval")
        self.assertEqual(models.lookup_global_config('testname'), 'testval')
        self.assertEqual(models.lookup_global_config(
            'nonsense', 'apple'), 'apple')