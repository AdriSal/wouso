from django.contrib.auth.models import User
from django.test.client import Client
from django.test import TestCase
from django.core.urlresolvers import reverse
from wouso.core.scoring.models import Formula
from wouso.core.tests import WousoTest
from wouso.core.magic.models import Spell, SpellHistory

class addPlayerTestCase(TestCase):
    def setUp(self):
        self.user, new = User.objects.get_or_create(username='_test1', is_staff=True, is_superuser=True)
        self.user.set_password('secret')
        self.user.save()

    def test_add_user(self):
        old_number = len(User.objects.all())
        self.client = Client()
        self.client.login(username='_test1', password='secret')
        User.objects.get(pk=1).is_staff
        resp = self.client.post('/cpanel/add_player/', {'username': '_test2', 'password': 'secret'})
        new_number = len(User.objects.all())

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(old_number + 1, new_number)

class CpanelViewsTest(WousoTest):
    def setUp(self):
        super(CpanelViewsTest, self).setUp()
        self.admin = self._get_superuser()
        self.client = Client()
        self.client.login(username='admin', password='admin')

    def test_edit_formula_view_get(self):
        formula = Formula.objects.create(name='test_formula1', definition='points=1234',
                                         description='First formula of the game')
        response = self.client.get(reverse('edit_formula', args=[formula.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="test_formula1"')
        self.assertContains(response, 'value="points=1234"')
        self.assertContains(response, 'First formula of the game')

    def test_edit_formula_view_post(self):
        formula = Formula.objects.create(name='test_formula1', definition='points=1234',
                                         description='First formula of the game')
        data = {'name': 'test_formula2', 'definition': 'points=4321',
                'description': 'Second formula of the game'}
        response = self.client.post(reverse('edit_formula', args=[formula.pk]), data)
        self.assertEqual(response.status_code, 302)
        updated_formula = Formula.objects.get(pk=formula.pk)
        self.assertEqual(updated_formula.name, 'test_formula2')
        self.assertEqual(updated_formula.definition, 'points=4321')
        self.assertEqual(updated_formula.description, 'Second formula of the game')

    def test_add_formula_view_get(self):
        response = self.client.get(reverse('add_formula'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add Formula')
        self.assertContains(response, 'Name:')
        self.assertContains(response, 'Definition:')
        self.assertContains(response, 'Description:')

    def test_add_formula_view_post(self):
        # Check the view with a valid form
        data = {'name': 'test_formula1', 'definition': 'points=4321',
                'description': 'Test Formula'}
        response = self.client.post(reverse('add_formula'), data)
        self.assertEqual(response.status_code, 302)
        formulas = Formula.objects.all()
        self.assertEqual(len(formulas), 1)
        formula = formulas[0]
        self.assertEqual(formula.name, 'test_formula1')
        self.assertEqual(formula.definition, 'points=4321')
        self.assertEqual(formula.description, 'Test Formula')

        # Check the view with an invalid form
        data = {}
        response = self.client.post(reverse('add_formula'), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required')

    def test_spells_view(self):
        spell1 = Spell.objects.create(name='spell1', title='Spell no. 1')
        spell2 = Spell.objects.create(name='spell2', title='Spell no. 2')
        spell3 = Spell.objects.create(name='spell3', title='Spell no. 3')
        user1 = self._get_player(1)
        user2 = self._get_player(2)
        SpellHistory.objects.create(type='b', user_from=user1, spell=spell1)
        SpellHistory.objects.create(type='b', user_from=user1, spell=spell2)
        SpellHistory.objects.create(type='b', user_from=user2, spell=spell1)
        SpellHistory.objects.create(type='u', user_from=user2, user_to=user1,
                                    spell=spell1)
        response = self.client.get(reverse('spells'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Spell no. 1')
        self.assertContains(response, 'Spell no. 2')
        self.assertContains(response, 'Spell no. 3')
        self.assertContains(response, 'Spell History')
        self.assertContains(response, '<td> 1 </td>', 3)
        self.assertContains(response, '<td> 2 </td>')
        self.assertContains(response, '<td> 3 </td>')

    def test_edit_spell_view_get(self):
        spell = Spell.objects.create(name='spell1', title='Spell no. 1')
        response = self.client.get(reverse('edit_spell', args=[spell.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Spell')
        self.assertContains(response, 'spell1')
        self.assertContains(response, 'Spell no. 1')
    
    def test_edit_spell_view_post(self):
        # Check the view with an invalid form
        spell = Spell.objects.create(name='spell1', title='Spell no. 1')
        data = {'name': 'updated_spell', 'title': 'Spell was updated'}
        response = self.client.post(reverse('edit_spell', args=[spell.pk]), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required')

        # Check the view with a valid form
        data.update({'percents': 80, 'level_required': 4,
                     'type': 'o', 'due_days': 5,
                     'price': 40})
        response = self.client.post(reverse('edit_spell', args=[spell.pk]), data)
        spell = Spell.objects.get(pk=spell.pk)
        self.assertEqual(spell.name, 'updated_spell')
        self.assertEqual(spell.title, 'Spell was updated')
